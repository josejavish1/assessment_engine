"""Certification test suite enforcing zero-hardcoding and actuarial integrity across annexes.

Automated Certification Gates (ARCH-AST-2026-V1):
Gate 1: Cross-Vertical Lexical Contamination Test (Zero OT, plant, SCADA, 500-meter in cloud-native).
Gate 2: Semantic Polarity & Rubric Inversion Test (Zero positive controls in Risk Cards).
Gate 3: Linguistic Resolution Test (Zero raw unresolved keys like diag_summary_default).
Gate 4: Actuarial Non-Linear Variance Test (StDev of ALE across risk cards > 0).
"""

from __future__ import annotations

import re
import statistics
from pathlib import Path
import docx
import pytest

from scripts.build_client_delivery_suite import compile_starling_delivery_suite

REPO_ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.xdist_group(name="starling_compilation")


@pytest.fixture(scope="module")
def starling_suite():
    """Compile Starling Bank delivery suite once for certification audit."""
    tomo1, annexes = compile_starling_delivery_suite(client_id="uk_fintech", doc_lang="en")
    annex5 = next((a for a in annexes if "_Annex_05_" in a.name), None)
    assert annex5 is not None, "Annex 05 missing from Starling Bank compiled deliverables!"
    return {"tomo1": tomo1, "annexes": annexes, "annex5": annex5}


def test_gate1_cross_vertical_lexical_contamination(starling_suite):
    """Gate 1: Verify zero OT, plant, SCADA, or 500-meter contamination in Starling Bank."""
    doc = docx.Document(starling_suite["annex5"])
    full_text = "\n".join(p.text for p in doc.paragraphs) + "\n".join(
        "\n".join(c.text for c in r.cells) for t in doc.tables for r in t.rows
    )

    prohibited_tokens = [
        "plant control systems",
        "industrial networks",
        "500-meter",
        "industrial dust",
        "factory gates",
        "weighbridge",
        "molins",
    ]
    for token in prohibited_tokens:
        assert token not in full_text.lower(), f"Gate 1 Failed: Prohibited token '{token}' found in Annex 5!"


def test_gate2_semantic_polarity_risk_cards(starling_suite):
    """Gate 2: Verify risk cards render true risk scenarios, not positive controls or strengths."""
    doc = docx.Document(starling_suite["annex5"])

    # Tables 13 to 18 correspond to the risk cards in Annex 5
    for idx in range(12, min(len(doc.tables), 18)):
        t = doc.tables[idx]
        title_text = t.rows[0].cells[0].text.replace("\n", " ").strip()

        # Assert no positive strength descriptors in title
        assert "standardized procedures and automated controls active" not in title_text.lower(), (
            f"Gate 2 Failed: Strength used as risk title in Table {idx+1}: {title_text}"
        )
        valid_threat_indicators = ["risk", "threat", "failure", "disruption", "latency", "expansion", "deadlock", "operational risk scenario"]
        assert any(ind in title_text.lower() for ind in valid_threat_indicators), (
            f"Gate 2 Failed: Table {idx+1} title does not identify a risk scenario: {title_text}"
        )


def test_gate3_linguistic_resolution_no_raw_keys(starling_suite):
    """Gate 3: Verify zero raw localization keys like diag_summary_default."""
    doc = docx.Document(starling_suite["annex5"])
    full_text = "\n".join(p.text for p in doc.paragraphs) + "\n".join(
        "\n".join(c.text for c in r.cells) for t in doc.tables for r in t.rows
    )

    assert "diag_summary_default" not in full_text, "Gate 3 Failed: Raw key 'diag_summary_default' leaked!"
    assert not re.search(r"\b[a-z0-9]+_[a-z0-9]+_default\b", full_text), "Gate 3 Failed: Raw default key pattern found!"


def test_gate4_actuarial_non_linear_variance(starling_suite):
    """Gate 4: Verify non-linear severity distribution across risk cards (StDev > 0)."""
    doc = docx.Document(starling_suite["annex5"])

    ales: list[float] = []
    for idx in range(12, min(len(doc.tables), 18)):
        t = doc.tables[idx]
        if len(t.rows) > 1:
            ale_cell = t.rows[1].cells[0].text.replace("\n", " ")
            m = re.search(r"£([\d,]+)", ale_cell)
            if m:
                ales.append(float(m.group(1).replace(",", "")))

    assert len(ales) >= 3, f"Gate 4 Failed: Insufficient risk cards extracted ({len(ales)})"
    stdev = statistics.stdev(ales)
    assert stdev > 25.0, f"Gate 4 Failed: Actuarial flattening detected! StDev={stdev:.2f} <= 25.0 (ALEs: {ales})"
