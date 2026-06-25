from __future__ import annotations

from domain.schemas.common import VersionedPayload


def test_payload_versioning_integrity_tier1() -> None:
    """Verifica la integridad de versiones en los payloads del dominio."""
    payload = VersionedPayload()
    assert payload.generation_metadata is None
