"""Unit tests for ScoreReconciler and MathematicalIntegrity domain services.

Verifies deterministic SSOT projection, preservation of qualitative narratives,
split-brain error detection, and mathematical dot-product invariants.
"""

from __future__ import annotations

import pytest

from assessment_engine.domain.services.score_reconciler import (
    QuantitativeSplitBrainError,
    reconcile_tower_scores,
)
from assessment_engine.domain.validation.mathematical_integrity import (
    MathematicalIntegrityViolation,
    assert_tower_mathematical_integrity,
)


@pytest.fixture
def mock_scoring_ssot() -> dict:
    """Authoritative output from run_scoring.py (e.g. Tower 1 with score 2.61)."""
    return {
        "tower_id": "T1",
        "tower_name": "Physical Data Center & Facilities",
        "tower_score_exact": 2.6067,
        "tower_score_display_1d": 2.6,
        "pillar_scores": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Power & Electrical Continuity",
                "weight_pct": 24,
                "score_exact": 2.50,
            },
            {
                "pillar_id": "T1.P2",
                "pillar_name": "Cooling & Environmental Control",
                "weight_pct": 20,
                "score_exact": 1.6667,
            },
            {
                "pillar_id": "T1.P3",
                "pillar_name": "Physical Security & Access Control",
                "weight_pct": 16,
                "score_exact": 2.3333,
            },
            {
                "pillar_id": "T1.P4",
                "pillar_name": "Fire Protection & Safety",
                "weight_pct": 22,
                "score_exact": 4.00,
            },
            {
                "pillar_id": "T1.P5",
                "pillar_name": "Facilities Operations & Maintenance",
                "weight_pct": 18,
                "score_exact": 2.3333,
            },
        ],
    }


@pytest.fixture
def corrupted_llm_payload() -> dict:
    """Mock corrupted LLM payload (simulating the split-brain bug observed in production)."""
    return {
        "tower_id": "T1",
        "score": 2.61,
        "pillars_analysis": [
            {
                "pillar_id": "T1.P1",
                "pillar_name": "Power & Electrical Continuity",
                "score": 2.20,  # Hallucinated
                "weight": 0.20,
                "executive_narrative": "Power distribution lacks per-branch metering.",
                "health_check_asis": [{"node_id": "t1-hc-01", "finding": "SPOF in ATS switch"}],
                "epistemic_status": "VERIFIED_DISSONANT",
            },
            {
                "pillar_id": "T1.P2",
                "pillar_name": "Cooling & Environmental Control",
                "score": 2.00,  # Hallucinated
                "weight": 0.20,
                "executive_narrative": "CRAC units lack cold-aisle containment.",
                "health_check_asis": [{"node_id": "t1-hc-02", "finding": "Thermal recirculation"}],
                "epistemic_status": "VERIFIED_DISSONANT",
            },
            {
                "pillar_id": "T1.P3",
                "pillar_name": "Physical Security & Access Control",
                "score": 2.30,  # Hallucinated
                "weight": 0.20,
                "executive_narrative": "Manual sign-in logbook for facility visitors.",
                "health_check_asis": [{"node_id": "t1-hc-03", "finding": "Keypad door access only"}],
                "epistemic_status": "CONVERGENT",
            },
            {
                "pillar_id": "T1.P4",
                "pillar_name": "Fire Protection & Safety",
                "score": 2.40,  # Hallucinated (official is 4.00)
                "weight": 0.20,
                "executive_narrative": "Clean-agent gas suppression certified recently.",
                "health_check_asis": [{"node_id": "t1-hc-04", "finding": "VESDA deployed"}],
                "epistemic_status": "CONVERGENT",
            },
            {
                "pillar_id": "T1.P5",
                "pillar_name": "Facilities Operations & Maintenance",
                "score": 2.30,  # Hallucinated
                "weight": 0.20,
                "executive_narrative": "Maintenance records kept in spreadsheet.",
                "health_check_asis": [{"node_id": "t1-hc-05", "finding": "Lack of DCIM"}],
                "epistemic_status": "CONVERGENT",
            },
        ],
    }


def test_reconciler_eradicates_hallucinated_scores(
    corrupted_llm_payload: dict, mock_scoring_ssot: dict
) -> None:
    # 1. Corrupted payload fails mathematical integrity
    with pytest.raises(MathematicalIntegrityViolation, match="SPLIT-BRAIN DETECTED"):
        assert_tower_mathematical_integrity(corrupted_llm_payload)

    # 2. Reconcile with SSOT
    healed_payload = reconcile_tower_scores(corrupted_llm_payload, mock_scoring_ssot)

    # 3. Assert healed payload now satisfies mathematical integrity
    assert_tower_mathematical_integrity(healed_payload)

    # 4. Verify exact pillar score restoration
    pillars = healed_payload["pillars_analysis"]
    assert pillars[0]["score"] == 2.50
    assert pillars[0]["weight_pct"] == 24.0
    assert pillars[1]["score"] == 1.67
    assert pillars[1]["weight_pct"] == 20.0
    assert pillars[2]["score"] == 2.33
    assert pillars[2]["weight_pct"] == 16.0
    assert pillars[3]["score"] == 4.00
    assert pillars[3]["weight_pct"] == 22.0
    assert pillars[4]["score"] == 2.33
    assert pillars[4]["weight_pct"] == 18.0


