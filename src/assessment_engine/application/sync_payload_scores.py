"""CLI and Application Service to synchronize generated tower JSON payloads

with the deterministic Single Source of Truth (SSOT) from run_scoring.py::build_scoring().
Guarantees mathematical conservation and eradicates split-brain divergence across any topology.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from assessment_engine.application.run_scoring import build_scoring
from assessment_engine.domain.services.score_reconciler import reconcile_tower_scores
from assessment_engine.domain.validation.mathematical_integrity import (
    assert_tower_mathematical_integrity,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def parse_raw_responses(responses_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Parses raw text or JSON questionnaire responses into domain/tower-keyed answer lists."""
    answers_by_tower: Dict[str, List[Dict[str, Any]]] = {}

    if responses_path.suffix.lower() == ".json":
        with open(responses_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        for item in data.get("answers", []):
            if not isinstance(item, dict):
                continue
            k_id = str(item.get("kpi_id") or item.get("question_id") or "").strip()
            raw_val = item.get("value")
            if raw_val is None or not k_id:
                continue
            try:
                val = float(raw_val)
            except (ValueError, TypeError):
                continue
            explicit_tower = str(item.get("tower_id") or item.get("domain_id") or "").strip().upper()
            if explicit_tower:
                t_code = explicit_tower
            elif "." in k_id:
                t_code = k_id.split(".")[0].upper()
            else:
                continue
            answers_by_tower.setdefault(t_code, []).append({"kpi_id": k_id, "value": val})
        return answers_by_tower

    with open(responses_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                q_id = parts[0].strip()
                try:
                    val = float(parts[1])
                except ValueError:
                    continue
                if "." in q_id:
                    tokens = q_id.split(".")
                    t_code = tokens[0].upper()
                    if len(tokens) > 2 and re.match(r"^(PR|Q|QUESTION)\d+$", tokens[-1], re.IGNORECASE):
                        kpi_id = ".".join(tokens[:-1])
                    elif len(tokens) >= 3:
                        kpi_id = ".".join(tokens[:3])
                    else:
                        kpi_id = q_id
                    answers_by_tower.setdefault(t_code, []).append({"kpi_id": kpi_id, "value": val})

    return answers_by_tower


def _discover_topology_domains(
    config_dir: Path,
    answers_by_tower: Dict[str, List[Dict[str, Any]]],
) -> List[str]:
    """Dynamically discovers all domain/tower identifiers without hardcoding T1..T10."""
    discovered: Set[str] = set(answers_by_tower.keys())

    for def_file in config_dir.rglob("tower_definition_*.json"):
        code = def_file.stem.replace("tower_definition_", "").strip().upper()
        if code:
            discovered.add(code)

    def _natural_sort_key(code: str) -> tuple[str, int, str]:
        prefix = "".join(ch for ch in code if not ch.isdigit())
        digits = "".join(ch for ch in code if ch.isdigit())
        return (prefix, int(digits) if digits else 0, code)

    return sorted(discovered, key=_natural_sort_key)


def _atomic_write_json(target_path: Path, payload: Dict[str, Any]) -> None:
    """Writes JSON payload to disk atomically with fsync and guaranteed temp file cleanup."""
    temp_file = target_path.with_name(f".{target_path.name}.{os.getpid()}.tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        temp_file.replace(target_path)
    except Exception:
        if temp_file.exists():
            temp_file.unlink(missing_ok=True)
        raise


def synchronize_tenant_payloads(
    responses_path: Path,
    config_dir: Path,
    payloads_dir: Path,
    target_towers: List[str] | None = None,
) -> Dict[str, Dict[str, Any]]:
    """Computes deterministic scores via build_scoring() and reconciles all tower payloads on disk."""
    if not responses_path.exists():
        raise FileNotFoundError(f"Responses file not found at: {responses_path}")
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found at: {config_dir}")

    answers_by_tower = parse_raw_responses(responses_path)
    if not answers_by_tower:
        raise ValueError(f"No valid questionnaire answers parsed from: {responses_path}")

    if target_towers is None:
        target_towers = _discover_topology_domains(config_dir, answers_by_tower)

    reconciled_map: Dict[str, Dict[str, Any]] = {}

    for t_code in target_towers:
        t_code_u = t_code.strip().upper()
        def_path = config_dir / t_code_u / f"tower_definition_{t_code_u}.json"
        if not def_path.exists():
            def_path = config_dir / f"tower_definition_{t_code_u}.json"
        if not def_path.exists():
            logger.warning("Tower definition for '%s' not found in %s. Skipping.", t_code_u, config_dir)
            continue

        with open(def_path, "r", encoding="utf-8-sig") as f:
            tower_def = json.load(f)

        case_input = {
            "case_id": f"CASE_{t_code_u}",
            "tower_id": t_code_u,
            "tower_name": tower_def.get("tower_name", t_code_u),
            "answers": answers_by_tower.get(t_code_u, []),
        }

        # 1. Compute deterministic SSOT
        scoring_ssot = build_scoring(case_input, tower_def)

        # 2. Locate on-disk payload
        t_code_l = t_code_u.lower()
        payload_file = payloads_dir / t_code_u / f"blueprint_{t_code_l}_payload.json"
        if not payload_file.exists():
            payload_file = payloads_dir / f"blueprint_{t_code_l}_payload.json"
        if not payload_file.exists():
            logger.warning("Tower payload file for '%s' not found in %s. Skipping.", t_code_u, payloads_dir)
            continue

        with open(payload_file, "r", encoding="utf-8-sig") as f:
            raw_payload = json.load(f)

        # 3. Apply deterministic state reconciler
        healed_payload = reconcile_tower_scores(
            tower_payload=raw_payload,
            scoring_ssot=scoring_ssot,
        )

        assert_tower_mathematical_integrity(healed_payload)

        _atomic_write_json(payload_file, healed_payload)

        logger.info(
            "Successfully synchronized %s | Tower Score: %.2f (Pillars: %d)",
            payload_file.name,
            healed_payload["score"],
            len(healed_payload.get("pillars_analysis", [])),
        )
        reconciled_map[t_code_u] = healed_payload

    return reconciled_map


def main() -> None:
    """Synchronize scoring payloads across active workspaces."""
    parser = argparse.ArgumentParser(
        description="Synchronize Tower Payloads with Questionnaire Scoring SSOT."
    )
    parser.add_argument(
        "--responses",
        required=True,
        type=Path,
        help="Path to client questionnaire responses (.txt or .json).",
    )
    parser.add_argument(
        "--config-dir",
        required=True,
        type=Path,
        help="Path to engine_config/towers directory.",
    )
    parser.add_argument(
        "--payloads-dir",
        required=True,
        type=Path,
        help="Path to tenant working payloads directory.",
    )
    parser.add_argument(
        "--towers",
        nargs="*",
        default=None,
        help="Optional explicit list of domain/tower codes (e.g. D1 D2 or T1 T2).",
    )
    args = parser.parse_args()

    synchronize_tenant_payloads(
        responses_path=args.responses,
        config_dir=args.config_dir,
        payloads_dir=args.payloads_dir,
        target_towers=args.towers,
    )


if __name__ == "__main__":
    """Synchronize scoring payloads across active workspaces."""
    main()
