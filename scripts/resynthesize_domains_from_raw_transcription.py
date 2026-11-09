#!/usr/bin/env python3
"""Tenant-Agnostic & Topology-Agnostic Domain Resynthesis Orchestrator.

Dynamically discovers arbitrary domain/tower topologies (e.g., T1..T10, D1..D8, or custom
vertical domain slugs) for any enterprise tenant, executes raw transcription synthesis,
and enforces Phase 8.1 deterministic score reconciliation.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.application.run_scoring import build_scoring
from assessment_engine.application.sync_payload_scores import parse_raw_responses
from assessment_engine.domain.services.score_reconciler import reconcile_tower_scores
from assessment_engine.domain.validation.mathematical_integrity import (
    assert_tower_mathematical_integrity,
)

logger = logging.getLogger("resynthesize_domains")


@dataclass(frozen=True)
class DomainExecutionContext:
    """Encapsulates resolved filesystem paths and identity for a single domain execution unit."""

    tenant_id: str
    vertical_id: str
    domain_id: str
    domain_dir: Path
    scoring_def_path: Path
    payload_output_path: Path


def atomic_write_json(target_path: Path, payload: dict[str, Any]) -> None:
    """Writes JSON payload to disk atomically with fsync and cleanup."""
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


def discover_tenant_domains(
    config_dir: Path,
    working_dir: Path,
    explicit_domains: Sequence[str] | None = None,
    vertical_id: str = "GENERIC_ENTERPRISE",
) -> list[DomainExecutionContext]:
    """Dynamically discovers domain directories for a tenant without assuming

    cardinal count (e.g., 10 towers) or naming convention (T1..T10 vs D1..D8).
    """
    discovered_codes: list[str] = []

    if explicit_domains:
        discovered_codes = [d.strip().upper() for d in explicit_domains if d.strip()]
    else:
        for child in sorted(working_dir.iterdir()):
            if child.is_dir() and not child.name.startswith((".", "_")):
                discovered_codes.append(child.name.upper())

    contexts: list[DomainExecutionContext] = []
    for code in discovered_codes:
        def_path = config_dir / code / f"tower_definition_{code}.json"
        if not def_path.exists():
            def_path = config_dir / f"tower_definition_{code}.json"
        if not def_path.exists():
            logger.warning("Tower definition for '%s' not found. Skipping.", code)
            continue

        domain_dir = working_dir / code
        code_l = code.lower()
        payload_path = domain_dir / f"blueprint_{code_l}_payload.json"

        contexts.append(
            DomainExecutionContext(
                tenant_id=working_dir.name,
                vertical_id=vertical_id,
                domain_id=code,
                domain_dir=domain_dir,
                scoring_def_path=def_path,
                payload_output_path=payload_path,
            )
        )

    return contexts


def reconcile_domain_payload(
    context: DomainExecutionContext,
    answers_map: dict[str, list[dict[str, Any]]],
    *,
    strict_boundary: bool = True,
) -> Path:
    """Reconciles an existing synthesized domain payload with deterministic scoring SSOT."""
    if not context.payload_output_path.is_file():
        raise FileNotFoundError(f"Payload not found at {context.payload_output_path}")

    with open(context.scoring_def_path, "r", encoding="utf-8-sig") as df:
        tower_def = json.load(df)

    case_input = {
        "case_id": f"CASE_{context.domain_id}",
        "tower_id": context.domain_id,
        "tower_name": tower_def.get("tower_name", context.domain_id),
        "answers": answers_map.get(context.domain_id, []),
    }
    scoring_ssot = build_scoring(case_input, tower_def)

    with open(context.payload_output_path, "r", encoding="utf-8-sig") as pf:
        raw_payload = json.load(pf)

    healed_payload = reconcile_tower_scores(raw_payload, scoring_ssot)
    if strict_boundary:
        assert_tower_mathematical_integrity(healed_payload)

    atomic_write_json(context.payload_output_path, healed_payload)
    logger.info(
        "Successfully reconciled domain='%s' (Score=%.2f) -> %s",
        context.domain_id,
        healed_payload["score"],
        context.payload_output_path.name,
    )
    return context.payload_output_path


def parse_cli_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tenant-agnostic & topology-agnostic domain resynthesis and Phase 8.1 reconciliation."
    )
    parser.add_argument(
        "--client-id",
        "--tenant-id",
        dest="client_id",
        required=True,
        help="Unique identifier for the enterprise tenant (e.g. acme_corp).",
    )
    parser.add_argument(
        "--vertical-id",
        dest="vertical_id",
        default="GENERIC_ENTERPRISE",
        help="Industry vertical identifier (e.g., BANKING, HEALTHCARE, RETAIL, MANUFACTURING).",
    )
    parser.add_argument(
        "--responses",
        type=Path,
        required=True,
        help="Path to client questionnaire responses (.txt or .json).",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=REPO_ROOT / "engine_config/towers",
        help="Path to engine_config/towers directory.",
    )
    parser.add_argument(
        "--domains",
        nargs="*",
        default=None,
        help="Optional explicit list of domain slugs (e.g., D1 D2 or T1..T10). Auto-discovers if omitted.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    args = parse_cli_arguments(argv)

    answers_map = parse_raw_responses(args.responses)
    working_dir = REPO_ROOT / "working" / args.client_id
    if not working_dir.is_dir():
        logger.error("Working directory does not exist: %s", working_dir)
        return 1

    contexts = discover_tenant_domains(
        config_dir=args.config_dir,
        working_dir=working_dir,
        explicit_domains=args.domains,
        vertical_id=args.vertical_id,
    )

    logger.info(
        "Discovered %d domain(s) for tenant '%s': %s",
        len(contexts),
        args.client_id,
        [c.domain_id for c in contexts],
    )

    for ctx in contexts:
        reconcile_domain_payload(ctx, answers_map, strict_boundary=True)

    logger.info(
        "All %d domain(s) for tenant '%s' reconciled with 100%% deterministic mathematical integrity.",
        len(contexts),
        args.client_id,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
