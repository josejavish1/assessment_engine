from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from pydantic import BaseModel, ValidationError

from assessment_engine.scripts.lib.ai_client import (
    _robust_unwrap_and_validate,
    run_agent,
)


class MockSchema(BaseModel):
    result: str


@pytest.mark.asyncio
async def test_run_agent_mocked_success(caplog):
    """Verifica que run_agent funciona correctamente con una respuesta mockeada."""
    mock_app = MagicMock()
    mock_event = {"content": {"parts": [{"text": '{"result": "success"}'}]}}

    class AsyncIter:
        def __init__(self, items):
            self.items = items

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)

    mock_app.async_stream_query.side_effect = lambda *args, **kwargs: AsyncIter(
        [mock_event]
    )

    result = await run_agent(
        app=mock_app,
        user_id="test-user",
        message="hello",
        schema=MockSchema,
        run_id="test_id",
    )

    assert result == {"result": "success"}
    mock_app.async_stream_query.assert_called_once()
    assert "[run_id=test_id]" in caplog.text


@pytest.mark.asyncio
async def test_run_agent_caches_results(caplog):
    """Verifica que run_agent cachea los resultados en llamadas idénticas."""
    mock_app = MagicMock()
    # Definir atributos del agente mock para la clave de caché
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_agent.instruction = "test_instruction"
    mock_app._agent = mock_agent
    
    # La respuesta mockeada de la IA
    mock_response_text = '{"result": "cached_success"}'
    mock_response_lines = [str({"content": {"parts": [{"text": mock_response_text}]}})]

    with patch(
        "assessment_engine.scripts.lib.ai_client._execute_query_with_retry",
        new_callable=AsyncMock,
    ) as mock_execute_query:
        # Configurar el mock para que devuelva un futuro (corutina)
        async def mock_coro(*args, **kwargs):
            return (mock_response_text, [], mock_response_lines)
        
        mock_execute_query.side_effect = mock_coro
        mock_execute_query.retry.statistics = {"attempt_number": 1}

        # --- Primera llamada (debería llamar a la función y cachear) ---
        result1 = await run_agent(
            app=mock_app,
            user_id="test-user-cache",
            message="same_message",
            schema=MockSchema,
            run_id="test_cache_1",
        )

        # Verificar que la primera llamada fue exitosa
        assert result1 == {"result": "cached_success"}
        mock_execute_query.assert_called_once()

        # --- Segunda llamada (debería usar el caché) ---
        result2 = await run_agent(
            app=mock_app,
            user_id="test-user-cache",
            message="same_message",
            schema=MockSchema,
            run_id="test_cache_2",
        )

        # Verificar que el resultado es el mismo y que la función mockeada no fue llamada de nuevo
        assert result2 == {"result": "cached_success"}
        mock_execute_query.assert_called_once() # Sigue siendo una sola llamada


@pytest.mark.asyncio
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
            app=mock_app,
            user_id="test-user",
            message="hello",
            schema=MockSchema,
            run_id="test_id",
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
