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


def _load_json(path: Path, optional: bool = False) -> dict:
    """Loads a JSON file with UTF-8-sig encoding, enforcing fail-fast validation."""
    if not path.exists():
        if optional:
            logger.info("Optional file not present at '%s'; defaulting to empty dictionary.", path)
            return {}
        raise FileNotFoundError(f"Mandatory configuration or payload file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    """Executes the enrichment pipeline stage with fail-fast enforcement."""
    args = parse_args()

    # Enforce fail-fast on mandatory files
    raw_payload = _load_json(args.input_payload, optional=False)
    taxonomy_catalog = _load_json(args.taxonomy_path, optional=False)
    tenant_config = _load_json(args.tenant_config_path, optional=False)

    # Actuarial and forensic ledger files are optional if uncalibrated yet
    actuarial_gate_data = _load_json(args.actuarial_gate_path, optional=True)
    forensic_ledger = _load_json(args.forensic_ledger_path, optional=True)

    enricher = UniversalPayloadEnricher(
        taxonomy_catalog=taxonomy_catalog,
        actuarial_gate_data=actuarial_gate_data,
        forensic_ledger=forensic_ledger,
        tenant_config=tenant_config,
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
