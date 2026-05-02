"""
Módulo assemble_tower_annex.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import json
import logging
from pathlib import Path

from assessment_engine.scripts.lib.config_loader import normalize_tower_name  # type: ignore
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_case_dir,
    resolve_tower_definition_file,
)

logger = logging.getLogger(__name__)


CASE_DIR = resolve_case_dir()
TOWER_DEF_FILE = resolve_tower_definition_file()
TOWER_DEFINITION = json.loads(TOWER_DEF_FILE.read_text(encoding="utf-8"))
TOWER_ID = TOWER_DEFINITION["tower_id"]
TOWER_NAME = normalize_tower_name(TOWER_DEFINITION["tower_name"])
OUT_FILE = CASE_DIR / f"approved_annex_{TOWER_ID.lower()}.generated.json"

FILES = {
    "scoring": CASE_DIR / "scoring_output.json",
    "asis": CASE_DIR / "approved_asis.generated.json",
    "risks": CASE_DIR / "approved_risks.generated.json",
    "tobe": CASE_DIR / "approved_tobe.generated.json",
    "gap": CASE_DIR / "approved_gap.generated.json",
    "todo": CASE_DIR / "approved_todo.generated.json",
    "conclusion": CASE_DIR / "approved_conclusion.generated.json",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def first_non_null(*values):
    for value in values:
        if value is not None:
            return value
    return None


def main() -> None:
    data = {name: load_json(path) for name, path in FILES.items()}
    case_input = load_json(CASE_DIR / "case_input.json")

    score_display = first_non_null(
        data["scoring"].get("display_score"),
        data["scoring"].get("score_display"),
        data["scoring"].get("tower_score_display_1d"),
        data["asis"].get("maturity_summary", {}).get("score_display"),
    )
    maturity_band = first_non_null(
        data["scoring"].get("maturity_band"),
        data["scoring"].get("maturity_label"),
        data["scoring"].get("maturity_band_from_exact", {}).get("label"),
        data["asis"].get("maturity_summary", {}).get("maturity_band"),
    )

    annex = {
        "artifact_type": "tower_annex",
        "artifact_version": "1.1",
        "tower_id": TOWER_ID,
        "tower_name": TOWER_NAME,
        "case_id": case_input.get("case_id"),
        "status": "assembled",
        "sections": {
            "asis": data["asis"],
            "risks": data["risks"],
            "tobe": data["tobe"],
            "gap": data["gap"],
            "todo": data["todo"],
            "conclusion": data["conclusion"],
        },
        "summary": {
            "score_display": score_display,
            "maturity_band": maturity_band,
            "target_maturity": data["tobe"]
            .get("target_maturity", {})
            .get("recommended_level"),
            "section_statuses": {
                "asis": data["asis"].get("status"),
                "risks": data["risks"].get("status"),
                "tobe": data["tobe"].get("status"),
                "gap": data["gap"].get("status"),
                "todo": data["todo"].get("status"),
                "conclusion": data["conclusion"].get("status"),
            },
        },
    }

    OUT_FILE.write_text(
        json.dumps(annex, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info(f"Anexo ensamblado en: {OUT_FILE}")
    logger.info("Secciones incluidas:", ", ".join(annex["sections"].keys()))
    logger.info("Estado general:", annex["status"])
    logger.info("score_display:", annex["summary"]["score_display"])
    logger.info("maturity_band:", annex["summary"]["maturity_band"])


if __name__ == "__main__":
    main()
