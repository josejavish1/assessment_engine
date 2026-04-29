import pytest
from assessment_engine.schemas.blueprint import PillarBlueprintDraft

def test_pydantic_import():
    """Verifica que los esquemas Pydantic se importan correctamente."""
    assert PillarBlueprintDraft is not None

def test_sys_path():
    """Verifica que 'src' está en el sys.path."""
    import sys
    assert any("src" in path for path in sys.path)

@pytest.mark.asyncio
async def test_async_works():
    """Verifica que el plugin de asyncio para pytest funciona."""
    import asyncio
    await asyncio.sleep(0.1)
    assert True
