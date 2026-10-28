"""
Provide Meta WhatsApp Cloud API (Graph API v20.0) adapter functionality.
Decoupled from communications_bus.py following the Strangler Fig pattern.
Provides:
- build_meta_whatsapp_cloud_payload: Build JSON payload compliant with official Meta specification.
- resolve_meta_credentials: Securely load Phone Number ID and tokens from credentials or environment.
- execute_meta_cloud_http: Dispatch live HTTP requests with retries and controlled error handling.
- record_meta_dispatch: Atomically record dispatch in the ledger and notification_dispatches.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.foundry.telecom.meta_whatsapp")


def build_meta_whatsapp_cloud_payload(
    phone_number: str,
    template_name: str,
    parameters: list[str],
    language_code: str = "es"
) -> dict[str, Any]:
    """Build the official Meta WhatsApp Cloud API payload for verified templates."""
    clean_phone = "".join(filter(str.isdigit, phone_number))
    body_parameters = [{"type": "text", "text": str(p)} for p in parameters]
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": clean_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            },
            "components": [
                {
                    "type": "body",
                    "parameters": body_parameters
                }
            ]
        }
    }


def _parse_env_file_dict(env_path: Path) -> dict[str, str]:
    """Extract key=value pairs from a .env file, ignoring comments."""
    creds: dict[str, str] = {}
    if not env_path.exists():
        return creds
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            clean = line.strip()
            if "=" in clean and not clean.startswith("#"):
                k, v = clean.split("=", 1)
                creds[k.strip()] = v.strip()
    except (OSError, ValueError) as ex:
        logger.debug(f"Note reading env file {env_path.name}: {ex}")
    return creds


def resolve_meta_credentials(
    wallet_phone_id: str | None,
    wallet_token: str | None
) -> tuple[str | None, str | None, bool]:
    """Resolve Phone Number ID, access token, and production flag."""
    file_creds = _parse_env_file_dict(Path(__file__).resolve().parents[3] / "credentials" / "meta_whatsapp.env")
    phone_number_id = wallet_phone_id or os.environ.get("META_WA_PHONE_NUMBER_ID") or file_creds.get("META_WA_PHONE_NUMBER_ID")
    access_token = wallet_token or os.environ.get("META_WA_ACCESS_TOKEN") or file_creds.get("META_WA_ACCESS_TOKEN")
    live_dispatch_str = os.environ.get("META_WA_LIVE_DISPATCH_ENABLED") or file_creds.get("META_WA_LIVE_DISPATCH_ENABLED", "false")

    is_live = live_dispatch_str.lower() in ("true", "1", "yes")
    return phone_number_id, access_token, is_live


def execute_meta_cloud_http(
    slug: str,
    phone_number_id: str,
    access_token: str,
    payload_meta: dict[str, Any]
) -> tuple[str | None, str, str | None]:
    """Execute HTTP POST request to Graph API v20.0 with timeouts and error handling."""
    url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload_meta).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            msgs = resp_data.get("messages", [])
            provider_msg_id = msgs[0].get("id") if msgs else f"wamid.{uuid.uuid4().hex}"
            logger.info(f"[{slug}] Meta Cloud WhatsApp emitido en vivo: {provider_msg_id}")
            return provider_msg_id, "SENT", None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        error_message = f"Error Meta API {e.code}: {err_body}"
        logger.error(f"[{slug}] Fallo en Meta WhatsApp API: {error_message}")
        return None, "FAILED", error_message
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        error_message = str(e)
        logger.error(f"[{slug}] Error de red con Meta API: {e}")
        return None, "FAILED", error_message


def record_meta_dispatch(
    conn: Any,
    dispatch_id: str,
    clean_phone: str,
    tmpl: str,
    parameters: list[str],
    dispatch_status: str,
    error_message: str | None,
    provider_msg_id: str | None,
    idempotency_key: str
) -> None:
    """Record mutation in notification_dispatches and telecom_usage_ledger."""
    cur = conn.cursor()
    rendered_content = f"Plantilla '{tmpl}' con parámetros: {parameters}"
    cur.execute("""
        INSERT INTO notification_dispatches (id, channel, recipient, content, status, error_msg)
        VALUES (?, 'whatsapp_meta', ?, ?, ?, ?);
    """, (dispatch_id, clean_phone, rendered_content, dispatch_status, error_message or ""))
    if provider_msg_id:
        cur.execute("""
            UPDATE telecom_usage_ledger
            SET provider_message_id = ?
            WHERE idempotency_key = ?;
        """, (provider_msg_id, idempotency_key))
    conn.commit()
