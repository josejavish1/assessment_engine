"""
Unit test suite for Tier-1 Dynamic Lexical Epistemic Sanitizer.

Verifies:
1. Extraction and authorization of verified entity mentions from evidence chunks.
2. Interception of unverified vendor product hallucinations.
3. Substitution of unauthorized entities with canonical functional capability archetypes.
4. Grammatical determiner agreement ('a/an') and multilingual support.
"""

from assessment_engine.domain.validation.lexical_epistemic_sanitizer import (
    LexicalEpistemicSanitizer,
    VerifiedEntityRegistry,
)


def test_verified_entity_registry_ingestion_and_authorization():
    """Verify that evidence ingestion accurately registers entities and authorizes scoped mentions."""
    registry = VerifiedEntityRegistry()

    chunk_1 = "The infrastructure leverages Okta for identity federation and Palo Alto perimeter firewalls."
    registry.ingest_evidence_text(chunk_1, evidence_id="CHUNK_001")

    # Okta and Palo Alto should be authorized under CHUNK_001
    assert registry.is_entity_authorized("Okta", active_evidence_ids=["CHUNK_001"]) is True
    assert registry.is_entity_authorized("palo alto", active_evidence_ids=["CHUNK_001"]) is True

    # BitLocker was not in chunk 1, so it is unauthorized
    assert registry.is_entity_authorized("BitLocker", active_evidence_ids=["CHUNK_001"]) is False

    # Scoped check: if CHUNK_002 is active, chunk 1 entities are unauthorized
    assert registry.is_entity_authorized("Okta", active_evidence_ids=["CHUNK_002"]) is False


def test_lexical_sanitizer_replaces_unauthorized_hallucinations_with_archetypes():
    """Verify that unauthorized product names are replaced with capability archetypes while authorized ones remain."""
    registry = VerifiedEntityRegistry()

    # Evidence only verifies Okta
    registry.ingest_evidence_text("We currently use Okta for SSO.", evidence_id="CHUNK_AUTH")

    sanitizer = LexicalEpistemicSanitizer(registry)

    # Narrative mentions authorized Okta AND unauthorized BitLocker and CrowdStrike
    raw_narrative = (
        "The client relies on Okta for access, while endpoints are secured with a BitLocker deployment "
        "and monitored by an CrowdStrike agent."
    )

    sanitized, hallucinations = sanitizer.compile_and_sanitize(
        raw_narrative,
        scoped_evidence_ids=["CHUNK_AUTH"],
        doc_lang="en",
    )

    # Okta was authorized, so it must remain intact
    assert "Okta" in sanitized

    # BitLocker and CrowdStrike were unauthorized, so they must be intercepted and replaced
    assert "BitLocker" not in sanitized
    assert "operating system-level volume encryption mechanism" in sanitized
    assert "CrowdStrike" not in sanitized
    assert "endpoint detection and response (EDR) platform" in sanitized

    # Verify intercepted list
    assert "bitlocker" in hallucinations
    assert "crowdstrike" in hallucinations


def test_lexical_sanitizer_preserves_article_agreement():
    """Verify that grammatical articles ('a' vs 'an') are adjusted to match the replacement archetype."""
    sanitizer = LexicalEpistemicSanitizer()

    # 'a BitLocker' -> starts with vowel 'operating' -> should become 'an operating system-level...'
    raw_text = "The laptops utilize a BitLocker configuration."
    sanitized, _ = sanitizer.compile_and_sanitize(raw_text, doc_lang="en")

    assert "an operating system-level volume encryption mechanism" in sanitized
    assert "a operating" not in sanitized


def test_lexical_sanitizer_spanish_archetype_substitution():
    """Verify that Spanish deliverables receive localized functional capability archetypes."""
    sanitizer = LexicalEpistemicSanitizer()

    raw_text = "El acceso a salas se protege mediante lectores biométricos y sistemas VESDA."
    sanitized, intercepted = sanitizer.compile_and_sanitize(raw_text, doc_lang="es")

    assert "VESDA" not in sanitized
    assert "detección precoz por aspiración" in sanitized
    assert "vesda" in intercepted
