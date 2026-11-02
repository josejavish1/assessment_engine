"""CLI entrypoint for executing UniversalPayloadEnricher within an isolated pipeline step."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from assessment_engine.application.universal_payload_enricher import (
    UniversalPayloadEnricher,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("enrich_tower_payload_cli")


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments for the universal enrichment step."""
    parser = argparse.ArgumentParser(
        description="Enrich raw tower payload with taxonomy, forensics, and CFO telemetry."
    )
    parser.add_argument("--tower-id", required=True, help="Tower ID (T1..T10)")
    parser.add_argument("--input-payload", type=Path, required=True)
    parser.add_argument("--output-payload", type=Path, required=True)
    parser.add_argument("--taxonomy-path", type=Path, required=True)
    parser.add_argument("--actuarial-gate-path", type=Path, required=True)
    parser.add_argument("--forensic-ledger-path", type=Path, required=True)
    parser.add_argument("--tenant-config-path", type=Path, required=True)
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    if not path.exists():
        logger.warning("File not found at '%s'; returning empty dict.", path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    """Executes the enrichment pipeline stage."""
    args = parse_args()

    raw_payload = _load_json(args.input_payload)
    if not raw_payload:
        logger.error("Input payload at '%s' is empty or missing.", args.input_payload)
        return 1

    enricher = UniversalPayloadEnricher(
        taxonomy_catalog=_load_json(args.taxonomy_path),
        actuarial_gate_data=_load_json(args.actuarial_gate_path),
        forensic_ledger=_load_json(args.forensic_ledger_path),
        tenant_config=_load_json(args.tenant_config_path),
    )

    enriched_model = enricher.enrich(raw_payload=raw_payload, tower_id=args.tower_id)

    args.output_payload.parent.mkdir(parents=True, exist_ok=True)
    args.output_payload.write_text(
        enriched_model.model_dump_json(indent=2),
        encoding="utf-8",
    )
    logger.info("Enriched payload written to '%s'.", args.output_payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
