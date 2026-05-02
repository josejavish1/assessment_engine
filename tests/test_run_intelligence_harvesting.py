from __future__ import annotations

import sys
from pathlib import Path

from assessment_engine.scripts import run_intelligence_harvesting


def test_main_uses_runtime_client_dir(monkeypatch) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(sys, "argv", ["run_intelligence_harvesting.py", "smoke_ivirma"])
    monkeypatch.setattr(
        run_intelligence_harvesting,
        "resolve_client_intelligence_path",
        lambda client_name: (
            Path("/tmp/runtime-working") / client_name / "client_intelligence.json"
        ),
    )
    monkeypatch.setattr(
        run_intelligence_harvesting,
        "run_market_intelligence",
        lambda client_name, output_path: captured.update(
            {"client_name": client_name, "output_path": output_path}
        ),
    )
    monkeypatch.setattr(
        run_intelligence_harvesting.asyncio,
        "run",
        lambda result: result,
    )

    run_intelligence_harvesting.main()

    assert captured["client_name"] == "smoke_ivirma"
    assert captured["output_path"] == Path(
        "/tmp/runtime-working/smoke_ivirma/client_intelligence.json"
    )
