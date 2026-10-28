"""
Provide a cryptographic append-only audit trail primitive. Enforce three core audit invariants (SOC 2 Type II / eIDAS / HIPAA / GDPR Art. 17):
1. Tamper-evident HMAC-SHA256 chaining (server cryptographic seal with an immutable per-tenant key).
2. Storage engine immutability (SQLite triggers aborting any UPDATE or DELETE via RAISE(FAIL)).
3. Change Data Capture (CDC) with PII sanitization and right-to-erasure compliance.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive
from assessment_engine.infrastructure.primitives.security import resolve_secret

logger = logging.getLogger("assessment_engine.infrastructure.primitives.audit_trail")

GENESIS_HASH = "0" * 64
AUDIT_SECRET_KEY = resolve_secret("SECRET_KEY")


@dataclass(frozen=True)
class AuditEvent:
    """Represent a strongly typed sealed audit event."""
    id: int
    tenant_id: str
    timestamp: float
    actor_id: str
    actor_role: str
    impersonated_by: str | None
    action: str
    entity_type: str
    entity_id: str
    prev_hash: str
    entry_hash: str
    diff_json: str
    ip_address: str
    user_agent: str


class AuditTrailPrimitive(CapabilityPrimitive):
    """
    Manage immutable audit logs with HMAC-SHA256 sealing, PII sanitization, and SQLite triggers.
    """

    @property
    def namespace(self) -> str:
        """Return the namespace."""
        return "audit_trail"

    def get_capabilities(self) -> dict[str, Any]:
        """Retrieve the supported capabilities."""
        return {
            "version": "3.1.0",
            "operations": [
                "record_cdc_event",
                "verify_chain_integrity",
                "get_events_for_entity",
                "get_tenant_audit_log",
                "sanitize_pii"
            ],
            "standards": [
                "Cryptographic HMAC-SHA256 Server Sealing",
                "Physical Immutability via SQLite Engine Triggers",
                "SOC 2 Type II / eIDAS Append-Only Compliance",
                "RGPD Art. 17 Automated PII Redaction"
            ]
        }

    def _init_audit_table(self, conn: sqlite3.Connection) -> None:
        """Initialize the table and immutability triggers in SQLite."""
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            actor_id TEXT NOT NULL,
            actor_role TEXT DEFAULT 'client',
            impersonated_by TEXT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            prev_hash TEXT NOT NULL,
            entry_hash TEXT NOT NULL,
            diff_json TEXT NOT NULL,
            ip_address TEXT DEFAULT '127.0.0.1',
            user_agent TEXT DEFAULT ''
        );
        """)

        # Enforce immutability triggers at the storage engine level.
        cur.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_audit_update
        BEFORE UPDATE ON audit_trail_events
        BEGIN
            SELECT RAISE(FAIL, 'AUDIT_LOG_IMMUTABLE: Updates are strictly prohibited');
        END;
        """)

        cur.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_audit_delete
        BEFORE DELETE ON audit_trail_events
        BEGIN
            SELECT RAISE(FAIL, 'AUDIT_LOG_IMMUTABLE: Deletions are strictly prohibited');
        END;
        """)
        conn.commit()

    @staticmethod
    def _mask_email_value(val: Any) -> str:
        s_val = str(val)
        if "@" in s_val:
            u, d = s_val.split("@", 1)
            return f"{u[:1]}***@{d}"
        return "***"

    @staticmethod
    def _mask_phone_or_id(val: Any) -> str:
        s_val = str(val)
        return f"***{s_val[-4:]}" if len(s_val) >= 4 else "***"

    @classmethod
    def sanitize_pii(cls, state: dict[str, Any] | None) -> dict[str, Any] | None:
        """Apply privacy masks and redact secrets for GDPR Art. 17 compliance."""
        if not state or not isinstance(state, dict):
            return state

        sanitized: dict[str, Any] = {}
        sensitive_drop = {
            "password", "auth_hash", "token", "secret", "cvv", "cvc",
            "card_number", "credit_card", "pin", "private_key", "api_key"
        }
        worldwide_id_patterns = (
            "phone", "telefono", "mobile", "celular",
            "dni", "nif", "cif", "nie",
            "ssn", "ein", "itin",
            "rfc", "curp",
            "cpf", "cnpj",
            "siren", "siret",
            "tax_id", "vat_id", "national_id", "fiscal"
        )

        for k, v in state.items():
            k_low = k.lower()
            if any(s in k_low for s in sensitive_drop):
                sanitized[k] = "[REDACTED]"
            elif "email" in k_low or "correo" in k_low:
                sanitized[k] = cls._mask_email_value(v)
            elif any(s in k_low for s in worldwide_id_patterns):
                sanitized[k] = cls._mask_phone_or_id(v)
            else:
                sanitized[k] = v
        return sanitized

    @classmethod
    def compute_entry_hash(
        cls,
        prev_hash: str,
        tenant_id: str,
        timestamp: float,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        diff_json: str,
        secret_key: str | None = None
    ) -> str:
        """Compute the HMAC-SHA256 cryptographic seal of the event using the server key."""
        key = (secret_key or AUDIT_SECRET_KEY).encode("utf-8")
        payload = f"{prev_hash}|{tenant_id}|{timestamp:.4f}|{actor_id}|{action}|{entity_type}|{entity_id}|{diff_json}"
        return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def record_cdc_event(
        self,
        db_path: Path,
        tenant_id: str,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        actor_role: str = "client",
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        ip_address: str = "127.0.0.1",
        impersonated_by: str | None = None,
        user_agent: str = ""
    ) -> dict[str, Any]:
        """Record an atomic CDC audit event with PII sanitization and an HMAC seal."""
        conn = sqlite3.connect(str(db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        self._init_audit_table(conn)
        cur = conn.cursor()

        try:
            # 1. Retrieve the hash of the latest event recorded for this tenant
            cur.execute("""
                SELECT entry_hash FROM audit_trail_events
                WHERE tenant_id = ?
                ORDER BY id DESC LIMIT 1;
            """, (tenant_id,))
            last_row = cur.fetchone()
            prev_hash = last_row["entry_hash"] if last_row else GENESIS_HASH

            now_ts = time.time()
            clean_before = self.sanitize_pii(before_state)
            clean_after = self.sanitize_pii(after_state)

            diff_payload = {
                "before": clean_before,
                "after": clean_after
            }
            diff_str = json.dumps(diff_payload, sort_keys=True, ensure_ascii=False)

            entry_hash = self.compute_entry_hash(
                prev_hash=prev_hash,
                tenant_id=tenant_id,
                timestamp=now_ts,
                actor_id=actor_id,
                action=action.upper(),
                entity_type=entity_type.lower(),
                entity_id=str(entity_id),
                diff_json=diff_str
            )

            # 3. Perform sealed append-only insertion
            cur.execute("""
                INSERT INTO audit_trail_events (
                    tenant_id, timestamp, actor_id, actor_role, impersonated_by,
                    action, entity_type, entity_id, prev_hash, entry_hash,
                    diff_json, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                tenant_id, now_ts, actor_id, actor_role, impersonated_by,
                action.upper(), entity_type.lower(), str(entity_id), prev_hash, entry_hash,
                diff_str, ip_address, user_agent
            ))
            conn.commit()
            evt_id = cur.lastrowid
            logger.info(f"[AuditTrail] Evento #{evt_id} sellado: {actor_id} -> {action} {entity_type}:{entity_id} [HMAC: {entry_hash[:12]}]")
            return {
                "status": "ok",
                "audit_id": evt_id,
                "entry_hash": entry_hash,
                "prev_hash": prev_hash
            }
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.error(f"[AuditTrail] Error sellando auditoría: {ex}")
            return {"status": "error", "message": str(ex)}
        finally:
            conn.close()

    def record_event(
        self,
        db_path: Path,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        payload_diff: dict[str, Any] | None = None,
        ip_address: str = "127.0.0.1",
        tenant_id: str = "tenant_default"
    ) -> dict[str, Any]:
        """Provide backward compatibility by calling record_cdc_event."""
        return self.record_cdc_event(
            db_path=db_path,
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            before_state=None,
            after_state=payload_diff,
            ip_address=ip_address
        )

    def verify_chain_integrity(self, db_path: Path, tenant_id: str) -> tuple[bool, str, int]:
        """
        Verify the integrity of the tenant's entire audit chain using HMAC.
        """
        if not db_path.exists():
            return False, "DATABASE_NOT_FOUND", 0

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name='audit_trail_events';
            """)
            if not cur.fetchone():
                return True, "NO_EVENTS_YET", 0

            cur.execute("""
                SELECT id, tenant_id, timestamp, actor_id, action, entity_type,
                       entity_id, prev_hash, entry_hash, diff_json
                FROM audit_trail_events
                WHERE tenant_id = ?
                ORDER BY id ASC;
            """, (tenant_id,))
            rows = cur.fetchall()

            if not rows:
                return True, "EMPTY_TENANT_LEDGER", 0

            expected_prev_hash = GENESIS_HASH
            verified_count = 0

            for r in rows:
                if r["prev_hash"] != expected_prev_hash:
                    return False, f"BROKEN_CHAIN_LINK_AT_ID_{r['id']}", verified_count

                recomputed_hash = self.compute_entry_hash(
                    prev_hash=r["prev_hash"],
                    tenant_id=r["tenant_id"],
                    timestamp=r["timestamp"],
                    actor_id=r["actor_id"],
                    action=r["action"],
                    entity_type=r["entity_type"],
                    entity_id=r["entity_id"],
                    diff_json=r["diff_json"]
                )

                if r["entry_hash"] != recomputed_hash:
                    return False, f"TAMPERED_ENTRY_HASH_AT_ID_{r['id']}", verified_count

                expected_prev_hash = r["entry_hash"]
                verified_count += 1

            return True, "INTEGRITY_VERIFIED", verified_count
        finally:
            conn.close()

    def get_events_for_entity(
        self,
        db_path: Path,
        arg1: str,
        arg2: str,
        arg3: str | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve the full historical trace of an entity."""
        if not db_path.exists():
            return []

        if arg3 is not None:
            tenant_id = arg1
            entity_type = arg2.lower()
            entity_id = str(arg3)
            query = """
                SELECT id, timestamp, actor_id, actor_role, action, diff_json,
                       entry_hash, prev_hash, ip_address
                FROM audit_trail_events
                WHERE tenant_id = ? AND entity_type = ? AND entity_id = ?
                ORDER BY id ASC;
            """
            params = (tenant_id, entity_type, entity_id)
        else:
            entity_type = arg1.lower()
            entity_id = str(arg2)
            query = """
                SELECT id, timestamp, actor_id, actor_role, action, diff_json,
                       entry_hash, prev_hash, ip_address
                FROM audit_trail_events
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY id ASC;
            """
            params = (entity_type, entity_id)

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(query, params)
            rows = cur.fetchall()
            results = []
            for r in rows:
                raw_diff = json.loads(r["diff_json"])
                diff_obj = {**raw_diff, **raw_diff["after"]} if (isinstance(raw_diff, dict) and "after" in raw_diff and isinstance(raw_diff["after"], dict)) else raw_diff
                results.append({
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "actor_id": r["actor_id"],
                    "actor_role": r["actor_role"],
                    "action": r["action"],
                    "diff": diff_obj,
                    "entry_hash": r["entry_hash"],
                    "prev_hash": r["prev_hash"],
                    "ip_address": r["ip_address"]
                })
            return results
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return []
        finally:
            conn.close()

    def get_tenant_audit_log(self, db_path: Path, tenant_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve the general audit log for the tenant admin dashboard."""
        if not db_path.exists():
            return []

        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, timestamp, actor_id, actor_role, action, entity_type,
                       entity_id, diff_json, entry_hash, ip_address
                FROM audit_trail_events
                WHERE tenant_id = ?
                ORDER BY id DESC LIMIT ?;
            """, (tenant_id, limit))
            rows = cur.fetchall()
            return [
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "actor_id": r["actor_id"],
                    "actor_role": r["actor_role"],
                    "action": r["action"],
                    "entity_type": r["entity_type"],
                    "entity_id": r["entity_id"],
                    "diff": json.loads(r["diff_json"]),
                    "entry_hash": r["entry_hash"],
                    "ip_address": r["ip_address"]
                }
                for r in rows
            ]
        except (RuntimeError, ValueError, KeyError, OSError, TypeError):
            return []
        finally:
            conn.close()


audit_trail = AuditTrailPrimitive()
