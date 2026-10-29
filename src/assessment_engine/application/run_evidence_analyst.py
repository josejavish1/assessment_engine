"""Coordinates the evidence analysis process.

This module orchestrates an AI agent's analysis of client feedback. It supplies the agent with both quantitative scores and their corresponding full-text qualitative responses. This dual-input architecture enables a more sophisticated, context-aware evaluation than would be possible with numerical data alone.
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.domain.maturity_band import resolve_maturity_band
from assessment_engine.domain.prompts.intelligence_prompts import (
    get_technical_analyst_prompt,
)
from assessment_engine.infrastructure.ai_client import run_agent
from assessment_engine.infrastructure.runtime_paths import ROOT


def load_json(path: Path) -> dict[str, Any]:
    """Parse a UTF-8 encoded JSON file from a file system path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def first_evidence_refs(
    evidences: list[dict], pillar_id: str, limit: int = 3
) -> list[str]:
    """Extracts up to a specified limit of evidence IDs for a given pillar.

    This function iterates through a list of evidence dictionaries in their
    provided order. It collects the 'evidence_id' from each dictionary where
    the 'pillar_ids' list contains the specified `pillar_id`, stopping once
    the `limit` is reached.

    Args:
        evidences: A list of dictionaries representing evidence items. Each item
            must contain an 'evidence_id' key (str) and may optionally contain
            a 'pillar_ids' key (list[str]).
        pillar_id: The identifier for the pillar to retrieve evidence for.
        limit: The maximum number of evidence IDs to return.

    Returns:
        A list of evidence ID strings, maintaining their original relative order,
        with a length no greater than `limit`.

    Raises:
        KeyError: If a dictionary in `evidences` is missing the required
            'evidence_id' key.
    """
    refs = []
    for evidence in evidences:
        if pillar_id in evidence.get("pillar_ids", []):
            refs.append(evidence["evidence_id"])
        if len(refs) >= limit:
            break
    return refs


def band_for_score(score: float, tower_definition: dict) -> str:
    """Retrieves the maturity band label for a given score and tower definition.

    This function determines the appropriate maturity band for a score by consulting
    the `score_bands` list within the provided tower definition. It then
    extracts and returns the 'label' from the resulting band dictionary.

    Args:
        score: The numerical score to classify into a band.
        tower_definition: A dictionary containing the tower configuration. This
            dictionary is expected to contain a "score_bands" key, which holds
            a list of band definition dictionaries.

    Returns:
        The string label of the maturity band corresponding to the input score.

    Raises:
        KeyError: If the resolved band dictionary does not contain a "label" key.
        TypeError: If no matching band can be found and the underlying resolution
            logic returns a non-subscriptable type (e.g., None).
    """
    return resolve_maturity_band(score, tower_definition.get("score_bands", []))[
        "label"
    ]


def _format_answers_summary(answers: list[dict[str, Any]]) -> str:
    """Format assessment answers into a structured text summary for LLM context."""
    lines: list[str] = []
    for ans in answers:
        score = (
            ans.get("value")
            if ans.get("value") is not None
            else ans.get("score", "N/A")
        )
        kpi_label = ans.get("kpi_name", "")
        q_text = (
            ans.get("question_text") or ans.get("context") or "No question text provided"
        )
        prefix = (
            f"- KPI {ans.get('kpi_id')} ({kpi_label}):"
            if kpi_label
            else f"- KPI {ans.get('kpi_id')}:"
        )
        lines.append(f"{prefix} Score {score} | Question/Context: {q_text}")
    return "\n".join(lines) + ("\n" if lines else "")


