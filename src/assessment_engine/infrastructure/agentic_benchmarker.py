import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional

from google.adk.agents import Agent
from pydantic import BaseModel, Field
from vertexai.agent_engines import AdkApp

from assessment_engine.domain.schemas.rubric import FrameworkRubric
from assessment_engine.infrastructure.ai_client import run_agent
from assessment_engine.infrastructure.config_loader import (
    load_framework_rubric,
    load_industry_profile,
)
from assessment_engine.infrastructure.evidence_governance import (
    EvidenceSnapshotter,
)

logger = logging.getLogger(__name__)


class TowerBenchmarkSnapshot(BaseModel):
    """Represents the dynamic grounding and evaluation state of a single tower's benchmark."""

    tower_id: str = Field(description="The tower code, e.g., 'T6'")
    framework_id: str = Field(description="The active framework ID, e.g., 'ens_alta'")
    framework_name: str = Field(description="Official name of the standard or regulation.")
    dynamic_score: float = Field(
        description="The final computed maturity score from Python evaluation."
    )
    extracted_metric_value: float = Field(
        description="The raw numeric percentage/metric extracted from live evidence."
    )
    evidence_quote: str = Field(
        description="The exact verbatim quote/claim extracted from the source document."
    )
    evidence_source_url: str = Field(
        description="The official online URL where the evidence was located."
    )
    local_snapshot_path: Optional[str] = Field(
        None,
        description="The relative path to the local PDF/HTML backup in the vault.",
    )
    verification_status: str = Field(
        description="The status of adversarial cross-examination ('verified', 'failed')."
    )
    justification_text: str = Field(
        description="The detailed narrative justification for the score, citing the law and evidence."
    )


class IndustryBenchmarksSnapshot(BaseModel):
    """The master collection of dynamic RAGE benchmarks for a specific client session."""

    client_id: str = Field(description="The unique identifier of the client.")
    industry: str = Field(description="The industrial sector.")
    snapshots: Dict[str, TowerBenchmarkSnapshot] = Field(default_factory=dict)


class FactExtractionOutput(BaseModel):
    """Output schema for the Grounding Agent's raw extraction."""

    extracted_value: float = Field(
        description="The exact numeric percentage (0-100) extracted from the evidence, e.g., 65.0"
    )
    verbatim_quote: str = Field(
        description="The exact verbatim quote containing the extracted value."
    )
    source_url: str = Field(
        description="The authoritative URL of the official document or news page."
    )
    justification: str = Field(
        description="A concise summary of the finding citing the source."
    )


class VerificationOutput(BaseModel):
    """Output schema for the Adversarial Verifier Agent."""

    is_verified: bool = Field(
        description="True if the verbatim quote and value are 100% verified against the source text."
    )
    critique: str = Field(
        description="Explanation of any discrepancy, or validation confirmation."
    )


