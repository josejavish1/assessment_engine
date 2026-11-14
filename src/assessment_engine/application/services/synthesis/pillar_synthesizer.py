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
- NO GOSSIP OR SINGULAR INDIVIDUALS: NEVER cite individual employees (e.g., "a DBA in Croatia"), personal knowledge silos, or informal meeting transcripts. Discuss "governance of technical knowledge" and "team topology" abstractly.
- NO DEROGATORY ADJECTIVES: Never use subjective or demeaning words like "artesanal", "obsolete", "archaic", or "rudimentary". Use objective terms like "manual execution", "legacy", or "decentralized".
- NO PLATFORM SHAMING: Never shame an internal tool by name (e.g., do not say "obsolete MoinMoin wiki"); say "legacy documentation platforms".
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

### NARRATIVE STRUCTURE & MULTI-PARAGRAPH FORMATTING
You MUST structure the narrative into exactly 2 to 3 distinct, well-proportioned paragraphs separated by a blank line (\n\n). Monolithic single-paragraph walls of text are strictly forbidden.

1. PARAGRAPH 1 - BASELINE ARCHITECTURE & OPERATIONAL FOOTPRINT:
   Anchor in verified topological facts, configurations, and running production systems for this capability. Describe current components and their role in day-to-day operational continuity.

2. PARAGRAPH 2 - OPERATIONAL FRICTION, TECHNICAL DEBT & RISK EXPOSURES:
   Explain observed constraints, maintenance overhead, manual procedures, lack of automation, single points of failure, or unmonitored operational dependencies.

3. PARAGRAPH 3 (OPTIONAL / COMPLEX SCENARIOS) - SYSTEMIC CONTINUITY & BUSINESS IMPLICATIONS:
   Explain how this specific technical configuration conditions operational agility, recovery times, or business resilience across the enterprise.

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

        raw_score = pillar_data.get("score") if pillar_data.get("score") is not None else pillar_data.get("score_exact")
        pillar_score: float | None = float(raw_score) if raw_score is not None else None

        maturity_guidance = ""
        if pillar_score is not None:
            from assessment_engine.domain.governance.scale_engine import GovernanceScaleEngine
            scale_engine = GovernanceScaleEngine.get_instance()
            resolved = scale_engine.resolve_maturity(pillar_score, locale=str(target_lang))
            lvl = resolved.level
            band_lbl = resolved.label

            level_guidance_map = {
                1: (
                    f"- TARGET MATURITY REALITY: LEVEL 1 - {band_lbl.upper()} ({pillar_score:.2f} / 5.00).\n"
                    "  This capability operates with foundational gaps, manual configurations, and absence of declarative automation.\n"
                    "  You are STRICTLY FORBIDDEN from claiming 'alta madurez técnica', 'high maturity', or Level 5 capabilities.\n"
                    "  Objectively explain the foundational operational gaps and manual dependencies justifying this initial maturity stage."
                ),
                2: (
                    f"- TARGET MATURITY REALITY: LEVEL 2 - {band_lbl.upper()} ({pillar_score:.2f} / 5.00).\n"
                    "  Basic operations are functional and repeatable at team/project level, but rely on decentralized execution without unified policy-as-code.\n"
                    "  Focus analysis on lack of cross-organizational standardization and reactive operational dependencies."
                ),
                3: (
                    f"- TARGET MATURITY REALITY: LEVEL 3 - {band_lbl.upper()} ({pillar_score:.2f} / 5.00).\n"
                    "  Standard documented procedures and corporate-wide baselines are active and governed.\n"
                    "  Acknowledge formal controls; frame residual risks around multi-site stress, edge concurrency, and scale limits."
                ),
                4: (
                    f"- TARGET MATURITY REALITY: LEVEL 4 - {band_lbl.upper()} ({pillar_score:.2f} / 5.00).\n"
                    "  Capability is quantitatively managed with statistical process control, granular telemetry, SLOs, and error budgets.\n"
                    "  Analyze how quantitative metrics drive operational stability, and frame risks around systemic drift and complex dependencies."
                ),
                5: (
                    f"- TARGET MATURITY REALITY: LEVEL 5 - {band_lbl.upper()} ({pillar_score:.2f} / 5.00).\n"
                    "  Operational excellence with continuous automated optimization, self-healing architectures, and proactive chaos engineering.\n"
                    "  Acknowledge cutting-edge resilience; frame residual challenges around novel multi-cloud or geopolitical external disruption."
                ),
            }
            maturity_guidance = level_guidance_map.get(lvl, "")

        client_name = firmographics.get("client_name") or firmographics.get("name") or "the organization"
        industry = firmographics.get("industry") or firmographics.get("industry_vertical") or "Enterprise Operations"
        raw_frameworks = firmographics.get("regulatory_frameworks") or firmographics.get("frameworks") or []
        frameworks_list = [str(f) for f in raw_frameworks] if isinstance(raw_frameworks, list) else [str(raw_frameworks)]
        frameworks_str = ", ".join(frameworks_list) if frameworks_list else "Standard Enterprise Governance"

        firmographic_guidance = (
            f"- TARGET ENTERPRISE PROFILE: {client_name}\n"
            f"- INDUSTRY VERTICAL: {industry}\n"
            f"- REGULATORY & COMPLIANCE FRAMEWORKS: {frameworks_str}\n"
            "  Frame technical risks and operational exposure with appropriate domain context matching this industry vertical."
        )

        prompt = f"""### TARGET ASSIGNMENT
- **Tower:** [{tower_id}] {tower_name}
- **Target Pillar:** [{pillar_id}] {pillar_name}

### ENTERPRISE & REGULATORY PROFILE
{firmographic_guidance}

### MATURITY & DOMAIN DISCIPLINE
{maturity_guidance}
- STRICT DOMAIN FOCUS: Confine analysis exclusively to {pillar_name} within the scope of {tower_name}. Do NOT evaluate or describe assets, platforms, or disciplines that belong to other technology domains.

### DIRECT PILLAR EVIDENCE (PRIMARY TRUTH)
{findings_str}

### EXECUTION INSTRUCTION
Write the forensic narrative (`asis_architecture_description`) for **{pillar_name}** in {lang_name} (matching standard enterprise report localization).
Write cohesive, fluent technical prose without artificial structural fragmentation. Use paragraph breaks (`\\n\\n`) naturally where logical shifts occur.
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
        raw_score = pillar_data.get("score") if pillar_data.get("score") is not None else pillar_data.get("score_exact")
        pillar_score: float | None = float(raw_score) if raw_score is not None else None
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
                        score=pillar_score,
                    )
                    clean_narrative = self.gatekeeper.sanitize_executive_dignity(clean_narrative)
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
