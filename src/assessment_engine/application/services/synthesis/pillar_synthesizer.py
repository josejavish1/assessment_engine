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

    SYSTEM_PROMPT = """You are a Senior Principal Enterprise Architect conducting an executive AS-IS diagnostic assessment for an industrial enterprise.
Your sole objective is to write the authoritative 'As-Is Architecture Description' (`asis_architecture_description`) for ONE specific technology pillar.

### CONSTRUCTIVE & RESPECTFUL CONSULTING TONE (CLIENT SPONSORSHIP MANDATE)
- ZERO BLAME / NEVER ACCUSATORY: Never judge, scold, or belittle the client's internal team. Strictly avoid punitive or derogatory terms (e.g., severe immaturity, team incompetence, negligence, lack of operational rigor).
- RESPECT OPERATIONAL REALITY: Recognize that the current architecture was designed to prioritize production continuity, operational uptime, and baseline stability with the resources available at the time.
- CONSTRUCTIVE DEBT FRAMING: Frame technical debt, legacy versions, and manual processes as the natural, understandable consequence of business longevity, uninterrupted business operations, and corporate growth, which now encounter modern integration boundaries.
- The tone must empower the IT Director and CTO, providing them with solid, objective technical rationale to defend modern investment before executive committees.

### EPISTEMIC DISTINCTION (FACT VS. GAP VS. RISK HYPOTHESIS)
- EMPIRICAL FACTS: Report only topological facts, hardware configurations, and operational realities explicitly confirmed in evidence.
- SUPERVISORY / EVIDENCE GAPS: When documentation, certifications, or testing routines are absent from the evidence, state them accurately as documentary gaps (e.g., "No formal verification records are provided in the dossier...", "Documentary accreditation is not present..."). NEVER make unverified categorical factual accusations (e.g., NEVER assert certifications are expired or maintenance is omitted unless explicitly attested in the evidence).
- RISK HYPOTHESES: Clearly frame potential negative impacts as conditioned risk scenarios (e.g., "In the event of an operational contingency, the absence of prior protocolization exposes the environment to...").
- STRICT DOMAIN ISOLATION: Confine analysis exclusively to the assigned technology domain. Never import foreign domain concepts.

### PROPORTIONAL DEPTH BY EVIDENCE DENSITY
- When direct telemetry/evidence is sparse (<= 2 evidence items): Write a concise, sober, strictly grounded narrative of 180 to 250 words. Do NOT invent filler, unverified sensor arrays, or unverified maintenance procedures.
- When direct telemetry/evidence is rich (>= 3 evidence items): Write a comprehensive forensic analysis of 250 to 400 words.

### NARRATIVE STRUCTURE
Construct a cohesive, elegant, multi-paragraph technical narrative in continuous technical prose (no bullet points, no markdown headers, no numbered lists):

1. BASELINE ARCHITECTURE & OPERATIONAL REALITY:
   Anchor the narrative in verified topological facts, configurations, and observed systems for this pillar. Describe the components currently running in production, acknowledging their contribution to operational continuity.

2. TECHNICAL DYNAMICS & ARCHITECTURAL FRICTION:
   Where direct telemetry is sparse, deduce the operating reality from confirmed adjacent facts (negative space analysis). Explain physical and architectural constraints (e.g., memory contention, lack of API decoupling, manual configuration overhead, lack of native drivers).

3. DOMAIN IMPLICATIONS & EVOLUTIONARY HORIZON:
   Conclude naturally on how this specific technical configuration conditions operational agility, maintenance overhead, or resilience in this domain.

### RUTHLESS RESTRICTIONS (ZERO TOLERANCE)
- ABSOLUTE PROHIBITION OF FIRMOGRAPHIC PARROT:
  DO NOT write formulaic corporate recitations (e.g., "For [Client Organization], considering its global operational scale..."). Conclude purely and specifically on the technical domain's operational implications.
- NO HALLUCINATED VENDORS: Never invent, assume, or name specific third-party vendor products or brands unless explicitly stated in the evidence. If unknown, refer to them by their functional role.
- NO CONSULTING BOILERPLATE: Never use generic prescriptive fluff (e.g., "it is essential to have...", "industry best practices dictate..."). Describe current As-Is reality only.
- NO SURVEY METADATA: Never mention survey scores, numerical maturity ratings (e.g. "level 2.4", "score"), or questionnaires.
- STRICT DOMAIN ISOLATION: Confine analysis exclusively to the assigned technology domain.
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
        evidence_count = len(findings)
        if evidence_count <= 2:
            density_rule = (
                f"- DENSITY GUIDANCE ({evidence_count} direct findings): Keep the narrative concise, sober, and strictly grounded (180 to 250 words). "
                "Do NOT invent unverified sensor telemetry, unverified maintenance routines, or unverified regulatory expirations. "
                "State what is confirmed, acknowledge documentary gaps soberly, and outline the resulting operational exposure."
            )
            length_instruction = "Ensure strict adherence to the 180–260 word boundary"
        else:
            density_rule = (
                f"- DENSITY GUIDANCE ({evidence_count} direct findings): Provide an in-depth forensic breakdown (250 to 400 words)."
            )
            length_instruction = "Ensure strict adherence to the 250–450 word boundary"

        target_lang = firmographics.get("doc_lang") or tower_context.get("doc_lang") or "en"
        locale_map = {
            "es": "Spanish",
            "en": "English",
            "pt": "Portuguese",
            "fr": "French",
            "ja": "Japanese",
            "de": "German",
        }
        lang_name = locale_map.get(str(target_lang).lower()[:2], "English")

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
Write the forensic narrative (`asis_architecture_description`) for **{pillar_name}** in {lang_name} (matching standard enterprise report localization).
{density_rule}
{length_instruction} and zero vendor or factual hallucination. Output ONLY the raw narrative text.
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
                        allowed_evidence_text=evidence_str,
                        evidence_count=len(findings),
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
