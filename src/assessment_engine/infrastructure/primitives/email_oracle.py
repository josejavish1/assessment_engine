"""
Transactional Email & SMTP Verification Oracle — GEMA 19 (Mailpit / SOTA 2026).
Simulates and tests transactional email delivery (confirmations, invoices, password resets).
Enables deterministic unit testing of outgoing emails without sending real messages to the internet.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("assessment_engine.infrastructure.primitives.email_oracle")


@dataclass
class OutgoingEmail:
    to_address: str
    from_address: str
    subject: str
    html_body: str
    text_body: str = ""


class EmailOraclePrimitive:
    """
    Provide a transactional email oracle for testing and development.
    """

    def __init__(self) -> None:
        self.sent_mailbox: list[OutgoingEmail] = []

    def send_email(self, email: OutgoingEmail) -> bool:
        """Simulate sending an email and capture it in the test mailbox."""
        if not email.to_address or "@" not in email.to_address:
            logger.warning(f"[EmailOracle] Dirección de destino inválida: '{email.to_address}'")
            return False

        self.sent_mailbox.append(email)
        logger.info(f"[EmailOracle] Correo enviado a '{email.to_address}': {email.subject}")
        return True

    def find_emails_to(self, to_address: str) -> list[OutgoingEmail]:
        """Busca correos enviados a un destinatario."""
        return [m for m in self.sent_mailbox if m.to_address.lower() == to_address.lower()]

    def clear(self) -> None:
        """Clear the mailbox."""
        self.sent_mailbox.clear()


email_oracle = EmailOraclePrimitive()
