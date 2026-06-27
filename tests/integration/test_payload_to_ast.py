# golden-path: ignore
from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.domain.schemas.ast import DocumentAST


def test_payload_to_ast_bridge_conversion(tmp_path: Path):
    """Verify that PayloadToASTBridge successfully parses payloads and builds a valid DocumentAST.
    
    This integration test ensures that our technical document compiler generates
    the correct corporate cover layout nodes, preventing regressions during document compilation.
    """
    # 1. --- ARRANGE ---
    # Create valid minimal payloads for both blueprint and annex templates
    blueprint_payload = {
        "document_meta": {
            "language": "es",
            "tower_name": "Seguridad de Red",
            "tower_code": "T5",
            "client_name": "NTT DATA Client",
            "version": "1.0",
            "date": "Junio 2026",
            "currency": "€"
        },
        "total_fair_ale": 150000.00,
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
    
    # 2. --- ACT ---
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
    assert "NTT DATA CLIENT" in client_paragraph.text
