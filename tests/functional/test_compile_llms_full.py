"""Tests for the unified context compiler tool.

This test file verifies that compile_llms_full correctly parses llms.txt,
concatenates all valid reference files, and handles missing sitemaps or empty paths.
"""

from pathlib import Path

from assessment_engine.application.tools.compile_llms_full import compile_llms_full


def test_compile_llms_full_success(tmp_path: Path) -> None:
    """Verifies that the context compiler parses a mock sitemap and builds output.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    mock_sitemap = tmp_path / "llms.txt"
    mock_output = tmp_path / "llms-full.txt"

    # Create mock sitemap links
    mock_sitemap.write_text(
        "# Index\n\n- [AGENTS.md](AGENTS.md)\n- [docs/arch.md](docs/arch.md)\n",
        encoding="utf-8",
    )

    # Create referenced files
    agents_file = tmp_path / "AGENTS.md"
    agents_file.write_text("AGENTS_CONTENT_HERE", encoding="utf-8")

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    arch_file = docs_dir / "arch.md"
    arch_file.write_text("ARCH_CONTENT_HERE", encoding="utf-8")

    # Run compiler
    result = compile_llms_full(str(tmp_path))

    # Assertions
    assert result is True
    assert mock_output.exists()

    output_text = mock_output.read_text(encoding="utf-8")
    assert "AGENTS_CONTENT_HERE" in output_text
    assert "ARCH_CONTENT_HERE" in output_text
    assert "START OF FILE: AGENTS.md" in output_text
    assert "END OF FILE: docs/arch.md" in output_text


def test_compile_llms_full_missing_sitemap(tmp_path: Path) -> None:
    """Verifies that the compiler handles a missing sitemap file gracefully.

    Args:
        tmp_path: Pytest temporary path fixture.
    """
    result = compile_llms_full(str(tmp_path / "non_existent_folder"))
    assert result is False


def test_real_llms_compilation_succeeds(tmp_path: Path) -> None:
    """Ensures that compiling the repository's real llms.txt succeeds deterministically.

    Verifies that all documents referenced in the active llms.txt sitemap exist,
    can be read, and compile cleanly into a unified output bundle without error.
    """
    repo_root = Path(__file__).resolve().parents[2]
    real_sitemap = repo_root / "llms.txt"

    assert real_sitemap.exists(), "Repository's 'llms.txt' is missing!"

    temp_output = tmp_path / "llms-full.txt.tmp"

    # Compile the real repository documents to our temporary file
    success = compile_llms_full(str(repo_root), str(temp_output))
    assert success is True, "Failed to compile the real repository documents."

    assert temp_output.exists(), "Compiled output file was not generated."
    content = temp_output.read_text(encoding="utf-8")
    assert len(content) > 5000, "Compiled bundle is suspiciously small."
    assert "AGENTS.md" in content, "AGENTS.md was not compiled into output bundle."
    assert "README.md" in content, "README.md was not compiled into output bundle."
    assert "CONTRIBUTING.md" in content, (
        "CONTRIBUTING.md was not compiled into output bundle."
    )


# --- ARRANGE ---
# --- ACT ---
# --- ASSERT ---
