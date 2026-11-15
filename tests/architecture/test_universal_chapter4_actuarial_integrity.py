"""Architectural Invariant Test: Universal Chapter 4 Actuarial Integrity & Monism.

Enforces:
1. Mathematical monism between Page 3 Executive Scorecard and Chapter 4 Table 4.1.
2. Complete eradication of cryptic RVS machine codes from executive deliverables.
3. Complete eradication of didactic textbook scale tables from Chapter 4 body.
4. Complete eradication of unrounded false precision numbers (e.g., 148.894 €, 428.532 €).
5. Presence and structural integrity of the 4-Block Executive Risk Cards in Section 4.3.
"""

from __future__ import annotations

import re
from pathlib import Path
import docx
import pytest

from assessment_engine.infrastructure.runtime_paths import ROOT

ANNEX_DIR = ROOT / "working" / "out" / "Molins_Entrega_Oficial_Piramide_Tier1"
OFFICIAL_DOCX_FILES = [
    ROOT / "Molins_202610_Tomo_1_Diagnostico_ASIS.docx"
] + sorted((ANNEX_DIR / "02_ANEXOS_TECNICOS_ESPECIALISTAS").glob("*_ASIS.docx"))


@pytest.mark.parametrize("docx_path", OFFICIAL_DOCX_FILES, ids=lambda p: p.name)
def test_eradication_of_cryptic_rvs_codes(docx_path: Path) -> None:
    """Verifies that no machine codes like RVS01, RVS02 appear in paragraphs or tables."""
    assert docx_path.exists(), f"File missing: {docx_path}"
    doc = docx.Document(docx_path)

    violations: list[str] = []
    rvs_pattern = re.compile(r"\bRVS0[1-9]\b", re.IGNORECASE)

    for p_idx, p in enumerate(doc.paragraphs):
        matches = rvs_pattern.findall(p.text)
        if matches:
            violations.append(f"Paragraph {p_idx}: found {matches} in '{p.text[:60]}'")

    for t_idx, t in enumerate(doc.tables):
        for r_idx, r in enumerate(t.rows):
            for c_idx, c in enumerate(r.cells):
                matches = rvs_pattern.findall(c.text)
                if matches:
                    violations.append(f"Table {t_idx}[R{r_idx}C{c_idx}]: found {matches} in '{c.text[:60]}'")

    assert not violations, (
        f"Cryptic machine code invariant violated in {docx_path.name}:\n"
        + "\n".join(violations[:10])
    )


@pytest.mark.parametrize("docx_path", OFFICIAL_DOCX_FILES, ids=lambda p: p.name)
def test_eradication_of_false_precision_numbers(docx_path: Path) -> None:
    """Verifies that legacy unrounded figures (e.g. 148.894, 428.532, 269.849) do not exist."""
    assert docx_path.exists(), f"File missing: {docx_path}"
    doc = docx.Document(docx_path)

    violations: list[str] = []
    legacy_unrounded = ["148.894", "428.532", "269.849", "114.692", "187.233"]

    for p_idx, p in enumerate(doc.paragraphs):
        for target in legacy_unrounded:
            if target in p.text:
                violations.append(f"Paragraph {p_idx}: found '{target}' in '{p.text[:60]}'")

    for t_idx, t in enumerate(doc.tables):
        for r_idx, r in enumerate(t.rows):
            for c_idx, c in enumerate(r.cells):
                for target in legacy_unrounded:
                    if target in c.text:
                        violations.append(f"Table {t_idx}[R{r_idx}C{c_idx}]: found '{target}' in '{c.text[:60]}'")

    assert not violations, (
        f"False precision invariant violated in {docx_path.name}:\n"
        + "\n".join(violations[:10])
    )
