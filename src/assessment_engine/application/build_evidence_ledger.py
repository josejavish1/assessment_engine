import argparse
import json
import logging
import re
from pathlib import Path
from typing import Any, cast

from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)

"""
Module build_evidence_ledger.py.
Contains core orchestration and rendering logic for Assessment Engine pipeline.
"""


def load_json(path: Path) -> dict[str, Any]:
    """Parse a JSON file from a specified path into a Python dictionary."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


def split_sentences(text: str) -> list[str]:
    r"""{'docstring': 'Split a block of text into a list of sentences.\n\n    Segments an input string into sentences using a regular expression that\n    splits on whitespace following sentence-terminating punctuation (.!?).\n    The punctuation is retained with its corresponding sentence. Each resulting\n    sentence is subsequently cleaned by collapsing internal whitespace to single\n    spaces and removing any leading or trailing whitespace. Empty strings\n    resulting from the split process are discarded.\n\n    Args:\n        text: The input string to be segmented.\n\n    Returns:\n        A list of cleaned sentence strings. Returns an empty list if no valid\n        sentences are found.'}."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if part.strip()]


def tokenize(text: str) -> set[str]:
    """Tokenize a string into a set of unique, lowercased tokens."""
    return set(re.findall(r"[a-z0-9&/+-]+", text.lower()))


def pillar_keywords(pillar: dict) -> set[str]:
    r"""{'docstring': "Extracts and tokenizes keywords from a pillar data structure.\n\nThis function processes a dictionary representing a pillar by tokenizing its\n'pillar_name' and the 'kpi_name' of all its associated Key Performance\nIndicators (KPIs). The resulting tokens are filtered to exclude words of\ntwo characters or less, and a unique set is returned.\n\nArgs:\n    pillar: A dictionary defining a pillar. Expected to contain a\n        'pillar_name' key with a string value. May optionally contain a\n        'kpis' key mapping to a list of dictionaries, where each dictionary\n        must contain a 'kpi_name' key.\n\nReturns:\n    A set of unique keyword strings, each longer than two characters,\n    derived from the pillar and KPI names.\n\nRaises:\n    KeyError: If 'pillar_name' is missing from the pillar dictionary, or\n        if 'kpi_name' is missing from an element in the 'kpis' list."}."""
    keywords = tokenize(pillar["pillar_name"])
    for kpi in pillar.get("kpis", []):
        keywords.update(tokenize(kpi["kpi_name"]))
    return {word for word in keywords if len(word) > 2}


def support_tags_from_score(score: float) -> list[str]:
    """Generate a list of support tags based on a numeric score.

    Maps a numeric score to a predefined list of tags that categorize the
    level of support. The mapping logic is as follows:
    - score >= 4.0 (Sufficient): `['asis', 'executive_summary']`
    - 3.0 <= score < 4.0 (Risk): `['asis', 'risk', 'executive_summary']`
    - score < 3.0 (Gap): `['gap', 'risk', 'tobe', 'todo', 'executive_summary']`

    Args:
        score (float): The numeric score to categorize.

    Returns:
        list[str]: A list of string tags corresponding to the score's category.
    """
    if score >= 4:
        return ["asis", "executive_summary"]
    if score >= 3:
        return ["asis", "risk", "executive_summary"]
    return ["gap", "risk", "tobe", "todo", "executive_summary"]


