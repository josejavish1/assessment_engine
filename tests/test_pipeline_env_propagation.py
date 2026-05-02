from __future__ import annotations

from assessment_engine.scripts import (
    run_commercial_pipeline,
    run_global_pipeline,
    run_tower_pipeline,
)
from assessment_engine.scripts.tools import regenerate_smoke_artifacts


def test_regenerate_smoke_artifacts_propagates_skip_vertex_preflight(
    monkeypatch,
) -> None:
    captured: list[tuple[list[str], str, dict[str, str], bool]] = []

    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "generate_smoke_inputs",
        lambda **_kwargs: (
            regenerate_smoke_artifacts.ROOT
            / "working"
            / "smoke_ivirma"
            / "context.txt",
            regenerate_smoke_artifacts.ROOT
            / "working"
            / "smoke_ivirma"
            / "responses.txt",
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
        item
        for item in captured
        if item[1].startswith("Resume tower pipeline from strategic blueprint")
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


def test_regenerate_smoke_artifacts_runs_global_pipeline_without_legacy_switches(
    monkeypatch,
) -> None:
    captured: list[tuple[list[str], str, dict[str, str], bool]] = []

    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "generate_smoke_inputs",
        lambda **_kwargs: (
            regenerate_smoke_artifacts.ROOT
            / "working"
            / "smoke_ivirma"
            / "context.txt",
            regenerate_smoke_artifacts.ROOT
            / "working"
            / "smoke_ivirma"
            / "responses.txt",
        ),
    )
    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "run_step",
        lambda cmd_args, step_name, env, dry_run: captured.append(
            (cmd_args, step_name, dict(env), dry_run)
        ),
    )

    regenerate_smoke_artifacts.main(["--with-global", "--dry-run"])

    global_step = next(item for item in captured if item[1] == "Run global pipeline")
    assert "--blueprint-only" not in global_step[0]
    assert "--allow-global-legacy-fallback" not in global_step[0]


def test_regenerate_smoke_artifacts_runs_multiple_towers(monkeypatch) -> None:
    captured: list[tuple[list[str], str, dict[str, str], bool]] = []

    monkeypatch.setattr(
        regenerate_smoke_artifacts,
        "generate_smoke_inputs",
        lambda **_kwargs: (
            regenerate_smoke_artifacts.ROOT
            / "working"
            / "vodafone_demo"
            / "context.txt",
            regenerate_smoke_artifacts.ROOT
            / "working"
            / "vodafone_demo"
            / "responses.txt",
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
        [
            "--client",
            "vodafone_demo",
            "--scenario",
            "vodafone-public",
            "--towers",
            "T2",
            "T3",
            "T5",
            "--with-global",
            "--with-commercial",
            "--with-web",
            "--dry-run",
        ]
    )

    tower_resume_steps = [
        item
        for item in captured
        if item[1].startswith("Resume tower pipeline from strategic blueprint")
    ]
    assert [step[0][step[0].index("--tower") + 1] for step in tower_resume_steps] == [
        "T2",
        "T3",
        "T5",
    ]
    assert any(item[1] == "Run global pipeline" for item in captured)
    assert any(item[1] == "Run commercial pipeline" for item in captured)
    assert any(item[1] == "Render web dashboard" for item in captured)


def test_run_tower_pipeline_renders_annex_with_semantic_styles(monkeypatch) -> None:
    captured: list[tuple[list[str], str]] = []

    async def _fake_run_step_async(cmd_args, env, step_name):
        captured.append((cmd_args, step_name))

    monkeypatch.setattr(
        run_tower_pipeline,
        "run_step_async",
        _fake_run_step_async,
    )
    monkeypatch.setattr(run_tower_pipeline, "build_runtime_env", lambda: {})
    monkeypatch.setattr(
        run_tower_pipeline,
        "prepare_case_runtime",
        lambda env, client_id, tower_id: (
            run_tower_pipeline.Path("/tmp") / client_id / tower_id
        ),
    )
    monkeypatch.setattr(
        run_tower_pipeline, "validate_runtime_environment", lambda env: None
    )
    monkeypatch.setattr(run_tower_pipeline, "resolve_python_bin", lambda: "python")
    monkeypatch.setattr(
        run_tower_pipeline,
        "resolve_blueprint_payload_path",
        lambda client_id, tower_id: (
            run_tower_pipeline.Path("/tmp")
            / client_id
            / tower_id
            / f"blueprint_{tower_id.lower()}_payload.json"
        ),
    )
    monkeypatch.setattr(
        run_tower_pipeline,
        "resolve_tower_annex_template_path",
        lambda: run_tower_pipeline.Path("/tmp/template.docx"),
    )
    monkeypatch.setattr(
        run_tower_pipeline,
        "run_vertex_ai_preflight",
        lambda env=None: {"project": "p", "location": "l", "model": "m"},
    )

    monkeypatch.setattr(
        run_tower_pipeline.Path,
        "exists",
        lambda self: False,
        raising=False,
    )

    monkeypatch.setattr(
        run_tower_pipeline.argparse.ArgumentParser,
        "parse_args",
        lambda self: run_tower_pipeline.argparse.Namespace(
            tower="T5",
            client="smoke_ivirma",
            context_file="/tmp/context.txt",
            responses_file="/tmp/responses.txt",
            start_from="Engine: Executive Annex Synthesizer",
        ),
    )

    run_tower_pipeline.SKIP_MODE = False
    run_tower_pipeline.START_FROM = None
    run_tower_pipeline.asyncio.run(run_tower_pipeline.run_pipeline())

    render_step = next(item for item in captured if item[1] == "Render short DOCX")
    assert render_step[0][-1] == "--semantic-styles"