def test_reconciler_preserves_narratives_and_findings(
    corrupted_llm_payload: dict, mock_scoring_ssot: dict
) -> None:
    healed_payload = reconcile_tower_scores(corrupted_llm_payload, mock_scoring_ssot)
    p1 = healed_payload["pillars_analysis"][0]

    assert p1["executive_narrative"] == "Power distribution lacks per-branch metering."
    assert len(p1["health_check_asis"]) == 1
    assert p1["health_check_asis"][0]["node_id"] == "t1-hc-01"
    assert p1["epistemic_status"] == "VERIFIED_DISSONANT"


def test_reconciler_cardinality_violation(mock_scoring_ssot: dict) -> None:
    invalid_payload = {
        "tower_id": "T1",
        "score": 2.61,
        "pillars_analysis": [{"pillar_id": "T1.P1", "score": 2.5}],  # Only 1 pillar instead of 5
    }
    with pytest.raises(QuantitativeSplitBrainError, match="Cardinality violation"):
        reconcile_tower_scores(invalid_payload, mock_scoring_ssot)


def test_reconciler_tower_id_mismatch(
    corrupted_llm_payload: dict, mock_scoring_ssot: dict
) -> None:
    corrupted_llm_payload["tower_id"] = "T2"
    with pytest.raises(QuantitativeSplitBrainError, match="Topology mismatch"):
        reconcile_tower_scores(corrupted_llm_payload, mock_scoring_ssot)


def test_mathematical_integrity_percentage_and_normalized_weights() -> None:
    # Test normalized weights (sum == 1.0)
    normalized_payload = {
        "tower_id": "T1",
        "score": 3.00,
        "pillars_analysis": [
            {"pillar_id": "P1", "score": 2.00, "weight": 0.50},
            {"pillar_id": "P2", "score": 4.00, "weight": 0.50},
        ],
    }
    assert_tower_mathematical_integrity(normalized_payload)

    # Test percentage weights (sum == 100.0)
    percentage_payload = {
        "tower_id": "T1",
        "score": 3.00,
        "pillars_analysis": [
            {"pillar_id": "P1", "score": 2.00, "weight_pct": 50.0},
            {"pillar_id": "P2", "score": 4.00, "weight_pct": 50.0},
        ],
    }
    assert_tower_mathematical_integrity(percentage_payload)


def test_empirical_supremacy_rejects_survey_inflation() -> None:
    """RFC-085 (Empirical Supremacy): Rejects survey inflation (>1.0 delta) when empirical score is foundational (<=1.59)."""
    survey_ssot = {
        "tower_id": "T2",
        "tower_score_exact": 2.46,
        "pillar_scores": [
            {"pillar_id": "T2.P1", "score_exact": 2.75, "weight_pct": 22},
            {"pillar_id": "T2.P2", "score_exact": 4.25, "weight_pct": 19},  # Survey delusion
            {"pillar_id": "T2.P3", "score_exact": 1.50, "weight_pct": 21},
            {"pillar_id": "T2.P4", "score_exact": 1.00, "weight_pct": 18},
            {"pillar_id": "T2.P5", "score_exact": 2.75, "weight_pct": 20},
        ],
    }

    empirical_payload = {
        "tower_id": "T2",
        "score": 1.89,
        "pillars_analysis": [
            {"pillar_id": "T2.P1", "score": 2.75},
            {"pillar_id": "T2.P2", "score": 1.25},  # Discovery proved zero containers
            {"pillar_id": "T2.P3", "score": 1.50},
            {"pillar_id": "T2.P4", "score": 1.00},
            {"pillar_id": "T2.P5", "score": 2.75},
        ],
    }

    reconciled = reconcile_tower_scores(empirical_payload, survey_ssot)

    # T2.P2 must enforce empirical score 1.25, NOT 4.25
    p2 = [p for p in reconciled["pillars_analysis"] if p["pillar_id"] == "T2.P2"][0]
    assert p2["score"] == 1.25
    assert p2["survey_declared_score"] == 4.25
    assert p2["perception_gap_delta"] == 3.0
    assert p2["perception_gap_warning"] is True

    # Tower root score must be recomputed as the mathematical dot product
    assert reconciled["score"] == pytest.approx(1.89, rel=1e-2)
    assert_tower_mathematical_integrity(reconciled)


def test_has_empirical_absence_evidence_patterns() -> None:
    """Verify empirical absence and embryonic pattern recognition."""
    from assessment_engine.domain.services.score_reconciler import (
        _has_empirical_absence_evidence,
    )

    # Core English absence patterns
    assert _has_empirical_absence_evidence("Client lacks automated provisioning tools") is True
    assert _has_empirical_absence_evidence("Found zero containers deployed in production") is True
    assert _has_empirical_absence_evidence("Container platform is non-existent") is True
    assert _has_empirical_absence_evidence("Adoption remains in an embryonic state") is True
    assert _has_empirical_absence_evidence("Current initiative is purely a proof of concept (poc)") is True

    # Negative lookahead: zero-trust and zero-downtime are NOT absence indicators
    assert _has_empirical_absence_evidence("Mature zero-trust architecture deployed") is False
    assert _has_empirical_absence_evidence("Enterprise zero-downtime cluster topology") is False
    assert _has_empirical_absence_evidence("Standard active operations and documented procedures") is False

    # Extra tokens via injection (e.g. localized synonyms)
    assert _has_empirical_absence_evidence("No dispone de herramientas", extra_tokens=["no dispone"]) is True

