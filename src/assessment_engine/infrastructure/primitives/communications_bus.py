"""
Communications Bus Primitive — GEMA 14 / Radar Primitive 14 (RFC-014 SOTA).
Unified multichannel dispatching engine: WhatsApp Web QR ($0.00), Meta WhatsApp Cloud,
Managed Telecom Wallet (SMS Arbitrage with ~100% markup), Transactional Email and Signed Webhooks.
Template variable interpolation ({{name}}, {{date}}) with delivery tracking in app.db (SQLite WAL).
Stripe-grade HMAC-SHA256 signature headers (X-Autonomuos-Signature) for outgoing webhooks.
GDPR-compliant anonymized ledger using SHA-256 recipient phone hashes.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import time
import urllib.parse
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.email_oracle import email_oracle, OutgoingEmail
from assessment_engine.infrastructure.foundry.telecom.meta_whatsapp import (
    build_meta_whatsapp_cloud_payload as _telecom_build_meta_payload,
    resolve_meta_credentials as _telecom_resolve_meta_creds,
    execute_meta_cloud_http as _telecom_exec_meta_http,
    record_meta_dispatch as _telecom_record_meta_dispatch,
)
from assessment_engine.infrastructure.foundry.telecom.twilio_sms import (
    resolve_twilio_credentials as _telecom_resolve_twilio_creds,
    execute_twilio_dispatch as _telecom_exec_twilio_dispatch,
    record_sms_dispatch as _telecom_record_sms_dispatch,
)
from assessment_engine.infrastructure.foundry.telecom.whatsapp_qr import (
    generate_whatsapp_qr_session as _telecom_gen_qr,
    request_whatsapp_pairing_code as _telecom_req_pair,
    confirm_whatsapp_pairing as _telecom_confirm_pair,
    disconnect_whatsapp as _telecom_disconnect_wa,
)
from assessment_engine.infrastructure.foundry.telecom.webhooks import (
    dispatch_signed_webhook as _telecom_dispatch_webhook,
    dispatch_transactional_email_adapter as _telecom_dispatch_email,
)

from assessment_engine.infrastructure.foundry.telecom.models import (
    SMS_WHOLESALE_COST_CENTS,
    SMS_RETAIL_PRICE_CENTS,
    SMS_NET_MARGIN_CENTS,
    DEFAULT_WALLET_THRESHOLD_CENTS,
    DEFAULT_WALLET_RECHARGE_CENTS,
    MessageTemplate,
    TelecomWallet,
    TelecomLedgerEntry,
    RechargeInvoice,
    DispatchResult,
)
from assessment_engine.infrastructure.foundry.telecom.wallet_engine import TelecomWalletEngine

logger = logging.getLogger("assessment_engine.infrastructure.primitives.communications_bus")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))


class CommunicationsBusPrimitive:
    """
    Dispatch multichannel notifications with a wallet managed in SQLite WAL (RFC-014).
    """

    def __init__(self, workspaces_dir: Path | None = None) -> None:
        self.workspaces_dir = workspaces_dir or WORKSPACES_DIR
        self._wallet_engine = TelecomWalletEngine(self._get_db)

    def _get_db(self, slug: str) -> sqlite3.Connection:
        db_path = self.workspaces_dir / slug / "app.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notification_dispatches (
                id TEXT PRIMARY KEY,
                channel TEXT NOT NULL,
                recipient TEXT NOT NULL,
                subject TEXT DEFAULT '',
                content TEXT NOT NULL,
                status TEXT NOT NULL,
                error_msg TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telecom_wallets (
                tenant_id TEXT PRIMARY KEY,
                balance_cents INTEGER NOT NULL DEFAULT 0,
                threshold_cents INTEGER NOT NULL DEFAULT 500,
                recharge_amount_cents INTEGER NOT NULL DEFAULT 2500,
                auto_recharge_enabled INTEGER NOT NULL DEFAULT 1,
                stripe_customer_id TEXT,
                stripe_payment_method_id TEXT,
                sender_id TEXT NOT NULL DEFAULT 'AVISO',
                whatsapp_mode TEXT NOT NULL DEFAULT 'none',
                whatsapp_phone TEXT,
                whatsapp_status TEXT NOT NULL DEFAULT 'DISCONNECTED',
                whatsapp_phone_number_id TEXT,
                whatsapp_access_token TEXT,
                whatsapp_waba_id TEXT,
                whatsapp_template_name TEXT DEFAULT 'recordatorio_cita',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
        """)
        for col_name, col_type in [
            ("whatsapp_phone_number_id", "TEXT"),
            ("whatsapp_access_token", "TEXT"),
            ("whatsapp_waba_id", "TEXT"),
            ("whatsapp_template_name", "TEXT DEFAULT 'recordatorio_cita'"),
        ]:
            try:
                cur.execute(f"ALTER TABLE telecom_wallets ADD COLUMN {col_name} {col_type};")
            except sqlite3.OperationalError:
                pass
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telecom_usage_ledger (
                ledger_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                recipient_hash TEXT NOT NULL,
                cost_cents INTEGER NOT NULL,
                price_cents INTEGER NOT NULL,
                margin_cents INTEGER NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                provider_message_id TEXT,
                created_at REAL NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telecom_recharge_invoices (
                invoice_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL,
                tax_cents INTEGER NOT NULL,
                total_cents INTEGER NOT NULL,
                stripe_charge_id TEXT NOT NULL,
                invoice_number TEXT NOT NULL UNIQUE,
                verifactu_qr_payload TEXT NOT NULL,
                created_at REAL NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        return conn

    def render_template(self, template_str: str, variables: dict[str, Any]) -> str:
        """Sustituye variables con sintaxis {{variable}}."""
        rendered = template_str
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered


    def get_or_create_wallet(self, slug: str, tenant_id: str = "default") -> TelecomWallet:
        """Retrieve or initialize the telecom wallet for the tenant."""
        return self._wallet_engine.get_or_create_wallet(slug, tenant_id)

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
        """Update wallet operational parameters (threshold, alphanumeric sender, card)."""
        return self._wallet_engine.update_wallet_settings(
            slug, tenant_id, threshold_cents, recharge_amount_cents,
            auto_recharge_enabled, sender_id, stripe_payment_method_id
        )

    def recharge_wallet(
        self,
        slug: str,
        tenant_id: str,
        amount_cents: int = DEFAULT_WALLET_RECHARGE_CENTS,
        stripe_charge_id: str | None = None,
    ) -> tuple[TelecomWallet, RechargeInvoice]:
        """Recharge the wallet balance and issue a legal Veri*Factu invoice in SQLite WAL."""
        return self._wallet_engine.recharge_wallet(slug, tenant_id, amount_cents, stripe_charge_id)

    def deduct_telecom_usage(
        self,
        slug: str,
        tenant_id: str,
        channel: str,
        recipient_phone: str,
        idempotency_key: str,
    ) -> TelecomLedgerEntry:
        """Deduct wallet balance by recording an immutable ledger entry with arbitrage."""
        return self._wallet_engine.deduct_telecom_usage(slug, tenant_id, channel, recipient_phone, idempotency_key)

    def get_wallet_ledger_history(
        self,
        slug: str,
        tenant_id: str = "default",
        limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return the audited telecom usage history for the tenant."""
        return self._wallet_engine.get_wallet_ledger_history(slug, tenant_id, limit)


    def generate_whatsapp_qr_session(self, slug: str, tenant_id: str = "default") -> dict[str, Any]:
        """Initiate a multi-device pairing session and emit a QR code to scan within 10s."""
        self.get_or_create_wallet(slug, tenant_id)
        conn = self._get_db(slug)
        try:
            return _telecom_gen_qr(conn, tenant_id)
        finally:
            conn.close()

    def request_whatsapp_pairing_code(
        self,
        slug: str,
        tenant_id: str,
        phone_number: str
    ) -> dict[str, Any]:
        """Generate an 8-character pairing code to link WhatsApp directly from mobile."""
        self.get_or_create_wallet(slug, tenant_id)
        conn = self._get_db(slug)
        try:
            res = _telecom_req_pair(conn, tenant_id, phone_number)
            logger.info(f"[{slug}] Pairing code generado para '+{phone_number}'")
            return res
        finally:
            conn.close()

    def confirm_whatsapp_pairing(
        self,
        slug: str,
        tenant_id: str,
        phone_number: str
    ) -> dict[str, Any]:
        """Confirm device pairing and mark the session as CONNECTED."""
        self.get_or_create_wallet(slug, tenant_id)
        conn = self._get_db(slug)
        try:
            res = _telecom_confirm_pair(conn, tenant_id, phone_number)
            logger.info(f"[{slug}] WhatsApp emparejado con éxito para inquilino '{tenant_id}' con teléfono '+{phone_number}'")
            return res
        finally:
            conn.close()

    def disconnect_whatsapp(self, slug: str, tenant_id: str) -> dict[str, Any]:
        """Unlink the tenant's WhatsApp device."""
        self.get_or_create_wallet(slug, tenant_id)
        conn = self._get_db(slug)
        try:
            return _telecom_disconnect_wa(conn, tenant_id)
        finally:
            conn.close()


    def configure_meta_whatsapp_cloud(
        self,
        slug: str,
        tenant_id: str,
        phone_number_id: str,
        access_token: str,
        waba_id: str | None = None,
        phone_number: str | None = None,
        template_name: str = "recordatorio_cita",
    ) -> TelecomWallet:
        """Configure and activate the connection with Meta WhatsApp Cloud API (Graph API v20.0)."""
        self.get_or_create_wallet(slug, tenant_id)
        now_ts = time.time()
        clean_phone = "".join(filter(str.isdigit, phone_number)) if phone_number else None
        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE telecom_wallets
                SET whatsapp_mode = 'meta',
                    whatsapp_status = 'CONNECTED',
                    whatsapp_phone_number_id = ?,
                    whatsapp_access_token = ?,
                    whatsapp_waba_id = ?,
                    whatsapp_phone = coalesce(?, whatsapp_phone),
                    whatsapp_template_name = ?,
                    updated_at = ?
                WHERE tenant_id = ?;
            """, (phone_number_id, access_token, waba_id, clean_phone, template_name, now_ts, tenant_id))
            conn.commit()
        finally:
            conn.close()

        logger.info(f"[{slug}] Meta WhatsApp Cloud configurado con éxito para '{tenant_id}' (Phone Number ID: {phone_number_id})")
        return self.get_or_create_wallet(slug, tenant_id)

    def _resolve_meta_credentials(self, wallet: TelecomWallet) -> tuple[str | None, str | None, bool]:
        return _telecom_resolve_meta_creds(wallet.whatsapp_phone_number_id, wallet.whatsapp_access_token)

    def _execute_meta_cloud_http(
        self, slug: str, phone_number_id: str, access_token: str, payload_meta: dict[str, Any]
    ) -> tuple[str | None, str, str | None]:
        return _telecom_exec_meta_http(slug, phone_number_id, access_token, payload_meta)

    def _record_meta_dispatch(
        self, slug: str, dispatch_id: str, clean_phone: str, tmpl: str, parameters: list[str],
        dispatch_status: str, error_message: str | None, provider_msg_id: str | None, key: str
    ) -> None:
        conn = self._get_db(slug)
        try:
            _telecom_record_meta_dispatch(conn, dispatch_id, clean_phone, tmpl, parameters, dispatch_status, error_message, provider_msg_id, key)
        finally:
            conn.close()

    def dispatch_meta_whatsapp_cloud(
        self,
        slug: str,
        tenant_id: str,
        recipient_phone: str,
        parameters: list[str],
        template_name: str | None = None,
        language_code: str = "es",
        idempotency_key: str | None = None,
    ) -> DispatchResult:
        """Send an official WhatsApp template via Meta Graph API v20.0 in the cloud."""
        clean_phone = "".join(filter(str.isdigit, recipient_phone))
        wallet = self.get_or_create_wallet(slug, tenant_id)
        tmpl = template_name or wallet.whatsapp_template_name or "recordatorio_cita"
        key = idempotency_key or f"meta_wa_{clean_phone}_{int(time.time())}"

        self.deduct_telecom_usage(slug, tenant_id, "whatsapp_meta", clean_phone, key)
        dispatch_id = f"WAM-{uuid.uuid4().hex[:10].upper()}"

        phone_number_id, access_token, is_live = self._resolve_meta_credentials(wallet)
        payload_meta = self.build_meta_whatsapp_cloud_payload(
            phone_number=clean_phone,
            template_name=tmpl,
            parameters=parameters,
            language_code=language_code
        )

        provider_msg_id = None
        dispatch_status = "SENT"
        error_message = None

        if phone_number_id and access_token:
            if is_live:
                provider_msg_id, dispatch_status, error_message = self._execute_meta_cloud_http(
                    slug, phone_number_id, access_token, payload_meta
                )
            else:
                provider_msg_id = f"wamid.HBgM_mock_{uuid.uuid4().hex[:16]}"
                logger.info(f"[{slug}] Meta WhatsApp Sandbox (Cuota Protegida): Mensaje simulado hacia '+{clean_phone}'. Active META_WA_LIVE_DISPATCH_ENABLED=true para emisión física.")
        else:
            provider_msg_id = f"wamid.mock_{uuid.uuid4().hex[:16]}"

        self._record_meta_dispatch(slug, dispatch_id, clean_phone, tmpl, parameters, dispatch_status, error_message, provider_msg_id, key)

        result_payload = {
            "to": clean_phone,
            "template_name": tmpl,
            "parameters": parameters,
            "provider": "Meta WhatsApp Cloud API (Graph v20.0)" if (phone_number_id and access_token and is_live) else "Meta WhatsApp Cloud (Simulation)",
            "provider_message_id": provider_msg_id,
            "graph_payload": payload_meta
        }
        return DispatchResult(dispatch_id, "whatsapp_meta", clean_phone, dispatch_status, result_payload, error_message)

    # DESPACHO UNIFICADO MULTICANAL

    def _resolve_twilio_credentials(self) -> tuple[str | None, str | None, str | None, bool]:
        return _telecom_resolve_twilio_creds()

    def _execute_twilio_dispatch(
        self, slug: str, clean_phone: str, message_text: str,
        account_sid: str | None, auth_token: str | None, from_sender: str, is_live_enabled: bool
    ) -> tuple[str | None, str, str | None]:
        return _telecom_exec_twilio_dispatch(slug, clean_phone, message_text, account_sid, auth_token, from_sender, is_live_enabled)

    def _record_sms_dispatch(
        self, slug: str, dispatch_id: str, clean_phone: str, message_text: str,
        dispatch_status: str, error_message: str | None, provider_msg_id: str | None, ledger_id: int
    ) -> None:
        conn = self._get_db(slug)
        try:
            _telecom_record_sms_dispatch(conn, dispatch_id, clean_phone, message_text, dispatch_status, error_message, provider_msg_id, ledger_id)
        finally:
            conn.close()

    def _resolve_chosen_channel(self, preferred_channel: str, wallet: TelecomWallet) -> str:
        if preferred_channel != "auto":
            return preferred_channel
        if wallet.whatsapp_status == "CONNECTED":
            return "whatsapp"
        elif wallet.balance_cents >= SMS_RETAIL_PRICE_CENTS or wallet.auto_recharge_enabled:
            return "sms"
        return "email"

    def _dispatch_whatsapp_channel(
        self, slug: str, tenant_id: str, clean_phone: str, message_text: str, idempotency_key: str, wallet: TelecomWallet
    ) -> DispatchResult:
        if wallet.whatsapp_mode == "meta" and (wallet.whatsapp_phone_number_id or os.environ.get("META_WA_PHONE_NUMBER_ID")):
            return self.dispatch_meta_whatsapp_cloud(
                slug=slug,
                tenant_id=tenant_id,
                recipient_phone=clean_phone,
                parameters=[message_text],
                idempotency_key=idempotency_key
            )
        self.deduct_telecom_usage(slug, tenant_id, "whatsapp_qr", clean_phone, idempotency_key)
        return self.dispatch_whatsapp_message(
            slug=slug,
            phone_number=clean_phone,
            template_text=message_text,
            variables={}
        )

    def _dispatch_sms_channel(
        self, slug: str, tenant_id: str, clean_phone: str, message_text: str, idempotency_key: str, wallet: TelecomWallet
    ) -> DispatchResult:
        ledger = self.deduct_telecom_usage(slug, tenant_id, "sms", clean_phone, idempotency_key)
        dispatch_id = f"SMS-{uuid.uuid4().hex[:10].upper()}"

        account_sid, auth_token, from_number, is_live_enabled = self._resolve_twilio_credentials()
        from_sender = from_number or wallet.sender_id

        provider_msg_id, dispatch_status, error_message = self._execute_twilio_dispatch(
            slug, clean_phone, message_text, account_sid, auth_token, from_sender, is_live_enabled
        )

        self._record_sms_dispatch(slug, dispatch_id, clean_phone, message_text, dispatch_status, error_message, provider_msg_id, ledger.ledger_id)

        payload = {
            "to": clean_phone,
            "message": message_text,
            "sender_id": wallet.sender_id,
            "cost_cents": ledger.cost_cents,
            "price_cents": ledger.price_cents,
            "margin_cents": ledger.margin_cents,
            "provider": "Twilio REST API Engine (LIVE)" if (account_sid and auth_token and is_live_enabled) else "Twilio Sandbox (Simulation Protected)",
            "provider_message_id": provider_msg_id
        }
        logger.info(f"[{slug}] SMS #{dispatch_id} ({wallet.sender_id}) enviado a '+{clean_phone}' por {ledger.price_cents/100:.2f}€")
        return DispatchResult(dispatch_id, "sms", clean_phone, dispatch_status, payload, error_message)

    def dispatch_multichannel(
        self,
        slug: str,
        tenant_id: str,
        recipient_phone: str,
        recipient_email: str,
        message_text: str,
        idempotency_key: str,
        preferred_channel: str = "auto",
        subject: str = "Aviso Importante",
    ) -> DispatchResult:
        """Dispatch message based on the following channel priorities:
1. If Meta Cloud API is connected -> send official Meta cloud template.
2. If WhatsApp QR is connected -> send via WhatsApp.
3. If wallet balance is available -> send via managed SMS.
4. Fallback (no balance or WhatsApp) -> send via transactional email."""
        wallet = self.get_or_create_wallet(slug, tenant_id)
        chosen_channel = self._resolve_chosen_channel(preferred_channel, wallet)
        clean_phone = "".join(filter(str.isdigit, recipient_phone))

        if chosen_channel == "whatsapp":
            return self._dispatch_whatsapp_channel(slug, tenant_id, clean_phone, message_text, idempotency_key, wallet)
        elif chosen_channel == "sms":
            return self._dispatch_sms_channel(slug, tenant_id, clean_phone, message_text, idempotency_key, wallet)

        self.deduct_telecom_usage(slug, tenant_id, "email", clean_phone or recipient_email, idempotency_key)
        return self.dispatch_transactional_email(
            slug=slug,
            to_email=recipient_email,
            subject=subject,
            template_html=f"<div style='font-family: sans-serif; padding: 20px;'><p>{message_text}</p></div>",
            variables={}
        )

    # LEGACY AND SPECIFIC CHANNELS (BACKWARD COMPATIBILITY)

    def dispatch_whatsapp_message(
        self,
        slug: str,
        phone_number: str,
        template_text: str,
        variables: dict[str, Any]
    ) -> DispatchResult:
        """Dispatch a WhatsApp message (Click-to-Chat or Meta Cloud payload)."""
        clean_phone = "".join(filter(str.isdigit, phone_number))
        rendered_msg = self.render_template(template_text, variables)
        dispatch_id = f"WA-{uuid.uuid4().hex[:10].upper()}"

        wa_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(rendered_msg)}"
        payload = {
            "to": clean_phone,
            "message": rendered_msg,
            "wa_click_to_chat_url": wa_url,
            "provider": "Meta WhatsApp Cloud Protocol"
        }

        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO notification_dispatches (id, channel, recipient, content, status)
                VALUES (?, 'whatsapp', ?, ?, 'SENT');
            """, (dispatch_id, clean_phone, rendered_msg))
            conn.commit()
            logger.info(f"[{slug}] WhatsApp #{dispatch_id} despachado para '{clean_phone}'")
            return DispatchResult(dispatch_id, "whatsapp", clean_phone, "SENT", payload)
        finally:
            conn.close()

    def build_meta_whatsapp_cloud_payload(
        self,
        phone_number: str,
        template_name: str,
        parameters: list[str],
        language_code: str = "es"
    ) -> dict[str, Any]:
        """Generate the official Meta WhatsApp Cloud API (Graph API v20.0) JSON payload."""
        return _telecom_build_meta_payload(phone_number, template_name, parameters, language_code)

    def dispatch_transactional_email(
        self,
        slug: str,
        to_email: str,
        subject: str,
        template_html: str,
        variables: dict[str, Any],
        from_email: str = "notificaciones@autonomuos.app"
    ) -> DispatchResult:
        """Dispatch a transactional email via the mail oracle."""
        rendered_html = self.render_template(template_html, variables)
        rendered_sub = self.render_template(subject, variables)
        conn = self._get_db(slug)
        try:
            dispatch_id, status = _telecom_dispatch_email(conn, slug, to_email, rendered_sub, rendered_html, from_email)
            return DispatchResult(
                dispatch_id, "email", to_email, status,
                {"subject": rendered_sub, "html": rendered_html}
            )
        finally:
            conn.close()

    def dispatch_signed_webhook(
        self,
        slug: str,
        target_url: str,
        event_name: str,
        payload_data: dict[str, Any],
        webhook_secret: str = "whsec_autonomuos_default_32"
    ) -> DispatchResult:
        """Prepare and sign an outbound webhook with the X-Autonomuos-Signature header."""
        dispatch_id = f"WH-{uuid.uuid4().hex[:10].upper()}"
        timestamp = int(time.time())
        json_body = json.dumps(payload_data, ensure_ascii=False)

        signed_payload = f"{timestamp}.{json_body}".encode("utf-8")
        sig = hmac.new(webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        signature_header = f"t={timestamp},v1={sig}"

        headers = {
            "Content-Type": "application/json",
            "X-Autonomuos-Event": event_name,
            "X-Autonomuos-Signature": signature_header
        }

        conn = self._get_db(slug)
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO notification_dispatches (id, channel, recipient, subject, content, status)
                VALUES (?, 'webhook', ?, ?, ?, 'QUEUED');
            """, (dispatch_id, target_url, event_name, json_body))
            conn.commit()
            logger.info(f"[{slug}] Webhook #{dispatch_id} ({event_name}) preparado para '{target_url}'")
            return DispatchResult(
                dispatch_id, "webhook", target_url, "QUEUED",
                {"headers": headers, "body": payload_data}
            )
        finally:
            conn.close()


communications_bus = CommunicationsBusPrimitive()
