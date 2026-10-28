# golden-path: ignore
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from assessment_engine.application.tools import validate_semantic_drift as v_drift


def test_get_modified_py_files_mocked(tmp_path: Path):
    with patch("subprocess.run") as mock_run:
        # Mock git diff origin/main...HEAD response
        mock_run.return_value = MagicMock(
            stdout="src/assessment_engine/ports/document_compiler.py\nsrc/domain/schemas/ast.py\nREADME.md\n",
            returncode=0,
        )
        files = v_drift.get_modified_py_files(tmp_path)
        assert len(files) == 2
        assert "src/assessment_engine/ports/document_compiler.py" in files
        assert "src/domain/schemas/ast.py" in files
        assert mock_run.call_args.kwargs.get("check") is True
        assert mock_run.call_args.kwargs.get("capture_output") is True
        assert mock_run.call_args.kwargs.get("text") is True


def test_get_modified_py_files_fallback_on_origin_main_failure(tmp_path: Path):
    import subprocess

    def fake_subprocess_run(cmd, *args, **kwargs):
        if "origin/main...HEAD" in cmd:
            if kwargs.get("check"):
                raise subprocess.CalledProcessError(1, cmd)
            return MagicMock(returncode=1, stdout="fatal: bad revision origin/main.py\n")
        return MagicMock(returncode=0, stdout="src/domain/schemas/ast.py\n")

    with patch("subprocess.run", side_effect=fake_subprocess_run) as mock_run:
        files = v_drift.get_modified_py_files(tmp_path)
        assert len(files) == 1
        assert "src/domain/schemas/ast.py" in files
        assert "origin/main.py" not in files
        assert mock_run.call_count == 2


def test_get_git_diff_mocked(tmp_path: Path):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=" - class BlueprintPayload:\n+  # updated", returncode=0
        )
        diff = v_drift.get_git_diff(tmp_path, "src/domain/schemas/blueprint.py")
        assert "class BlueprintPayload" in diff


def test_query_gemini_api_mocked():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = b"""{
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "NO_DRIFT"
                            }
                        ]
                    }
                }
            ]
        }"""
        mock_urlopen.return_value.__enter__.return_value = mock_response

        text = v_drift.query_gemini_api("mock_key", "mock prompt")
        assert text.strip() == "NO_DRIFT"
