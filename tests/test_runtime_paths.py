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


def test_resolve_case_dir_uses_client_helper(monkeypatch) -> None:
    monkeypatch.setattr(runtime_paths, "ROOT", Path("/tmp/assessment-engine"))
    monkeypatch.delenv("ASSESSMENT_CASE_DIR", raising=False)
    monkeypatch.delenv("ASSESSMENT_CLIENT_ID", raising=False)
    monkeypatch.delenv("ASSESSMENT_TOWER_ID", raising=False)

    case_dir = runtime_paths.resolve_case_dir("smoke_ivirma", "T5")

    assert case_dir == Path("/tmp/assessment-engine/working/smoke_ivirma/T5")
