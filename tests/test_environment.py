import importlib.util

import pytest

from assessment_engine.schemas.blueprint import PillarBlueprintDraft


def test_pydantic_import():
    """Verifica que los esquemas Pydantic se importan correctamente."""
    assert PillarBlueprintDraft is not None

def test_package_is_importable():
    """Verifica que el paquete instalado es importable sin hacks de sys.path."""
    spec = importlib.util.find_spec("assessment_engine")
    assert spec is not None
    assert spec.origin is not None
    assert "src/assessment_engine" in spec.origin

@pytest.mark.asyncio
async def test_async_works():
    """Verifica que el plugin de asyncio para pytest funciona."""
    import asyncio
    await asyncio.sleep(0.1)
    assert True
