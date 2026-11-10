"""Deterministic Test Oracle for Phase 1: Semantic Epistemic Router (RFC 084).

Comprehensive coverage across:
1. Proposition-level chunking without arbitrary line truncation.
2. Cross-lingual semantic affinity routing across 10 technology towers without hardcoded keyword lists.
3. The 'Needle in a Haystack' Recall Gate (line 4,200 in 5,000-line transcript).
4. EpistemicContextPacket structural typing and Technical English decoupling.
5. Mathematical edge cases: empty vectors, cosine similarities, polarities, speaker parsing, custom taxonomies.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import pytest

from assessment_engine.application.services.semantic_epistemic_router import (
    CANONICAL_TOWERS,
    EpistemicContextPacket,
    EpistemicGraphRouter,
    SemanticEpistemicRouter,
    SemanticProposition,
    _compute_tf_vector,
    _cosine_similarity,
    _extract_strings_recursive,
    _infer_polarity,
    _parse_speaker_and_body,
    _tokenize_and_stem,
)


def test_epistemic_context_packet_structure() -> None:
    """Verifies the typed contract of EpistemicContextPacket."""
    prop = SemanticProposition(
        text="Core routing switches lack redundant power supplies.",
        turn_index=12,
        speaker="Lead Infrastructure Engineer",
        polarity="NEGATIVE",
    )

    # Immutability verification (kills frozen=True -> False mutant)
    with pytest.raises(dataclasses.FrozenInstanceError):
        prop.text = "Attempted mutation"  # type: ignore[misc]

    packet = EpistemicContextPacket(
        tower_code="T3",
        propositions=[prop],
        semantic_density_score=0.88,
        epistemic_state="OBSERVED_EXPLICIT",
    )

    assert packet.tower_code == "T3"
    assert len(packet.propositions) == 1
    assert packet.propositions[0].turn_index == 12
    assert packet.propositions[0].polarity == "NEGATIVE"
    assert packet.epistemic_state == "OBSERVED_EXPLICIT"
    assert 0.0 <= packet.semantic_density_score <= 1.0

    assert packet.tower_code == "T3"
    assert len(packet.propositions) == 1
    assert packet.propositions[0].turn_index == 12
    assert packet.propositions[0].polarity == "NEGATIVE"
    assert packet.epistemic_state == "OBSERVED_EXPLICIT"
    assert 0.0 <= packet.semantic_density_score <= 1.0


def test_proposition_chunking_lossless() -> None:
    """Verifies that transcript chunking preserves 100% of input statements."""
    router = EpistemicGraphRouter()
    raw_lines = [
        "Speaker A: Good morning everyone, let's start the architecture assessment.",
        "   ",
        "",
        "Speaker B: Our primary concern is the hypervisor cluster approaching 94% memory utilization.",
        "Speaker A: Are there automated evacuation routines in place?",
        "Speaker B: None whatsoever. Manual vMotion is required for any maintenance window.",
    ]

    propositions = router.chunk_transcript(raw_lines)
    # The two blank lines should be safely skipped, leaving 4 valid propositions
    assert len(propositions) == 4
    assert any("memory utilization" in p.text for p in propositions)
    assert any("Manual vMotion" in p.text for p in propositions)
    assert propositions[0].speaker == "Speaker A"
    assert propositions[1].speaker == "Speaker B"


def test_multi_label_semantic_affinity_routing() -> None:
    """Verifies multi-label routing for complex cross-cutting enterprise assertions."""
    router = EpistemicGraphRouter()

    assertion = (
        "The recent Broadcom renewal freeze impedes migrating legacy CentOS hypervisor "
        "clusters while driving up unbudgeted operational licensing liabilities and leaving critical CVE security vulnerabilities unpatched."
    )

    packets = router.route_transcript([assertion])

    assert isinstance(packets, dict)
    assert len(packets) == 10

    t2_packet = packets.get("T2")
    t6_packet = packets.get("T6")

    assert t2_packet is not None
    assert t6_packet is not None

    t2_texts = " ".join(p.text for p in t2_packet.propositions)
    t6_texts = " ".join(p.text for p in t6_packet.propositions)

    assert "Broadcom" in t2_texts or "hypervisor" in t2_texts
    assert "Broadcom" in t6_texts or "CVE" in t6_texts or "unpatched" in t6_texts or "vulnerabilities" in t6_texts


def test_needle_in_a_haystack_gate_5000_lines() -> None:
    """Gate 1: Needle in a Haystack recall verification.

    Generates 5,000 lines of neutral background dialog and injects a single critical
    risk statement at index 4,200. Verifies 100% recall and zero context truncation.
    """
    router = EpistemicGraphRouter()

    synthetic_transcript = [
        f"Turn {i}: Reviewing standard weekly operational status and routine cadence updates."
        for i in range(5000)
    ]

    needle_index = 4200
    needle_text = (
        "Our legacy Solaris 10 jumpbox in the industrial DMZ has an expired TLS 1.0 "
        "certificate and unpatched privilege escalation vulnerabilities with no vendor support."
    )
    synthetic_transcript[needle_index] = f"Turn {needle_index}: {needle_text}"

    packets = router.route_transcript(synthetic_transcript)

    assert "T6" in packets
    t6_props = packets["T6"].propositions

    matching_props = [p for p in t6_props if "Solaris 10" in p.text or "TLS 1.0" in p.text]
    assert len(matching_props) >= 1
    assert matching_props[0].turn_index == needle_index


def test_unobserved_blindspot_state_on_silent_domains() -> None:
    """Verifies that towers receiving zero relevant propositions enter UNOBSERVED_BLINDSPOT state."""
    router = EpistemicGraphRouter()

    pure_storage_transcript = [
        "We maintain NetApp MetroCluster SAN arrays replicated synchronously over dark fiber.",
        "Snapshot retention is 30 days on immutable secondary storage tier.",
    ]

    packets = router.route_transcript(pure_storage_transcript)

    assert packets["T4"].epistemic_state == "OBSERVED_EXPLICIT"
    assert len(packets["T4"].propositions) >= 1

    silent_towers = [t_code for t_code, pkt in packets.items() if len(pkt.propositions) == 0]
    assert len(silent_towers) > 0
    for t_code in silent_towers:
        assert packets[t_code].epistemic_state == "UNOBSERVED_BLINDSPOT"
        assert packets[t_code].semantic_density_score == 0.0


def test_polarity_inference_variants() -> None:
    """Tests positive, negative, and neutral polarity detection."""
    assert _infer_polarity("The cluster has unpatched critical vulnerability and outage risk") == "NEGATIVE"
    assert _infer_polarity("We have automated redundant synchronous ha clusters") == "POSITIVE"
    assert _infer_polarity("The meeting covered general scheduling and roadmap") == "NEUTRAL"
    # Equal hits between positive and negative default to neutral
    assert _infer_polarity("The redundant automated cluster suffered an unpatched outage") == "NEUTRAL"


def test_speaker_parsing_boundaries() -> None:
    """Tests speaker extraction with standard, missing, or malformed prefixes."""
    assert _parse_speaker_and_body("Alice: Storage is full") == ("Alice", "Storage is full")
    assert _parse_speaker_and_body("Chief Architect / VP: Network is degraded") == ("Participant", "Chief Architect / VP: Network is degraded")
    assert _parse_speaker_and_body("Just a statement without colon") == ("Participant", "Just a statement without colon")
    assert _parse_speaker_and_body(": Invalid empty prefix") == ("Participant", ": Invalid empty prefix")


def test_vector_and_similarity_edge_cases() -> None:
    """Tests sparse term-frequency and cosine similarity math."""
    # Empty inputs
    assert _compute_tf_vector([]) == {}
    assert _cosine_similarity({}, {"a": 1.0}) == 0.0
    assert _cosine_similarity({"a": 1.0}, {}) == 0.0
    assert _cosine_similarity({}, {}) == 0.0

    # Orthogonal vectors
    vec1 = _compute_tf_vector(["hypervisor", "cluster"])
    vec2 = _compute_tf_vector(["generator", "cooling"])
    assert _cosine_similarity(vec1, vec2) == 0.0

    # Identical vectors
    assert round(_cosine_similarity(vec1, vec1), 4) == 1.0

    # Sublinear scaling
    sublinear_vec = _compute_tf_vector(["hypervisor", "hypervisor", "cluster"], sublinear=True)
    assert len(sublinear_vec) == 2


def test_recursive_json_string_extractor() -> None:
    """Tests _extract_strings_recursive across scalar, list, and nested dicts."""
    data = {
        "title": "Compute",
        "nested": ["cluster", {"sub": "virtualization"}],
        "count": 42,
    }
    strings = _extract_strings_recursive(data)
    assert "Compute" in strings
    assert "cluster" in strings
    assert "virtualization" in strings
    assert 42 not in strings


def test_custom_taxonomy_loading(tmp_path: Path) -> None:
    """Tests dynamic taxonomy loading with valid and invalid paths."""
    # Invalid non-existent file
    router_fallback = EpistemicGraphRouter(taxonomy_path=tmp_path / "non_existent.json")
    assert len(router_fallback._tower_corpuses) == len(CANONICAL_TOWERS)

    # Valid custom json file
    custom_taxonomy = {
        "towers": {
            "T1": {"name": "Bespoke Facility Datacenter"},
        }
    }
    custom_file = tmp_path / "custom_taxonomy.json"
    custom_file.write_text(json.dumps(custom_taxonomy), encoding="utf-8")

    router_custom = EpistemicGraphRouter(taxonomy_path=custom_file)
    assert "Bespoke" in router_custom._tower_corpuses["T1"]


def test_alias_semantic_epistemic_router() -> None:
    """Ensures SemanticEpistemicRouter alias is identical to EpistemicGraphRouter."""
    assert SemanticEpistemicRouter is EpistemicGraphRouter


def test_compute_affinities_empty_text() -> None:
    """Ensures empty text returns 0.0 for all canonical towers."""
    router = EpistemicGraphRouter()
    affinities = router.compute_affinities("")
    assert len(affinities) == 10
    assert all(score == 0.0 for score in affinities.values())


def test_route_verified_claims_model_driven_modality() -> None:
    """Verifies that route_verified_claims maps typed epistemic status directly without keyword lists."""
    from assessment_engine.application.services.semantic_epistemic_router import (
        EpistemicGraphRouter,
        EpistemicModality,
    )
    from assessment_engine.domain.schemas.evidence_extraction import (
        ClaimStatus,
        ExtractionLedger,
        VerifiedEpistemicClaim,
    )

    ledger = ExtractionLedger(
        tenant_id="test_tenant",
        claims=[
            VerifiedEpistemicClaim.create(
                tower_code="T2",
                canonical_entity="NetApp",
                claim_statement="Storage array for corporate files",
                status=ClaimStatus.ACTIVE_PRODUCTION,
                verbatim_evidence_quote="La NetApp la hemos comprado para ficheros",
            ),
            VerifiedEpistemicClaim.create(
                tower_code="T2",
                canonical_entity="Kubernetes",
                claim_statement="Aspirational target to migrate to containers",
                status=ClaimStatus.FUTURE_PLAN,
                verbatim_evidence_quote="A mí me gustaría irnos más a modelo contenedor Kubernetes",
            ),
            VerifiedEpistemicClaim.create(
                tower_code="T2",
                canonical_entity="Infrastructure as Code",
                claim_statement="Zero automation tools in vCenter",
                status=ClaimStatus.CONFIRMED_ABSENCE,
                verbatim_evidence_quote="Carecemos de herramientas de automatización",
            ),
        ],
    )

    router = EpistemicGraphRouter()
    packets = router.route_verified_claims(ledger)
    t2_packet = packets["T2"]

    assert len(t2_packet.propositions) == 3
    asis_facts = t2_packet.get_asis_facts()
    assert len(asis_facts) == 2
    assert asis_facts[0].modality == EpistemicModality.FACT_PRODUCTION_ASIS
    assert asis_facts[1].modality == EpistemicModality.TECHNICAL_ABSENCE_GAP

    tobe_wishes = t2_packet.get_tobe_aspirations()
    assert len(tobe_wishes) == 1
    assert tobe_wishes[0].modality == EpistemicModality.ASPIRATIONAL_TOBE


def test_epistemic_context_packet_get_asis_facts_omits_wishes() -> None:
    """Verifies that get_asis_facts strictly omits future TO-BE wishes from AS-IS context."""
    from assessment_engine.application.services.semantic_epistemic_router import (
        EpistemicContextPacket,
        EpistemicModality,
        SemanticProposition,
    )

    packet = EpistemicContextPacket(
        tower_code="T2",
        propositions=[
            SemanticProposition(text="6 nodos HPE SimpliVity con VMware", turn_index=1, modality=EpistemicModality.FACT_PRODUCTION_ASIS),
            SemanticProposition(text="queríamos empezar a usar contenedores", turn_index=2, modality=EpistemicModality.ASPIRATIONAL_TOBE),
            SemanticProposition(text="me gustaría ir a Kubernetes", turn_index=3, modality=EpistemicModality.ASPIRATIONAL_TOBE),
            SemanticProposition(text="sin herramientas de automatización", turn_index=4, modality=EpistemicModality.TECHNICAL_ABSENCE_GAP),
        ],
        semantic_density_score=0.85,
        epistemic_state="OBSERVED_EXPLICIT",
    )

    asis_facts = packet.get_asis_facts()
    assert len(asis_facts) == 2
    assert all(p.modality != EpistemicModality.ASPIRATIONAL_TOBE for p in asis_facts)
    assert asis_facts[0].text == "6 nodos HPE SimpliVity con VMware"
    assert asis_facts[1].text == "sin herramientas de automatización"

    tobe_wishes = packet.get_tobe_aspirations()
    assert len(tobe_wishes) == 2
    assert all(p.modality == EpistemicModality.ASPIRATIONAL_TOBE for p in tobe_wishes)



def test_context_packet_density_scaling() -> None:
    """Kills arithmetic operator mutations (* vs //) in density calculation."""
    router = EpistemicGraphRouter()
    prop = SemanticProposition(
        text="Compute cluster virtualization",
        turn_index=0,
        affinity_scores={"T2": 0.20},
    )
    # With * 3.5, 0.20 * 3.5 = 0.70. With // 3.5, 0.20 // 3.5 = 0.0 -> density 0.01
    packet = router._build_context_packet("T2", [prop])
    assert packet.semantic_density_score > 0.50
    assert packet.semantic_density_score == pytest.approx(0.70, rel=1e-2)
