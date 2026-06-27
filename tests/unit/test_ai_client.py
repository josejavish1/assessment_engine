# golden-path: ignore
from __future__ import annotations

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch

from assessment_engine.infrastructure.ai_client import run_agent, VertexQueryTimeoutError
from assessment_engine.infrastructure.json_from_model import parse_json_from_text
from assessment_engine.application.run_global_synthesizer_tobe import Phase1Strategy


# =========================================================================
# ACCIÓN 1: TEST DE ROBUSTEZ ANTE TIMEOUTS DE VERTEX AI
# =========================================================================

@pytest.mark.asyncio
async def test_run_agent_timeout_error_handling():
    """Verify that run_agent raises a robust exception when Vertex AI query times out."""
    # Arrange - Setup a custom asynchronous generator mock for the ADK app
    class MockAppWithTimeout:
        def __init__(self):
            self._agent = type("MockAgent", (object,), {"model": "gemini-2.5-pro", "name": "TestAgent"})()

        async def async_stream_query(self, user_id, message):
            # Simulate a TimeoutError being raised directly during the asynchronous iteration
            raise asyncio.TimeoutError("Vertex service timed out")
            yield  # Make it an async generator
            
    mock_app = MockAppWithTimeout()

    # Act & Assert - Ensure it intercepts and wraps the TimeoutError into VertexQueryTimeoutError
    with pytest.raises(VertexQueryTimeoutError) as exc:
        await run_agent(mock_app, "user_test_timeout", "This prompt will trigger a timeout")
        
    assert "timed out after" in str(exc.value)


# =========================================================================
# ACCIÓN 3: TEST DE CAOS DE STREAMING TRUNCADO (FUZZING DE JSON DEL LLM)
# =========================================================================

def test_parse_json_from_text_heuristics():
    """Fuzz the JSON extraction engine with different malformed, fenced, and decorated strings.
    
    Ensures the parser can robustly extract valid JSON objects from surrounding raw model text.
    """
    # 1. Markdown Fenced JSON (The standard LLM output)
    markdown_fenced = "```json\n{\"executive_vision\": \"Ensuring edge security\"}\n```"
    assert parse_json_from_text(markdown_fenced) == {"executive_vision": "Ensuring edge security"}

    # 2. Markdown Fenced JSON with uppercase fence
    markdown_fenced_upper = "```JSON\n{\"key\": \"val\"}\n```"
    assert parse_json_from_text(markdown_fenced_upper) == {"key": "val"}

    # 3. JSON surrounded by chatty text (Prefix and Postfix)
    chatty_text = "Here is the compiled analysis:\n{\n  \"status\": \"optimal\"\n}\nHope this helps!"
    assert parse_json_from_text(chatty_text) == {"status": "optimal"}

    # 4. Truncated or malformed inputs must raise JSONDecodeError cleanly
    with pytest.raises(json.JSONDecodeError):
        parse_json_from_text("This is pure raw text with no JSON braces.")

    with pytest.raises(json.JSONDecodeError):
        parse_json_from_text("")


def test_robust_unwrap_and_validate_nested_recovery():
    """Verify that the unwrap mechanism recovers and parses nested schemas successfully."""
    # Arrange - Setup a nested dict where the schema is wrapped inside a single-key envelope
    # e.g., representing an LLM wrapping the response under the schema class name key.
    nested_response = {
        "Phase1Strategy": {
            "executive_vision": "Secure cloud edge vision.",
            "transformation_strategy": "Migrating core to microservices.",
            "document_purpose": "Guide next-gen security.",
            "document_scope": "Full platform coverage.",
            "maturity_approach": "C-Level alignment."
        }
    }

    # Act & Assert - Verify Pydantic successfully unwraps the nested dictionary and parses it
    try:
        from assessment_engine.infrastructure.ai_client import _robust_unwrap_and_validate
        validated_data = _robust_unwrap_and_validate(nested_response, Phase1Strategy)
        assert validated_data["executive_vision"] == "Secure cloud edge vision."
        assert validated_data["document_purpose"] == "Guide next-gen security."
    except Exception as e:
        pytest.fail(f"_robust_unwrap_and_validate failed to unwrap nested dictionary: {e}")


@pytest.mark.asyncio
async def test_run_agent_grpc_resource_exhausted_resilience():
    """Verify that run_agent handles Google API-specific gRPC ResourceExhausted (Rate Limit) exceptions."""
    from google.api_core.exceptions import ResourceExhausted
    
    # Arrange - Setup mock ADK app that raises a real Google Cloud ResourceExhausted exception
    class MockAppWithRateLimit:
        def __init__(self):
            self._agent = type("MockAgent", (object,), {"model": "gemini-2.5-pro", "name": "TestAgent"})()
            
        async def async_stream_query(self, user_id, message):
            raise ResourceExhausted("Quota exceeded: Rate limit hit")
            yield  # Make it an async generator

    mock_app = MockAppWithRateLimit()
    
    # Act & Assert - Verify that the connection is retried and eventually propagates the exception
    # when all retry attempts are exhausted under the standard Tenacity wrapper.
    with (
        patch("tenacity.wait_exponential.__call__", return_value=0.01),
        pytest.raises(ResourceExhausted)
    ):
        await run_agent(mock_app, "user_test", "prompt")


def test_robust_unwrap_and_validate_with_extra_keys():
    """Verify that _robust_unwrap_and_validate filters out extra/hallucinated JSON keys gracefully."""
    from assessment_engine.infrastructure.ai_client import _robust_unwrap_and_validate
    
    # Arrange - Setup data containing extra, unexpected hallucinated keys
    extra_data = {
        "executive_vision": "Secure cloud edge vision.",
        "transformation_strategy": "Migrating core to microservices.",
        "document_purpose": "Guide next-gen security.",
        "document_scope": "Full platform coverage.",
        "maturity_approach": "C-Level alignment.",
        "hallucinated_extra_key_by_gemini": "Should be ignored cleanly"
    }
    
    # Act - Validate against Phase1Strategy
    validated = _robust_unwrap_and_validate(extra_data, Phase1Strategy)
    
    # Assert - Extra keys are ignored while standard fields are correctly compiled
    assert "hallucinated_extra_key_by_gemini" not in validated
    assert validated["executive_vision"] == "Secure cloud edge vision."

