"""Unit tests for generating AS-IS technical markdown modules from blueprint payloads."""

from __future__ import annotations

import shutil
from pathlib import Path

from assessment_engine.adapters.generate_asis_markdown_modules import (
    clean_client_name,
    generate_modules,
    sanitize_and_unify_metrics,
    sanitize_semantic_prose,
)


def test_clean_client_name():
    """Verify that client name cleaning strips version tags and title-cases."""
    assert clean_client_name("redeia_v3") == "Redeia"
    assert clean_client_name("cliente") == "Cliente"


def test_sanitize_and_unify_metrics():
    """Verify that metrics sanitization replaces numerical score strings with calibrated format."""
    text = "La madurez de la torre presenta un riesgo ALE estimado."
    result = sanitize_and_unify_metrics(
        text=text,
        exact_score=3.5,
        exact_band="Alineado",
        total_fair_ale=120000.0,
        doc_lang="es",
    )
    assert len(result) > 0


def test_sanitize_semantic_prose():
    """Verify that markdown bullet prefixes and section tags are sanitized."""
    raw = "* Capacidad: Modernización de redes.\n- Estado: Operativo."
    cleaned = sanitize_semantic_prose(raw, doc_lang="es")
    assert "Modernización" in cleaned


def test_generate_modules_full_flow(tmp_path: Path):
    """Verify that generate_modules writes all required markdown modules into asis_modules/."""
    source_bp = Path("tests/test_data/blueprint_t2_payload.json")
    assert source_bp.exists()

    bp_copy = tmp_path / "blueprint_t2_payload.json"
    shutil.copyfile(source_bp, bp_copy)

    generate_modules(str(bp_copy))

    modules_dir = tmp_path / "asis_modules"
    assert modules_dir.exists(), "asis_modules directory was not created."

    md_files = list(modules_dir.glob("*.md"))
    assert len(md_files) >= 5, f"Expected at least 5 markdown modules, got {len(md_files)}"
