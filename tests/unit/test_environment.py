from __future__ import annotations

from assessment_engine.domain.schemas.blueprint import BlueprintPayload


def test_pydantic_import() -> None:
    assert BlueprintPayload is not None
