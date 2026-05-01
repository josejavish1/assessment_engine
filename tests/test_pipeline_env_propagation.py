from __future__ import annotations

from assessment_engine.scripts import run_commercial_pipeline, run_global_pipeline
from assessment_engine.scripts.tools import regenerate_smoke_artifacts


def test_regenerate_smoke_artifacts_propagates_skip_vertex_preflight(monkeypatch) -> None:
    captured: list[tuple[list[str], str, dict[str, str], bool]] = []

    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "generate_smoke_inputs",
        lambda **_kwargs: (
            regenerate_smoke_artifacts.ROOT / "working" / "smoke_ivirma" / "context.txt",
            regenerate_smoke_artifacts.ROOT / "working" / "smoke_ivirma" / "responses.txt",
        ),
    )
    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "run_step",
        lambda cmd_args, step_name, env, dry_run: captured.append(
            (cmd_args, step_name, dict(env), dry_run)
        ),
    )

    regenerate_smoke_artifacts.main(["--skip-vertex-preflight", "--dry-run"])

    assert captured
    tower_step = next(
        item for item in captured if item[1] == "Resume tower pipeline from strategic blueprint"
    )
    assert tower_step[2]["ASSESSMENT_SKIP_VERTEX_PREFLIGHT"] == "1"


def test_run_global_pipeline_passes_validated_env_to_steps(monkeypatch) -> None:
    captured: list[tuple[list[str], dict[str, str]]] = []

    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    monkeypatch.setattr(
        run_global_pipeline,
        "run_vertex_ai_preflight",
        lambda env: {
            "project": env["GOOGLE_CLOUD_PROJECT"],
            "location": env["GOOGLE_CLOUD_LOCATION"],
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        run_global_pipeline,
        "run_module_step",
        lambda cmd_args, _step_name, env: captured.append((cmd_args, dict(env))),
    )

    run_global_pipeline.main(["run_global_pipeline", "smoke_ivirma"])

    assert captured
    assert all(env["GOOGLE_CLOUD_PROJECT"] for _, env in captured)
    assert all(env["GOOGLE_CLOUD_LOCATION"] for _, env in captured)


def test_run_global_pipeline_propagates_blueprint_only_flag(monkeypatch) -> None:
    captured: list[list[str]] = []

    monkeypatch.setattr(
        run_global_pipeline,
        "run_vertex_ai_preflight",
        lambda env: {
            "project": env["GOOGLE_CLOUD_PROJECT"],
            "location": env["GOOGLE_CLOUD_LOCATION"],
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        run_global_pipeline,
        "run_module_step",
        lambda cmd_args, _step_name, _env: captured.append(cmd_args),
    )

    run_global_pipeline.main(
        ["run_global_pipeline", "smoke_ivirma", "--blueprint-only"]
    )

    build_step = next(
        cmd_args
        for cmd_args in captured
        if "assessment_engine.scripts.build_global_report_payload" in cmd_args
    )
    assert build_step[-1] == "--blueprint-only"


def test_run_commercial_pipeline_passes_validated_env_to_steps(monkeypatch) -> None:
    captured: list[dict[str, str]] = []

    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    monkeypatch.setattr(
        run_commercial_pipeline,
        "run_vertex_ai_preflight",
        lambda env: {
            "project": env["GOOGLE_CLOUD_PROJECT"],
            "location": env["GOOGLE_CLOUD_LOCATION"],
            "model": "test-model",
        },
    )
    monkeypatch.setattr(
        run_commercial_pipeline,
        "run_module_step",
        lambda _cmd_args, _step_name, env: captured.append(dict(env)),
    )

    run_commercial_pipeline.main(["run_commercial_pipeline", "smoke_ivirma"])

    assert captured
    assert all(env["GOOGLE_CLOUD_PROJECT"] for env in captured)
    assert all(env["GOOGLE_CLOUD_LOCATION"] for env in captured)


def test_regenerate_smoke_artifacts_propagates_global_blueprint_only(monkeypatch) -> None:
    captured: list[tuple[list[str], str, dict[str, str], bool]] = []

    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "generate_smoke_inputs",
        lambda **_kwargs: (
            regenerate_smoke_artifacts.ROOT / "working" / "smoke_ivirma" / "context.txt",
            regenerate_smoke_artifacts.ROOT / "working" / "smoke_ivirma" / "responses.txt",
        ),
    )
    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "run_step",
        lambda cmd_args, step_name, env, dry_run: captured.append(
            (cmd_args, step_name, dict(env), dry_run)
        ),
    )

    regenerate_smoke_artifacts.main(
        ["--with-global", "--global-blueprint-only", "--dry-run"]
    )

    global_step = next(item for item in captured if item[1] == "Run global pipeline")
    assert global_step[0][-1] == "--blueprint-only"
