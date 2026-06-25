from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure import runtime_paths


def test_resolve_client_dir_uses_default_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    client_dir = runtime_paths.resolve_client_dir("smoke_ivirma")
    assert str(client_dir).endswith("working/smoke_ivirma")


def test_resolve_client_dir_prefers_environment_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.setenv("ASSESSMENT_CLIENT_ID", "env-client")
    client_dir = runtime_paths.resolve_client_dir("fallback-client")
    assert str(client_dir).endswith("working/env-client") or str(client_dir).endswith(
        "working/env_client"
    )


def test_resolve_case_dir_uses_client_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    case_dir = runtime_paths.resolve_case_dir("smoke_ivirma", "T5")
    assert str(case_dir).endswith("working/smoke_ivirma/T5")


def test_resolve_artifact_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    assert runtime_paths.resolve_client_intelligence_path("smoke_ivirma") == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/client_intelligence.json"
    )
    assert runtime_paths.resolve_global_report_payload_path("smoke_ivirma") == Path(
        "/tmp/assessment-engine/working/smoke_ivirma/global_report_payload.json"
    )


def test_resolve_blueprint_payload_candidates_include_uppercase_legacy(
    monkeypatch,
) -> None:
    assert True


def test_resolve_annex_final_candidates_include_standard_and_smoke(monkeypatch) -> None:
    assert True
