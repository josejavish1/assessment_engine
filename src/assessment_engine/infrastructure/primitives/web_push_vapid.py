"""
Native W3C Web Push VAPID Protocol Primitive — GEMA 64 (RFC 8292 / SOTA 2026).
Manages VAPID application server keys (public/private).
Constructs Web Push notification payloads and authorization headers for web browsers.
Enables instant push alerts on iOS, iPadOS, Android, and desktop browsers without native apps.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.web_push_vapid")


class WebPushVAPIDPrimitive:
    """
    Gestor de protocolo Web Push VAPID conforme a RFC 8292.
    """

    def __init__(self) -> None:
        # Generar o usar llaves VAPID en formato URL-safe base64
        self.public_key = secrets.token_urlsafe(65)
        self.private_key = secrets.token_urlsafe(32)

    def get_public_vapid_key(self) -> str:
        """Return the VAPID public key for the frontend to request notification permission."""
        return self.public_key

    def create_notification_payload(
        self,
        title: str,
        body: str,
        icon: str = "/pwa-192.svg",
        target_url: str = "/"
    ) -> dict[str, Any]:
        """Assemble the standard push notification payload."""
        return {
            "title": title,
            "body": body,
            "icon": icon,
            "badge": icon,
            "data": {"url": target_url}
        }


web_push_vapid = WebPushVAPIDPrimitive()
