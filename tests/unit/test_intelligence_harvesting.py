# golden-path: ignore
from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.application.run_intelligence_harvesting import (
    load_pdf_cache,
    save_pdf_cache,
)
from assessment_engine.domain.prompts.intelligence_prompts import (
    get_business_harvester_prompt,
    get_grounding_harvester_prompt,
    get_regulatory_harvester_prompt,
    get_tech_harvester_prompt,
    get_technical_analyst_prompt,
)
from assessment_engine.adapters.compilers.payload_to_ast import PayloadToASTBridge
from assessment_engine.adapters.generate_asis_markdown_modules import generate_modules


def test_pdf_cache_loading_and_saving(tmp_path: Path):
    """Verify that load_pdf_cache and save_pdf_cache correctly load and save PDF extraction results."""
    cache_file = tmp_path / "test_pdf_cache.json"

    # 1. Loading from non-existent file should return empty dict
    cache = load_pdf_cache(cache_file)
    assert cache == {}

    # 2. Save cache with some sample entries
    sample_data = {
        "hash_abc123": "Extracted text content for ABC",
        "hash_xyz789": "Extracted text content for XYZ",
    }
    save_pdf_cache(cache_file, sample_data)
    assert cache_file.exists()

    # 3. Load cache from existing file
    loaded_cache = load_pdf_cache(cache_file)
    assert loaded_cache == sample_data

    # 4. Handle corrupted cache file gracefully
    cache_file.write_text("{invalid json", encoding="utf-8")
    loaded_corrupted = load_pdf_cache(cache_file)
    assert loaded_corrupted == {}


def test_intelligence_harvesting_prompt_security():
    """Verify that harvesting prompts contain XML prompt sandboxing tags and security warnings."""
    # 1. Grounding prompt
    grounding_prompt = get_grounding_harvester_prompt("test_context_text")
    assert "<ground_truth_fragments>" in grounding_prompt
    assert "</ground_truth_fragments>" in grounding_prompt
    assert "⚠️ NOTA DE SEGURIDAD" in grounding_prompt

    # 2. Business prompt
    business_prompt = get_business_harvester_prompt("test_client", "test_context_text")
    assert "<untrusted_rag_context>" in business_prompt
    assert "</untrusted_rag_context>" in business_prompt
    assert "⚠️ NOTA DE SEGURIDAD" in business_prompt

    # 3. Tech prompt
    tech_prompt = get_tech_harvester_prompt("test_client", "test_context_text")
    assert "<untrusted_rag_context>" in tech_prompt
    assert "</untrusted_rag_context>" in tech_prompt
    assert "⚠️ NOTA DE SEGURIDAD" in tech_prompt

    # 4. Regulatory prompt
    regulatory_prompt = get_regulatory_harvester_prompt("test_client", "test_context_text")
    assert "<untrusted_rag_context>" in regulatory_prompt
    assert "</untrusted_rag_context>" in regulatory_prompt
    assert "⚠️ NOTA DE SEGURIDAD" in regulatory_prompt

    # 5. Technical Analyst prompt
    analyst_prompt = get_technical_analyst_prompt("T1", "Pillar 1", 3.5, "Context", "Evidence Text")
    assert "<untrusted_evidence_fragments>" in analyst_prompt
    assert "</untrusted_evidence_fragments>" in analyst_prompt
    assert "⚠️ NOTA DE SEGURIDAD" in analyst_prompt


def test_ast_bridge_systemic_risk_table(tmp_path: Path):
    """Verify that PayloadToASTBridge correctly parses client_intelligence.json and injects the Systemic Risk table in Spanish."""
    client_dir = tmp_path / "test_client"
    tower_dir = client_dir / "T2"
    tower_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create mock client_intelligence.json with MCDA and Epistemic Graph metrics
    intelligence_data = {
        "version": "3.0",
        "client_name": "TestClient",
        "tower_overrides": {
            "T2": {
                "target_maturity": 4.2,
                "metrics": {
                    "business_criticality": 95.0,
                    "regulatory_compliance": 85.0,
                    "implementation_feasibility": 70.0,
                },
                "sensitivity_analysis": {
                    "decision_instability_indices": {
                        "dii_threshold_03_pct": 5.4,
                    }
                }
            }
        },
        "epistemic_graph": {
            "audits": {
                "single_point_of_failure_by_cascade": "T2",
                "single_point_of_failure_by_centrality": "T5",
                "eigenvector_risk_centrality": {
                    "T2": 0.85,
                }
            }
        }
    }
    intelligence_file = client_dir / "client_intelligence.json"
    intelligence_file.write_text(json.dumps(intelligence_data, ensure_ascii=False), encoding="utf-8")

    # 2. Create mock blueprint_payload.json
    blueprint_payload = {
        "document_meta": {
            "tower_code": "T2",
            "tower_name": "Substation Systems",
            "client_name": "TestClient",
            "version": "1.0",
            "date": "June 2026",
            "language": "es",
        },
        "executive_summary": {
            "global_score": "2.4",
            "global_band": "Nivel 2 - Básico",
        },
        "pillars_analysis": []
    }
    blueprint_file = tower_dir / "blueprint_t2_payload.json"
    blueprint_file.write_text(json.dumps(blueprint_payload, ensure_ascii=False), encoding="utf-8")

    # 3. Instantiate and run convert
    bridge = PayloadToASTBridge()
    ast = bridge.convert(str(blueprint_file), str(tower_dir / "approved_annex_t2.template_payload.json"))

    # 4. Assertions on the generated AST nodes
    headings = [node.text for node in ast.nodes if hasattr(node, "text") and node.__class__.__name__ == "HeadingNode"]
    assert "Análisis de Interdependencias Tecnológicas y Negocio" in headings

    # Verify that all texts (including table cells) contain expected metrics in Spanish
    all_texts = []
    for node in ast.nodes:
        if hasattr(node, "text"):
            all_texts.append(node.text)
        elif node.__class__.__name__ == "TableNode":
            for row in node.rows:
                for cell in row.cells:
                    all_texts.append(cell.text)

    assert any("Criticidad de Negocio" in t for t in all_texts)
    assert any("Consistencia del Diagnóstico" in t for t in all_texts)


