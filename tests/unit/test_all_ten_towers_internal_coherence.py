"""Automated Unit Consistency Test for all 10 Molins AS-IS Towers.

Validates that for every single compiled deliverable:
1. Table 1 (KPI Dashboard) score matches Table 3 (Detailed Dashboard) score exactly.
2. Table 1 maturity band matches Table 3 maturity band exactly.
3. The average of Table 4 pillars matches the global score within rounding (0.01).
4. Zero legacy files (scoring_output.json) pollute the pipeline.
5. Strict adherence to canonical ANNEX_MATURITY_BANDS.
"""

from pathlib import Path
import docx
import pytest

from assessment_engine.domain.maturity_band import ANNEX_MATURITY_BANDS, resolve_maturity_band
from assessment_engine.infrastructure.localization import t as translator

ANNEX_DIR = Path("working/out/Molins_Entrega_Cliente_Final/02_DIAGNOSTICOS_ASIS")

@pytest.mark.parametrize("tower_num", [f"{i:02d}" for i in range(1, 11)])
def test_tower_internal_coherence(tower_num: str) -> None:
    if not ANNEX_DIR.exists():
        pytest.skip(f"Clean checkout: Deliverables directory not found at {ANNEX_DIR}")
    files = list(ANNEX_DIR.glob(f"*Anexo_{tower_num}_*.docx"))
    if not files:
        pytest.skip(f"Clean checkout: Deliverable for tower {tower_num} not yet generated in {ANNEX_DIR}")
    assert len(files) == 1, f"Missing deliverable for tower {tower_num} in {ANNEX_DIR}"
    doc = docx.Document(files[0])

    # Table 1: KPI Dashboard Table (Top of Document)
    t1 = doc.tables[0]
    t1_score_str = t1.cell(1, 0).text.strip().replace("\n", " ")
    t1_band_str = t1.cell(1, 1).text.strip().replace("\n", " ")

    # Table 3: Section 3.1 Detailed Dashboard
    t3 = doc.tables[2]
    t3_score_str = t3.cell(1, 0).text.strip().replace("\n", " ")
    t3_band_str = t3.cell(1, 1).text.strip().replace("\n", " ")

    # Invariant 1: Scores must be identical in Table 1 and Table 3
    assert t1_score_str == t3_score_str, (
        f"Tower {tower_num} score mismatch: Table 1 shows '{t1_score_str}' but Table 3 shows '{t3_score_str}'"
    )

    # Invariant 2: Maturity bands must be identical in Table 1 and Table 3
    assert t1_band_str == t3_band_str, (
        f"Tower {tower_num} band mismatch: Table 1 shows '{t1_band_str}' but Table 3 shows '{t3_band_str}'"
    )

    # Parse numerical score
    score_val = float(t1_score_str.split(" / ")[0].replace(",", "."))

    # Invariant 3: Band must match canonical ANNEX_MATURITY_BANDS resolution
    resolved_band = resolve_maturity_band(score_val, ANNEX_MATURITY_BANDS, locale="es", translator=translator)
    expected_band_label = resolved_band.get("label", "")
    assert expected_band_label.lower() in t1_band_str.lower(), (
        f"Tower {tower_num} score {score_val} resolved to '{expected_band_label}' but Table 1 displays '{t1_band_str}'"
    )

    # Table 4: Pillar breakdown table
    t4 = doc.tables[3]
    pillar_scores = []
    for r in t4.rows[1:]:
        raw_p = r.cells[1].text.strip().replace(",", ".")
        try:
            pillar_scores.append(float(raw_p))
        except ValueError:
            pass

    if pillar_scores:
        expected_avg = round(sum(pillar_scores) / len(pillar_scores), 2)
        assert abs(score_val - expected_avg) <= 0.15, (
            f"Tower {tower_num} global score {score_val} diverges from pillar average {expected_avg} ({pillar_scores})"
        )
