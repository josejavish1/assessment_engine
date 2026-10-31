"""Empirical Certification Test for Multilingual Document Compilation Purity.

Asserts that compiling a document with doc_lang="en" yields 100% English headings,
CMMI tables, MCDA interdependences, FAIR methodology appendices, and decision matrices,
with ZERO Spanish section leakages.
"""

from __future__ import annotations

import json
from pathlib import Path
from docx import Document
import pytest

from assessment_engine.adapters.compile_asis_docx_from_modules import compile_docx


@pytest.mark.xdist_group(name="locales")
def test_english_annex_compilation_purity(tmp_path: Path) -> None:
    """ASSERTS that an English document compiles with pure English sections and no Spanish leaks."""
    modules_dir = tmp_path / "asis_modules"
    modules_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write mock markdown modules
    (modules_dir / "01_introduccion_alcance.md").write_text(
        "# 1. Introduction and Scope\nDetailed diagnostic methodology and enterprise boundaries.",
        encoding="utf-8",
    )
    (modules_dir / "02_resumen_ejecutivo.md").write_text(
        "# 2. Executive Summary\nExecutive posture for the evaluated security domain.",
        encoding="utf-8",
    )
    (modules_dir / "03_descripcion_plataforma.md").write_text(
        "# 3. Platform Architecture\nCurrent technical architecture and operational baseline.",
        encoding="utf-8",
    )
    (modules_dir / "04_analisis_pilares.md").write_text(
        "# 4. Pillar Diagnostic\nCore capabilities, gaps, and technical debt analysis.",
        encoding="utf-8",
    )
    (modules_dir / "05_transversal.md").write_text(
        "# 5. Cross-Domain Analysis\nTopological dependencies and structural risks.",
        encoding="utf-8",
    )
    (modules_dir / "07_conclusiones.md").write_text(
        "# 7. Conclusions\nStrategic roadmap and operational takeaways.",
        encoding="utf-8",
    )

    # 2. Write mock O-FAIR CSV matrix
    csv_content = (
        "Capability_Header;Finding;Business_Risk;TEF;LM;ALE\n"
        "Security - Encryption;Missing encryption at rest;Confidential data breach;2.5;50000;100000\n"
    )
    (modules_dir / "06_matriz_riesgos_fair.csv").write_text(csv_content, encoding="utf-8-sig")

    # 3. Write mock English blueprint payload
    blueprint_payload = {
        "document_meta": {
            "language": "en",
            "doc_lang": "en",
            "tower_name": "Infrastructure Security & Identity",
            "tower_code": "T6",
            "client_name": "Global Holding Enterprise",
            "version": "2.0",
            "date": "October 2026",
            "currency": "EUR",
            "currency_symbol": "€",
        },
        "total_fair_ale": 180000.00,
        "executive_summary": {
            "global_score": "3.80 / 5.00",
            "global_band": "Managed",
        },
        "pillar_score_profile": {
            "pillars": [
                {
                    "pilar_name": "Security Architecture",
                    "score": 3.8,
                    "band": "Managed",
                    "executive_reading": "Resilient zero trust control plane active.",
                }
            ]
        },
        "epistemic_analysis": {
            "business_criticality": 85.0,
            "regulatory_compliance": 90.0,
            "implementation_feasibility": 70.0,
            "audits": {
                "decision_instability_index": {"T6": 8.5},
                "eigenvector_risk_centrality": {"T6": 0.65},
                "single_point_of_failure_by_cascade": "T6",
            },
        },
        }
    (tmp_path / "blueprint_t6_payload.json").write_text(
        json.dumps(blueprint_payload, ensure_ascii=False), encoding="utf-8"
    )

    # 3.1 Write client intelligence with tower overrides for epistemic metrics
    intel_data = {
        "tower_overrides": {
            "T6": {
                "metrics": {
                    "business_criticality": 85.0,
                    "regulatory_compliance": 90.0,
                    "implementation_feasibility": 70.0,
                },
                "sensitivity_analysis": {
                    "decision_instability_indices": {"dii_threshold_03_pct": 8.5}
                },
            }
        },
        "epistemic_graph": {
            "audits": {
                "eigenvector_risk_centrality": {"T6": 0.65},
                "single_point_of_failure_by_cascade": "T6",
            }
        },
    }
    (tmp_path / "client_intelligence.json").write_text(
        json.dumps(intel_data, ensure_ascii=False), encoding="utf-8"
    )

    # 4. Act: Compile English DOCX report
    output_docx = tmp_path / "Technical_Annex_T6_English.docx"
    compile_docx(str(tmp_path), str(output_docx))
    assert output_docx.exists()

    # 5. Assert: Extract all text from paragraphs and tables
    doc = Document(str(output_docx))
    full_text = []
    for p in doc.paragraphs:
        if p.text:
            full_text.append(p.text)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                if cell.text:
                    full_text.append(cell.text)
    corpus = " \n ".join(full_text)

    # Check for expected canonical English phrases
    expected_en = [
        "Maturity Level",
        "Operational Maturity Level Interpretation",
        "Strategic Indicator",
        "Business Criticality (MCDA)",
        "Quantitative Risk Methodology",
        "Strategic Conclusions and Decision Framework",
        "Path A: Inaction (Status Quo)",
        "Path B: Structural Modernization",
        "Operational Resilience & Economic Exposure:",
        "Annual Loss Exposure (ALE):",
        "Worst Case (CVaR):",
        "Self-Assessment Questionnaire",
        "Enterprise Context Dossier",
        "Platform Intelligence Layer",
        "The technical assessment places tower maturity at",
    ]
    for en_phrase in expected_en:
        assert en_phrase in corpus, f"Expected English phrase '{en_phrase}' not found in compiled DOCX"

    # Check that legacy Spanish headers and sentences do NOT appear in the English document
    banned_es = [
        "Nivel de Madurez",
        "Descripción de Estado de Prácticas",
        "Indicador Estratégico",
        "Conclusiones y Coste de Inacción",
        "Camino A: Inacción (Do Nothing)",
        "Camino B: Modernización Estructural",
        "Exposición Cuantitativa (FAIR):",
        "Exposición Financiera Proyectada:",
        "Pérdida Anualizada (ALE):",
        "Peor Caso (CVaR):",
        "Cuestionario de Autoevaluación",
        "Dossier de Contexto",
        "Capa de Inteligencia de la Plataforma",
        "Pérdida Anualizada (ALE - Annual Loss Exposure):",
        "Déficit Esperado Condicional",
        "La calificación cuantitativa obtenida de",
        "sitúa a la plataforma en la banda de",
        "Prácticas operativas consolidadas",
        "Gobernanza estándar",
        "Justificación de Estándares Sectoriales",
        "Evidencia extraída",
        "Bóveda local",
    ]
    for es_phrase in banned_es:
        assert es_phrase not in corpus, f"Banned Spanish phrase '{es_phrase}' leaked into English DOCX"
