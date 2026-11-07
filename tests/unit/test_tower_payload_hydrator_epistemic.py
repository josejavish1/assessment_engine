"""Unit tests for TowerPayloadHydrator epistemic ledger integration (RFC 082 / RFC 083)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from assessment_engine.application.services.tower_payload_hydrator import (
    TowerPayloadHydrator,
)


def test_tower_payload_hydrator_loads_epistemic_ledger(tmp_path: Path) -> None:
    """Verify TowerPayloadHydrator reads epistemic ledger and attaches verified telemetry."""
    client_slug = "acme_corp"
    client_working_dir = tmp_path / "working" / client_slug
    client_working_dir.mkdir(parents=True, exist_ok=True)

    t1_dir = client_working_dir / "T1"
    t1_dir.mkdir(parents=True, exist_ok=True)
    raw_t1_payload: Dict[str, Any] = {
        "tower_code": "T1",
        "tower_name": "Physical Data Center & Facilities",
        "pillars_analysis": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Power & Electrical Continuity",
                "score": 3.0,
            }
        ],
    }
    (t1_dir / "blueprint_t1_payload.json").write_text(
        json.dumps(raw_t1_payload), encoding="utf-8"
    )

    sample_ledger: Dict[str, Any] = {
        "client_id": client_slug,
        "schema_version": "2.1.0-RFC082",
        "epistemic_entries": [
            {
                "entry_id": "EVD-0001",
                "domain_taxonomy_ref": "T1",
                "canonical_assertion": "T1: Redundant UPS infrastructure verified.",
                "truth_status": "VERIFIED_CONSISTENT",
                "composite_confidence": 0.95,
                "supporting_fragments": [
                    {
                        "fragment_id": "00000000-0000-0000-0000-000000000001",
                        "polarity": "POSITIVE",
                        "canonical_assertion": "Dual UPS paths active under continuous telemetry.",
                        "metadata": {
                            "resolved_entities": [
                                {
                                    "original_token": "Simply",
                                    "canonical_entity": "HPE SimpliVity",
                                    "confidence": 1.0,
                                }
                            ]
                        },
                    },
                    {
                        "fragment_id": "00000000-0000-0000-0000-000000000002",
                        "polarity": "NEGATIVE",
                        "canonical_assertion": "Absence of cold aisle containment in primary room.",
                        "metadata": {},
                    },
                ],
            }
        ],
    }
    (client_working_dir / "epistemic_ledger.json").write_text(
        json.dumps(sample_ledger), encoding="utf-8"
    )

    global_payload: Dict[str, Any] = {
        "meta": {"client": "Acme Corp", "currency": "EUR"},
        "financial_telemetry": {
            "annual_revenue": 50_000_000.0,
            "currency": "EUR",
            "domain_weights": {"T1": 120_000.0},
        },
    }

    hydrated_map = TowerPayloadHydrator.load_and_hydrate_all_towers(
        repo_root=tmp_path,
        global_payload=global_payload,
        doc_lang="en",
        target_towers=["T1"],
        persist_to_disk=False,
    )

    assert "T1" in hydrated_map
    t1 = hydrated_map["T1"]
    assert "epistemic_ledger_entry" in t1
    assert t1["epistemic_truth_status"] == "VERIFIED_CONSISTENT"
    assert t1["epistemic_composite_confidence"] == 0.95
    assert len(t1["epistemic_supporting_fragments"]) == 2
    assert "Dual UPS paths active under continuous telemetry." in t1["epistemic_positive_assertions"]
    assert "Absence of cold aisle containment in primary room." in t1["epistemic_negative_assertions"]
    assert len(t1["verified_entities"]) == 1
    assert t1["verified_entities"][0]["canonical_entity"] == "HPE SimpliVity"
