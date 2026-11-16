"""
Unit Test Suite for GATE-31.3: Cross-Tower Semantic Shielding.

Validates the Homomorphic Graph Projection algorithm:
1. When generating context for horizontal governance towers (like T8), all out-of-scope 
   ontological entities (e.g., PHYSICAL_INFRA, NETWORK_STORAGE) are homomorphically
   projected into their abstract hypernym equivalents (e.g., [Primary Colocation Facility]).
2. T8 is strictly shielded from specific brand names like 'Equinix', 'SCADA', 'Oracle',
   preventing the LLM from leaking these physical implementations into governance logic.
3. The context payload for T8 maintains high epistemic value for FinOps without 
   sacrificing cross-tower isolation.
"""

import pytest

from assessment_engine.infrastructure.cross_tower_graph_projector import (
    CrossTowerGraphProjector,
    OntologicalLayer,
    EvidenceChunk,
)


def test_gate_31_3_homomorphic_graph_projection_t8():
    """GATE-31.3: Projector masks out-of-scope ontology entities for T8."""
    raw_chunk = EvidenceChunk(
        chunk_id="chk_01",
        verbatim_text="El tráfico principal se rutea por Equinix NY4 usando BGP hacia la base de datos Oracle.",
        confidence=1.0,
        extracted_entities=["Equinix NY4", "BGP", "Oracle"],
        ontological_layer=OntologicalLayer.PHYSICAL_INFRA,
        hypernym_fallback="Enterprise IT Asset",
    )
    
    # Project the chunk for T8 Governance
    projected = CrossTowerGraphProjector.project_chunk(raw_chunk, target_tower_id="T8")
    
    # T8 should not receive physical infra specifics
    assert "Equinix" not in projected.verbatim_text
    assert "Oracle" not in projected.verbatim_text
    assert "BGP" not in projected.verbatim_text
    
    # The text should contain the hypernym replacements
    assert "[Enterprise IT Asset]" in projected.verbatim_text
    # Confidence should be slightly discounted due to abstraction
    assert projected.confidence == 0.85


def test_gate_31_3_preserves_in_scope_ontology_t1():
    """GATE-31.3: Projector preserves entities when the tower is cleared for that ontology."""
    raw_chunk = EvidenceChunk(
        chunk_id="chk_02",
        verbatim_text="El tráfico principal se rutea por Equinix NY4 usando BGP hacia la base de datos Oracle.",
        confidence=1.0,
        extracted_entities=["Equinix NY4", "BGP", "Oracle"],
        ontological_layer=OntologicalLayer.PHYSICAL_INFRA,
        hypernym_fallback="Enterprise IT Asset",
    )
    
    # Project the chunk for T1 Facilities (which is cleared for PHYSICAL_INFRA)
    projected = CrossTowerGraphProjector.project_chunk(raw_chunk, target_tower_id="T1")
    
    # T1 should receive the exact verbatim text with zero abstraction
    assert "Equinix NY4" in projected.verbatim_text
    assert projected.confidence == 1.0