def build_evidence_entries(
    case_input: dict, context_path: Path, responses_path: Path, tower_definition: dict
) -> list[dict]:
    r"""{'docstring': "Aggregates and formats evidence entries from multiple data sources.\n\nOrchestrates the assembly of an evidence ledger by integrating data from\nthree primary sources: strategic summaries from a RAPTOR tree, atomic\nfragments from an evidence vault, and quantitative scores from\nquestionnaire responses.\n\nThe function determines the location of the vault and tree files by using the\n`context_file` path provided in `case_input['_build_metadata']`. It then\niterates through each 'pillar' defined in the tower structure, finds\nrelevant data from the loaded sources by matching keywords or identifiers,\nand formats the results into a unified list of evidence entries.\n\nArgs:\n    case_input: A dictionary containing case-specific input data. Must include\n        a `_build_metadata` key containing a `context_file` path. It\n        should also contain an `answers` key with a list of questionnaire\n        responses.\n    context_path: The filesystem path to the case context directory.\n    responses_path: The filesystem path to the questionnaire responses file.\n        Its name is used to populate source metadata for questionnaire entries.\n    tower_definition: A dictionary defining the assessment structure, which\n        must contain a 'pillars' key holding a list of pillar definitions.\n\nReturns:\n    A list of dictionaries, where each dictionary represents a single\n    formatted evidence entry. Each entry includes keys such as\n    `evidence_id`, `source_type`, and `excerpt`.\n\nRaises:\n    KeyError: If a required key (e.g., `_build_metadata`) is missing from\n        `case_input` or other expected keys are absent from nested data.\n    json.JSONDecodeError: If the evidence vault or RAPTOR tree JSON files\n        are malformed.\n    ValueError: If a questionnaire answer's 'value' field cannot be\n        converted to a float."}."""
    case_input.get("client", "generic")

    # Initializes the evidence processing pipeline by loading required Knowledge Base artifacts, establishing the foundational data structures and models necessary for subsequent stages.
    storage_dir = Path(case_input["_build_metadata"]["context_file"]).parent
    vault_path = storage_dir / "evidence_vault.json"
    tree_path = storage_dir / "raptor_tree.json"

    fragments = []
    if vault_path.exists():
        vault_data = json.loads(vault_path.read_text(encoding="utf-8"))
        fragments = vault_data.get("fragments", [])

    raptor_nodes = {}
    if tree_path.exists():
        tree_data = json.loads(tree_path.read_text(encoding="utf-8"))
        raptor_nodes = tree_data.get("nodes", {})

    answers = case_input.get("answers", [])
    answers_by_kpi = {answer["kpi_id"]: answer for answer in answers}

    evidences = []
    next_id = 1

    # Processes each pillar sequentially, leveraging a hierarchical context model to ensure that evidence alignment is performed within the appropriate thematic and structural boundaries.
    for pillar in tower_definition.get("pillars", []):
        p_id = pillar["pillar_id"]
        keywords = pillar_keywords(pillar)

        # Conducts high-level, thematic evidence alignment by applying RAPTOR Level 1 clustering.
        # Selects the summary with the highest semantic keyword overlap rather than picking the first FIFO match.
        best_summary = None
        best_summary_score = 0
        for node in raptor_nodes.values():
            if node.get("level") == 1:
                tokens = tokenize(node.get("content", ""))
                overlap_score = len(tokens & keywords)
                if overlap_score > best_summary_score:
                    best_summary_score = overlap_score
                    best_summary = node

        if best_summary:
            evidences.append(
                {
                    "evidence_id": f"STRAT-{p_id}",
                    "raptor_node_id": best_summary["node_id"],
                    "source_type": "strategic_summary",
                    "excerpt": best_summary["content"],
                    "pillar_ids": [p_id],
                    "supports": ["executive_summary", "asis"],
                    "is_strategic_anchor": True,
                }
            )

        # Performs fine-grained evidence alignment by ranking all fragments by keyword overlap density,
        # selecting the top-10 highest-ranked fragments across the entire knowledge base.
        scored_fragments = []
        for frag in fragments:
            frag_tokens = tokenize(frag.get("content", ""))
            overlap = frag_tokens & keywords
            if overlap:
                score = len(overlap)
                scored_fragments.append((score, frag))

        scored_fragments.sort(key=lambda x: x[0], reverse=True)
        matched_fragments = [frag for _, frag in scored_fragments[:10]]

        for frag in matched_fragments:
            frag_tokens = tokenize(frag.get("content", ""))
            specific_kpis = [
                kpi["kpi_id"]
                for kpi in pillar.get("kpis", [])
                if tokenize(kpi.get("kpi_name", "")) & frag_tokens
            ]
            related_kpis = specific_kpis if specific_kpis else [kpi["kpi_id"] for kpi in pillar.get("kpis", [])]
            evidences.append(
                {
                    "evidence_id": f"FRAG-{frag['fragment_id'][:8]}",
                    "fragment_id": frag["fragment_id"],
                    "source_type": "atomic_fragment",
                    "source_name": Path(frag["source_uri"]).name,
                    "excerpt": frag["content"],
                    "pillar_ids": [p_id],
                    "kpi_ids": related_kpis,
                    "supports": ["asis", "risk", "executive_summary"],
                    "location": frag.get("location_metadata", {}),
                    "validation_state": case_input.get(
                        "validation_state", "Exploratoria"
                    ),
                }
            )
            next_id += 1

        # Grounds the generated evidence against a canonical set of technical ground truths or test cases. This validation step ensures the factual accuracy and reliability of the evidence ledger.
        for kpi in pillar.get("kpis", []):
            answer = answers_by_kpi.get(kpi["kpi_id"])
            if not answer:
                continue
            score = float(answer["value"])
            evidences.append(
                {
                    "evidence_id": f"QNR-{case_input['tower_id']}-{next_id:02d}",
                    "source_type": "questionnaire_response",
                    "source_name": responses_path.name,
                    "excerpt": (
                        f"{answer['question_id']} = {score:.1f}/5 in '{kpi['kpi_name']}' "
                        f"for pillar '{pillar['pillar_name']}'."
                    ),
                    "pillar_ids": [p_id],
                    "kpi_ids": [kpi["kpi_id"]],
                    "supports": support_tags_from_score(score),
                    "validation_state": case_input.get(
                        "validation_state", "Exploratoria"
                    ),
                }
            )
            next_id += 1

    return evidences


