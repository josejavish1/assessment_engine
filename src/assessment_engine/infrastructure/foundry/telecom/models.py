"""
Define telecommunications typed models and constants. Decoupled from communications_bus.py following the Strangler Fig pattern. Provides:
- TelecomWallet: Tenant wallet structure.
- TelecomLedgerEntry: Immutable consumption ledger entry.
- RechargeInvoice: Legal Veri*Factu invoice issued after a recharge.
- DispatchResult: Unified message dispatch result.
- MessageTemplate: Transactional template definition.
- B2B arbitrage rates and constants.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# Standard telecom arbitrage costs and rates (in euro cents).
SMS_WHOLESALE_COST_CENTS = 38      # 0,038 € coste mayorista
SMS_RETAIL_PRICE_CENTS = 80        # €0.080 rate billed to the customer.
SMS_NET_MARGIN_CENTS = 42          # +0,042 € margen limpio por mensaje (+110% markup)

DEFAULT_WALLET_THRESHOLD_CENTS = 500       # €5.00 auto-recharge trigger threshold.
DEFAULT_WALLET_RECHARGE_CENTS = 2500       # €25.00 auto-recharge amount.


@dataclass(frozen=True)
class MessageTemplate:
    id: str
    channel: str  # "whatsapp", "email", "sms"
    name: str
    body: str
    variables: list[str]
    is_active: bool = True


@dataclass(frozen=True)
class TelecomWallet:
    tenant_id: str
    balance_cents: int
    threshold_cents: int = DEFAULT_WALLET_THRESHOLD_CENTS
    recharge_amount_cents: int = DEFAULT_WALLET_RECHARGE_CENTS
    auto_recharge_enabled: bool = True
    stripe_customer_id: str | None = None
    stripe_payment_method_id: str | None = None
    sender_id: str = "AVISO"
    whatsapp_mode: str = "none"  # "qr" | "meta" | "none"
    whatsapp_phone: str | None = None
    whatsapp_status: str = "DISCONNECTED"  # "DISCONNECTED" | "PAIRING" | "CONNECTED"
    whatsapp_phone_number_id: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_waba_id: str | None = None
    whatsapp_template_name: str = "recordatorio_cita"
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        d = asdict(self)
        d["balance_formatted"] = f"{self.balance_cents / 100:.2f} €"
        d["threshold_formatted"] = f"{self.threshold_cents / 100:.2f} €"
        d["recharge_amount_formatted"] = f"{self.recharge_amount_cents / 100:.2f} €"
        return d


@dataclass(frozen=True)
class TelecomLedgerEntry:
    ledger_id: str
    tenant_id: str
    channel: str  # "sms" | "whatsapp_qr" | "whatsapp_meta" | "email"
    recipient_hash: str
    cost_cents: int
    price_cents: int
    margin_cents: int
    idempotency_key: str
    status: str  # "DELIVERED" | "FAILED" | "PENDING"
    provider_message_id: str | None = None
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return asdict(self)


@dataclass(frozen=True)
class RechargeInvoice:
    invoice_id: str
    tenant_id: str
    amount_cents: int
    tax_cents: int
    total_cents: int
    stripe_charge_id: str
    invoice_number: str
    verifactu_qr_payload: str
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return asdict(self)


@dataclass
class DispatchResult:
    dispatch_id: str
    channel: str  # "whatsapp", "email", "webhook", "sms"
    recipient: str
    status: str   # "SENT", "QUEUED", "FAILED"
    payload: dict[str, Any]
    error_message: str | None = None
