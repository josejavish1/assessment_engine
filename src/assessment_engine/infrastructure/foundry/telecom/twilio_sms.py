"""
Provide a Twilio B2B SMS messaging adapter decoupled from communications_bus.py following the Strangler Fig pattern. Key functions:
- resolve_twilio_credentials: Load SID/Token credentials and regulated sender.
- execute_twilio_dispatch: Dispatch HTTP Basic Auth requests to the official Twilio REST API v2010.
- record_sms_dispatch: Atomically record in notification_dispatches and telecom_usage_ledger.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.foundry.telecom.twilio_sms")


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


def resolve_twilio_credentials() -> tuple[str | None, str | None, str | None, bool]:
    """Load Twilio SMS credentials securely."""
    file_creds = _parse_env_file_dict(Path(__file__).resolve().parents[3] / "credentials" / "twilio.env")
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID") or file_creds.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN") or file_creds.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER") or file_creds.get("TWILIO_FROM_NUMBER")
    live_dispatch_str = os.environ.get("TWILIO_LIVE_DISPATCH_ENABLED") or file_creds.get("TWILIO_LIVE_DISPATCH_ENABLED", "false")

    is_live_enabled = live_dispatch_str.lower() in ("true", "1", "yes")
    return account_sid, auth_token, from_number, is_live_enabled


def execute_twilio_dispatch(
    slug: str,
    clean_phone: str,
    message_text: str,
    account_sid: str | None,
    auth_token: str | None,
    from_sender: str,
    is_live_enabled: bool
) -> tuple[str | None, str, str | None]:
    """Execute SMS dispatch via the Twilio REST API or generate a mock identifier in sandbox mode."""
    provider_msg_id = None
    dispatch_status = "SENT"
    error_message = None

    if not (account_sid and auth_token):
        return provider_msg_id, dispatch_status, error_message

    if is_live_enabled:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        auth_header = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")

        post_data = urllib.parse.urlencode({
            "To": f"+{clean_phone}" if not clean_phone.startswith("+") else clean_phone,
            "From": from_sender,
            "Body": message_text
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=post_data,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                provider_msg_id = resp_data.get("sid")
                logger.info(f"[{slug}] Twilio LIVE SMS emitido con éxito. SID={provider_msg_id}")
        except urllib.error.HTTPError as e:
            dispatch_status = "FAILED"
            err_body = e.read().decode("utf-8")
            error_message = f"Error Twilio {e.code}: {err_body}"
            logger.error(f"[{slug}] Fallo en Twilio API: {error_message}")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            dispatch_status = "FAILED"
            error_message = str(e)
            logger.error(f"[{slug}] Error de red con Twilio: {e}")
    else:
        provider_msg_id = f"SMsandbox_{uuid.uuid4().hex[:16]}"
        logger.info(
            f"[{slug}] Twilio Sandbox (Cuota Protegida): SMS simulado hacia '+{clean_phone}'. "
            "Active TWILIO_LIVE_DISPATCH_ENABLED=true para envío físico real."
        )

    return provider_msg_id, dispatch_status, error_message


def record_sms_dispatch(
    conn: Any,
    dispatch_id: str,
    clean_phone: str,
    message_text: str,
    dispatch_status: str,
    error_message: str | None,
    provider_msg_id: str | None,
    ledger_id: int | str
) -> None:
    """Record SMS dispatch in notification_dispatches and update the usage ledger."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notification_dispatches (id, channel, recipient, content, status, error_msg)
        VALUES (?, 'sms', ?, ?, ?, ?);
    """, (dispatch_id, clean_phone, message_text, dispatch_status, error_message or ""))
    if provider_msg_id:
        cur.execute("""
            UPDATE telecom_usage_ledger
            SET provider_message_id = ?
            WHERE ledger_id = ?;
        """, (provider_msg_id, ledger_id))
    conn.commit()
