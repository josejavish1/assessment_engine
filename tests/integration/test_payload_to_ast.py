# golden-path: ignore
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.domain.schemas.ast import DocumentAST, ParagraphNode, TableNode
import pytest


@pytest.mark.xdist_group(name="locales")
def test_payload_to_ast_bridge_conversion(tmp_path: Path):
    """Verify that PayloadToASTBridge successfully parses payloads and builds a valid DocumentAST.

    This integration test ensures that our technical document compiler generates
    the correct corporate cover layout nodes, parses CSV matrices, translates Markdown,
    and calculates risk values, preventing regressions during document compilation.
    """
    # 1. --- ARRANGE ---
    # Create the modular sandbox folder structure
    modules_dir = tmp_path / "asis_modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    # Write dummy Markdown platform overview module
    desc_file = modules_dir / "03_descripcion_plataforma.md"
    desc_file.write_text(
        "# 4. Descripción\nEsta es la descripción detallada de la plataforma actual.",
        encoding="utf-8",
    )

    # Write dummy Markdown cross-functional module
    trans_file = modules_dir / "05_transversal.md"
    trans_file.write_text(
        "# 5. Transversal\nAnálisis transversal de capacidades operativas.",
        encoding="utf-8",
    )

    # Write dummy O-FAIR CSV Quantitative Risk Matrix
    risks_file = modules_dir / "06_matriz_riesgos_fair.csv"
    csv_content = (
        "Capability_Header;Finding;Business_Risk;TEF;LM;ALE\n"
        "Security - Cifrado;Falta cifrado en reposo;Fuga de datos;2.5;50000;100000\n"
        "Operations - Monitoreo;Falta observabilidad;Retraso respuesta;4.0;20000;80000\n"
    )
    risks_file.write_text(csv_content, encoding="utf-8-sig")

    # Create valid minimal payloads for both blueprint and annex templates
    blueprint_payload = {
        "document_meta": {
            "language": "es",
            "tower_name": "Seguridad de Red",
            "tower_code": "T5",
            "client_name": "Generic Corporate Client",
            "version": "1.0",
            "date": "Junio 2026",
            "currency": "€",
        },
        "total_fair_ale": 180000.00,
        "executive_summary": {
            "global_score": "4,50 / 5,00",
            "global_band": "Optimizado",
        },
        "pillar_score_profile": {
            "pillars": [
                {
                    "pilar_name": "Computing",
                    "score": 4.5,
                    "band": "Optimizado",
                    "executive_reading": "Gobernanza de seguridad robusta en edge.",
                }
            ]
        },
    }

    annex_payload = {
        "document_meta": {"tower_code": "T5", "tower_name": "Seguridad de Red"},
        "remediations": [
            {
                "title": "Cifrado de datos",
                "cost": 50000,
                "benefit": "Mitiga intercepción",
            }
        ],
    }

    blueprint_path = tmp_path / "blueprint_t5_payload.json"
    annex_path = tmp_path / "approved_annex_t5.template_payload.json"

    blueprint_path.write_text(json.dumps(blueprint_payload), encoding="utf-8")
    annex_path.write_text(json.dumps(annex_payload), encoding="utf-8")

    # Mock load_brand_profile to return styling with is_critical=True declaratively!
    # This prevents coupling our tests to hardcoded client name strings!
    mock_brand_data = {
        "company_name": "NTT DATA",
        "default_classification": "Confidencial",
        "styling": {
            "is_critical": True,
            "primary_color_hex": "0072BC",
            "alternate_row_color_hex": "F2F2F2",
        },
    }

    # 2. --- ACT ---
    with patch(
        "assessment_engine.infrastructure.config_loader.load_brand_profile",
        return_value=mock_brand_data,
    ):
        bridge = PayloadToASTBridge()
        ast = bridge.convert(str(blueprint_path), str(annex_path))

    # 3. --- ASSERT ---
    # Check that the returned object is a valid DocumentAST
    assert isinstance(ast, DocumentAST)
    assert len(ast.nodes) > 0, "The DocumentAST should contain generated layout nodes."

    # Verify cover page elements are present in the AST
    title_node_text = ast.nodes[1].text
    assert "Informe de Situación Actual" in title_node_text

    # Verify technical title contains our tower name
    title_heading = ast.nodes[2]  # HeadingNode for tech annex
    assert "Seguridad de Red" in title_heading.text

    # Verify client is correctly embedded
    client_paragraph = ast.nodes[4]
    assert "GENERIC CORPORATE CLIENT" in client_paragraph.text

    # Verify that the new direct Chapter 3 introduction is present
    has_chapter_intro = any(
        isinstance(node, ParagraphNode) and "hallazgos operativos" in node.text
        for node in ast.nodes
    )
    assert has_chapter_intro, (
        "New strategic Chapter 3 introduction was not compiled into AST."
    )

    # Verify that the transversal Markdown module was compiled and merged into the AST
    has_transversal_desc = any(
        isinstance(node, ParagraphNode) and "Análisis transversal" in node.text
        for node in ast.nodes
    )
    assert has_transversal_desc, (
        "Transversal Markdown module was not compiled into AST."
    )

    # Verify that the CSV Risk Matrix was parsed into a native TableNode
    has_risk_tables = any(isinstance(node, TableNode) for node in ast.nodes)
    assert has_risk_tables, (
        "FAIR CSV risk matrix was not compiled into TableNode in AST."
    )

    # Invariante de calibración sectorial: cuando is_critical=True, inyecta la nota regulatoria
    has_critical_note = any(
        isinstance(node, ParagraphNode) and "Nota de Calibración de Sector" in node.text
        for node in ast.nodes
    )
    assert has_critical_note, (
        "Compilación con is_critical=True debe inyectar la nota de sector crítico."
    )

    # Invariante de aislamiento: cuando is_critical=False o ausente (None), no debe inyectar la nota (Aniquilador COR)
    mock_default_styling = dict(mock_brand_data)
    mock_default_styling["styling"] = {}  # styling sin la clave is_critical
    with patch(
        "assessment_engine.infrastructure.config_loader.load_brand_profile",
        return_value=mock_default_styling,
    ):
        ast_default = PayloadToASTBridge().convert(str(blueprint_path), str(annex_path))
        has_crit_default = any(
            isinstance(node, ParagraphNode) and "Nota de Calibración de Sector" in node.text
            for node in ast_default.nodes
        )
        assert not has_crit_default, (
            "Cuando is_critical no está especificado (None), el valor por defecto debe ser False."
        )


