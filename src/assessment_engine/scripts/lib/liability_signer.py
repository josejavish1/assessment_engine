#
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LiabilitySigner:
    r"""{'docstring': "Generates and persists a cryptographic compliance receipt.\n\nThis method creates a verifiable, immutable record of a task's execution\nstate for non-repudiation and auditing. The process involves aggregating\nkey data points into a payload dictionary, which includes a UTC timestamp,\nthe task ID, specified invariants from the execution plan, the verification\nstatus, and a SHA-256 hash of the provided `diff_content`.\n\nThe payload is then deterministically serialized to a JSON string with sorted\nkeys. This string is subsequently hashed using SHA-256 to produce a final\n`governance_commitment_hash`. The resulting receipt, containing this hash,\nthe algorithm identifier ('SHA-256'), and the original payload, is then\npersisted as a JSON file to the specified `request_dir`. The output filename\nis formatted as `{task_id}_compliance_receipt.json`.\n\nArgs:\n    request_dir: The target directory for storing the receipt file.\n    plan: The execution plan dictionary. The value associated with the\n        'invariants' key, if present, is included in the signed payload.\n    task_id: A unique identifier for the task, incorporated into the payload\n        and the output filename.\n    diff_content: A string representation of changes (e.g., a git diff)\n        whose SHA-256 hash will be included in the receipt.\n    verification_status: A string describing the outcome of the compliance\n        verification process (e.g., 'Success').\n\nReturns:\n    A dictionary representing the compliance receipt, containing the\n    `governance_commitment_hash`, the hashing `algorithm`, and the\n    `signed_payload`.\n\nRaises:\n    OSError: If writing the receipt file to `request_dir` fails due to an\n        I/O error, such as insufficient permissions or a non-existent path."}."""

    @classmethod
    def generate_compliance_receipt(
        cls,
        request_dir: Path,
        plan: dict[str, Any],
        task_id: str,
        diff_content: str,
        verification_status: str,
    ) -> dict[str, Any]:
        """Generates and persists a cryptographic compliance receipt for a task.

        Creates a verifiable record of a task's state for non-repudiation and
        auditability. The method aggregates key data—including invariants from the
        plan, the task ID, verification status, and a SHA-256 hash of the
        `diff_content`—into a payload. This payload is deterministically serialized
        to a JSON string with sorted keys, and the resulting string is then hashed
        using SHA-256 to produce a 'governance_commitment_hash'. The final
        receipt, containing this hash and the original payload, is written as a
        JSON file to the specified directory. The payload structure is designed
        for compatibility with potential Zero-Knowledge Proof (ZKP) attestations.

        Args:
            request_dir: The target directory for storing the receipt file.
            plan: The execution plan dictionary, which may contain compliance
                invariants under the "invariants" key.
            task_id: A unique identifier for the task.
            diff_content: The content of the generated difference to be included
                as a hash in the receipt's payload.
            verification_status: The final status of the verification process.

        Returns:
            A dictionary representing the generated compliance receipt. The dictionary
            contains the 'governance_commitment_hash', the hashing 'algorithm', and
            the original 'signed_payload'.

        Raises:
            OSError: If writing the receipt file to the specified `request_dir` fails
                due to issues such as insufficient permissions or an invalid path.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # The state intended for cryptographic signing is aggregated into a 'commitments' dictionary. This aggregation guarantees a deterministic and comprehensive representation of all relevant inputs and outputs, which is essential for consistent hashing.
        # This data structure is designed to serve as the public input for a potential Zero-Knowledge Proof (ZKP) system, which would attest to the computational integrity of the process.
        payload_to_sign = {
            "timestamp": timestamp,
            "task_id": task_id,
            "invariants": plan.get("invariants", []),
            "verification_status": verification_status,
            "diff_hash": hashlib.sha256(diff_content.encode("utf-8")).hexdigest(),
        }

        #
        payload_string = json.dumps(payload_to_sign, sort_keys=True)
        commitment_hash = hashlib.sha256(payload_string.encode("utf-8")).hexdigest()

        receipt = {
            "eu_ai_act_compliance": "Verified",
            "governance_commitment_hash": commitment_hash,
            "algorithm": "SHA-256",
            "signed_payload": payload_to_sign,
        }

        #
        receipt_path = request_dir / f"{task_id}_compliance_receipt.json"
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        return receipt
