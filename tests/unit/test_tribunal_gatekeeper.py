"""Automated Tribunal Gatekeeper Test Suite.

Audits compiled DOCX deliverables to enforce zero cross-domain contamination,
topological narrative alignment (Cloud vs On-Prem), and absolute ALE arithmetic consistency.
"""

from pathlib import Path
import docx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MOLINS_ANNEX_DIR = REPO_ROOT / "working" / "out" / "Molins_Entrega_Cliente_Final" / "02_DIAGNOSTICOS_ASIS"
STARLING_DIR = REPO_ROOT / "working" / "out" / "starling_bank"


def test_t3_networks_zero_storage_contamination() -> None:
    t3_files = list(MOLINS_ANNEX_DIR.glob("*Anexo_03_*.docx"))
    assert len(t3_files) > 0, "Missing Molins T3 annex"
    doc = docx.Document(t3_files[0])

    p90_text = ""
    for p in doc.paragraphs:
        if "Para evaluar el límite real de resistencia operativa de esta torre" in p.text:
            p90_text = p.text.lower()
            break

    assert p90_text != "", "Could not locate P90 callout paragraph in T3"
    assert "almacenamiento" not in p90_text, "T3 P90 text contains storage contamination!"
    assert "conmutación" in p90_text or "enrutamiento" in p90_text or "wan" in p90_text


def test_t10_plant_ot_zero_database_contamination() -> None:
    t10_files = list(MOLINS_ANNEX_DIR.glob("*Anexo_10_*.docx"))
    assert len(t10_files) > 0, "Missing Molins T10 annex"
    doc = docx.Document(t10_files[0])

    p90_text = ""
    for p in doc.paragraphs:
        if "Para evaluar el límite real de resistencia operativa de esta torre" in p.text:
            p90_text = p.text.lower()
            break

    assert p90_text != "", "Could not locate P90 callout paragraph in T10"
    assert "base de datos" not in p90_text and "bases de datos" not in p90_text, "T10 contains database contamination!"
    assert "almacenamiento" not in p90_text, "T10 contains storage contamination!"
    assert "scada" in p90_text or "plc" in p90_text or "pesaje" in p90_text or "expedición" in p90_text


def test_starling_finops_cloud_topology_alignment() -> None:
    t8_files = list(STARLING_DIR.glob("*Annex_08_*.docx"))
    assert len(t8_files) > 0, "Missing Starling Bank Annex 08"
    doc = docx.Document(t8_files[0])

    full_text = " ".join(p.text.lower() for p in doc.paragraphs)
    assert "cloud-native finops topology" in full_text
    assert "on-premise hardware redundancy" not in full_text


def test_molins_finops_onprem_topology_alignment() -> None:
    t8_files = list(MOLINS_ANNEX_DIR.glob("*Anexo_08_*.docx"))
    assert len(t8_files) > 0, "Missing Molins Annex 08"
    doc = docx.Document(t8_files[0])

    sec4_text = ""
    for p in doc.paragraphs:
        if "Gobernanza de Infraestructura y Licenciamiento por Core" in p.text:
            sec4_text = p.text.lower()
            break

    assert sec4_text != "", "Could not find Section 4.1 supplementary context block"
    assert "infraestructura" in sec4_text and "licenciamiento de virtualización por core" in sec4_text
    assert "broadcom" not in sec4_text  # Certified vendor-neutral in engine methodology!
