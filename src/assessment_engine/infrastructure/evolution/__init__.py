"""
Provide modular evolution services composed under the Strangler Fig pattern:
- daemon_supervisor.py: Manage daemon lifecycle, pre-flight checks, and mission execution.
- roadmap_synthesizer.py: Synthesize relational schemas, typed SDKs, and backlogs.
- eval_runner.py: Run closed-loop Playwright evaluations, F5 persistence, and self-healing.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from google import genai

from assessment_engine.infrastructure.evolution.ast_signature_guard import (
    AstSignatureGuard,
    CognitiveArbiterReport,
    FunctionSignature,
    ModuleSignatureSnapshot,
    SignatureViolation,
    VerdictStatus,
    ast_signature_guard,
    diff_ast_signatures,
    diff_directory_snapshots,
    diff_module_signatures,
    extract_module_signatures,
    extract_signatures_from_code,
    snapshot_directory,
    snapshot_file,
)
from assessment_engine.infrastructure.evolution.closure_tribunal import (
    ClosureTribunal,
    ClosureTribunalReport,
    ForensicASTSecurityVisitor,
    SurgicalCorrectionTicket,
    audit_cubo_1_parity,
    audit_cubo_3_anti_features,
    audit_forensic_security,
    closure_tribunal,
)
from assessment_engine.infrastructure.evolution.cognitive_arbiter import (
    MAX_CYCLOMATIC_COMPLEXITY_THRESHOLD,
    MAX_DIALECTIC_ROUNDS,
    MIN_MUTATION_SCORE_THRESHOLD,
    CognitiveArbiter,
    DeterministicHarnessEvaluator,
    SkepticRole,
    SynthesizerRole,
    cognitive_arbiter,
)
from assessment_engine.infrastructure.evolution.complexity_guard import (
    ComplexityGuard,
    ComplexityReport,
    ComplexityViolation,
    audit_code_complexity,
    audit_file_complexity,
    complexity_guard,
    compute_mccabe_complexity,
)
from assessment_engine.infrastructure.evolution.darwinian_distiller import (
    CausalAttribution,
    DarwinianDistiller,
    DarwinianPostMortemReport,
    darwinian_distiller,
)
from assessment_engine.infrastructure.evolution.daemon_supervisor import DaemonSupervisor
from assessment_engine.infrastructure.evolution.epistemic_distiller import (
    EpistemicDistiller,
    ProductStrategyDossier,
    epistemic_distiller,
)
from assessment_engine.infrastructure.evolution.eval_runner import EvolutionEvalRunner
from assessment_engine.infrastructure.evolution.fault_localizer import (
    FaultLocalizationReport,
    FaultLocalizer,
    SuspiciousLine,
    compute_ochiai_ranking,
    compute_ochiai_score,
    fault_localizer,
)
from assessment_engine.infrastructure.evolution.mutation_ctf_probe import (
    MutationCtfProbe,
    MutationProbeResult,
    mutation_ctf_probe,
    run_mutation_ctf,
)
from assessment_engine.infrastructure.evolution.roadmap_synthesizer import RoadmapSynthesizer
from assessment_engine.infrastructure.evolution.worktree_runner import (
    EphemeralWorktree,
    GitWorktreeRunner,
    worktree_runner,
)
from assessment_engine.infrastructure.genai_client import create_genai_client

logger = logging.getLogger("autonomous_evolution_engine")


class AutonomousEvolutionEngine:
    """
    Tier-1 Long-Horizon Autonomous SWE Engine.
    Fachada modular que delega en los submódulos especializados de core/evolution/.
    """

    def __init__(self) -> None:
        try:
            self.client: genai.Client | None = create_genai_client()
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.debug(f"GenAI client init note: {e}")
            self.client = None

    async def ensure_daemon_running(self, slug: str) -> bool:
        """Ensure the daemon process for the specified application slug is running."""
        return await DaemonSupervisor.ensure_daemon_running(slug)

    async def synthesize_relational_schema(self, slug: str, goal: str, ui_paradigm: str) -> dict[str, Any]:
        """Synthesize a relational database schema based on the specified goal and UI paradigm."""
        return await RoadmapSynthesizer.synthesize_relational_schema(self.client, slug, goal, ui_paradigm)

    async def synthesize_domain_api(self, slug: str, goal: str, schema_info: dict[str, Any]) -> bool:
        """Synthesize the domain API using the provided goal and relational schema information."""
        return await RoadmapSynthesizer.synthesize_domain_api(slug, goal, schema_info)

    def generate_typed_sdk_js(self, slug: str, schema_info: dict[str, Any]) -> str:
        """Generate a typed JavaScript SDK based on the provided schema definitions."""
        return RoadmapSynthesizer.generate_typed_sdk_js(slug, schema_info)

    async def search_market_leaders(self, goal: str, sector: str) -> list[str]:
        """Search for market-leading applications within the specified sector and goal."""
        return await RoadmapSynthesizer.search_market_leaders(self.client, goal, sector)

    async def synthesize_dynamic_backlog(
        self, goal: str, leaders: list[str], ui_paradigm: str, contract_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Synthesize a dynamic product backlog for the specified project requirements."""
        return await RoadmapSynthesizer.synthesize_dynamic_backlog(self.client, goal, leaders, ui_paradigm, contract_data)

    async def synthesize_roadmap(self, slug: str) -> dict[str, Any]:
        """Synthesize a structured development roadmap for the specified application slug."""
        return await RoadmapSynthesizer.synthesize_roadmap(self.client, slug)

    async def audit_with_playwright(
        self, slug: str, schema_info: dict[str, Any] | None = None, contract_data: dict[str, Any] | None = None
    ) -> tuple[bool, str, dict[str, Any]]:
        """Audit the web application interface and behavior using Playwright."""
        return await EvolutionEvalRunner.audit_with_playwright(
            slug, daemon_ensure_fn=self.ensure_daemon_running, schema_info=schema_info, contract_data=contract_data
        )

    def _count_sqlite_domain_rows(self, db_file: Path) -> int:
        return EvolutionEvalRunner.count_sqlite_domain_rows(db_file)

    async def execute_milestone_code(
        self,
        slug: str,
        milestone: dict[str, Any],
        roadmap: dict[str, Any],
        contract_data: dict[str, Any],
        schema_info: dict[str, Any] | None = None
    ) -> bool:
        """Execute the code implementation tasks for a specified development milestone."""
        return await EvolutionEvalRunner.execute_milestone_code(
            self.client, slug, milestone, roadmap, contract_data, schema_info
        )

    async def heal_code_with_playwright_error(
        self, slug: str, error_msg: str, telemetry: dict[str, Any] | None = None
    ) -> None:
        """Repair failing application code using Playwright error diagnostics."""
        await EvolutionEvalRunner.heal_code_with_playwright_error(
            self.client, slug, error_msg, telemetry
        )

    async def run_evolution_mission(
        self,
        slug: str,
        goal: str,
        contract_data: dict[str, Any],
        broadcaster: Any = None
    ) -> dict[str, Any]:
        """Run an automated evolution mission to iteratively improve the application."""
        return await DaemonSupervisor.run_evolution_mission(
            self.client, slug, goal, contract_data, broadcaster
        )


