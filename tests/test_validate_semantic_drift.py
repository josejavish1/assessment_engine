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
