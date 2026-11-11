"""Architectural Test: Deep Immutability of Payloads across Compilers (SR 11-7).

Asserts that compiling payloads into Word/AST nodes causes ZERO in-place mutations
to the input payload dictionaries or DTOs.
"""

from __future__ import annotations

import copy
from pathlib import Path

from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
)


def _build_test_compilation_fixtures() -> tuple[dict, dict]:
    global_payload = {
        "meta": {
            "client": "Acme Aerospace Global",
            "date": "November 2026",
            "version": "v1.0",
            "language": "en",
        },
        "domain_scope": "scoped",
        "heatmap": [
            {"id": "T1", "name": "Datacenter & Core Facilities", "score": 2.50, "ale": 150000.0},
        ],
        "financial_telemetry": {
            "corporate_ale": 150000.0,
            "annual_p90_var": 350000.0,
            "currency": "EUR",
        },
        "total_fair_ale": 150000.0,
        "total_fair_p90": 350000.0,
    }

    tower_payloads = {
        "T1": {
            "score": 2.50,
            "tower_name": "Datacenter & Core Facilities",
            "total_fair_ale": 150000.0,
            "total_fair_p90": 350000.0,
            "pillars_analysis": [
                {
                    "pillar_id": "T1.P1",
                    "pillar_name": "Power & Cooling",
                    "score": 2.50,
                    "health_check_asis": [
                        {
                            "node_id": "T1_F001",
                            "capability": "UPS Battery Degradation",
                            "severity": "CRITICAL",
                            "fair_ale_score": 150000.0,
                            "fair_p90_score": 350000.0,
                            "threat_event_frequency": 0.35,
                            "recovery_time_hours": 6.0,
                        }
                    ],
                }
            ],
        }
    }
    return global_payload, tower_payloads


def test_tomo_asis_compiler_deep_immutability(tmp_path: Path) -> None:
    """Verifies that Volume1AsisASTCompiler does not mutate input global_payload or tower_payloads in-place."""
    global_payload, tower_payloads = _build_test_compilation_fixtures()

    global_before = copy.deepcopy(global_payload)
    tower_before = copy.deepcopy(tower_payloads)

    out_docx = tmp_path / "Immutability_Test_Tomo1.docx"
    compiler = Volume1AsisASTCompiler()
    compiler.compile(
        global_payload=global_payload,
        tower_payloads=tower_payloads,
        output_docx_path=out_docx,
        doc_lang="en",
    )

    # Assert deep immutability: zero in-place mutations
    assert global_payload == global_before, "Compilation violated immutability on global_payload!"
    assert tower_payloads == tower_before, "Compilation violated immutability on tower_payloads!"