async def build_findings(
    case_input: dict,
    evidence_ledger: dict,
    scoring_output: dict,
    tower_definition: dict,
) -> dict:
    """Generate qualitative findings by analyzing evidence and scores with an AI agent.

    This function orchestrates an AI-powered analysis for a given assessment case.
    For each scored pillar, it aggregates strategic context, granular evidence
    fragments, and the user's test answers. It then prompts a Gemini-based AI
    agent to synthesize this information into actionable insights. The agent
    identifies specific strengths, gaps, risks, and proposes candidate
    initiatives for improvement. The results for all pillars are compiled into a
    single, structured findings report.

    Args:
        case_input: A dictionary containing the raw inputs for the assessment case,
            including user-provided answers to KPIs.
        evidence_ledger: A dictionary containing all extracted evidence fragments,
            categorized and linked to relevant pillars.
        scoring_output: A dictionary with the quantitative scoring results,
            including the overall tower score and individual pillar scores.
        tower_definition: A dictionary containing the configuration and metadata for
            the specific assessment tower, including maturity band definitions.

    Returns:
        A dictionary representing the complete findings report, structured
        according to the 'findings' schema. This includes a summary, case
        metadata, and detailed, AI-generated qualitative analysis for each pillar.

    Raises:
        KeyError: If essential keys (e.g., 'pillar_id', 'pillar_name', 'score_exact'
            within a pillar entry, or 'tower_score_display_1d' in `scoring_output`)
            are missing from the input dictionaries.
        Exception: Propagates exceptions from the underlying AI agent client
            during the `run_agent` call, which may include network errors,
            API authentication failures, or timeouts.
    """
    evidences = evidence_ledger.get("evidences", [])
    tower_id = scoring_output.get("tower_id", "Unknown")
    case_input.get("context_summary", "")

    answers_text = _format_answers_summary(case_input.get("answers", []))

    #
    from assessment_engine.infrastructure.config_loader import (
        get_consultant_company_name,
        resolve_model_for_role,
    )
    from assessment_engine.infrastructure.localization import (
        resolve_target_language_name,
    )

    company = get_consultant_company_name()
    doc_lang = case_input.get("language") or "en"
    target_lang = resolve_target_language_name(doc_lang)

    agent = Agent(
        name="technical_analyst",
        model=resolve_model_for_role("analyst"),
        instruction=(
            f"You are a Senior Infrastructure & Enterprise Architecture Analyst at {company}.\n\n"
            f"### CRITICAL LANGUAGE MANDATE:\n"
            f"You MUST generate all analytical narratives, findings, observations, and evidence references EXCLUSIVELY in {target_lang}."
        ),
    )
    app = AdkApp(agent=agent)

    pillar_findings = []
    all_valid_fragment_ids = {
        str(e.get("fragment_id")): e for e in evidences if e.get("fragment_id")
    }

    async def _analyze_single_pillar(pillar: dict[str, Any]) -> dict[str, Any]:
        p_id = pillar["pillar_id"]
        p_name = pillar["pillar_name"]
        p_score = pillar["score_exact"]

        print(
            f"    -> Analyzing pillar {p_id} with AI (Hierarchical Context + Assessment Answers)..."
        )

        # Partitioning evidence is a prerequisite for the agent's hierarchical analysis. Strategic evidence provides high-level context, while granular evidence is used for detailed, KPI-specific evaluation.
        p_strat_context = [
            e.get("excerpt", "")
            for e in evidences
            if p_id in e.get("pillar_ids", [])
            and e.get("source_type") == "strategic_summary"
        ]
        p_granular_evidence = [
            f"[{e.get('fragment_id')}] {e.get('excerpt')}"
            for e in evidences
            if p_id in e.get("pillar_ids", [])
            and e.get("source_type") == "atomic_fragment"
        ]

        strat_str = "\n".join(p_strat_context)
        # Expand context budget up to 60,000 chars to prevent arbitrary information loss
        granular_str = "\n".join(p_granular_evidence)
        if len(granular_str) > 60000:
            granular_str = granular_str[:60000].rsplit("\n", 1)[0]

        # Isolate test responses relevant to the current analytical pillar. This scopes the agent's context to a specific strategic area, preventing cross-contamination of evidence and maintaining analytical focus.
        p_answers = "\n".join(
            [a for a in answers_text.split("\n") if f"KPI {p_id}." in a]
        )

        full_analysis_context = f"""
        STRATEGIC CONTEXT SUMMARY:
        {strat_str}

        ASSESSMENT RESPONSES ANALYSIS:
        {p_answers}
        """

        # Invoke the agent with the granular evidence subset for detailed analysis. This payload contains the specific data points required for generating pillar-specific insights.
        analysis = await run_agent(
            app,
            user_id=f"tech_analyst_{p_id}",
            message=get_technical_analyst_prompt(
                tower_id, p_name, p_score, full_analysis_context, granular_str
            ),
        )

        pillar_valid_refs = [
            str(e.get("fragment_id"))
            for e in evidences
            if p_id in e.get("pillar_ids", []) and e.get("fragment_id")
        ]

        strength_text = analysis.get("strength", "Validated operational capability.")
        strength_frag = analysis.get("strength_fragment_id")
        if strength_frag and str(strength_frag) not in all_valid_fragment_ids:
            logger.warning(
                f"⚠️ [Evidence Gate] fragment_id '{strength_frag}' not found in ledger. Reassigning to valid reference."
            )
            strength_frag = pillar_valid_refs[0] if pillar_valid_refs else None

        gap_text = analysis.get("gap", "Identified maturity gap.")
        gap_frag = analysis.get("gap_fragment_id")
        if gap_frag and str(gap_frag) not in all_valid_fragment_ids:
            logger.warning(
                f"⚠️ [Evidence Gate] fragment_id '{gap_frag}' not found in ledger. Reassigning to valid reference."
            )
            gap_frag = pillar_valid_refs[0] if pillar_valid_refs else None

        r_title = analysis.get("risk_title", f"Operational Risk in {p_name}")
        e_tef = int(analysis.get("elicited_tef_score", 3) or 3)
        e_lm = int(analysis.get("elicited_lm_score", 3) or 3)

        inits_data = analysis.get("initiatives", [])
        candidate_initiatives = []
        for idx, init_data in enumerate(inits_data):
            # Dynamic multi-dimensional priority
            if p_score < 2.0 or e_lm >= 4:
                init_priority = "Critical"
            elif p_score < 3.0 or e_tef >= 4:
                init_priority = "High"
            else:
                init_priority = "Medium"

            candidate_initiatives.append(
                {
                    "initiative_id": f"{p_id}-INIT-0{idx + 1}",
                    "title": init_data.get(
                        "title", f"Improvement Plan {p_name} {idx + 1}"
                    ),
                    "priority": init_priority,
                    "horizon": init_data.get("horizon", "Mid-term"),
                    "rationale": init_data.get(
                        "rationale", "Operational resilience improvement."
                    ),
                }
            )

        # Coherence Gate: Map severity deterministically crossing mathematical score and loss magnitude
        if p_score >= 4.0 and e_lm <= 2:
            calibrated_severity = "Low"
        elif p_score < 2.0 or e_lm >= 5:
            calibrated_severity = "Critical"
        elif p_score < 3.0 or e_lm >= 4:
            calibrated_severity = "High"
        else:
            calibrated_severity = "Medium"

        return {
            "pillar_id": p_id,
            "pillar_name": p_name,
            "score_exact": p_score,
            "score_display_1d": round(p_score, 1),
            "current_maturity_band": band_for_score(p_score, tower_definition),
            "strengths": [
                {"statement": strength_text, "fragment_id": strength_frag}
            ],
            "gaps": [{"statement": gap_text, "fragment_id": gap_frag}],
            "risks": [
                {
                    "title": r_title,
                    "severity": calibrated_severity,
                    "_elicited_tef": e_tef,
                    "_elicited_lm": e_lm,
                }
            ],
            "candidate_initiatives": candidate_initiatives,
        }

    pillar_tasks = [
        _analyze_single_pillar(p) for p in scoring_output.get("pillar_scores", [])
    ]
    pillar_findings = await asyncio.gather(*pillar_tasks)

    return {
        "schema_name": "findings",
        "case_id": scoring_output.get("case_id"),
        "tower_id": tower_id,
        "assessment_summary": {
            "key_messages": [
                {
                    "message": f"Tower {tower_id} demonstrates an assessed maturity score of {scoring_output['tower_score_display_1d']}.",
                    "derived_from": [p["pillar_id"] for p in pillar_findings],
                }
            ]
        },
        "pillar_findings": pillar_findings,
    }