def test_systemic_risk_bullets_mutation_gate() -> None:
    """Verify that systemic risk bullet formatters rigorously evaluate relational thresholds."""
    from assessment_engine.adapters.compilers.payload_to_ast import (
        _build_criticality_bullet,
        _build_dii_bullet,
        _build_regulatory_bullet,
    )

    node_dii = _build_dii_bullet(5.0, locale="es")
    assert "Alta Estabilidad" in node_dii.text

    node_crit = _build_criticality_bullet(90.0, locale="es")
    assert "Extrema" in node_crit.text

    node_reg = _build_regulatory_bullet(85.0, locale="es")
    assert "Crítica" in node_reg.text


@pytest.mark.xdist_group(name="locales")
def test_english_ast_bullets_and_appendices() -> None:
    """Verify that systemic risk bullet formatters and appendices support English without Spanish leakages."""
    from assessment_engine.adapters.compilers.ast_appendices_builder import (
        build_appendix_d_methodology,
    )
    from assessment_engine.adapters.compilers.payload_to_ast import (
        _build_criticality_bullet,
        _build_dii_bullet,
        _build_erc_bullet,
        _build_feasibility_bullet,
        _build_regulatory_bullet,
        _build_spof_bullet,
    )
    from assessment_engine.domain.schemas.ast import HeadingNode, ParagraphNode

    # 1. Assert English bullets
    en_crit = _build_criticality_bullet(90.0, locale="en")
    assert "Business Criticality (MCDA)" in en_crit.text
    assert "Extreme" in en_crit.text
    assert "Extrema" not in en_crit.text

    en_reg = _build_regulatory_bullet(85.0, locale="en")
    assert "Regulatory Pressure (MCDA)" in en_reg.text
    assert "Critical" in en_reg.text
    assert "Crítica" not in en_reg.text

    en_viab = _build_feasibility_bullet(75.0, locale="en")
    assert "Operational Feasibility (MCDA)" in en_viab.text
    assert "Feasible" in en_viab.text

    en_dii = _build_dii_bullet(5.0, locale="en")
    assert "Diagnostic Consistency (DII)" in en_dii.text
    assert "High Stability" in en_dii.text

    en_erc = _build_erc_bullet(0.65, locale="en")
    assert "Cascading Fault Propagation (ERC)" in en_erc.text
    assert "High" in en_erc.text

    en_spof = _build_spof_bullet("YES", locale="en")
    assert "Single Point of Failure (SPOF)" in en_spof.text
    assert "Critical" in en_spof.text
    assert "SÍ - Crítico" not in en_spof.text

    # 2. Assert English Appendix D Methodology Nodes
    ctx = {
        "vocab": {},
        "meta_lang": "en",
        "currency": "EUR",
        "tower_id": "T6",
        "blueprint_data": {
            "pillars_analysis": [
                {
                    "pillar_name": "Security Architecture",
                    "weight_pct": 25,
                    "kpis": [{"kpi_name": "Zero Trust Core"}],
                }
            ]
        },
    }
    nodes: list[Any] = []
    build_appendix_d_methodology(
        ctx=ctx,
        nodes=nodes,
        primary_color_rgb=[0, 114, 188],
        brand_data={"styling": {"is_critical": False}},
        alt_row_hex="F2F2F2",
    )

    headings = [n.text for n in nodes if isinstance(n, HeadingNode)]
    assert "Maturity Assessment Methodology" in headings
    assert "Evaluated Capabilities and Score Calculation" in headings
    assert "Quantitative Risk Methodology" in headings
    assert "Threat Event Frequency Criteria (TEF)" in headings
    assert "Direct/Indirect Loss Magnitude Criteria (LM)" in headings
    assert "Advanced Systemic Resilience Indicators" in headings

    paragraphs = [n.text for n in nodes if isinstance(n, ParagraphNode)]
    corpus = " \n ".join(paragraphs)
    assert "Metodología Cuantitativa de Riesgos" not in corpus
    assert "Falacia de los Promedios" not in corpus
    assert "Flaw of Averages" in corpus
    assert "O-FAIR (Factor Analysis of Information Risk)" in corpus

