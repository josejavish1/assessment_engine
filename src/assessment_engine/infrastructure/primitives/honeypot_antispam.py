"""
Inject invisible honeypot fields with aria-hidden and negative tabindex, alongside HMAC-SHA256-signed time-based speed traps to mitigate bots without CAPTCHAs (OWASP OAT-017).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any
from assessment_engine.infrastructure.primitives.security import resolve_secret

logger = logging.getLogger("assessment_engine.infrastructure.primitives.honeypot_antispam")

DEFAULT_SECRET = resolve_secret("AUTONOMUOS_ANTISPAM_SECRET")
DEFAULT_MIN_SECONDS = 2.0
DEFAULT_MAX_SECONDS = 86400.0  # 24 horas


class HoneypotAntiSpamPrimitive:
    """
    Filter spam and automated requests transparently for human users (OWASP OAT-017).
    """

    HONEYPOT_FIELD_NAME = "_hp_website_verification"
    TIMESTAMP_FIELD_NAME = "_hp_ts_token"

    def _get_dynamic_field_name(self, ts_str: str, secret: str) -> str:
        """Derive the decoy field name dynamically: _hp_<hmac[:8]>."""
        sig = hmac.new(secret.encode("utf-8"), ts_str.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"_hp_{sig[:8]}"

    def generate_honeypot_input_html(
        self,
        ts_str: str | None = None,
        secret: str = DEFAULT_SECRET,
    ) -> str:
        """Generate the decoy field with -9999px CSS positioning and an optional dynamic field name."""
        field_name = self._get_dynamic_field_name(ts_str, secret) if ts_str else self.HONEYPOT_FIELD_NAME
        # Apply polymorphic CSS obfuscation to evade bots checking for 'opacity: 0' or 'display: none'.
        style = "position: absolute; left: -9999px; transform: scale(0); pointer-events: none;"
        return (
            f'<div style="{style}" aria-hidden="true">\n'
            f'  <label for="{field_name}">Secondary Phone / Fax</label>\n'
            f'  <input type="text" id="{field_name}" name="{field_name}" tabindex="-1" autocomplete="off" />\n'
            f'</div>'
        )

    def generate_timestamp_token(
        self,
        secret: str = DEFAULT_SECRET,
        current_time: float | None = None,
        client_ip: str = "0.0.0.0",
        user_agent: str = "unknown",
    ) -> str:
        """
        Generate an HMAC-SHA256-signed time-based speed trap salted with IP and User-Agent.
        """
        now = time.time() if current_time is None else current_time
        ts_str = f"{now:.4f}"
        payload = f"{ts_str}|{client_ip}|{user_agent}"
        signature = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{ts_str}.{signature}"

    def generate_form_protection_html(
        self,
        secret: str = DEFAULT_SECRET,
        client_ip: str = "0.0.0.0",
        user_agent: str = "unknown",
    ) -> str:
        """
        Emit complete protection payload: rotating decoy honeypot field and hidden input with salted HMAC speed trap.
        """
        token = self.generate_timestamp_token(secret=secret, client_ip=client_ip, user_agent=user_agent)
        ts_str = token.split(".", 1)[0]
        hp_html = self.generate_honeypot_input_html(ts_str=ts_str, secret=secret)
        ts_input = f'<input type="hidden" name="{self.TIMESTAMP_FIELD_NAME}" value="{token}" />'
        return f"{hp_html}\n{ts_input}"

    def verify_timestamp_token(
        self,
        token: str,
        secret: str = DEFAULT_SECRET,
        min_seconds: float = DEFAULT_MIN_SECONDS,
        max_seconds: float = DEFAULT_MAX_SECONDS,
        current_time: float | None = None,
        client_ip: str = "0.0.0.0",
        user_agent: str = "unknown",
    ) -> tuple[bool, str]:
        """
        Verify speed trap validity: IP/UA-salted HMAC signature, minimum elapsed time, and expiration.
        """
        if not token or "." not in token:
            return (False, "INVALID_TOKEN_FORMAT")

        parts = token.rsplit(".", 1)
        ts_str, received_sig = parts[0], parts[1]

        payload = f"{ts_str}|{client_ip}|{user_agent}"
        expected_sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, received_sig):
            return (False, "TAMPERED_SIGNATURE")

        try:
            ts_float = float(ts_str)
        except ValueError:
            return (False, "INVALID_TIMESTAMP_VALUE")

        now = time.time() if current_time is None else current_time
        elapsed = now - ts_float

        if elapsed < min_seconds:
            logger.warning(f"[Honeypot] Speed-trap activada: Formulario enviado en {elapsed:.2f}s (< {min_seconds}s)")
            return (False, "SPEED_TRAP_TRIGGERED")

        if elapsed > max_seconds:
            logger.info(f"[Honeypot] Token de formulario expirado tras {elapsed:.1f}s (> {max_seconds}s)")
            return (False, "EXPIRED_TIMESTAMP_TOKEN")

        return (True, "VALID")

    def validate_submission(
        self,
        form_data: dict[str, Any],
        secret: str = DEFAULT_SECRET,
        min_seconds: float = DEFAULT_MIN_SECONDS,
        max_seconds: float = DEFAULT_MAX_SECONDS,
        current_time: float | None = None,
        client_ip: str = "0.0.0.0",
        user_agent: str = "unknown",
    ) -> tuple[bool, str]:
        """
        Validate the form submission against the dynamic honeypot and salted HMAC speed trap.
        """
        # 1. Check speed trap if the token is present.
        token = form_data.get(self.TIMESTAMP_FIELD_NAME)
        ts_str = None
        if token is not None:
            token_str = str(token)
            is_valid_ts, ts_reason = self.verify_timestamp_token(
                token=token_str,
                secret=secret,
                min_seconds=min_seconds,
                max_seconds=max_seconds,
                current_time=current_time,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            if not is_valid_ts:
                return (False, ts_reason)
            ts_str = token_str.rsplit(".", 1)[0]

        field_name = self._get_dynamic_field_name(ts_str, secret) if ts_str else self.HONEYPOT_FIELD_NAME
        
        # Check both dynamic and legacy fallback fields.
        for fname in (field_name, self.HONEYPOT_FIELD_NAME):
            val = form_data.get(fname)
            if val is not None and str(val).strip() != "":
                logger.warning(f"[Honeypot] Bot capturado con señuelo {fname}: '{str(val)[:30]}'")
                return (False, "HONEYPOT_FIELD_FILLED")

        return (True, "CLEAN_HUMAN")

    def is_spam(
        self,
        form_data: dict[str, Any],
        secret: str | None = None,
        min_seconds: float = DEFAULT_MIN_SECONDS,
        max_seconds: float = DEFAULT_MAX_SECONDS,
        current_time: float | None = None,
    ) -> bool:
        """Determine whether the submission originates from a bot.
Maintain strict backward compatibility with the previous API."""
        active_secret = secret or DEFAULT_SECRET
        is_clean, _ = self.validate_submission(
            form_data=form_data,
            secret=active_secret,
            min_seconds=min_seconds,
            max_seconds=max_seconds,
            current_time=current_time,
        )
        return not is_clean


honeypot_antispam = HoneypotAntiSpamPrimitive()

__all__ = [
    "DEFAULT_MAX_SECONDS",
    "DEFAULT_MIN_SECONDS",
    "DEFAULT_SECRET",
    "HoneypotAntiSpamPrimitive",
    "honeypot_antispam",
]
