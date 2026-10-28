"""
Dispatch signed webhooks and transactional emails. Decoupled from communications_bus.py following the Strangler Fig pattern. Provides:
- dispatch_signed_webhook: HMAC-SHA256 cryptographic signing with X-Autonomuos-Signature header.
- dispatch_transactional_email: Rendered email delivery via EmailOracle.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import uuid
from typing import Any

from assessment_engine.infrastructure.primitives.email_oracle import email_oracle, OutgoingEmail

logger = logging.getLogger("assessment_engine.infrastructure.foundry.telecom.webhooks")


def dispatch_signed_webhook(
    target_url: str,
    event_name: str,
    payload_data: dict[str, Any],
    webhook_secret: str = "whsec_autonomuos_default_32"
) -> dict[str, Any]:
    """Prepare and sign an outgoing webhook with an X-Autonomuos-Signature header."""
    dispatch_id = f"WH-{uuid.uuid4().hex[:10].upper()}"
    timestamp = int(time.time())
    json_body = json.dumps(payload_data, ensure_ascii=False)

    signed_payload = f"{timestamp}.{json_body}".encode("utf-8")
    sig = hmac.new(webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    signature_header = f"t={timestamp},v1={sig}"

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Autonomuos-Communications-Bus/1.0",
        "X-Autonomuos-Event": event_name,
        "X-Autonomuos-Delivery": dispatch_id,
        "X-Autonomuos-Signature": signature_header
    }

    return {
        "dispatch_id": dispatch_id,
        "target_url": target_url,
        "event_name": event_name,
        "headers": headers,
        "body": json_body,
        "status": "PREPARED"
    }


def dispatch_transactional_email_adapter(
    conn: Any,
    slug: str,
    to_email: str,
    subject: str,
    html_body: str,
    from_email: str = "notificaciones@autonomuos.app"
) -> tuple[str, str]:
    """Dispatch a transactional email and persist it to notification_dispatches."""
    dispatch_id = f"EML-{uuid.uuid4().hex[:10].upper()}"
    mail = OutgoingEmail(
        to_address=to_email,
        from_address=from_email,
        subject=subject,
        html_body=html_body
    )
    ok = email_oracle.send_email(mail)
    status = "SENT" if ok else "FAILED"

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO notification_dispatches (id, channel, recipient, subject, content, status)
        VALUES (?, 'email', ?, ?, ?, ?);
    """, (dispatch_id, to_email, subject, html_body, status))
    conn.commit()
    logger.info(f"[{slug}] Email #{dispatch_id} ({subject}) despachado para '{to_email}' ({status})")
    return dispatch_id, status
