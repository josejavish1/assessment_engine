"""Constructs a synthetic and deterministic dataset for the `smoke_ivirma` smoke test."""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.client_intelligence import (
    coerce_client_dossier_v3,
)
from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)

DEFAULT_CLIENT = "smoke_ivirma"
DEFAULT_SEED = 42
DEFAULT_SCENARIO = "baseline"
DEFAULT_TOWERS = ["T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]
DEFAULT_TOWER_TARGETS: dict[str, tuple[float, float]] = {
    "T2": (2.0, 3.0),
    "T3": (1.5, 2.5),
    "T4": (2.5, 3.5),
    "T5": (1.0, 2.0),
    "T6": (1.5, 2.5),
    "T7": (2.0, 3.0),
    "T8": (3.0, 4.0),
    "T9": (2.5, 3.5),
}
DEFAULT_CONTEXT_TEXT = """
Technology Assessment Workshop Notes for IVIRMA (Smoke Test).

Business Context:
The enterprise is in an international inorganic expansion phase backed by KKR, targeting revenue expansion to €1,300M.
The CEO's priority is ensuring accelerated integration of newly acquired clinics while preserving clinical and operational excellence.

Technology:
Microsoft Azure is the designated strategic cloud hyperscaler. However, rapid acquisition has fragmented enterprise wide-area networking.
Medical imaging archives and electronic health records represent mission-critical business assets, yet lack an air-gapped immutable recovery vault.

Security and Governance:
The CISO highlights heightened ransomware risk within the healthcare sector. Furthermore, the mandatory EU NIS2 directive directly impacts the enterprise as an essential service entity, with current infrastructure failing audit gates.

Operations:
Clinical and medical staff IT support relies on manual procedures and rudimentary ITSM workflows. Standardized industrial automation and centralized CMDB asset visibility are absent, impeding scalable M&A integration.
"""

VODAFONE_PUBLIC_CONTEXT_TEXT = """
Synthetic technology assessment workshop for a pan-European telecommunications operator modeled on public disclosures.

Business Context:
The organization delivers enterprise, consumer, and public sector services across mobile, fixed broadband, cloud, IoT, and cybersecurity.
Executive strategy prioritizes operational simplification, B2B digital service monetization, cash-flow expansion, and high-margin connectivity platforms.

Technology:
Technology strategy mandates common core platforms, automated operations, access network modernization, end-to-end observability, and hybrid cloud consistency.
Architecture domains T2, T3, and T5 face acute reliability pressure as customer SLA depends on resilient platforms, deterministic throughput, and rapid disaster recovery.

Security and Governance:
Regulatory posture is governed by NIS2, operational resilience frameworks, consumer privacy regulations, service continuity mandates, and supply-chain governance.
The enterprise must prove rigorous technical governance, audit traceability, and sub-hour RTO/RPO metrics aligned with mission-critical infrastructure standards.

Operations:
Core engineering domains demonstrate high maturity, but regional fragmentation, legacy operational toil, redundant toolchains, and varied incident triage processes persist.
The assessment objective is establishing a pragmatic transformation roadmap to consolidate platforms, eliminate architectural complexity, and reinforce operational resilience.
"""

SCENARIOS: dict[str, dict[str, Any]] = {
    "baseline": {
        "context_text": DEFAULT_CONTEXT_TEXT,
        "tower_targets": DEFAULT_TOWER_TARGETS,
        "client_dossier": None,
    },
    "vodafone-public": {
        "context_text": VODAFONE_PUBLIC_CONTEXT_TEXT,
        "tower_targets": {
            **DEFAULT_TOWER_TARGETS,
            "T2": (3.1, 4.0),
            "T3": (3.0, 3.9),
            "T5": (2.8, 3.7),
        },
        "client_dossier": {
            "industry": "Telecommunications",
            "financial_tier": "Tier 1",
            "priority_markets": ["Germany", "United Kingdom", "Spain", "Italy"],
            "business_lines": [
                "Convergent B2C",
                "Digital B2B",
                "IoT",
                "Cloud & Cybersecurity",
            ],
            "active_transformations": [
                "Cross-country core platform consolidation",
                "Automated operations and end-to-end observability",
                "Mission-critical resilience program",
            ],
            "business_constraints": [
                "Margin pressure and cash-flow discipline",
                "Zero tolerance for service outages in 24x7 operations",
            ],
            "regulatory_pressures": [
                "Requirement to demonstrate critical infrastructure resilience and continuity",
                "Heightened scrutiny on operational traceability and supply chain governance",
            ],
            "regulatory_frameworks": [
                "NIS2",
                "GDPR",
                "Telecom Security Act / local sectoral directives",
                "ISO 22301",
            ],
            "ceo_agenda": (
                "Simplify operations, protect margins, accelerate B2B digital services, "
                "and ensure consistent customer experience in competitive markets."
            ),
            "technological_drivers": [
                "Network and platform operations automation",
                "Toolchain consolidation and end-to-end observability",
                "Operational resilience for mission-critical services",
                "Hybrid modernization of core business support platforms",
            ],
            "vendor_dependencies": [
                "Hyperscalers for hybrid workloads and analytics",
                "Multi-country network and security vendors",
            ],
            "operating_constraints": [
                "Duplicated toolchains and regional operational legacy",
                "Restricted change windows for mission-critical services",
            ],
            "recent_incident_signals": [
                "Major incident recovery and operational resilience are explicit executive focus areas",
                "High sensitivity to network and platform outages due to strict service continuity dependencies",
            ],
            "osint_footprint": (
                "Distributed footprint with strong platform dependencies, multinational operations, "
                "and high demand for cross-domain standardization."
            ),
            "transformation_horizon": (
                "Phased 24-36 month transformation program pairing operational quick wins "
                "with foundational platform consolidation."
            ),
            "target_maturity_matrix": {
                "T1": 3.4,
                "T2": 3.9,
                "T3": 3.8,
                "T4": 3.6,
                "T5": 3.7,
                "T6": 4.0,
                "T7": 3.6,
                "T8": 3.7,
                "T9": 3.5,
                "T10": 3.2,
            },
            "evidences": [
                "Synthetic scenario derived from public pan-European telco disclosures.",
                "Operating context focused on connectivity, common platforms, and resilience.",
            ],
        },
    },
}


def normalize_towers(towers: list[str] | None) -> list[str]:
    """Normalize and deduplicate a list of tower identifiers.

    Each identifier is converted to uppercase and stripped of leading/trailing
    whitespace. Duplicates and identifiers that become empty strings after
    normalization are discarded. The original relative order of the first
    occurrence of each identifier is preserved. If `towers` is `None`, a
    predefined default list of towers is used.

    Args:
        towers: A list of tower identifiers to process, or `None` to use a
            default list.

    Returns:
        A list containing the unique, normalized tower identifiers.
    """
    normalized: list[str] = []
    for tower in towers or DEFAULT_TOWERS:
        tower_id = tower.upper().strip()
        if tower_id and tower_id not in normalized:
            normalized.append(tower_id)
    return normalized


def resolve_scenario_config(name: str) -> dict[str, Any]:
    """Resolve and retrieve the configuration for a given scenario name.

    The name is stripped of leading and trailing whitespace. If the resulting
    string is empty, the default scenario name is used for the lookup.

    Args:
        name: The name of the scenario configuration to retrieve.

    Returns:
        A dictionary containing the configuration for the resolved scenario.

    Raises:
        ValueError: If the resolved scenario name does not correspond to a
            defined scenario.
    """
    scenario_name = name.strip() or DEFAULT_SCENARIO
    if scenario_name not in SCENARIOS:
        available = ", ".join(sorted(SCENARIOS))
        raise ValueError(
            f"Escenario desconocido: {scenario_name}. Disponibles: {available}"
        )
    return SCENARIOS[scenario_name]


def build_responses(
    root: Path,
    towers: list[str],
    seed: int,
    tower_targets: dict[str, tuple[float, float]] | None = None,
) -> list[str]:
    """Generates mock response lines from tower KPI definition files.

    This function iterates through a list of tower IDs, locating and parsing their
    corresponding JSON definition files to generate mock data. For each Key
    Performance Indicator (KPI) found within a tower's definition, a random score
    is generated and formatted into a response string.

    The function expects tower definitions to be located at:
    `{root}/engine_config/towers/{tower_id}/tower_definition_{tower_id}.json`.
    Tower IDs for which a definition file does not exist are silently skipped.

    The score for each KPI is a float, randomly generated within a specified
    range. This range is determined by the `tower_targets` dictionary. If a
    tower is not present in the dictionary, a default range of (2.0, 3.0) is used.

    Args:
        root: The root path of the configuration directory structure.
        towers: A list of tower string identifiers for which to generate responses.
        seed: An integer used to seed the random number generator, ensuring
            deterministic output.
        tower_targets: An optional dictionary mapping tower IDs to a `(min, max)`
            tuple, defining the score generation range for each tower.

    Returns:
        A list of strings, where each string represents a mock response in the
        format "kpi_id.PR1: score".

    Raises:
        json.JSONDecodeError: If a tower definition file contains malformed JSON.
        KeyError: If a KPI dictionary within a tower definition file is missing
            the required 'kpi_id' key.
    """
    rng = random.Random(seed)
    responses_lines: list[str] = []
    targets = tower_targets or DEFAULT_TOWER_TARGETS

    for tower_id in towers:
        def_file = (
            root
            / "engine_config"
            / "towers"
            / tower_id
            / f"tower_definition_{tower_id}.json"
        )
        if not def_file.exists():
            continue

        data = json.loads(def_file.read_text(encoding="utf-8"))
        min_score, max_score = targets.get(tower_id, (2.0, 3.0))
        for pillar in data.get("pillars", []):
            for kpi in pillar.get("kpis", []):
                score = round(rng.uniform(min_score, max_score), 1)
                responses_lines.append(f"{kpi['kpi_id']}.PR1: {score}")

    return responses_lines


def generate_smoke_inputs(
    client: str = DEFAULT_CLIENT,
    towers: list[str] | None = None,
    seed: int = DEFAULT_SEED,
    scenario: str = DEFAULT_SCENARIO,
    root: Path = ROOT,
    write_files: bool = True,
) -> tuple[Path, Path]:
    """Generates smoke test input files for a specified client and scenario.

    This function orchestrates the generation of test data, creating a dedicated
    working directory for the client. This directory is populated with `responses.txt`,
    `context.txt`, and optionally `client_intelligence.json` based on the selected
    scenario configuration. If a scenario does not define a client dossier, any
    pre-existing dossier file in the client's directory is removed. The
    `write_files` parameter allows for a dry-run mode where file paths are
    determined without performing I/O operations.

    Args:
        client: The identifier for the client, which determines the name of the
            client-specific working directory. Defaults to `DEFAULT_CLIENT`.
        towers: An optional list of tower names for response generation. If `None`,
            a default set of towers is used.
        seed: The seed for the random number generator to ensure reproducible data
            generation. Defaults to `DEFAULT_SEED`.
        scenario: The name of the scenario configuration. This determines the
            context content, tower targets, and client dossier template.
            Defaults to `DEFAULT_SCENARIO`.
        root: The root directory containing input data and the target 'working'
            output directory. Defaults to the project's `ROOT` constant.
        write_files: If `True`, all filesystem I/O (directory creation, file
            writing/deletion) is performed. If `False`, the function operates in a
            dry-run mode, returning the calculated paths without modifying the
            filesystem.

    Returns:
        A tuple containing the `pathlib.Path` objects for the context file and
        the responses file, respectively.

    Raises:
        FileNotFoundError: If the configuration file for the specified `scenario`
            cannot be found.
        OSError: If a filesystem error occurs, such as insufficient permissions to
            create the client directory or write files.
    """
    client_id = client.strip() or DEFAULT_CLIENT
    client_dir = root / "working" / client_id
    scenario_config = resolve_scenario_config(scenario)
    if write_files:
        client_dir.mkdir(parents=True, exist_ok=True)

    normalized_towers = normalize_towers(towers)
    responses_lines = build_responses(
        root,
        normalized_towers,
        seed,
        tower_targets=scenario_config["tower_targets"],
    )

    responses_path = client_dir / "responses.txt"
    context_path = client_dir / "context.txt"
    dossier_path = client_dir / "client_intelligence.json"
    if write_files:
        responses_path.write_text("\n".join(responses_lines) + "\n", encoding="utf-8")
        context_path.write_text(
            str(scenario_config["context_text"]).strip() + "\n",
            encoding="utf-8",
        )
        dossier_template = scenario_config.get("client_dossier")
        if dossier_template:
            dossier = coerce_client_dossier_v3(
                client_name=client_id,
                data=dossier_template,
            )
            dossier_path.write_text(
                json.dumps(dossier, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        elif dossier_path.exists():
            dossier_path.unlink()

    return context_path, responses_path


def main(argv: list[str] | None = None) -> None:
    """Parses command-line arguments and executes smoke test data generation.

    This function serves as the main entry point for the script. It configures
    the data generation process by parsing command-line flags for the client,
    random seed, target towers, and generation scenario. Upon completion, it
    logs the file paths of the generated context and response data.

    Args:
        argv: A list of command-line arguments. If None, arguments are taken
            from `sys.argv`.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default=DEFAULT_CLIENT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--towers", nargs="*", default=DEFAULT_TOWERS)
    parser.add_argument(
        "--scenario", choices=sorted(SCENARIOS), default=DEFAULT_SCENARIO
    )
    args = parser.parse_args(argv)

    context_path, responses_path = generate_smoke_inputs(
        client=args.client,
        towers=args.towers,
        seed=args.seed,
        scenario=args.scenario,
    )

    responses_count = len(responses_path.read_text(encoding="utf-8").splitlines())
    logger.info(
        f"✅ Inputs smoke generados en {context_path.parent} "
        f"(contexto + {responses_count} respuestas)."
    )
    logger.info(f"   - {context_path}")
    logger.info(f"   - {responses_path}")


if __name__ == "__main__":
    main()