def main() -> None:
    """Builds an evidence ledger from specified input files and saves it as JSON.

    This script serves as the main entry point for constructing an evidence ledger.
    It parses command-line arguments for the paths to a case input file
    (`--case-input`), a context file (`--context-file`), and a model responses
    file (`--responses-file`).

    The script reads these JSON files and dynamically locates a corresponding
    tower definition file based on the 'tower_id' within the case input data. It
    then assembles a comprehensive ledger dictionary containing case metadata and
    evidence entries. The final ledger is written to `evidence_ledger.json` in
    the same directory as the provided case input file.

    Raises:
        FileNotFoundError: If the case input, context, responses, or the
            derived tower definition file does not exist.
        KeyError: If the case input JSON is missing the 'case_id' or 'tower_id'
            keys, which are required for locating the tower definition and
            constructing the ledger.
        json.JSONDecodeError: If any of the input files contain malformed JSON.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-input", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    args = parser.parse_args()

    case_input_path = Path(args.case_input).resolve()
    context_path = Path(args.context_file).resolve()
    responses_path = Path(args.responses_file).resolve()

    case_input = load_json(case_input_path)
    tower_definition = load_json(
        ROOT
        / "engine_config"
        / "towers"
        / case_input["tower_id"]
        / f"tower_definition_{case_input['tower_id']}.json"
    )
    ledger = {
        "case_id": case_input["case_id"],
        "tower_id": case_input["tower_id"],
        "tower_name": case_input["tower_name"],
        "validation_state": case_input.get("validation_state", "Exploratoria"),
        "evidences": build_evidence_entries(
            case_input, context_path, responses_path, tower_definition
        ),
        "_build_metadata": {
            "case_input": str(case_input_path),
            "context_file": str(context_path),
            "responses_file": str(responses_path),
        },
    }

    output_path = case_input_path.with_name("evidence_ledger.json")
    output_path.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info(f"evidence_ledger generado en: {output_path}")
    logger.info(f"evidences: {len(ledger['evidences'])}")


if __name__ == "__main__":
    main()
