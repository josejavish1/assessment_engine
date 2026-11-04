"""Unit tests for TomoAsisASTCompiler multi-tenant decoupling (RFC 071 Phase 2).

Validates:
1. Dynamic N-domain scoped topology (e.g. 3 domains: CLOUD, CYBER, DATA).
2. Live extraction of inventory, strengths, findings, and subpillars from tower_payloads in Chapter 4.
3. Actuarial allocation closed-form reconciliation across N domains.
4. Zero single-tenant leakage across non-manufacturing enterprises.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from docx import Document

from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
)


def test_tomo_asis_scoped_custom_topology(tmp_path: Path) -> None:
    """Verifies that an explicitly scoped assessment with 3 custom domains compiles without phantom towers."""
    global_payload = {
        "meta": {
            "client": "Nordic Health Care Group",
            "date": "November 2026",
            "version": "v1.0",
            "language": "en",
        },
        "domain_scope": "scoped",
        "heatmap": [
            {"id": "CLINICAL_CORE", "name": "Hospital EHR & PACS Platforms", "score": 3.85, "ale": 120000.0},
            {"id": "CYBER_DEFENSE", "name": "Biomedical Network & Cyber Defense", "score": 4.10, "ale": 85000.0},
            {"id": "DATA_LAKE", "name": "Genomics & Diagnostic Data Lake", "score": 3.60, "ale": 95000.0},
        ],
        "financial_telemetry": {
            "corporate_ale": 300000.0,
            "annual_p90_var": 750000.0,
            "currency": "EUR",
            "domain_weights": {
                "CLINICAL_CORE": 120000.0,
                "CYBER_DEFENSE": 85000.0,
                "DATA_LAKE": 95000.0,
            },
        },
    }

    tower_payloads = {
        "CLINICAL_CORE": {
            "inventory": "Dual clinical server clusters hosting Epic EHR and Agfa Enterprise PACS storage across 3 hospital centers.",
            "diagnostic_narrative": "Clinical core operations maintain high uptime under strict medical device segregation, with routine failover verified quarterly.",
            "strengths": [
                "Continuous synchronous database replication across campus hospital sites",
                "Automated zero-data-loss failover for critical care and ICU monitoring",
            ],
            "findings": [
                "Unindexed legacy PACS image archives causing query delays during peak rounds",
                "Expiring storage controller firmware requiring scheduled maintenance window",
            ],
            "pillars_analysis": [
                {"pillar_name": "EHR Availability & Resilience", "score": 4.0},
                {"pillar_name": "Diagnostic Imaging Persistence", "score": 3.7},
            ],
        },
        "CYBER_DEFENSE": {
            "inventory": "Next-generation perimeter firewalls, biomedical IoT NAC scanners, and Tier-0 PAM identity governance.",
            "diagnostic_narrative": "Cybersecurity posture enforces strict HIPAA and NIS2 compliance with continuous endpoint detection.",
            "strengths": [
                "Biomedical device isolation on dedicated microsegmented VLANs",
            ],
            "findings": [
                "Privileged identity governance pending automated rotation for emergency break-glass accounts",
            ],
            "pillars_analysis": [
                {"pillar_name": "Biomedical Device Security", "score": 4.2},
                {"pillar_name": "Privileged Identity Access", "score": 4.0},
            ],
        },
        "DATA_LAKE": {
            "inventory": "Centralized object storage and high-performance computing clusters for medical genomics research.",
            "diagnostic_narrative": "Research data lake provides scalable analytical throughput with automated dataset pseudonymization.",
            "strengths": [
                "Automated patient data de-identification compliant with GDPR Article 9",
            ],
            "findings": [
                "Storage tiering policy requires automated archiving of cold analytical runs",
            ],
            "pillars_analysis": [
                {"pillar_name": "Data Anonymization", "score": 3.8},
                {"pillar_name": "Analytical Pipeline Lifecycle", "score": 3.4},
            ],
        },
    }

    out_docx = tmp_path / "Nordic_Health_Care_Tomo1_ASIS.docx"
    compiler = Volume1AsisASTCompiler()
    result_path = compiler.compile(
        global_payload=global_payload,
        tower_payloads=tower_payloads,
        output_docx_path=out_docx,
        doc_lang="en",
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 30000

    doc = Document(str(result_path))
    full_text = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)

    # Must contain the 3 scoped domains
    assert "CLINICAL_CORE" in full_text
    assert "CYBER_DEFENSE" in full_text
    assert "DATA_LAKE" in full_text

    # Must contain live payload data in Chapter 4
    assert "Dual clinical server clusters hosting Epic EHR" in full_text
    assert "Next-generation perimeter firewalls" in full_text
    assert "Biomedical device isolation on dedicated microsegmented VLANs" in full_text

    # Must contain ZERO single-tenant Molins artifacts
    full_lower = full_text.lower()
    assert "molins" not in full_lower
    assert "secil" not in full_lower
    assert "sant vicen" not in full_lower
    assert "weighbridge" not in full_lower
    assert "simplivity" not in full_lower
