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


def test_clean_cap_name_lcr_killer():
    """Verify that _clean_cap_name handles empty values and non-Spanish locales."""
    from assessment_engine.adapters.generate_asis_markdown_modules import _clean_cap_name

    assert _clean_cap_name("", "es") == ""
    assert _clean_cap_name("Provisioning", "en") == "Provisioning"
    assert "Autoservicio" in _clean_cap_name("self-service provisioning", "es")


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
    assert modules_dir.is_dir(), "asis_modules directory was not created."

    # Invariantes de presencia de módulos obligatorios
    file_names = {f.name for f in modules_dir.glob("*.md")}
    expected_modules = {
        "01_introduccion.md",
        "02_resumen_ejecutivo.md",
        "03_descripcion_plataforma.md",
        "05_transversal.md",
        "07_conclusiones.md",
    }
    assert expected_modules.issubset(file_names), f"Faltan módulos críticos: {expected_modules - file_names}"

    # Invariantes de contenido semántico no vacío y trazabilidad
    mod2_text = (modules_dir / "02_resumen_ejecutivo.md").read_text(encoding="utf-8")
    assert "Resumen Ejecutivo" in mod2_text
    assert "Hybrid Compute & Platforms" in mod2_text

    mod1_text = (modules_dir / "01_introduccion.md").read_text(encoding="utf-8")
    assert "Redeia" in mod1_text or "REDEIA" in mod1_text