def test_generate_modules_tech_atoms(tmp_path: Path):
    """Verify that generate_modules extracts and embeds description cleanly without empty tech atom tables."""
    client_dir = tmp_path / "test_client"
    tower_dir = client_dir / "T2"
    tower_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create mock client_intelligence.json
    intelligence_data = {
        "version": "3.0",
        "client_name": "TestClient",
        "technology_context": {
            "technical_stack": [
                {
                    "technology": "ABB Cloud Hosting",
                    "vendor": "ABB",
                    "source": {"uri": "http://abb.com/substation"}
                }
            ],
            "field_metrics": []
        }
    }
    intelligence_file = client_dir / "client_intelligence.json"
    intelligence_file.write_text(json.dumps(intelligence_data, ensure_ascii=False), encoding="utf-8")

    # 2. Create mock blueprint_payload.json
    blueprint_payload = {
        "document_meta": {
            "tower_code": "T2",
            "tower_name": "Substation Systems",
            "client_name": "TestClient",
            "version": "1.0",
            "language": "es",
        },
        "pillars_analysis": [
            {
                "pilar_name": "Pilar T2",
                "score": 2.4,
                "asis_architecture_description": "Entorno de subestaciones con relés de protección y control de tensión ABB.",
            }
        ]
    }
    blueprint_file = tower_dir / "blueprint_t2_payload.json"
    blueprint_file.write_text(json.dumps(blueprint_payload, ensure_ascii=False), encoding="utf-8")

    # 3. Run generate_modules
    generate_modules(str(blueprint_file))

    # 4. Verify that the generated platform description file is clean and does NOT contain empty tech atoms tables
    platform_desc_file = tower_dir / "asis_modules" / "03_descripcion_plataforma.md"
    assert platform_desc_file.exists()
    content = platform_desc_file.read_text(encoding="utf-8")

    # The text description must be here, but NOT the ugly AI diagnostic tables
    assert "Descripción de la Plataforma de Infraestructura Actual" in content
    assert "Entorno de subestaciones" in content
    assert "Inventario de Átomos de Infraestructura" not in content


def test_source_vault_extracts_new_brands():
    """Verify that SourceVault correctly extracts newly integrated brands (Azure, GCP, VMware, Okta)."""
    from assessment_engine.application.run_intelligence_harvesting import SourceVault

    vault = SourceVault("TestClient")
    test_data = {
        "text": "The architecture is built on VMware and Azure, utilizing Okta for authentication and small services in GCP."
    }
    vault.ingest(test_data, "source_doc.docx", "Internal Document")

    atoms_values = [atom["value"] for atom in vault.atoms if atom["category"] == "stack"]
    assert "VMware" in atoms_values
    assert "Azure" in atoms_values
    assert "Okta" in atoms_values
    assert "GCP" in atoms_values


def test_source_vault_extracts_new_metrics():
    """Verify that SourceVault correctly extracts expanded units (kV, vCPUs, EUR, etc.)."""
    from assessment_engine.application.run_intelligence_harvesting import SourceVault

    vault = SourceVault("TestClient")
    test_data = {
        "text": "Se opera un circuito de 400 kV con servidores de 16 vCPUs and un coste de 1500 EUR o 200 €."
    }
    vault.ingest(test_data, "source_doc.docx", "Internal Document")

    metrics = [(atom["value"], atom["unit"]) for atom in vault.atoms if atom["category"] == "metric"]
    
    # Check that kV, vCPUs, EUR, and € are extracted
    units = [m[1] for m in metrics]
    assert "kV" in units
    assert "vCPUs" in units
    assert "EUR" in units
    assert "€" in units
