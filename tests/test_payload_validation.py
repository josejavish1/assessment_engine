from __future__ import annotations

from assessment_engine.domain.schemas.common import VersionedPayload


def test_payload_versioning_integrity_tier1() -> None:
    """Verify the integrity of versions in domain payloads."""
    payload = VersionedPayload()
    assert payload.generation_metadata is None
