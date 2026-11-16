"""
Phase G Characterization and Regression Test Suite: Regulatory Language Policy (NIS2).

Enforces the LanguagePolicy invariant regarding non-judicial regulatory framing:
1. Executive summary tables must not issue definitive legal compliance opinions such as
   'Conformidad Parcial (Directiva NIS2)'.
2. In accordance with the assessment methodology disclaimer (which notes that no formal statutory
   compliance audit was conducted), regulatory gaps must be phrased as operational resilience
   attention levels (e.g., 'Nivel de Atención Moderado (Alineación con {reg})').
3. engine_config/locales.json must formulate reg_gap_high, reg_gap_partial, and reg_gap_low
   as consultative resilience alignment levels, completely free of 'Conformidad Parcial'.
4. Compiled DOCX files must not contain judicial compliance verdicts.
"""

import json
from pathlib import Path
import docx
import pytest

from assessment_engine.infrastructure.runtime_paths import ROOT


def test_locales_regulatory_language_policy():
    """1. engine_config/locales.json must not formulate regulatory gaps as judicial 'Conformidad Parcial'."""
    locales_path = ROOT / "engine_config" / "locales.json"
    data = json.loads(locales_path.read_text(encoding="utf-8"))

    es_dict = data.get("es", {})
    reg_partial = es_dict.get("reg_gap_partial", "")
    reg_high = es_dict.get("reg_gap_high", "")

    assert "conformidad parcial" not in reg_partial.lower(), (
        f"Judicial compliance claim found in reg_gap_partial: '{reg_partial}'"
    )
    assert "atención prioritaria" not in reg_high.lower() or "alineación" in reg_high.lower(), (
        f"reg_gap_high should frame resilience alignment: '{reg_high}'"
    )


def test_compiled_docx_regulatory_cleanliness():
    """2. Compiled DOCX technical annexes must not contain judicial 'Conformidad Parcial' claims."""
    annex_dir = ROOT / "working" / "out" / "molins_fresh_e2e" / "02_ANEXOS_TECNICOS_ESPECIALISTAS"
    if not annex_dir.exists():
        pytest.skip(f"Annex directory not found at {annex_dir}")

    violations = []
    for docx_file in sorted(annex_dir.glob("*.docx")):
        doc = docx.Document(docx_file)
        for t in doc.tables:
            for r in t.rows:
                for c in r.cells:
                    if "conformidad parcial" in c.text.lower():
                        violations.append(f"{docx_file.name}: cell contains '{c.text.strip()}'")

    assert not violations, "Judicial compliance claims found in compiled DOCX tables:\n" + "\n".join(violations)
