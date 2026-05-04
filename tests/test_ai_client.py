from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from assessment_engine.scripts.lib.ai_client import (
    _robust_unwrap_and_validate,
    run_agent,
)


class MockSchema(BaseModel):
    result: str
@pytest.mark.asyncio
@patch("google.genai.Client")
async def test_run_agent_mocked_success(mock_client_class, caplog):
    """Verifica que run_agent funciona correctamente con una respuesta mockeada."""
    mock_client = mock_client_class.return_value
    mock_chat = AsyncMock()
    mock_client.aio.chats.create.return_value = mock_chat

    mock_response = MagicMock()
    mock_response.text = '{"result": "success"}'
    mock_chat.send_message.return_value = mock_response

    mock_app = MagicMock()
    mock_agent = MagicMock()
    mock_agent.model = "gemini-2.5-pro"
    mock_agent.instruction = "Test instruction"
    mock_agent.name = "test_agent"
    mock_agent.tools = []
    mock_app._tmpl_attrs = {"agent": mock_agent}
    mock_app._agent = mock_agent

    result = await run_agent(
        app=mock_app,
        user_id="test-user",
        message="hello",
        schema=MockSchema,
        run_id="test_id",
    )

    assert result == {"result": "success"}
    assert "[run_id=test_id]" in caplog.text

async def test_run_agent_empty_response():
    """Verifica que run_agent maneja correctamente respuestas vacías."""
    mock_app = MagicMock()

    class AsyncIter:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    mock_app.async_stream_query.side_effect = lambda *args, **kwargs: AsyncIter()

    # The retry logic will catch the RuntimeError from empty response and eventually fail
    with pytest.raises(Exception):
        await run_agent(
            app=mock_app, user_id="test-user", message="hello", schema=MockSchema
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
