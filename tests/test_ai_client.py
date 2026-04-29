import pytest
from unittest.mock import AsyncMock, MagicMock
from assessment_engine.scripts.lib.ai_client import run_agent, _robust_unwrap_and_validate
from pydantic import BaseModel, ValidationError

class MockSchema(BaseModel):
    result: str

@pytest.mark.asyncio
async def test_run_agent_mocked_success():
    """Verifica que run_agent funciona correctamente con una respuesta mockeada."""
    mock_app = MagicMock()
    mock_event = {
        "content": {
            "parts": [{"text": '{"result": "success"}'}]
        }
    }
    
    class AsyncIter:
        def __init__(self, items): self.items = items
        def __aiter__(self): return self
        async def __anext__(self):
            if not self.items: raise StopAsyncIteration
            return self.items.pop(0)

    mock_app.async_stream_query.side_effect = lambda *args, **kwargs: AsyncIter([mock_event])

    result = await run_agent(
        app=mock_app,
        user_id="test-user",
        message="hello",
        schema=MockSchema
    )

    assert result == {"result": "success"}
    mock_app.async_stream_query.assert_called_once()

@pytest.mark.asyncio
async def test_run_agent_empty_response():
    """Verifica que run_agent maneja correctamente respuestas vacías."""
    mock_app = MagicMock()
    
    class AsyncIter:
        def __aiter__(self): return self
        async def __anext__(self): raise StopAsyncIteration

    mock_app.async_stream_query.side_effect = lambda *args, **kwargs: AsyncIter()

    # The retry logic will catch the RuntimeError from empty response and eventually fail
    with pytest.raises(Exception):
        await run_agent(
            app=mock_app,
            user_id="test-user",
            message="hello",
            schema=MockSchema
        )

def test_robust_unwrap_and_validate_direct():
    """Verifica la validación directa."""
    data = {"result": "ok"}
    validated = _robust_unwrap_and_validate(data, MockSchema)
    assert validated == {"result": "ok"}

def test_robust_unwrap_and_validate_nested():
    """Verifica que la función desenvuelve JSONs anidados por el modelo."""
    data = {"nested_wrapper": {"result": "unwrapped"}}
    validated = _robust_unwrap_and_validate(data, MockSchema)
    assert validated == {"result": "unwrapped"}

def test_robust_unwrap_and_validate_failure():
    """Verifica que falla con datos incorrectos."""
    data = {"wrong_key": "bad"}
    with pytest.raises(ValidationError):
        _robust_unwrap_and_validate(data, MockSchema)
