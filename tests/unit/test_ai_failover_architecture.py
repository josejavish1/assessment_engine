from __future__ import annotations

import pytest

from assessment_engine.infrastructure.ai_client import estimate_cost, run_agent
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    get_fallback_model,
    get_model,
)


def test_ssot_model_resolution_and_fallback():
    """Verify single source of truth resolution and fallback mapping."""
    # Primary reasoning resolves to gemini-4-argon by default
    assert get_model(ModelTier.REASONING) == "gemini-4-argon"

    # Fallback for gemini-4-argon is gemini-3.1-pro-preview
    assert get_fallback_model("gemini-4-argon") == "gemini-3.1-pro-preview"

    # Primary fast resolves to gemini-3.8-flash
    assert get_model(ModelTier.FAST) == "gemini-3.8-flash"


def test_model_agnostic_cost_estimation():
    """Verify that estimate_cost applies tier rates dynamically without hardcoded model dictionaries."""
    # Flash models (any version) inherit flash rates: 0.075 / 0.30
    cost_flash = estimate_cost(1_000_000, 1_000_000, model="gemini-3.8-flash")
    assert cost_flash == round(0.075 + 0.30, 5)

    cost_future_flash = estimate_cost(1_000_000, 1_000_000, model="gemini-4.0-flash-preview")
    assert cost_future_flash == round(0.075 + 0.30, 5)

    # Reasoning models inherit reasoning rates: 1.25 / 5.00
    cost_argon = estimate_cost(1_000_000, 1_000_000, model="gemini-4-argon")
    assert cost_argon == round(1.25 + 5.00, 5)

    cost_pro = estimate_cost(1_000_000, 1_000_000, model="gemini-3.1-pro-preview")
    assert cost_pro == round(1.25 + 5.00, 5)


@pytest.mark.asyncio
async def test_run_agent_automatic_failover(monkeypatch):
    """Verify that run_agent automatically switches to fallback_model upon primary failure."""
    class MockAgent:
        def __init__(self):
            self.model = "gemini-4-argon"
            self.name = "test_architect"

    class MockApp:
        def __init__(self):
            self._agent = MockAgent()
            self.attempt = 0

        async def async_stream_query(self, user_id, message):
            self.attempt += 1
            if self.attempt == 1:
                # Primary attempt on gemini-4-argon fails
                raise RuntimeError("ResourceExhausted: 429 quota reached on gemini-4-argon")
            # Secondary failover attempt on gemini-3.1-pro-preview succeeds
            yield {"content": {"parts": [{"text": '{"result": "success_from_fallback"}'}]}}

    app = MockApp()
    res = await run_agent(app, user_id="test_user", message="generate plan")

    assert res == {"result": "success_from_fallback"}
    assert app._agent.model == "gemini-3.1-pro-preview"
    assert app.attempt == 2
