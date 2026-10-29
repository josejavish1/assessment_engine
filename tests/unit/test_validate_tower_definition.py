"""Tests for tower definition validation schema and semantic rules."""

from __future__ import annotations

from pathlib import Path

import pytest

from assessment_engine.application.validate_tower_definition import (
    load_json,
    validate_tower_definition,
)


@pytest.fixture
def sample_valid_definition() -> dict:
    """Fixture providing a minimal structurally valid tower definition."""
    return {
        "tower_id": "T1",
        "tower_name": "Workplace & End User Services",
        "working_rules": ["Regla 1", "Regla 2"],
        "score_bands": {"1": "Básico", "5": "Líder"},
        "maturity_scale": {"1": "Inicial", "5": "Optimizado"},
        "pillars": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Digital Workplace Architecture",
                "weight_pct": 50,
                "kpis": [
                    {
                        "kpi_id": "T1.P1.K1",
                        "kpi_name": "Virtual Desktop Infrastructure",
                        "questions": [
                            {
                                "question_id": "T1.P1.K1.PR1",
                                "question_text": "¿Cuál es la tasa de adopción de VDI?",
                            }
                        ],
                    }
                ],
            },
            {
                "pillar_id": "T1.P2",
                "pillar_name": "Collaboration & Productivity",
                "weight_pct": 50,
                "kpis": [
                    {
                        "kpi_id": "T1.P2.K1",
                        "kpi_name": "Unified Communications",
                        "questions": [
                            {
                                "question_id": "T1.P2.K1.PR1",
                                "question_text": "¿Existe solución integrada de voz y vídeo?",
                            }
                        ],
                    }
                ],
            },
        ],
        "questions": [
            {
                "question_id": "T1.P1.K1.PR1",
                "pillar_id": "T1.P1",
                "kpi_id": "T1.P1.K1",
                "question_text": "¿Cuál es la tasa de adopción de VDI?",
            },
            {
                "question_id": "T1.P2.K1.PR1",
                "pillar_id": "T1.P2",
                "kpi_id": "T1.P2.K1",
                "question_text": "¿Existe solución integrada de voz y vídeo?",
            },
        ],
    }


def test_validate_real_tower_t1() -> None:
    """Certify that canonical engine tower definition T1 validates with 0 errors."""
    t1_path = Path("engine_config/towers/T1/tower_definition_T1.json")
    if not t1_path.exists():
        pytest.skip("T1 tower definition file not found.")

    data = load_json(t1_path)
    errors, _ = validate_tower_definition(data)
    assert errors == [], f"Canonical T1 failed validation: {errors}"


def test_validate_tower_definition_valid(sample_valid_definition: dict) -> None:
    """Verify that a well-formed definition passes validation with 0 errors."""
    errors, warnings = validate_tower_definition(sample_valid_definition)
    assert errors == []
    assert warnings == []


def test_validate_tower_definition_missing_required_keys(
    sample_valid_definition: dict,
) -> None:
    """Verify that missing top-level keys are detected."""
    del sample_valid_definition["score_bands"]
    del sample_valid_definition["tower_name"]

    errors, _ = validate_tower_definition(sample_valid_definition)
    assert any("score_bands" in e for e in errors)
    assert any("tower_name" in e for e in errors)


def test_validate_tower_definition_weight_sum_invalid(
    sample_valid_definition: dict,
) -> None:
    """Verify that pillar weights not summing to 100 are rejected."""
    sample_valid_definition["pillars"][0]["weight_pct"] = 30
    sample_valid_definition["pillars"][1]["weight_pct"] = 30  # Sum is 60

    errors, _ = validate_tower_definition(sample_valid_definition)
    assert any("weight_pct is 60" in e or "weight_pct es 60" in e for e in errors)


def test_validate_tower_definition_prefix_mismatch(
    sample_valid_definition: dict,
) -> None:
    """Verify that hierarchy prefix mismatch triggers descriptive errors."""
    sample_valid_definition["pillars"][0]["pillar_id"] = (
        "T2.P1"  # Belongs to T2, not T1
    )

    errors, _ = validate_tower_definition(sample_valid_definition)
    assert any("T2.P1 does not belong to tower T1" in e or "T2.P1 no pertenece" in e for e in errors)


def test_validate_tower_definition_duplicate_ids(sample_valid_definition: dict) -> None:
    """Verify that duplicate pillar or KPI IDs are caught."""
    sample_valid_definition["pillars"][1]["pillar_id"] = "T1.P1"  # Duplicate

    errors, _ = validate_tower_definition(sample_valid_definition)
    assert any("duplicate" in e.lower() or "duplicado" in e.lower() for e in errors)
