# golden-path: ignore
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.domain.schemas.ast import DocumentAST, TableNode, ParagraphNode


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
    desc_file.write_text("# 4. Descripción\nEsta es la descripción detallada de la plataforma actual.", encoding="utf-8")

    # Write dummy Markdown cross-functional module
    trans_file = modules_dir / "05_transversal.md"
    trans_file.write_text("# 5. Transversal\nAnálisis transversal de capacidades operativas.", encoding="utf-8")

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
            "currency": "€"
        },
        "total_fair_ale": 180000.00,
        "executive_summary": {
            "global_score": "4,50 / 5,00",
            "global_band": "Optimizado"
        },
        "pillar_score_profile": {
            "pillars": [
                {
                    "pilar_name": "Computing",
                    "score": 4.5,
                    "band": "Optimizado",
                    "executive_reading": "Gobernanza de seguridad robusta en edge."
                }
            ]
        }
    }
    
    annex_payload = {
        "document_meta": {
            "tower_code": "T5",
            "tower_name": "Seguridad de Red"
        },
        "remediations": [
            {
                "title": "Cifrado de datos",
                "cost": 50000,
                "benefit": "Mitiga intercepción"
            }
        ]
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
            "alternate_row_color_hex": "F2F2F2"
        }
    }

    # 2. --- ACT ---
    with patch("assessment_engine.infrastructure.config_loader.load_brand_profile", return_value=mock_brand_data):
        bridge = PayloadToASTBridge()
        ast = bridge.convert(str(blueprint_path), str(annex_path))
    
    # 3. --- ASSERT ---
    # Check that the returned object is a valid DocumentAST
    assert isinstance(ast, DocumentAST)
    assert len(ast.nodes) > 0, "The DocumentAST should contain generated layout nodes."
    
    # Verify cover page elements are present in the AST
    first_node_text = ast.nodes[1].text  # ParagraphNode for corporate name (NTT DATA)
    assert "NTT DATA" in first_node_text
    
    # Verify technical title contains our tower name
    title_heading = ast.nodes[3]  # HeadingNode for tech annex
    assert "Seguridad de Red" in title_heading.text
    
    # Verify client is correctly embedded
    client_paragraph = ast.nodes[5]
    assert "GENERIC CORPORATE CLIENT" in client_paragraph.text

    # Verify that the Markdown platform overview was compiled and merged into the AST
    has_platform_desc = any(
        isinstance(node, ParagraphNode) and "descripción detallada" in node.text
        for node in ast.nodes
    )
    assert has_platform_desc, "Platform description Markdown module was not compiled into AST."

    # Verify that the CSV Risk Matrix was parsed into a native TableNode
    has_risk_tables = any(
        isinstance(node, TableNode)
        for node in ast.nodes
    )
    assert has_risk_tables, "FAIR CSV risk matrix was not compiled into TableNode in AST."
