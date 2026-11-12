import asyncio
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from assessment_engine.application.services.synthesis.exceptions import SemanticQualityError
from assessment_engine.application.services.synthesis.gatekeeper import SemanticGatekeeper

logger = logging.getLogger(__name__)


class PillarSynthesisResult(BaseModel):
    pillar_id: str
    pillar_name: str
    asis_architecture_description: str = Field(
        description="The complete, cohesive 250-400 word forensic narrative combining all 4 analytical slots into seamless technical prose."
    )
    word_count: int
    attempts_taken: int


class PillarForensicSynthesizer:
    """
    Executes atomic, high-density forensic synthesis for a single architectural pillar.
    Enforces a 4-Slot Narrative Architecture and Negative Space Inference.
    """

    SYSTEM_PROMPT = """You are a Principal Enterprise Architect & Forensic Systems Auditor conducting a Tier-1 technical due diligence assessment.
Your sole objective is to write the 'As-Is Architecture Description' (`asis_architecture_description`) for ONE specific technology pillar.

### MANDATORY 4-SLOT NARRATIVE ARCHITECTURE
You must construct a cohesive, dense, multi-paragraph technical narrative (strictly between 250 and 450 words) that seamlessly integrates the following four analytical slots in exact sequential order. DO NOT use markdown headers, bullet points, or numbered lists in your output—write purely in continuous, authoritative executive-technical prose.

1. SLOT 1: Empirical Baseline (State & Evidence)
   Anchor the narrative in the exact verified telemetry, configurations, topological facts, and architectural states present in the provided Pillar Evidence. Cite specific mechanisms, protocols, or structural patterns observed.

2. SLOT 2: Failure Mechanics & Adjacent Inference (Negative Space Analysis)
   Where direct evidence for this specific pillar is sparse or omitted, you MUST deduce the operational reality from the broader Tower Context and Firmographic Profile. Explain the exact technical mechanics of how the system operates in the absence of mature controls (e.g., manual provisioning bottlenecks, unorchestrated state drift, lack of telemetry correlation).

3. SLOT 3: Architectural Risk Debt & Vulnerability
   Translate the empirical baseline and operational mechanics into concrete architectural debt. Identify single points of failure (SPOFs), blast-radius amplification vectors, synchronization fragility, or scalability ceilings inherent to this design.

4. SLOT 4: Factual Business & Firmographic Impact
   Connect the technical risk debt directly to the organization's specific firmographic reality (industry vertical, operational scale, regulatory posture, or transaction volume). Quantify or qualify the operational drag, recovery time degradation (RTO/RPO), or compliance exposure.

### RUTHLESS CONSTRAINTS (ZERO TOLERANCE)
- WORD COUNT: Strictly 250 to 450 words. Every sentence must carry high forensic information density.
- NO HALLUCINATED VENDORS: NEVER invent, assume, or name specific third-party vendor products, OEMs, or software brands (e.g., Cisco, NetApp, CrowdStrike, ServiceNow) unless they are explicitly stated in the provided evidence payload. If unknown, refer to them by their architectural function (e.g., "the legacy perimeter firewall appliance", "the incumbent directory service").
- NO CONSULTING BOILERPLATE: Never write prescriptive fluff such as "It is essential to have...", "Best practices dictate...", "Organizations should consider...", or "In today's modern landscape...". Describe ONLY the forensic reality of the current environment and its risk mechanics.
- NO SURVEY METADATA: NEVER mention survey scores, maturity numbers (e.g., "Level 2.4", "score of 3"), questionnaires, or assessment mechanics. Write as if you directly inspected the live production environment.
- DOMAIN ISOLATION: Strictly confine your technical vocabulary to the assigned Tower and Pillar. Do not bleed concepts from unrelated infrastructure domains.
"""

    def __init__(self, llm_client: Any, gatekeeper: SemanticGatekeeper):
        """
        :param llm_client: Async LLM interface supporting `.generate_text(system_prompt, user_prompt, temperature)`
        :param gatekeeper: Instance of SemanticGatekeeper for deterministic validation.
        """
        self.llm = llm_client
        self.gatekeeper = gatekeeper

    def _build_user_prompt(
        self,
        tower_id: str,
        tower_name: str,
        pillar_data: Dict[str, Any],
        tower_context: Dict[str, Any],
        firmographics: Dict[str, Any],
        feedback_history: List[str]
    ) -> str:
        pillar_id = pillar_data.get("pillar_id", "UNKNOWN_ID")
        pillar_name = pillar_data.get("pillar_name", "Unknown Pillar")
        
        # Extract findings to act as direct evidence
        findings = [hc.get("finding", "") for hc in pillar_data.get("health_check_asis", []) if isinstance(hc, dict) and hc.get("finding")]
        findings_str = " | ".join(findings) if findings else "No direct telemetry captured; rely on Negative Space Inference from Tower Context."

        adjacent_context = tower_context.get("adjacent_evidence_summary", "Standard enterprise operational baseline.")

        prompt = f"""### TARGET ASSIGNMENT
- **Tower:** [{tower_id}] {tower_name}
- **Target Pillar:** [{pillar_id}] {pillar_name}

### FIRMOGRAPHIC PROFILE
{firmographics}

### DIRECT PILLAR EVIDENCE (PRIMARY TRUTH)
{findings_str}

### ADJACENT TOWER CONTEXT (FOR NEGATIVE SPACE INFERENCE ONLY)
{adjacent_context}

### EXECUTION INSTRUCTION
Write the 4-slot forensic narrative (`asis_architecture_description`) for **{pillar_name}** in Spanish (matching standard enterprise report localization). Ensure strict adherence to the 250–450 word boundary and zero vendor hallucination. Output ONLY the raw narrative text.
"""
        if feedback_history:
            retry_block = "\n\n### CRITICAL VALIDATION FAILURES FROM PREVIOUS ATTEMPTS\n"
            for idx, fb in enumerate(feedback_history, 1):
                retry_block += f"Attempt {idx} REJECTED: {fb} Rewrite the entire narrative to fix this while maintaining all other constraints.\n"
            prompt += retry_block

        return prompt

    async def synthesize_pillar(
        self,
        tower_id: str,
        tower_name: str,
        pillar_data: Dict[str, Any],
        tower_context: Dict[str, Any],
        firmographics: Dict[str, Any],
        max_retries: int = 3,
        semaphore: Optional[asyncio.Semaphore] = None
    ) -> PillarSynthesisResult:
        """
        Executes atomic generation for a single pillar with an autonomous self-healing validation loop.
        """
        pillar_id = pillar_data.get("pillar_id", "UNKNOWN")
        pillar_name = pillar_data.get("pillar_name", "Unknown")
        feedback_history: List[str] = []

        async def _execute_with_retry() -> PillarSynthesisResult:
            for attempt in range(1, max_retries + 2):  # Initial attempt + max_retries
                user_prompt = self._build_user_prompt(
                    tower_id=tower_id,
                    tower_name=tower_name,
                    pillar_data=pillar_data,
                    tower_context=tower_context,
                    firmographics=firmographics,
                    feedback_history=feedback_history
                )

                # Slight temperature adjustment on retries to escape local minima
                temp = 0.2 if attempt == 1 else min(0.4, 0.2 + (attempt * 0.05))

                try:
                    # Determine LLM call based on the client type provided
                    # GenaiClient from this repo usually expects models.generate_content
                    # But the spec assumes .generate_text. Let's adapt to the real repo client.
                    if hasattr(self.llm, "models") and hasattr(self.llm.models, "generate_content"):
                        # Google GenAI SDK style
                        from assessment_engine.infrastructure.genai_client import ModelTier, get_model
                        model_name = get_model(ModelTier.REASONING)
                        response = self.llm.models.generate_content(
                            model=model_name,
                            contents=f"{self.SYSTEM_PROMPT}\n\n{user_prompt}"
                        )
                        raw_narrative = response.text
                    else:
                        # Fallback for mock/other
                        raw_narrative = await self.llm.generate_text(
                            system_prompt=self.SYSTEM_PROMPT,
                            user_prompt=user_prompt,
                            temperature=temp
                        )
                except Exception as ex:
                    logger.warning(f"[{tower_id}:{pillar_id}] LLM generation failed: {ex}")
                    raw_narrative = f"Error generating narrative: {ex}"

                clean_narrative = raw_narrative.strip()

                try:
                    findings = [hc.get("finding", "") for hc in pillar_data.get("health_check_asis", []) if isinstance(hc, dict) and hc.get("finding")]
                    evidence_str = " ".join(findings) + " " + tower_context.get("adjacent_evidence_summary", "")
                    
                    word_count = self.gatekeeper.validate(
                        text=clean_narrative,
                        tower_id=tower_id,
                        allowed_evidence_text=evidence_str
                    )
                    logger.info(f"[{tower_id}:{pillar_id}] Pillar synthesis succeeded on attempt {attempt} ({word_count} words).")
                    return PillarSynthesisResult(
                        pillar_id=pillar_id,
                        pillar_name=pillar_name,
                        asis_architecture_description=clean_narrative,
                        word_count=word_count,
                        attempts_taken=attempt
                    )
                except SemanticQualityError as e:
                    logger.warning(f"[{tower_id}:{pillar_id}] Gatekeeper rejection (Attempt {attempt}/{max_retries + 1}): {e.feedback}")
                    feedback_history.append(e.feedback)
                    if attempt == max_retries + 1:
                        logger.error(f"[{tower_id}:{pillar_id}] Exhausted all {max_retries} retries.")
                        # As a fallback when all retries are exhausted, just return what we have
                        # Alternatively, we could raise e, but to prevent entire tower failures, we might want to just return the degraded text.
                        # The spec says "raise e", so we will do that to strictly enforce the quality gate.
                        raise e

            raise RuntimeError("Unreachable state in retry loop.")

        if semaphore:
            async with semaphore:
                return await _execute_with_retry()
        return await _execute_with_retry()
