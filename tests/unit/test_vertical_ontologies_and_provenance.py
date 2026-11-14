"""Unit and architectural tests for Phase 2: Multi-Vertical Ontologies & Provenance Enveloping.

Validates Phase 2 of ARGON_GLOBAL_TIER1_MASTER_PLAN.md.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from assessment_engine.domain.ontology.ontology_registry import (
    OntologyRegistry,
    get_ontology_registry,
)
from assessment_engine.domain.ontology.vertical_ontology import (
    VerticalOntology,
    VerticalSectorId,
)
from assessment_engine.domain.provenance.provenance_enveloper import (
    EnvelopedMetric,
    ProvenanceClassification,
    ProvenanceEnveloper,
)


def test_all_eight_sector_ontologies_loaded_and_valid():
    """Verify that all 8 industry sector ontologies are loaded with valid Pydantic schemas."""
    registry = get_ontology_registry()
    ontologies = registry.list_all_verticals()
    assert len(ontologies) == 8, f"Expected exactly 8 sector ontologies, found {len(ontologies)}"

    expected_sectors = {
        VerticalSectorId.MANUFACTURING_OT,
        VerticalSectorId.BANKING_CAPITAL_MARKETS,
        VerticalSectorId.HEALTHCARE_LIFESCIENCES,
        VerticalSectorId.RETAIL_ECOMMERCE,
        VerticalSectorId.ENERGY_UTILITIES,
        VerticalSectorId.TELECOMMUNICATIONS,
        VerticalSectorId.SAAS_DIGITAL_NATIVE,
        VerticalSectorId.PUBLIC_SECTOR_DEFENSE,
    }

    loaded_sectors = {o.vertical_id for o in ontologies}
    assert loaded_sectors == expected_sectors


def test_sector_classification_from_corpus():
    """Verify accurate deterministic sector classification based on technical token overlap."""
    registry = get_ontology_registry()

    # 1. Banking corpus
    banking_text = "We process SWIFT international payments through our core-banking ledger with HSM signing."
    assert registry.classify_sector_from_text(banking_text).vertical_id == VerticalSectorId.BANKING_CAPITAL_MARKETS

    # 2. Healthcare corpus
    health_text = "The hospital EHR and PACS DICOM imaging systems must comply with strict HIPAA patient privacy."
    assert registry.classify_sector_from_text(health_text).vertical_id == VerticalSectorId.HEALTHCARE_LIFESCIENCES

    # 3. SaaS / Digital Native corpus
    saas_text = "Our multi-tenant SaaS runs on Kubernetes microservices behind an Envoy ingress gateway with FinOps."
    assert registry.classify_sector_from_text(saas_text).vertical_id == VerticalSectorId.SAAS_DIGITAL_NATIVE

    # 4. Manufacturing OT corpus
    mfg_text = "Factory SCADA network connects to Siemens PLCs and industrial historians for plant weighbridges."
    assert registry.classify_sector_from_text(mfg_text).vertical_id == VerticalSectorId.MANUFACTURING_OT


def test_provenance_enveloper_empirical_fact():
    """Verify empirical fact enveloping with 1.0 confidence and SHA-256 fingerprint."""
    metric = ProvenanceEnveloper.wrap_empirical_fact(
        metric_name="cluster_host_count",
        value=6,
        source_citation="Transcript Molins 260721 Fairfly p.14",
    )

    assert metric.classification == ProvenanceClassification.EMPIRICAL_VERIFIED
    assert metric.value == 6
    assert metric.mathematical_confidence == 1.0
    assert len(metric.provenance_hash) == 64  # Valid SHA-256 hex string


def test_provenance_enveloper_actuarial_estimate():
    """Verify actuarial estimate enveloping with Bayesian confidence interval."""
    metric = ProvenanceEnveloper.wrap_actuarial_estimate(
        metric_name="status_quo_annualized_loss_expectancy_p90",
        value=95000.0,
        model_citation="Open FAIR Gamma-Poisson Conjugate Kernel (10k iterations)",
        confidence=0.90,
    )

    assert metric.classification == ProvenanceClassification.ACTUARIALLY_DERIVED
    assert metric.value == 95000.0
    assert metric.mathematical_confidence == 0.90
    assert len(metric.provenance_hash) == 64


def test_enveloped_metric_immutability():
    """Verify that enveloped metrics are strictly frozen and immutable."""
    metric = ProvenanceEnveloper.wrap_empirical_fact(
        metric_name="cpu_overcommit",
        value="Elevated",
        source_citation="Client Interview",
    )

    with pytest.raises(ValidationError):
        # Mutating frozen field must fail
        metric.value = "Low"
