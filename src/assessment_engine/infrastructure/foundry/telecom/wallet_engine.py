"""
Manage B2B telecom wallets and financial arbitrage. Decoupled from communications_bus.py following the Strangler Fig pattern.
Provides:
- TelecomWalletEngine: Balance management, automatic top-ups with Veri*Factu invoices, and an immutable ledger.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.foundry.telecom.models import (
    TelecomWallet,
    TelecomLedgerEntry,
    RechargeInvoice,
    SMS_WHOLESALE_COST_CENTS,
    SMS_RETAIL_PRICE_CENTS,
    SMS_NET_MARGIN_CENTS,
    DEFAULT_WALLET_THRESHOLD_CENTS,
    DEFAULT_WALLET_RECHARGE_CENTS,
)

logger = logging.getLogger("assessment_engine.infrastructure.foundry.telecom.wallet_engine")


class TelecomWalletEngine:
    """Manage telecom wallets and legal Veri*Factu invoicing."""

    def __init__(self, db_conn_factory: Any) -> None:
        self._get_db = db_conn_factory

    def get_or_create_wallet(self, slug: str, tenant_id: str = "default") -> TelecomWallet:
        """Retrieve or initialize the telecom wallet for the tenant."""
        conn = self._get_db(slug)
        cur = conn.cursor()
        now_ts = time.time()
        try:
            cur.execute("SELECT * FROM telecom_wallets WHERE tenant_id = ?;", (tenant_id,))
            row = cur.fetchone()
            if row:
                return TelecomWallet(
                    tenant_id=row["tenant_id"],
                    balance_cents=row["balance_cents"],
                    threshold_cents=row["threshold_cents"],
                    recharge_amount_cents=row["recharge_amount_cents"],
                    auto_recharge_enabled=bool(row["auto_recharge_enabled"]),
                    stripe_customer_id=row["stripe_customer_id"],
                    stripe_payment_method_id=row["stripe_payment_method_id"],
                    sender_id=row["sender_id"],
                    whatsapp_mode=row["whatsapp_mode"],
                    whatsapp_phone=row["whatsapp_phone"],
                    whatsapp_status=row["whatsapp_status"],
                    whatsapp_phone_number_id=row["whatsapp_phone_number_id"] if "whatsapp_phone_number_id" in row.keys() else None,
                    whatsapp_access_token=row["whatsapp_access_token"] if "whatsapp_access_token" in row.keys() else None,
                    whatsapp_waba_id=row["whatsapp_waba_id"] if "whatsapp_waba_id" in row.keys() else None,
                    whatsapp_template_name=row["whatsapp_template_name"] if "whatsapp_template_name" in row.keys() and row["whatsapp_template_name"] else "recordatorio_cita",
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            cur.execute("""
                INSERT INTO telecom_wallets (
                    tenant_id, balance_cents, threshold_cents, recharge_amount_cents,
                    auto_recharge_enabled, sender_id, whatsapp_mode, whatsapp_status,
                    created_at, updated_at
                ) VALUES (?, 0, ?, ?, 1, 'AVISO', 'none', 'DISCONNECTED', ?, ?);
            """, (tenant_id, DEFAULT_WALLET_THRESHOLD_CENTS, DEFAULT_WALLET_RECHARGE_CENTS, now_ts, now_ts))
            conn.commit()
            return TelecomWallet(
                tenant_id=tenant_id,
                balance_cents=0,
                threshold_cents=DEFAULT_WALLET_THRESHOLD_CENTS,
                recharge_amount_cents=DEFAULT_WALLET_RECHARGE_CENTS,
                auto_recharge_enabled=True,
                sender_id="AVISO",
                whatsapp_mode="none",
                whatsapp_status="DISCONNECTED",
                created_at=now_ts,
                updated_at=now_ts,
            )
        finally:
            conn.close()

    def update_wallet_settings(
        self,
        slug: str,
        tenant_id: str,
        threshold_cents: int | None = None,
        recharge_amount_cents: int | None = None,
        auto_recharge_enabled: bool | None = None,
        sender_id: str | None = None,
        stripe_payment_method_id: str | None = None,
    ) -> TelecomWallet:
        """Update operational wallet parameters (threshold, alphanumeric sender ID, payment card)."""
        current = self.get_or_create_wallet(slug, tenant_id)
        now_ts = time.time()

        new_thresh = threshold_cents if threshold_cents is not None else current.threshold_cents
        new_recharge = recharge_amount_cents if recharge_amount_cents is not None else current.recharge_amount_cents
        new_auto = auto_recharge_enabled if auto_recharge_enabled is not None else current.auto_recharge_enabled
        new_pm = stripe_payment_method_id if stripe_payment_method_id is not None else current.stripe_payment_method_id

        clean_sender = current.sender_id
        if sender_id:
            clean_sender = "".join(c for c in sender_id.upper() if c.isalnum())[:11]
            if not clean_sender:
                clean_sender = "AVISO"

        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE telecom_wallets
                SET threshold_cents = ?, recharge_amount_cents = ?, auto_recharge_enabled = ?,
                    sender_id = ?, stripe_payment_method_id = ?, updated_at = ?
                WHERE tenant_id = ?;
            """, (new_thresh, new_recharge, int(new_auto), clean_sender, new_pm, now_ts, tenant_id))
            conn.commit()
        finally:
            conn.close()

        return self.get_or_create_wallet(slug, tenant_id)

    def recharge_wallet(
        self,
        slug: str,
        tenant_id: str,
        amount_cents: int = DEFAULT_WALLET_RECHARGE_CENTS,
        stripe_charge_id: str | None = None,
        tax_rate_percent: float = 21.0,
    ) -> tuple[TelecomWallet, RechargeInvoice]:
        """Top up the wallet balance and issue a verifiable digital invoice in SQLite WAL."""
        if amount_cents <= 0:
            raise ValueError("El importe de recarga debe ser estrictamente positivo.")

        now_ts = time.time()
        charge_id = stripe_charge_id or f"ch_mock_{uuid.uuid4().hex[:16]}"
        invoice_id = f"INV-TEL-{uuid.uuid4().hex[:8].upper()}"
        inv_number = f"FAC-TEL-{int(now_ts)}-{uuid.uuid4().hex[:4].upper()}"

        tax_cents = int(round(amount_cents * (tax_rate_percent / 100.0)))
        total_cents = amount_cents + tax_cents

        verifactu_qr = (
            f"https://verify.soverik.com/verifactu/fiscal-seal?"
            f"tenant={tenant_id}&num={inv_number}&date={time.strftime('%Y-%m-%d', time.gmtime(now_ts))}&total={total_cents/100:.2f}"
        )

        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE telecom_wallets
                SET balance_cents = balance_cents + ?, updated_at = ?
                WHERE tenant_id = ?;
            """, (amount_cents, now_ts, tenant_id))

            cur.execute("""
                INSERT INTO telecom_recharge_invoices (
                    invoice_id, tenant_id, amount_cents, tax_cents, total_cents,
                    stripe_charge_id, invoice_number, verifactu_qr_payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                invoice_id, tenant_id, amount_cents, tax_cents, total_cents,
                charge_id, inv_number, verifactu_qr, now_ts
            ))
            conn.commit()
        finally:
            conn.close()

        updated_wallet = self.get_or_create_wallet(slug, tenant_id)
        invoice = RechargeInvoice(
            invoice_id=invoice_id,
            tenant_id=tenant_id,
            amount_cents=amount_cents,
            tax_cents=tax_cents,
            total_cents=total_cents,
            stripe_charge_id=charge_id,
            invoice_number=inv_number,
            verifactu_qr_payload=verifactu_qr,
            created_at=now_ts,
        )
        logger.info(f"[{slug}] Monedero recargado con {amount_cents/100:.2f}€. Nuevo saldo: {updated_wallet.balance_cents/100:.2f}€ (Factura {inv_number})")
        return updated_wallet, invoice

    def deduct_telecom_usage(
        self,
        slug: str,
        tenant_id: str,
        channel: str,
        recipient_phone: str,
        idempotency_key: str,
    ) -> TelecomLedgerEntry:
        """Deduct balance from the wallet and record an immutable ledger entry with arbitrage."""
        conn = self._get_db(slug)
        cur = conn.cursor()
        now_ts = time.time()

        clean_phone = "".join(filter(str.isdigit, recipient_phone))
        recipient_hash = hashlib.sha256(f"salt_telecom_{clean_phone}".encode("utf-8")).hexdigest()

        try:
            cur.execute("SELECT * FROM telecom_usage_ledger WHERE idempotency_key = ?;", (idempotency_key,))
            existing = cur.fetchone()
            if existing:
                logger.info(f"[{slug}] Idempotency hit en telecom ledger para key='{idempotency_key}'")
                return TelecomLedgerEntry(
                    ledger_id=existing["ledger_id"],
                    tenant_id=existing["tenant_id"],
                    channel=existing["channel"],
                    recipient_hash=existing["recipient_hash"],
                    cost_cents=existing["cost_cents"],
                    price_cents=existing["price_cents"],
                    margin_cents=existing["margin_cents"],
                    idempotency_key=existing["idempotency_key"],
                    status=existing["status"],
                    provider_message_id=existing["provider_message_id"],
                    created_at=existing["created_at"],
                )

            if channel == "sms":
                cost = SMS_WHOLESALE_COST_CENTS
                price = SMS_RETAIL_PRICE_CENTS
                margin = SMS_NET_MARGIN_CENTS
            else:
                cost = 0
                price = 0
                margin = 0

            wallet = self.get_or_create_wallet(slug, tenant_id)
            if price > 0:
                if wallet.balance_cents < price:
                    if wallet.auto_recharge_enabled:
                        logger.info(f"[{slug}] Saldo insuficiente ({wallet.balance_cents}c < {price}c). Disparando Silent Top-Up desatendido...")
                        wallet, _ = self.recharge_wallet(
                            slug=slug,
                            tenant_id=tenant_id,
                            amount_cents=wallet.recharge_amount_cents,
                            stripe_charge_id=f"ch_auto_{uuid.uuid4().hex[:12]}"
                        )
                    else:
                        raise ValueError(f"Saldo insuficiente en monedero telecom ({wallet.balance_cents/100:.2f} €) para emitir SMS ({price/100:.2f} €).")

                cur.execute("""
                    UPDATE telecom_wallets
                    SET balance_cents = balance_cents - ?, updated_at = ?
                    WHERE tenant_id = ?;
                """, (price, now_ts, tenant_id))

            ledger_id = f"TX-{uuid.uuid4().hex[:12].upper()}"
            msg_id = f"msg_{uuid.uuid4().hex[:16]}"
            cur.execute("""
                INSERT INTO telecom_usage_ledger (
                    ledger_id, tenant_id, channel, recipient_hash, cost_cents,
                    price_cents, margin_cents, idempotency_key, status,
                    provider_message_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DELIVERED', ?, ?);
            """, (
                ledger_id, tenant_id, channel, recipient_hash, cost, price,
                margin, idempotency_key, msg_id, now_ts
            ))
            conn.commit()

            new_balance = wallet.balance_cents - price
            if wallet.auto_recharge_enabled and new_balance < wallet.threshold_cents:
                try:
                    self.recharge_wallet(
                        slug=slug,
                        tenant_id=tenant_id,
                        amount_cents=wallet.recharge_amount_cents,
                        stripe_charge_id=f"ch_auto_{uuid.uuid4().hex[:12]}"
                    )
                except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:
                    logger.error(f"[{slug}] Fallo en recarga automática preventiva: {e}")

            return TelecomLedgerEntry(
                ledger_id=ledger_id,
                tenant_id=tenant_id,
                channel=channel,
                recipient_hash=recipient_hash,
                cost_cents=cost,
                price_cents=price,
                margin_cents=margin,
                idempotency_key=idempotency_key,
                status="DELIVERED",
                provider_message_id=msg_id,
                created_at=now_ts,
            )
        finally:
            conn.close()

    def get_wallet_ledger_history(self, slug: str, tenant_id: str = "default", limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve telecom usage transaction history."""
        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT * FROM telecom_usage_ledger
                WHERE tenant_id = ?
                ORDER BY created_at DESC
                LIMIT ?;
            """, (tenant_id, limit))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
