"""
Módulo finalize_approved.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "working" / "client" / "T5"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> None:
    if len(argv if argv is not None else sys.argv) != 2:
        raise SystemExit("Uso: python scripts/finalize_approved.py <asis|risks>")

    section = (argv if argv is not None else sys.argv)[1].strip().lower()

    draft_file = CASE_DIR / f"draft_{section}.generated.json"
    review_file = CASE_DIR / f"review_{section}.generated.json"
    approved_file = CASE_DIR / f"approved_{section}.generated.json"

    if not draft_file.exists():
        raise FileNotFoundError(f"No existe: {draft_file}")
    if not review_file.exists():
        raise FileNotFoundError(f"No existe: {review_file}")

    draft = load_json(draft_file)
    review = load_json(review_file)

    if review.get("status") != "approve":
        raise RuntimeError(
            f"La seccion {section} no esta aprobada. Estado actual: {review.get('status')}"
        )

    draft["status"] = "approved"
    draft["_approval_metadata"] = {
        "review_status": review.get("status"),
        "overall_assessment": review.get("overall_assessment"),
        "review_notes": review.get("review_notes", []),
    }

    save_json(approved_file, draft)

    logger.info(f"Seccion {section} finalizada en: {approved_file}")
    logger.info("status:", draft["status"])


if __name__ == "__main__":
    main()
