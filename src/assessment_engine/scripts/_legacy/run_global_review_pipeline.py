"""
Módulo run_global_review_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import asyncio
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

import vertexai
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.prompts.global_prompts import (
    get_global_reviewer_instruction,
    get_global_reviewer_prompt,
)
from assessment_engine.schemas.global_report import GlobalReviewDraft
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.config_loader import (
    resolve_document_profile,
    resolve_model_profile_for_role,
)
from assessment_engine.scripts.lib.runtime_env import ensure_google_cloud_env_defaults

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_input_path(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (ROOT / p).resolve()


def find_duplicate_open_questions(document: dict) -> list[str]:
    sections = document.get("sections", {})
    questions = []
    for sec in sections.values():
        for q in sec.get("notes_for_reviewer", []):
            q = str(q).strip()
            if q:
                questions.append(q)
    counts = Counter(questions)
    return [q for q, n in counts.items() if n > 1]


def build_duplicate_questions_payload(document: dict) -> list[dict]:
    dupes = find_duplicate_open_questions(document)
    sections = document.get("sections", {})
    payload = []
    for d in dupes:
        item = {"question": d, "appearances": []}
        for s_id, s_data in sections.items():
            for q in s_data.get("notes_for_reviewer", []):
                if str(q).strip() == d:
                    item["appearances"].append(s_id)
        payload.append(item)
    return payload


async def run_global_review(
    tower_dir: str,
    tower_id: str,
    tower_name: str,
):
    ensure_google_cloud_env_defaults()
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ["GOOGLE_CLOUD_LOCATION"]

    vertexai.Client(project=project, location=location)

    reviewer_model_profile = resolve_model_profile_for_role("global_reviewer")
    resolve_document_profile()

    case_dir = Path(tower_dir)
    findings_file = case_dir / "findings.json"
    scoring_file = case_dir / "scoring_output.json"
    approved_annex_file = case_dir / f"approved_annex_{tower_id.lower()}.generated.json"

    findings = load_json(findings_file)
    scoring = load_json(scoring_file)
    annex = load_json(approved_annex_file)

    dupes_payload = build_duplicate_questions_payload(annex)

    reviewer_agent = Agent(
        model=reviewer_model_profile["model"],
        name="t5_global_reviewer_agent",
        instruction=get_global_reviewer_instruction(),
    )
    reviewer_app = AdkApp(agent=reviewer_agent)

    logger.info(f"\n=== Iniciando Global Review para {tower_id} ===")

    prompt = get_global_reviewer_prompt(
        tower_id=tower_id,
        tower_name=tower_name,
        findings_json=json.dumps(findings, ensure_ascii=False, indent=2),
        scoring_json=json.dumps(scoring, ensure_ascii=False, indent=2),
        annex_json=json.dumps(annex, ensure_ascii=False, indent=2),
        dupes_json=json.dumps(dupes_payload, ensure_ascii=False, indent=2),
    )

    review_data = await run_agent(
        reviewer_app,
        user_id="global_reviewer_local_dev",
        message=prompt,
        schema=GlobalReviewDraft,
    )

    if not review_data:
        raise RuntimeError("No se pudo obtener el Global Review.")

    output_file = case_dir / "global_review_report.json"
    save_json(output_file, review_data)
    logger.info(f"✅ Reporte de revisión global guardado en: {output_file}")


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 4:
        logger.info(
            "Uso: python -m assessment_engine.scripts.run_global_review_pipeline <tower_dir> <tower_id> <tower_name>"
        )
        sys.exit(1)

    tower_dir = (argv if argv is not None else sys.argv)[1]
    tower_id = (argv if argv is not None else sys.argv)[2]
    tower_name = (argv if argv is not None else sys.argv)[3]

    asyncio.run(run_global_review(tower_dir, tower_id, tower_name))


if __name__ == "__main__":
    main()