evolution_engine = AutonomousEvolutionEngine()

__all__ = [
    "MAX_CYCLOMATIC_COMPLEXITY_THRESHOLD",
    "MAX_DIALECTIC_ROUNDS",
    "MIN_MUTATION_SCORE_THRESHOLD",
    "AstSignatureGuard",
    "AutonomousEvolutionEngine",
    "ClosureTribunal",
    "ClosureTribunalReport",
    "CognitiveArbiter",
    "CognitiveArbiterReport",
    "ComplexityGuard",
    "ComplexityReport",
    "ComplexityViolation",
    "DaemonSupervisor",
    "DeterministicHarnessEvaluator",
    "EphemeralWorktree",
    "EpistemicDistiller",
    "EvolutionEvalRunner",
    "FaultLocalizationReport",
    "FaultLocalizer",
    "ForensicASTSecurityVisitor",
    "FunctionSignature",
    "GitWorktreeRunner",
    "ModuleSignatureSnapshot",
    "MutationCtfProbe",
    "MutationProbeResult",
    "ProductStrategyDossier",
    "RoadmapSynthesizer",
    "SignatureViolation",
    "SkepticRole",
    "SurgicalCorrectionTicket",
    "SuspiciousLine",
    "SynthesizerRole",
    "VerdictStatus",
    "ast_signature_guard",
    "audit_code_complexity",
    "audit_cubo_1_parity",
    "audit_cubo_3_anti_features",
    "audit_file_complexity",
    "audit_forensic_security",
    "closure_tribunal",
    "cognitive_arbiter",
    "complexity_guard",
    "compute_mccabe_complexity",
    "compute_ochiai_ranking",
    "compute_ochiai_score",
    "diff_ast_signatures",
    "diff_directory_snapshots",
    "diff_module_signatures",
    "epistemic_distiller",
    "evolution_engine",
    "extract_module_signatures",
    "extract_signatures_from_code",
    "fault_localizer",
    "mutation_ctf_probe",
    "run_mutation_ctf",
    "snapshot_directory",
    "snapshot_file",
    "worktree_runner",
]
