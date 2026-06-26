from __future__ import annotations

from assessment_engine.infrastructure.pipeline_runtime import build_runtime_env


def test_runtime_env_generation_tier1() -> None:
    """Verifica la generación de entornos de ejecución industriales."""
    env = build_runtime_env({"TEST_VAR": "value"})
    assert env["TEST_VAR"] == "value"
