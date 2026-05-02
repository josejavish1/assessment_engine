from __future__ import annotations

from pathlib import Path

from assessment_engine.scripts.lib import runtime_paths


def test_resolve_client_dir_uses_default_client(monkeypatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)

    client_dir = runtime_paths.resolve_client_dir("smoke_ivirma")

    assert client_dir == Path("/tmp/assessment-engine/working/smoke_ivirma")


def test_resolve_client_dir_prefers_environment_client(monkeypatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.setenv("ASSESSMENT_CLIENT_ID", "env-client")

    client_dir = runtime_paths.resolve_client_dir("fallback-client")

    assert client_dir == Path("/tmp/assessment-engine/working/env-client")


def test_resolve_client_dir_falls_back_to_legacy_working(monkeypatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: (
            str(self)
            == "/tmp/assessment-engine/src/assessment_engine/working/smoke_ivirma"
        ),
    )

    client_dir = runtime_paths.resolve_client_dir("smoke_ivirma")

    assert client_dir == Path(
        "/tmp/assessment-engine/src/assessment_engine/working/smoke_ivirma"
    )


def test_resolve_case_dir_uses_client_helper(monkeypatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CASE_DIR", raising=False)
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    monkeypatch.delenv("ASSESSMENT_TOWER_ID", raising=False)

    case_dir = runtime_paths.resolve_case_dir("smoke_ivirma", "T5")

    assert case_dir == Path("/tmp/assessment-engine/working/smoke_ivirma/T5")


def test_resolve_artifact_paths(monkeypatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    monkeypatch.delenv("ASSESSMENT_TOWER_ID", raising=False)

    assert runtime_paths.resolve_client_intelligence_path("smoke_ivirma") == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/client_intelligence.json"
    )
    assert runtime_paths.resolve_global_report_payload_path("smoke_ivirma") == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/global_report_payload.json"
    )
    assert runtime_paths.resolve_commercial_report_payload_path("smoke_ivirma") == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/commercial_report_payload.json"
    )
    assert runtime_paths.resolve_case_input_path("smoke_ivirma", "T5") == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/T5/case_input.json"
    )
    assert runtime_paths.resolve_blueprint_payload_path("smoke_ivirma", "T5") == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/T5/blueprint_t5_payload.json"
    )
    assert runtime_paths.resolve_annex_template_payload_path(
        "smoke_ivirma",
        "T5",
    ) == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/T5/approved_annex_t5.template_payload.json"
    )


def test_resolve_blueprint_payload_candidates_include_uppercase_legacy(
    monkeypatch,
) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    monkeypatch.delenv("ASSESSMENT_TOWER_ID", raising=False)

    candidates = runtime_paths.resolve_blueprint_payload_candidates(
        "smoke_ivirma", "T1"
    )

    assert candidates == (
        Path(
            "/tmp/assessment-engine/working/smoke_ivirma/T1/blueprint_t1_payload.json"
        ),
        Path(
            "/tmp/assessment-engine/working/smoke_ivirma/T1/blueprint_T1_payload.json"
        ),
    )


def test_resolve_template_paths(monkeypatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))

    assert runtime_paths.resolve_global_report_template_path() == Path(
        "/tmp/assessment-engine/source_docs/templates/11. Template Documento General Alpha v.05.docx"
    )
    assert runtime_paths.resolve_tower_annex_template_path() == Path(
        "/tmp/assessment-engine/templates/Template_Documento_Anexos_Alpha_v06_Tower_Annex_v2_6.docx"
    )
    assert runtime_paths.resolve_web_dashboard_template_path() == Path(
        "/tmp/assessment-engine/src/assessment_engine/templates/web_dashboard.html"
    )
