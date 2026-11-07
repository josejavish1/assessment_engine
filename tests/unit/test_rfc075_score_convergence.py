"""Unit tests for RFC 075: Maturity Score Single Source of Truth (SSOT) & Cross-Deliverable Convergence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
)
from assessment_engine.application.services.tower_payload_hydrator import (
    TowerPayloadHydrator,
)


def test_rfc075_pillar_math_canonical_score_t3() -> None:
    """Verify that a tower with T3's exact pillar scores resolves to 2.52 and never 3.0."""
    t3_pillars = [
        {"pilar_id": "T3.P1", "score": 3.8},
        {"pilar_id": "T3.P2", "score": 2.2},
        {"pilar_id": "T3.P3", "score": 2.3},
        {"pilar_id": "T3.P4", "score": 2.3},
        {"pilar_id": "T3.P5", "score": 2.0},
    ]
    raw_payload: Dict[str, Any] = {
        "tower_code": "T3",
        "pillars_analysis": t3_pillars,
        "executive_summary": None,  # Intentionally None to reproduce legacy bug condition
    }

    score = TowerPayloadHydrator.compute_canonical_score(raw_payload, doc_lang="es")
    assert score == 2.52


def test_rfc075_payload_to_ast_resolves_canonical_score_no_fallback_to_three(tmp_path: Path) -> None:
    """Verify that PayloadToASTBridge extracts 2.52 without falling back to legacy '3.0'."""
    bridge = PayloadToASTBridge()
    blueprint_data = {
        "tower_id": "T3",
        "pillars_analysis": [
            {"pilar_id": "T3.P1", "score": 3.8},
            {"pilar_id": "T3.P2", "score": 2.2},
            {"pilar_id": "T3.P3", "score": 2.3},
            {"pilar_id": "T3.P4", "score": 2.3},
            {"pilar_id": "T3.P5", "score": 2.0},
        ],
        "executive_summary": None,
    }
    bp_file = tmp_path / "blueprint_t3_payload.json"
    with open(bp_file, "w", encoding="utf-8") as f:
        json.dump(blueprint_data, f)

    ctx = bridge._extract_conversion_context(
        blueprint_payload_path=str(bp_file),
        approved_annex_path="",
        override_locale="es",
    )

    assert ctx["display_score_str"] == "2,52 / 5,00"
    assert "2.52" in ctx["global_score"]
    assert "3,00" not in ctx["display_score_str"]


def test_rfc075_cross_deliverable_convergence_matrix(tmp_path: Path) -> None:
    """Verify that Tomo 1 compiler and Annex compiler produce 100% identical scores for all 10 towers."""
    compiler = Volume1AsisASTCompiler()
    bridge = PayloadToASTBridge()

    pillar_matrix = {
        "T1": [2.5, 1.7, 2.3, 4.0, 2.3],  # Mean = 2.56
        "T2": [2.8, 4.2, 1.5, 1.0, 2.8],  # Mean = 2.46
        "T3": [3.8, 2.2, 2.3, 2.3, 2.0],  # Mean = 2.52
        "T4": [2.5, 3.0, 3.8, 3.7, 3.5],  # Mean = 3.30
        "T5": [2.0, 3.5, 2.0, 2.2, 1.0],  # Mean = 2.14
        "T6": [3.2, 4.5, 1.8, 1.5, 3.0],  # Mean = 2.80
        "T7": [2.5, 2.2, 2.5, 3.2],       # Mean = 2.60
        "T8": [3.0, 2.5, 2.2, 2.2, 2.2],  # Mean = 2.42
        "T9": [4.0, 3.5, 3.2, 2.2, 2.8],  # Mean = 3.14
        "T10": [2.2, 2.5, 2.5, 2.5, 2.2], # Mean = 2.38
    }

    hydrated_towers: Dict[str, Dict[str, Any]] = {}
    for code, scores in pillar_matrix.items():
        payload: Dict[str, Any] = {
            "tower_code": code,
            "pillars_analysis": [{"score": s} for s in scores],
            "executive_summary": None,
        }
        score = TowerPayloadHydrator.compute_canonical_score(payload, doc_lang="es")
        payload["score"] = score
        payload["exact_score"] = score
        hydrated_towers[code] = payload

    # 1. Resolve scores in Tomo 1
    topology = compiler._resolve_domain_topology(
        global_payload={"heatmap": []},
        doc_lang="es",
        tower_payloads=hydrated_towers,
    )
    tomo1_scores = {code: score for code, _, score, _, _ in topology}

    # 2. Resolve scores in Annex bridge
    for code in pillar_matrix:
        bp_file = tmp_path / f"blueprint_{code.lower()}_payload.json"
        with open(bp_file, "w", encoding="utf-8") as f:
            json.dump(hydrated_towers[code], f)

        ctx = bridge._extract_conversion_context(
            blueprint_payload_path=str(bp_file),
            approved_annex_path="",
            override_locale="es",
        )
        annex_score = float(ctx["global_score"])

        # Assert 0.00 divergence between Tomo 1 and Annex!
        assert tomo1_scores[code] == pytest.approx(annex_score, abs=0.01), (
            f"Split-Brain detected in {code}: Tomo 1={tomo1_scores[code]} vs Annex={annex_score}"
        )
