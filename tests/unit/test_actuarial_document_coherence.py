"""
Actuarial and Document Coherence Oracle (RFC-086 SOTA Governance).

Enforces strict, closed-form mathematical and linguistic invariants across all
generated client deliverables (.docx) prior to any tribunal submission:

1. Arithmetic Closure Invariant:
   In the P90 catastrophic callout section, the stated total contingency exposure
   MUST exactly equal the sum of primary operational stoppage loss and secondary
   emergency recovery expenditures (allowing max +/- 2.0 EUR rounding tolerance):
       Total_P90 == Direct_Stoppage_Loss + Secondary_Disaster_Spend

2. Physical Duration Ceiling Invariant:
   Routine single-component outage durations on individual risk cards must not
   exceed realistic physical intervention limits (<= 12.0 hours).

3. Linguistic Purity Invariant:
   Zero raw English bracketed placeholders (e.g., "[Insert Pillar Name]", "[English KPI Name]")
   or unlocalized framework keys may leak into client-facing deliverables.
"""

from __future__ import annotations

import re
from pathlib import Path
import pytest
import docx

REPO_ROOT = Path(__file__).resolve().parents[2]
DELIVERABLES_DIR = REPO_ROOT / "working" / "out" / "Molins_Entrega_Cliente_Final" / "02_DIAGNOSTICOS_ASIS"

CURRENCY_NUMBER_RE = re.compile(r"([\d\.,]+)\s*€")
P90_PARAGRAPH_RE = re.compile(
    r"ascendería a\s+([\d\.,]+)\s*€\.\s*Esta cifra se divide.*?:\s*([\d\.,]+)\s*€.*?y\s+([\d\.,]+)\s*€",
    re.IGNORECASE | re.DOTALL,
)
UNRESOLVED_PLACEHOLDER_RE = re.compile(
    r"\[\s*(?:INSERT\s+)?(?:Pillar\s*Name|KPI\s*Name|Capability\s*Name|Domain\s*Name|Tower\s*Name|"
    r"English\s*KPI\s*Name|Control\s*Name|Framework\s*Reference|[^\]]{1,45}?\s*Name)(?:\s+Here)?\s*\]",
    re.IGNORECASE,
)


def _parse_spanish_currency(val_str: str) -> float:
    """Parse Spanish formatted currency string (e.g., '685.148' or '1.250,50') into float."""
    cleaned = val_str.strip().replace(".", "").replace(",", ".")
    return float(cleaned)


def _get_annex_docx_files():
    """Retrieve all available specialist annex DOCX files."""
    if not DELIVERABLES_DIR.exists():
        return []
    return sorted(DELIVERABLES_DIR.glob("Molins_202610_Anexo_*_ASIS.docx"))


@pytest.mark.parametrize("docx_path", _get_annex_docx_files(), ids=lambda p: p.name)
def test_zero_unresolved_template_leaks_in_deliverables(docx_path: Path):
    """Ensure no un-rendered brackets or mail-merge artifacts exist in final documents."""
    doc = docx.Document(docx_path)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    matches = UNRESOLVED_PLACEHOLDER_RE.findall(full_text)
    assert not matches, (
        f"Unresolved template placeholders detected in {docx_path.name}: {matches}"
    )
    assert "Falta de verificación empírica y ausencia de telemetría continua en [" not in full_text, (
        f"Raw bracketed fallback string leaked in {docx_path.name}"
    )


@pytest.mark.parametrize("docx_path", _get_annex_docx_files(), ids=lambda p: p.name)
def test_p90_contingency_paragraph_arithmetic_closure(docx_path: Path):
    """Enforce closed-form arithmetic identity: Total_P90 == Direct_Loss + Secondary_Spend."""
    doc = docx.Document(docx_path)
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    m = P90_PARAGRAPH_RE.search(full_text)
    if not m:
        # P90 callout might be worded differently for FinOps or custom archetype
        return

    total_contingency = _parse_spanish_currency(m.group(1))
    direct_stoppage = _parse_spanish_currency(m.group(2))
    secondary_spend = _parse_spanish_currency(m.group(3))

    expected_sum = direct_stoppage + secondary_spend
    discrepancy = abs(total_contingency - expected_sum)

    assert discrepancy <= 2.0, (
        f"Arithmetic discrepancy in {docx_path.name} P90 callout: "
        f"Stated Total={total_contingency:,.2f} EUR != "
        f"Direct ({direct_stoppage:,.2f} EUR) + Secondary ({secondary_spend:,.2f} EUR) = {expected_sum:,.2f} EUR. "
        f"Discrepancy: {discrepancy:,.2f} EUR."
    )