async def main(argv: list[str] | None = None) -> None:
    """Executes the main evidence analysis pipeline from command-line arguments.

    This coroutine serves as the primary entry point for the script. It parses
    command-line arguments to obtain paths for a case input file, an evidence
    ledger, and a scoring output file. After loading these JSON-formatted inputs,
    it extracts the `tower_id` from the scoring data to dynamically locate and
    load the corresponding tower definition file. The collected data is then
    passed to the `build_findings` coroutine. Finally, the generated analysis
    findings are serialized and written to a `findings.json` file located in the
    same directory as the scoring output file.

    Raises:
        FileNotFoundError: If the case input, evidence ledger, scoring output,
            or the dynamically located tower definition file does not exist.
        KeyError: If the `tower_id` key is not found in the loaded scoring
            output data.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-input", required=True)
    parser.add_argument("--evidence-ledger", required=True)
    parser.add_argument("--scoring-output", required=True)
    args = parser.parse_args(argv)

    case_input = load_json(Path(args.case_input))
    evidence_ledger = load_json(Path(args.evidence_ledger))
    scoring_output = load_json(Path(args.scoring_output))

    tower_id = scoring_output["tower_id"]
    tower_def_path = (
        ROOT
        / "engine_config"
        / "towers"
        / tower_id
        / f"tower_definition_{tower_id}.json"
    )
    tower_definition = load_json(tower_def_path)

    print(f"🚀 Starting Senior AI Evidence Analysis for {tower_id}...")
    findings = await build_findings(
        case_input, evidence_ledger, scoring_output, tower_definition
    )

    output_path = Path(args.scoring_output).parent / "findings.json"
    output_path.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Hallazgos generados con IA Senior: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
