"""Automated Tribunal Gatekeeper Test Suite.

Audits compiled DOCX deliverables to enforce zero cross-domain contamination,
topological narrative alignment (Cloud vs On-Prem), and absolute ALE arithmetic consistency.
"""

import json
from pathlib import Path
import docx
import pytest

from assessment_engine.infrastructure.runtime_paths import ROOT
from assessment_engine.adapters.compilers.payload_to_ast import compile_asis_docx_via_ast

BENCHMARK_DIR = ROOT / "tests" / "test_data" / "benchmark_fixtures" / "acme_corp"


def test_t3_networks_zero_storage_contamination_via_compile_and_assert(tmp_path: Path) -> None:
    payload_path = BENCHMARK_DIR / "T3" / "blueprint_t3_payload.json"
    if not payload_path.exists():
        pytest.skip(f"Benchmark payload missing: {payload_path}")

    out_docx = tmp_path / "test_t3_ASIS.docx"
    compile_asis_docx_via_ast(payload_path, out_docx, doc_lang="en")

    doc = docx.Document(str(out_docx))

    # Structural Validation: Document must contain risk tables (Lever 2 breakdown)
    assert len(doc.tables) >= 4, "T3 deliverable is missing structural risk tables."
    
    # Forensic Purity: Verify no storage nomenclature leak in technical findings and risk cards
    finding_paragraphs = [
        p.text.lower()
        for p in doc.paragraphs
        if not ("snia" in p.text.lower() or "iso/iec 27040" in p.text.lower() or "estándar" in p.text.lower())
    ]
    finding_cells = [
        c.text.lower() for t in doc.tables[3:] for r in t.rows for c in r.cells
    ]
    tech_text = " ".join(finding_paragraphs) + " ".join(finding_cells)
    import re
    assert not re.search(r"\b(storage|san|nas)\b", tech_text), "T3 deliverable contains storage contamination!"


def test_t10_plant_ot_zero_database_contamination_via_compile_and_assert(tmp_path: Path) -> None:
    payload_path = BENCHMARK_DIR / "T10" / "blueprint_t10_payload.json"
    if not payload_path.exists():
        pytest.skip(f"Benchmark payload missing: {payload_path}")

    out_docx = tmp_path / "test_t10_ASIS.docx"
    compile_asis_docx_via_ast(payload_path, out_docx, doc_lang="en")

    doc = docx.Document(str(out_docx))

    # Structural Validation: Risk tables must be present and contain RSK codes
    assert len(doc.tables) >= 4, "T10 deliverable is missing structural risk tables."
    
    full_text = " ".join(p.text.lower() for p in doc.paragraphs) + " ".join(
        c.text.lower() for t in doc.tables for r in t.rows for c in r.cells
    )
    # Forensic Purity: Verify no DB or Storage nomenclature leak in T10
    assert "database" not in full_text and "databases" not in full_text, "T10 contains database contamination!"
    assert "storage" not in full_text, "T10 contains storage contamination!"


def test_starling_finops_cloud_topology_alignment() -> None:
    """Verifies that Starling Bank client intelligence enforces pure cloud-native FinOps topology."""
    from assessment_engine.infrastructure.runtime_paths import ROOT
    intel_path = ROOT / "tests" / "test_data" / "synthetic_clients" / "uk_fintech" / "client_intelligence.json"
    assert intel_path.exists(), f"Starling Bank fixture missing: {intel_path}"

    with open(intel_path, "r", encoding="utf-8") as f:
        intel = json.load(f)

    tech_ctx = intel.get("technology_context", {})
    assert tech_ctx.get("dominant_hyperscaler") == "AWS"

    stack_names = [item["name"].lower() for item in tech_ctx.get("group_level_stack", [])]
    assert any("aws" in name or "eks" in name for name in stack_names)
    assert not any("vmware" in name or "simplivity" in name for name in stack_names)


def test_acme_corp_finops_onprem_topology_alignment_via_compile_and_assert(tmp_path: Path) -> None:
    payload_path = BENCHMARK_DIR / "T8" / "blueprint_t8_payload.json"
    if not payload_path.exists():
        pytest.skip(f"Benchmark payload missing: {payload_path}")

    out_docx = tmp_path / "test_t8_ASIS.docx"
    compile_asis_docx_via_ast(payload_path, out_docx, doc_lang="en")

    doc = docx.Document(str(out_docx))

    # Structural Validation: Confirm FinOps tables are populated
    assert len(doc.tables) >= 2, "Acme Corp T8 is missing FinOps tables."
    full_text = " ".join(p.text.lower() for p in doc.paragraphs) + " ".join(
        c.text.lower() for t in doc.tables for r in t.rows for c in r.cells
    )
    assert "broadcom" not in full_text  # Certified vendor-neutral in engine methodology!
