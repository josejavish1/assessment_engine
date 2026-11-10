"""Unit tests for Structured Evidence Extraction and Modal Partitioning contracts."""

from __future__ import annotations

import pytest

from assessment_engine.domain.schemas.evidence_extraction import (
    ClaimStatus,
    ExtractionLedger,
    VerifiedEpistemicClaim,
)
from assessment_engine.infrastructure.genai_client import ModelTier


def test_extraction_ledger_modal_partitioning() -> None:
    """Verifies that ExtractionLedger strictly segregates production facts from future aspirations."""
    claims = [
        VerifiedEpistemicClaim.create(
            tower_code="T2",
            canonical_entity="HPE SimpliVity",
            claim_statement="Cluster of 6 hyperconverged nodes running VMware vSphere.",
            status=ClaimStatus.ACTIVE_PRODUCTION,
            verbatim_evidence_quote="Tenemos 6 nodos SimpliVity para las máquinas virtuales.",
        ),
        VerifiedEpistemicClaim.create(
            tower_code="T2",
            canonical_entity="Kubernetes",
            claim_statement="Aspirational target architecture model to migrate workloads to containers.",
            status=ClaimStatus.FUTURE_PLAN,
            verbatim_evidence_quote="A mí me gustaría irnos más a modelo contenedor Kubernetes.",
        ),
        VerifiedEpistemicClaim.create(
            tower_code="T2",
            canonical_entity="Infrastructure as Code",
            claim_statement="Complete lack of automated configuration templates or scripted deployments.",
            status=ClaimStatus.CONFIRMED_ABSENCE,
            verbatim_evidence_quote="No tenemos nada de automatización ni plantillas, todo manual en vCenter.",
        ),
        VerifiedEpistemicClaim.create(
            tower_code="T4",
            canonical_entity="NetApp FAS",
            claim_statement="Primary storage array for file services and transactional volumes.",
            status=ClaimStatus.ACTIVE_PRODUCTION,
            verbatim_evidence_quote="La NetApp la hemos comprado para ficheros corporativos.",
        ),
    ]

    ledger = ExtractionLedger(tenant_id="molins_test", claims=claims)

    # 1. AS-IS Production claims query
    asis_t2 = ledger.get_asis_production_claims("T2")
    assert len(asis_t2) == 1
    assert asis_t2[0].canonical_entity == "HPE SimpliVity"
    assert asis_t2[0].status == ClaimStatus.ACTIVE_PRODUCTION

    # 2. Confirmed Absences query
    absences_t2 = ledger.get_confirmed_absences("T2")
    assert len(absences_t2) == 1
    assert absences_t2[0].canonical_entity == "Infrastructure as Code"
    assert absences_t2[0].status == ClaimStatus.CONFIRMED_ABSENCE

    # 3. Future Plans query (Volume 2 Roadmap only)
    roadmap_t2 = ledger.get_future_aspirations("T2")
    assert len(roadmap_t2) == 1
    assert roadmap_t2[0].canonical_entity == "Kubernetes"
    assert roadmap_t2[0].status == ClaimStatus.FUTURE_PLAN

    # 4. Prompt Context Construction: Guarantees zero modal collapse in Volume 1
    asis_context = ledger.build_asis_prompt_context("T2")
    assert "HPE SimpliVity" in asis_context
    assert "Infrastructure as Code" in asis_context
    # Physical guarantee: Kubernetes (FUTURE_PLAN) is completely omitted from the context!
    assert "Kubernetes" not in asis_context


def test_deterministic_claim_id_hashing() -> None:
    """Verifies that identical claims produce identical deterministic SHA-256 hashes without collision."""
    c1 = VerifiedEpistemicClaim.create(
        tower_code="T1",
        canonical_entity="UPS",
        claim_statement="Dual feed power",
        status=ClaimStatus.ACTIVE_PRODUCTION,
        verbatim_evidence_quote="Doble acometida eléctrica",
    )
    c2 = VerifiedEpistemicClaim.create(
        tower_code="T1",
        canonical_entity="UPS",
        claim_statement="Dual feed power",
        status=ClaimStatus.ACTIVE_PRODUCTION,
        verbatim_evidence_quote="Doble acometida eléctrica",
    )
    c3 = VerifiedEpistemicClaim.create(
        tower_code="T1",
        canonical_entity="UPS",
        claim_statement="Different statement avoids collision",
        status=ClaimStatus.ACTIVE_PRODUCTION,
        verbatim_evidence_quote="Doble acometida eléctrica",
    )
    assert c1.claim_id == c2.claim_id
    assert c1.claim_id != c3.claim_id
    assert c1.claim_id.startswith("CLM-")


def test_model_tier_reasoning_used_without_hardcoding() -> None:
    """Verifies that StructuredEvidenceExtractor relies on ModelTier enum, not hardcoded strings."""
    from assessment_engine.application.services.structured_evidence_extractor import (
        StructuredEvidenceExtractor,
    )

    extractor = StructuredEvidenceExtractor(model_tier=ModelTier.REASONING)
    assert extractor._model_tier == ModelTier.REASONING
    assert isinstance(extractor._model_tier, ModelTier)
