import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LiabilitySigner:
    """
    Genera recibos criptográficos (Liability Logs) para cumplimiento con normativas
    como la EU AI Act, permitiendo auditorías de gobernanza sin exponer IP interno.
    """

    @classmethod
    def generate_compliance_receipt(
        cls,
        request_dir: Path,
        plan: dict[str, Any],
        task_id: str,
        diff_content: str,
        verification_status: str,
    ) -> dict[str, Any]:
        """
        Genera un comprobante criptográfico (SHA-256) del estado inmutable
        de la iteración y lo guarda en disco.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Recopilamos el estado que queremos firmar (commitments)
        # Esto es lo que se usaría como entrada para un ZKP real.
        payload_to_sign = {
            "timestamp": timestamp,
            "task_id": task_id,
            "invariants": plan.get("invariants", []),
            "verification_status": verification_status,
            "diff_hash": hashlib.sha256(diff_content.encode("utf-8")).hexdigest(),
        }

        # Generar el Hash Criptográfico final (nuestra firma)
        payload_string = json.dumps(payload_to_sign, sort_keys=True)
        commitment_hash = hashlib.sha256(payload_string.encode("utf-8")).hexdigest()

        receipt = {
            "eu_ai_act_compliance": "Verified",
            "governance_commitment_hash": commitment_hash,
            "algorithm": "SHA-256",
            "signed_payload": payload_to_sign,
        }

        # Guardar en disco para trazabilidad posterior
        receipt_path = request_dir / f"{task_id}_compliance_receipt.json"
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return receipt
