"""
Phase B Characterization and Regression Test Suite: Ambiguous Entity Resolution ('3 y 4').

Verifies the AmbiguousEntityReference invariant:
1. AmbiguousEntityReference models unresolved entity references with ResolutionStatus.AMBIGUOUS.
2. When resolution_status == AMBIGUOUS, is_claim_allowed() strictly forbids materializing
   the ambiguous reference into concrete topology claims (e.g., 'clústeres 3 y 4', 'clusters 3 and 4',
   'agrupaciones 3 y 4', 'nodos de SimpliVity 3 y 4').
3. Permitted claims are restricted to neutral unconfirmed references, e.g., 'elementos 3 y 4 (según
   visualización en consola, sin correspondencia topológica formalizada)'.
4. All tower payloads in working/molins_fresh_e2e must be free of unauthorized concrete materializations.
"""

from pathlib import Path
import pytest

from assessment_engine.domain.ingestion.epistemic_fact_registry import (
    AmbiguousEntityReference,
    ResolutionStatus,
)
from assessment_engine.infrastructure.runtime_paths import ROOT


def test_ambiguous_entity_reference_model_validation():
    """1. AmbiguousEntityReference models unconfirmed spans with ResolutionStatus.AMBIGUOUS."""
    ref = AmbiguousEntityReference(
        reference_id="REF-MOLINS-NODES-3-4",
        raw_span="en 3 y 4 más carga",
        source_chunk_id="chunk_interview_infra_042",
        resolution_status=ResolutionStatus.AMBIGUOUS,
        candidate_entity_types=["HOST", "VIRTUAL_MACHINE", "NODE"],
    )
    assert ref.resolution_status == ResolutionStatus.AMBIGUOUS
    assert "without formal topology confirmation" in ref.allowed_semantic_framing


def test_ambiguous_entity_reference_claim_policy():
    """2. is_claim_allowed() rejects concrete materializations of ambiguous references."""
    ref = AmbiguousEntityReference(
        reference_id="REF-MOLINS-NODES-3-4",
        raw_span="en 3 y 4 más carga",
        source_chunk_id="chunk_interview_infra_042",
        resolution_status=ResolutionStatus.AMBIGUOUS,
        candidate_entity_types=["HOST", "VIRTUAL_MACHINE", "NODE"],
    )

    # Permitted neutral claim
    valid_claim = "Determinados elementos 3 y 4 observados en vCenter presentaban mayor carga, con correspondencia no confirmada."
    assert ref.is_claim_allowed(valid_claim) is True

    # Prohibited claims asserting concrete topologies
    prohibited_claims = [
        "Los clústeres 3 y 4 de cómputo presentan sobrecarga.",
        "Las agrupaciones 3 y 4 concentran la carga de control industrial.",
        "Clusters 3 and 4 experience excessive CPU load.",
        "Nodos de SimpliVity 3 y 4 registraron contención.",
    ]
    for claim in prohibited_claims:
        assert ref.is_claim_allowed(claim) is False, f"Prohibited claim was incorrectly allowed: '{claim}'"


def test_all_tower_payloads_ambiguous_entity_cleanliness():
    """3. All tower payloads in molins_fresh_e2e must not materialize ambiguous '3 y 4' as clusters/agrupaciones."""
    forbidden_terms = [
        "clústeres 3 y 4",
        "clusteres 3 y 4",
        "clusters 3 and 4",
        "agrupaciones 3 y 4",
        "nodos de simplivity 3 y 4",
        "nodos simplivity 3 y 4",
    ]

    violations = []
    fresh_dir = ROOT / "working" / "molins_fresh_e2e"
    for i in range(1, 11):
        tid = f"T{i}"
        bp_path = fresh_dir / tid / f"blueprint_{tid.lower()}_payload.json"
        if not bp_path.exists():
            continue
        text = bp_path.read_text(encoding="utf-8-sig").lower()
        for term in forbidden_terms:
            if term in text:
                violations.append(f"Tower {tid}: found forbidden ambiguous entity materialization '{term}'")

    assert not violations, "Ambiguous Entity Invariant violated:\n" + "\n".join(violations)