class AgenticRageBenchmarker:
    """The core engine orchestrating Runtime Agentic Grounding & Evaluation (RAGE)."""

    def __init__(self, client_id: str, working_dir: Path, model_name: str = "gemini-2.5-pro"):
        self.client_id = client_id
        self.working_dir = working_dir
        self.model_name = model_name

        # Create localized evidence cache directory (the Vault)
        self.evidence_dir = self.working_dir / "evidence_cache"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.snapshotter = EvidenceSnapshotter(self.working_dir)

    async def run_rage_evaluation(self, industry_key: str) -> IndustryBenchmarksSnapshot:
        """Orchestrates the entire 5-step RAGE pipeline for all active towers under the industry.

        1. Read the active frameworks from the industry profile.
        2. Formulate search queries and extract facts using a Grounding Agent (with Google search).
        3. Securely download the evidence files locally to prevent link rot.
        4. Cross-examine the evidence via an adversarial verification agent.
        5. Evaluate the thresholds mathematically in Python and generate the master snapshot.
        """
        logger.info(f"🚀 [RAGE] Starting Runtime Grounding & Evaluation for client: {self.client_id}")

        # Step 1: Load industry profile and its active frameworks mapping
        profile_data = load_industry_profile(industry_key)
        active_frameworks = profile_data.get("active_frameworks_by_tower", {})
        if not active_frameworks:
            logger.warning(
                f"[RAGE] No active frameworks defined for industry '{industry_key}'. "
                "Utilizing standard baseline default fallbacks."
            )
            return IndustryBenchmarksSnapshot(client_id=self.client_id, industry=industry_key)

        master_snapshot = IndustryBenchmarksSnapshot(
            client_id=self.client_id, industry=industry_key
        )

        for tower_id, frameworks in active_frameworks.items():
            if not frameworks:
                continue

            # For simplicity, we evaluate the primary active framework listed for the tower
            framework_id = frameworks[0]
            try:
                # Step 2: Load framework rubric
                rubric_data = load_framework_rubric(framework_id)
                rubric = FrameworkRubric.model_validate(rubric_data)

                # Find the rule matching the current tower
                rule = next((r for r in rubric.rules if r.tower_id == tower_id), None)
                if not rule:
                    logger.warning(
                        f"[RAGE] No rubric rule found for tower {tower_id} in framework {framework_id}."
                    )
                    continue

                logger.info(f"[RAGE] Evaluating {tower_id} against {framework_id}...")

                # Step 3: Run Grounding Agent with Google Search
                extraction = await self._run_grounding_search(rule, rubric.framework_name)
                if not extraction:
                    logger.warning(f"❌ [RAGE] Grounding search failed for tower {tower_id}.")
                    continue

                # Step 4: Download the evidence locally (The Vault)
                local_snapshot_path = None
                if extraction.source_url:
                    logger.info(f"[RAGE] Downloading evidence locally from: {extraction.source_url}")
                    snapshot_meta = await self.snapshotter.capture_snapshot(extraction.source_url)
                    if snapshot_meta and snapshot_meta.get("status") == "verified":
                        # Convert to relative path from workspace root for portability
                        abs_path = Path(snapshot_meta["local_snapshot"])
                        try:
                            local_snapshot_path = str(abs_path.relative_to(Path.cwd()))
                        except ValueError:
                            local_snapshot_path = str(abs_path)
                        logger.info(f"✓ [RAGE] Evidence saved in vault: {local_snapshot_path}")
                    else:
                        logger.warning(f"⚠️ [RAGE] Could not capture secure snapshot for: {extraction.source_url}")

                # Step 5: Adversarial Cross-Examination (Verification)
                is_verified = await self._cross_examine_evidence(extraction, local_snapshot_path)
                verif_status = "verified" if is_verified else "failed"

                # Step 6: Mathematical Threshold Evaluation (Python Pure Engine)
                score = self._evaluate_mathematical_rubric(rule, extraction.extracted_value)
                logger.info(f"✓ [RAGE] Computed mathematical score for {tower_id}: {score}")

                # Step 7: Build justification text
                justification = (
                    f"El estándar de mercado está fijado dinámicamente en {score:,.1f}. "
                    f"Esta capacidad crítica se evalúa bajo las exigencias de {rubric.framework_name}. "
                    f"La investigación de cumplimiento sectorial en tiempo de ejecución confirma que: "
                    f"\"{extraction.verbatim_quote}\" "
                    f"Cita Oficial Online: {extraction.source_url}. "
                )
                if local_snapshot_path:
                    justification += f"Archivo de Respaldo Local: {local_snapshot_path} (Disponible para auditoría forense)."

                # Add to master snapshot
                master_snapshot.snapshots[tower_id] = TowerBenchmarkSnapshot(
                    tower_id=tower_id,
                    framework_id=framework_id,
                    framework_name=rubric.framework_name,
                    dynamic_score=score,
                    extracted_metric_value=extraction.extracted_value,
                    evidence_quote=extraction.verbatim_quote,
                    evidence_source_url=extraction.source_url,
                    local_snapshot_path=local_snapshot_path,
                    verification_status=verif_status,
                    justification_text=justification,
                )

            except Exception as e:
                logger.error(f"❌ [RAGE] Unexpected error evaluating tower {tower_id}: {e}")

        # Save the master benchmarks snapshot to disk
        snapshot_file = self.working_dir / "benchmarks_snapshot.json"
        try:
            snapshot_file.write_text(
                master_snapshot.model_dump_json(indent=2, by_alias=True), encoding="utf-8"
            )
            logger.info(f"✓ [RAGE] Completed and froze master snapshot at: {snapshot_file}")
        except Exception as e:
            logger.error(f"❌ [RAGE] Failed to write benchmarks snapshot file: {e}")

        return master_snapshot

    async def _run_grounding_search(self, rule: Any, framework_name: str) -> Optional[FactExtractionOutput]:
        """Queries Google search via Gemini grounding and extracts factual metrics matching the query template."""
        research_agent = Agent(
            name="rage_research_agent",
            model=self.model_name,
            instruction=(
                "Eres un analista de ciberseguridad y auditor de élite. Tu misión es buscar "
                "en internet utilizando Google Search para resolver de manera 100% real y objetiva "
                "la pregunta planteada. Extrae estrictamente un valor numérico porcentaje (0 a 100), "
                "la cita textual de donde lo leíste, y el link oficial."
            ),
            output_schema=FactExtractionOutput,
        )
        app = AdkApp(agent=research_agent)

        # Enable Google Search Grounding dynamically
        app.tools = [{"google_search": {}}]

        prompt = (
            f"Por favor realiza una investigación en internet sobre el estándar {framework_name}. "
            f"Resuelve la siguiente query de investigación técnica:\n"
            f"\"{rule.query_template}\"\n\n"
            f"Devuelve la respuesta estrictamente estructurada según el esquema JSON FactExtractionOutput."
        )

        try:
            result = await run_agent(
                app,
                user_id=f"rage_research_{rule.tower_id}",
                message=prompt,
                schema=FactExtractionOutput,
            )
            if isinstance(result, dict):
                return FactExtractionOutput.model_validate(result)
            elif isinstance(result, FactExtractionOutput):
                return result
        except Exception as e:
            logger.error(f"[RAGE] Error in grounding search agent: {e}")
        return None

    async def _cross_examine_evidence(
        self, extraction: FactExtractionOutput, local_snapshot_path: Optional[str]
    ) -> bool:
        """Runs an adversarial cross-examination agent to verify the facts against local snapshot source text."""
        if not local_snapshot_path:
            return False

        snapshot_file = Path(local_snapshot_path)
        if not snapshot_file.exists():
            return False

        # Read first 5000 characters of local snapshot as safe text context
        try:
            source_text = snapshot_file.read_text(encoding="utf-8", errors="ignore")[:5000]
        except Exception:
            return False

        verifier_agent = Agent(
            name="rage_verifier_agent",
            model=self.model_name,
            instruction=(
                "Eres un auditor forense de ciberseguridad escéptico. Tu único trabajo es verificar si "
                "la afirmación y valor extraídos por el investigador se corresponden al 100% de manera real "
                "con el texto fuente del documento descargado. Si hay discrepancias o mentiras, márcalo como no verificado."
            ),
            output_schema=VerificationOutput,
        )
        app = AdkApp(agent=verifier_agent)

        prompt = (
            f"DOCUMENTO FUENTE DESCARGADO (Primeros 5000 caracteres):\n"
            f"-------------------\n{source_text}\n-------------------\n\n"
            f"AFIRMACIÓN A VERIFICAR:\n"
            f"- Cita literal: \"{extraction.verbatim_quote}\"\n"
            f"- Valor numérico: {extraction.extracted_value}%\n"
            f"- URL de origen: {extraction.source_url}\n\n"
            f"Evalúa críticamente si el documento fuente confirma esta afirmación y responde según el esquema VerificationOutput."
        )

        try:
            result = await run_agent(
                app,
                user_id="rage_verifier",
                message=prompt,
                schema=VerificationOutput,
            )
            is_verif = False
            if isinstance(result, dict):
                is_verif = bool(result.get("is_verified", False))
            elif isinstance(result, VerificationOutput):
                is_verif = result.is_verified
            
            if is_verif:
                logger.info("✓ [RAGE] Evidencia verificada con éxito por el auditor adversario.")
                return True
            else:
                logger.warning("⚠️ [RAGE] El auditor adversario rechazó la veracidad de la evidencia.")
                return False
        except Exception as e:
            logger.error(f"[RAGE] Error in cross-examination verifier: {e}")
        return False

    def _evaluate_mathematical_rubric(self, rule: Any, fact_value: float) -> float:
        """The pure Python mathematical evaluation engine.

        Guarantees that no LLM subjectivity influences the score.
        Compares the fact_value (e.g. 65.0) against the rubric thresholds.
        """
        # Evaluates thresholds dynamically
        # Sorted from highest score/conditions to lowest for correct range resolution
        for thresh in rule.thresholds:
            cond = thresh.condition
            # Replace 'adoption' with the actual variable name and evaluate safely
            clean_cond = cond.replace(rule.evaluation_variable, str(fact_value))
            try:
                # Sanitize condition string for safety (only allow comparisons and numbers)
                if re.match(r"^[0-9\.\s><=\!]+$", clean_cond):
                    if eval(clean_cond):
                        return thresh.score
            except Exception as e:
                logger.error(f"[RAGE] Failed to evaluate mathematical threshold condition '{cond}': {e}")

        return rule.default_score
