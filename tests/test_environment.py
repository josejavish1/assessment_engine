from __future__ import annotations

import pytest

from domain.schemas.blueprint import BlueprintPayload


def test_pydantic_import() -> None:
    assert BlueprintPayload is not None


@pytest.mark.asyncio
async def test_async_works() -> None:
    import asyncio

    await asyncio.sleep(0.1)
    assert True
