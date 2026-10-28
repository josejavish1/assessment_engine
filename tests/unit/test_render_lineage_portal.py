"""Unit tests for the Unified Lineage Matrix Explorer HTML portal generator."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

from assessment_engine.adapters.render_lineage_portal import main, render_lineage_portal


def test_render_lineage_portal_html(tmp_path: Path):
    """Verify that render_lineage_portal generates a valid, non-empty HTML matrix explorer."""
    client_name = "Portal Client"
    client_dir = tmp_path / "portal_client"
    client_dir.mkdir(parents=True, exist_ok=True)

    global_payload = {
        "meta": {"client": client_name},
        "executive_summary": {"global_score": "3.5"},
    }
    (client_dir / "global_report_payload.json").write_text(
        json.dumps(global_payload), encoding="utf-8"
    )

    t2_dir = client_dir / "T2"
    t2_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        "tests/test_data/blueprint_t2_payload.json",
        t2_dir / "blueprint_t2_payload.json",
    )

    out_html = tmp_path / "lineage_matrix.html"

    with patch(
        "assessment_engine.adapters.render_lineage_portal.resolve_client_dir",
        return_value=client_dir,
    ), patch(
        "assessment_engine.adapters.render_lineage_portal.resolve_global_report_payload_path",
        return_value=client_dir / "global_report_payload.json",
    ):
        result = render_lineage_portal(client_name)

    assert result.is_file(), "El archivo HTML de lineage portal debe haber sido creado."
    assert result == client_dir / "portal" / "index.html"
    content = result.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content or "<html" in content
    assert client_name in content


def test_main_cli_lineage_portal(tmp_path: Path):
    """Verify CLI error handling and entry point."""
    assert main(["script"]) == 1
