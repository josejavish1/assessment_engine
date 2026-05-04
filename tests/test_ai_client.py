from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from assessment_engine.scripts.lib.ai_client import (
    _robust_unwrap_and_validate,
    run_agent,
)

# --- ARRANGE ---


class MockSchema(BaseModel):
    result: str


@pytest.mark.asyncio
async def test_run_agent_mocked_success(caplog):
    """Verifica que run_agent funciona correctamente con una respuesta mockeada."""
    mock_response = ('{"result": "success"}', ["line1"])
    with patch(
        "assessment_engine.scripts.lib.ai_client._execute_query_with_retry",
        return_value=mock_response,
    ):
        mock_app = MagicMock()
        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.model = "gemini-2.5-pro"
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


@pytest.mark.asyncio
async def test_run_agent_empty_response():
    """Verifica que run_agent maneja correctamente respuestas vacías."""
    # Simular que _execute_query_with_retry lanza RuntimeError por respuesta vacía
    with patch(
        "assessment_engine.scripts.lib.ai_client._execute_query_with_retry",
        side_effect=RuntimeError("Respuesta vacía"),
    ):
        mock_app = MagicMock()
        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.model = "gemini-2.5-pro"
        mock_app._agent = mock_agent

        with pytest.raises(RuntimeError, match="Respuesta vacía"):
            await run_agent(
                app=mock_app,
                user_id="test-user",
                message="hello",
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
