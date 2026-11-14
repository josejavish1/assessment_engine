"""Unit and architectural tests for the Cryptographic Provenance Enveloper.

Validates the Zero-Hallucination Epistemic Invariant of the Assessment Engine.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from assessment_engine.domain.provenance.provenance_enveloper import (
    EnvelopedMetric,
    ProvenanceClassification,
    ProvenanceEnveloper,
)


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
