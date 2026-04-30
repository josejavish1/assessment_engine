from __future__ import annotations

import pytest

from assessment_engine.scripts.lib import pipeline_runtime


def test_prepare_case_runtime_sets_case_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        pipeline_runtime,
        "resolve_client_dir",
        lambda client_id: tmp_path / "working" / client_id,
    )
    env: dict[str, str] = {}

    case_dir = pipeline_runtime.prepare_case_runtime(
        env,
        client_id="smoke_ivirma",
        tower_id="T5",
    )

    expected_dir = tmp_path / "working" / "smoke_ivirma" / "T5"
    assert case_dir == expected_dir
    assert case_dir.exists()
    assert env["ASSESSMENT_CLIENT_ID"] == "smoke_ivirma"
    assert env["ASSESSMENT_TOWER_ID"] == "T5"
    assert env["ASSESSMENT_CASE_DIR"] == str(expected_dir)


def test_validate_runtime_environment_requires_vertex_env() -> None:
    with pytest.raises(RuntimeError, match="Falta configuración de entorno para Vertex AI"):
        pipeline_runtime.validate_runtime_environment({"GOOGLE_CLOUD_PROJECT": ""})


@pytest.mark.parametrize(
    ("step_name", "expected"),
    [
        ("Engine: Tower Strategic Blueprint", 45.0),
        ("Strategic Executive Refinement", 45.0),
        ("Build case_input", None),
    ],
)
def test_resolve_ai_step_timeout_seconds_scopes_to_ai_steps(
    step_name: str,
    expected: float | None,
) -> None:
    env = {"ASSESSMENT_AI_STEP_TIMEOUT_SECONDS": "45"}

    assert pipeline_runtime.resolve_ai_step_timeout_seconds(env, step_name) == expected


@pytest.mark.parametrize("raw_value", ["invalid", "0", "-1"])
def test_resolve_ai_step_timeout_seconds_rejects_invalid_values(raw_value: str) -> None:
    env = {"ASSESSMENT_AI_STEP_TIMEOUT_SECONDS": raw_value}

    with pytest.raises(RuntimeError, match="ASSESSMENT_AI_STEP_TIMEOUT_SECONDS"):
        pipeline_runtime.resolve_ai_step_timeout_seconds(
            env,
            "Engine: Tower Strategic Blueprint",
        )
