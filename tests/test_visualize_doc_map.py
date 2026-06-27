"""Tests for the interactive documentation map generator script.

This test file verifies that the generate_interactive_map function correctly
parses YAML documentation-map inputs and outputs a valid interactive HTML file.
"""

from pathlib import Path

import yaml

from assessment_engine.application.tools.visualize_doc_map import (
    generate_interactive_map,
)


def test_generate_interactive_map(tmp_path: Path) -> None:
    """Verifies that the interactive map is generated correctly with valid inputs.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    mock_yaml = tmp_path / "mock_documentation_map.yaml"
    mock_html = tmp_path / "mock_output.html"

    # Create dummy documentation-map YAML
    doc_map_content = {
        "entries": [
            {
                "path": "docs/test_doc_1.md",
                "title": "Test Document 1",
                "doc_type": "canonical",
                "status": "Verified",
                "source_of_truth": ["src/some_code.py"],
            },
            {
                "path": "docs/test_doc_2.md",
                "title": "Test Document 2",
                "doc_type": "operational",
                "status": "Draft",
                "source_of_truth": ["docs/test_doc_1.md"],
            },
        ]
    }

    with open(mock_yaml, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc_map_content, f)

    # Generate the map
    result = generate_interactive_map(
        yaml_path_str=str(mock_yaml), output_html_str=str(mock_html)
    )

    # Assertions
    assert result is True
    assert mock_html.exists()

    with open(mock_html, "r", encoding="utf-8") as f:
        html_text = f.read()

    # Verify key elements are in the generated HTML
    assert "Sovereign DocMap v4" in html_text
    assert "d3.v7.min.js" in html_text
    assert "docs/test_doc_1.md" in html_text
    assert "Test Document 2" in html_text
    assert "src/some_code.py" in html_text


def test_generate_interactive_map_missing_file(tmp_path: Path) -> None:
    """Verifies that the generator handles missing YAML files gracefully.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    missing_yaml = tmp_path / "non_existent.yaml"
    mock_html = tmp_path / "mock_output.html"

    result = generate_interactive_map(
        yaml_path_str=str(missing_yaml), output_html_str=str(mock_html)
    )

    assert result is False
    assert not mock_html.exists()
