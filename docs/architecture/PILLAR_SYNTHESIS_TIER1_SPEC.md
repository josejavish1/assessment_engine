---
status: Verified
owner: docs-governance
source_of_truth:
- ../../docs/SYSTEM_ARCHITECTURE.md
- ../../src/assessment_engine/domain/
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
---
# TIER-1 ARCHITECTURE SPECIFICATION: ATOMIC PILLAR FORENSIC SYNTHESIS

**Document ID:** `ARCH-SPEC-2026-11-PILLAR-V2`  
**Author:** `gemini-4-argon` (Lead AI Systems Architect & Principal Software Engineer)  
**Date:** November 2026  
**Target System:** Enterprise Assessment Engine (Section 3 Narrative Pipeline)  
**Status:** MANDATORY IMPLEMENTATION DIRECTIVE  

---

## 1. EXECUTIVE SUMMARY & PROBLEM STATEMENT

The current implementation of `UniversalTowerSynthesizer` relies on a monolithic "Macro-Prompt" design pattern, instructing the LLM to generate the executive summary and all underlying pillar narratives (`asis_architecture_description`) for an entire technology tower in a single inference call. 

Under production load across 50 pillars and 10 towers, this pattern exhibits severe **Semantic Anemia**:
1. **Attention Dilution & Output Token Budgeting:** By the 4th or 5th pillar in a single completion payload, the model compresses outputs to 1–2 superficial sentences to conserve generation capacity.
2. **Evidence Sparsity Collapse:** When a specific pillar lacks dense direct telemetry, the model defaults to generic consulting boilerplate or hallucinates adjacent tower artifacts.
3. **Cross-Domain Contamination:** Shared context windows cause infrastructure tokens (e.g., `SAN`, `NetApp`, `BGP`) to bleed into endpoint or workplace narratives (e.g., `T9`).

This specification mandates the immediate deprecation of monolithic pillar generation and enforces an **Atomic Asynchronous Map-Reduce Architecture** governed by deterministic pre-commit validation gates (`SemanticGatekeeper`).

---

## 2. SYSTEM ARCHITECTURE & FILE TOPOLOGY

The refactoring introduces two new core modules and modifies the existing tower orchestrator.

```text
src/
└── synthesis/
    ├── __init__.py
    ├── exceptions.py                   # [NEW] Custom exception hierarchy
    ├── gatekeeper.py                   # [NEW] Deterministic validation & contamination engine
    ├── pillar_synthesizer.py           # [NEW] Atomic async per-pillar synthesizer & prompt engine
    └── universal_tower_synthesizer.py  # [MODIFIED] Map-Reduce integration
```

---

## 3. PHASE 1 & 2: ATOMIC SYNTHESIS & 4-SLOT PROMPT ARCHITECTURE

### 3.1 File: `src/synthesis/exceptions.py`

Define the custom exception used to trigger self-healing retry loops.

```python
class SemanticQualityError(Exception):
    """Raised when generated pillar narrative fails deterministic Tier-1 quality gates."""
    def __init__(self, feedback: str, failed_text: str = ""):
        super().__init__(feedback)
        self.feedback = feedback
        self.failed_text = failed_text
```

### 3.2 File: `src/synthesis/pillar_synthesizer.py`

This module implements `PillarForensicSynthesizer`. It isolates context to a single pillar, forces a 4-Slot Forensic Narrative structure, and manages the self-healing retry loop with the `SemanticGatekeeper`.

```python
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from src.synthesis.exceptions import SemanticQualityError
from src.synthesis.gatekeeper import SemanticGatekeeper

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
You must construct a cohesive, dense, multi-paragraph technical narrative (strictly between 250 and 400 words) that seamlessly integrates the following four analytical slots in exact sequential order. DO NOT use markdown headers, bullet points, or numbered lists in your output—write purely in continuous, authoritative executive-technical prose.

1. SLOT 1: Empirical Baseline (State & Evidence)
   Anchor the narrative in the exact verified telemetry, configurations, topological facts, and architectural states present in the provided Pillar Evidence. Cite specific mechanisms, protocols, or structural patterns observed.

2. SLOT 2: Failure Mechanics & Adjacent Inference (Negative Space Analysis)
   Where direct evidence for this specific pillar is sparse or omitted, you MUST deduce the operational reality from the broader Tower Context and Firmographic Profile. Explain the exact technical mechanics of how the system operates in the absence of mature controls (e.g., manual provisioning bottlenecks, unorchestrated state drift, lack of telemetry correlation).

3. SLOT 3: Architectural Risk Debt & Vulnerability
   Translate the empirical baseline and operational mechanics into concrete architectural debt. Identify single points of failure (SPOFs), blast-radius amplification vectors, synchronization fragility, or scalability ceilings inherent to this design.

4. SLOT 4: Factual Business & Firmographic Impact
   Connect the technical risk debt directly to the organization's specific firmographic reality (industry vertical, operational scale, regulatory posture, or transaction volume). Quantify or qualify the operational drag, recovery time degradation (RTO/RPO), or compliance exposure.

### RUTHLESS CONSTRAINTS (ZERO TOLERANCE)
- WORD COUNT: Strictly 250 to 400 words. Every sentence must carry high forensic information density.
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
        direct_evidence = pillar_data.get("evidence", "No direct telemetry captured; rely on Negative Space Inference from Tower Context.")
        adjacent_context = tower_context.get("adjacent_evidence_summary", "Standard enterprise operational baseline.")

        prompt = f"""### TARGET ASSIGNMENT
- **Tower:** [{tower_id}] {tower_name}
- **Target Pillar:** [{pillar_id}] {pillar_name}

### FIRMOGRAPHIC PROFILE
{firmographics}

### DIRECT PILLAR EVIDENCE (PRIMARY TRUTH)
{direct_evidence}

### ADJACENT TOWER CONTEXT (FOR NEGATIVE SPACE INFERENCE ONLY)
{adjacent_context}

### EXECUTION INSTRUCTION
Write the 4-slot forensic narrative (`asis_architecture_description`) for **{pillar_name}** in Spanish (matching standard enterprise report localization). Ensure strict adherence to the 250–400 word boundary and zero vendor hallucination. Output ONLY the raw narrative text.
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

                raw_narrative = await self.llm.generate_text(
                    system_prompt=self.SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=temp
                )
                clean_narrative = raw_narrative.strip()

                try:
                    word_count = self.gatekeeper.validate(
                        text=clean_narrative,
                        tower_id=tower_id,
                        allowed_evidence_text=f"{pillar_data.get('evidence', '')} {tower_context.get('adjacent_evidence_summary', '')}"
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
                        logger.error(f"[{tower_id}:{pillar_id}] Exhausted all {max_retries} retries. Raising terminal error.")
                        raise e

            raise RuntimeError("Unreachable state in retry loop.")

        if semaphore:
            async with semaphore:
                return await _execute_with_retry()
        return await _execute_with_retry()
```

---

## 4. PHASE 3: THE SEMANTIC GATEKEEPER & CONTAMINATION ENGINE

### 4.1 File: `src/synthesis/gatekeeper.py`

The `SemanticGatekeeper` enforces deterministic constraints before any LLM output is accepted into the assessment state object. It validates word counts, strips/rejects boilerplate, blocks survey score leaks, and enforces cross-tower lexical boundaries.

```python
import re
from typing import Dict, List, Set
from src.synthesis.exceptions import SemanticQualityError


class SemanticGatekeeper:
    """
    Deterministic validation engine enforcing lexical density, anti-boilerplate rules,
    and cross-domain contamination boundaries across all 10 technology towers.
    """

    MIN_WORDS: int = 250
    MAX_WORDS: int = 450

    # Forbidden cross-domain terms per Tower ID (Case-insensitive boundary matching)
    DEFAULT_CONTAMINATION_MATRIX: Dict[str, List[str]] = {
        "T1": ["endpoint", "impresora", "vdi", "citrix", "laptop", "mesa de ayuda", "helpdesk"],
        "T2": ["servidor físico", "rack", "chasis", "fibra oscura", "bgp", "ospf", "mainframe"],
        "T3": ["laptop", "impresora", "BYOD", "móvil", "licenciamiento office", "sharepoint"],
        "T4": ["cableado estructurado", "planta externa", "ups", "generador", "aire acondicionado"],
        "T5": ["bgp", "mpls", "sd-wan", "switch core", "almacenamiento san", "lun"],
        "T6": ["routing", "switching", "spanning-tree", "vlan trunk", "frecuencia de radio"],
        "T7": ["cinta lto", "hidratación de datos", "sql injection", "xss", "desarrollo ágil"],
        "T8": ["cooler", "pdu", "fibra óptica", "transceiver", "patch panel"],
        "T9": [
            "servidor físico", "san", "nas", "netapp", "bgp", "ospf", "mpls",
            "data center", "racks", "mainframe", "fibra oscura", "core switch", "lun", "raid"
        ],
        "T10": ["parcheo de cables", "configuración bgp", "reemplazo de discos", "tinta", "tóner"]
    }

    # Regex patterns for forbidden consulting boilerplate and score leakage
    FORBIDDEN_PATTERNS: List[tuple[str, str]] = [
        (r"\b(es esencial|resulta imprescindible|es fundamental|se recomienda encarecidamente)\b", "Contains prescriptive consulting boilerplate ('es esencial / se recomienda'). Describe only As-Is reality."),
        (r"\b(mejores prácticas|best practices|estándares de la industria dictan)\b", "Contains generic 'best practices' filler."),
        (r"\b(puntaje|puntuación|calificación|score|nivel de madurez\s+\d|encuesta|cuestionario)\b", "Leaks assessment survey metadata or numerical maturity scores."),
        (r"^(#|\*|-|\d+\.)", "Contains Markdown headers, bullet points, or numbered lists. Must be continuous prose.")
    ]

    def __init__(self, custom_contamination_matrix: Dict[str, List[str]] | None = None):
        self.contamination_matrix = custom_contamination_matrix or self.DEFAULT_CONTAMINATION_MATRIX

    def _count_words(self, text: str) -> int:
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    def _check_word_count(self, text: str) -> int:
        count = self._count_words(text)
        if count < self.MIN_WORDS:
            deficit = self.MIN_WORDS - count
            raise SemanticQualityError(
                feedback=f"Semantic Anemia detected: Output is {count} words (Minimum required is {self.MIN_WORDS}). You must expand the forensic analysis by at least {deficit} words, deepening Slot 2 (Failure Mechanics) and Slot 3 (Architectural Risk Debt).",
                failed_text=text
            )
        if count > self.MAX_WORDS:
            excess = count - self.MAX_WORDS
            raise SemanticQualityError(
                feedback=f"Verbosity violation: Output is {count} words (Maximum allowed is {self.MAX_WORDS}). Trim {excess} words by tightening prose without losing technical facts.",
                failed_text=text
            )
        return count

    def _check_contamination(self, text: str, tower_id: str, allowed_evidence_text: str) -> None:
        forbidden_terms = self.contamination_matrix.get(tower_id, [])
        if not forbidden_terms:
            return

        text_lower = text.lower()
        evidence_lower = allowed_evidence_text.lower()
        detected_contaminants: Set[str] = set()

        for term in forbidden_terms:
            term_lower = term.lower()
            # Use word boundary regex to prevent partial substring false positives (e.g., "san" in "saneamiento")
            pattern = rf"\b{re.escape(term_lower)}\b"
            if re.search(pattern, text_lower):
                # Exception: If the term was explicitly present in the raw input evidence for this pillar, allow it
                if not re.search(pattern, evidence_lower):
                    detected_contaminants.add(term)

        if detected_contaminants:
            terms_str = ", ".join(f"'{t}'" for t in sorted(detected_contaminants))
            raise SemanticQualityError(
                feedback=f"Cross-Domain Contamination in Tower {tower_id}: Text contains forbidden out-of-domain terms [{terms_str}] that do not exist in the source evidence. Remove all references to these concepts and strictly confine analysis to {tower_id}.",
                failed_text=text
            )

    def _check_structural_and_boilerplate_rules(self, text: str) -> None:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            for pattern, reason in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, stripped, flags=re.IGNORECASE):
                    raise SemanticQualityError(
                        feedback=f"Style/Constraint Violation: {reason}",
                        failed_text=text
                    )

    def validate(self, text: str, tower_id: str, allowed_evidence_text: str = "") -> int:
        """
        Runs all deterministic checks sequentially.
        Returns the verified word count if valid, or raises SemanticQualityError.
        """
        if not text or not text.strip():
            raise SemanticQualityError("Empty narrative generated.")

        self._check_structural_and_boilerplate_rules(text)
        self._check_contamination(text, tower_id, allowed_evidence_text)
        word_count = self._check_word_count(text)

        return word_count
```

---

## 5. PHASE 4: INTEGRATION WITH `UniversalTowerSynthesizer`

### 5.1 File: `src/synthesis/universal_tower_synthesizer.py`

Refactor `UniversalTowerSynthesizer.synthesize_tower` to execute an asynchronous **Map-Reduce** workflow:
1. **Map Step:** Fan out all pillars belonging to the tower concurrently via `asyncio.gather` using `PillarForensicSynthesizer.synthesize_pillar`.
2. **Reduce Step:** Aggregate the validated, high-density pillar descriptions and feed them into the Tower-level Executive Synthesis prompt (ensuring the Tower Summary is grounded in the newly synthesized 10/10 pillar narratives).

```python
import asyncio
import logging
from typing import Dict, Any, List

from src.synthesis.gatekeeper import SemanticGatekeeper
from src.synthesis.pillar_synthesizer import PillarForensicSynthesizer, PillarSynthesisResult

logger = logging.getLogger(__name__)


class UniversalTowerSynthesizer:
    """
    Orchestrates complete technology tower synthesis using an Atomic Map-Reduce architecture.
    """

    MAX_CONCURRENT_PILLARS: int = 5  # Protects upstream LLM rate limits per tower

    def __init__(self, llm_client: Any, custom_contamination_matrix: Dict[str, List[str]] | None = None):
        self.llm = llm_client
        self.gatekeeper = SemanticGatekeeper(custom_contamination_matrix=custom_contamination_matrix)
        self.pillar_synthesizer = PillarForensicSynthesizer(
            llm_client=self.llm,
            gatekeeper=self.gatekeeper
        )

    async def synthesize_tower(
        self,
        tower_payload: Dict[str, Any],
        firmographics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes the Map-Reduce synthesis pipeline for a single Technology Tower.

        :param tower_payload: Dict containing `tower_id`, `tower_name`, `adjacent_evidence_summary`, and `pillars` list.
        :param firmographics: Organization profile dictionary.
        :return: Completed Tower dictionary with guaranteed Tier-1 `asis_architecture_description` per pillar.
        """
        tower_id: str = tower_payload["tower_id"]
        tower_name: str = tower_payload["tower_name"]
        pillars_input: List[Dict[str, Any]] = tower_payload.get("pillars", [])

        tower_context = {
            "adjacent_evidence_summary": tower_payload.get("adjacent_evidence_summary", "")
        }

        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_PILLARS)

        logger.info(f"[{tower_id}] Starting Atomic Map-Reduce synthesis for {len(pillars_input)} pillars.")

        # =========================================================================
        # PHASE 1 (MAP): Concurrent Atomic Pillar Synthesis
        # =========================================================================
        tasks = [
            self.pillar_synthesizer.synthesize_pillar(
                tower_id=tower_id,
                tower_name=tower_name,
                pillar_data=pillar,
                tower_context=tower_context,
                firmographics=firmographics,
                max_retries=3,
                semaphore=semaphore
            )
            for pillar in pillars_input
        ]

        pillar_results: List[PillarSynthesisResult] = await asyncio.gather(*tasks)

        # Merge validated narratives back into the pillar data structures
        synthesized_pillars: List[Dict[str, Any]] = []
        for original_pillar, result in zip(pillars_input, pillar_results):
            updated_pillar = dict(original_pillar)
            updated_pillar["asis_architecture_description"] = result.asis_architecture_description
            updated_pillar["_synthesis_metadata"] = {
                "word_count": result.word_count,
                "attempts_taken": result.attempts_taken,
                "tier1_validated": True
            }
            synthesized_pillars.append(updated_pillar)

        # =========================================================================
        # PHASE 2 (REDUCE): Tower-Level Executive Synthesis from Verified Pillars
        # =========================================================================
        tower_executive_summary = await self._synthesize_tower_executive_narrative(
            tower_id=tower_id,
            tower_name=tower_name,
            synthesized_pillars=synthesized_pillars,
            firmographics=firmographics
        )

        return {
            "tower_id": tower_id,
            "tower_name": tower_name,
            "executive_summary": tower_executive_summary,
            "pillars": synthesized_pillars
        }

    async def _synthesize_tower_executive_narrative(
        self,
        tower_id: str,
        tower_name: str,
        synthesized_pillars: List[Dict[str, Any]],
        firmographics: Dict[str, Any]
    ) -> str:
        """
        Reduces the atomic pillar narratives into a cohesive Tower-level Executive Summary.
        """
        compiled_pillar_narratives = "\n\n".join(
            f"### PILLAR [{p['pillar_id']}] {p['pillar_name']}:\n{p['asis_architecture_description']}"
            for p in synthesized_pillars
        )

        system_prompt = (
            "You are a Principal Enterprise Architect. Synthesize an authoritative Tower Executive Summary "
            "strictly derived from the underlying verified pillar narratives. Do not introduce external vendors "
            "or contradict the pillar findings."
        )
        user_prompt = (
            f"Tower: [{tower_id}] {tower_name}\n"
            f"Firmographics: {firmographics}\n\n"
            f"Verified Pillar Narratives:\n{compiled_pillar_narratives}\n\n"
            "Write a 200-300 word executive synthesis of the overall tower posture in Spanish."
        )

        summary = await self.llm.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2
        )
        return summary.strip()
```

---

## 6. VERIFICATION & ACCEPTANCE TEST CRITERIA

Before merging this implementation into `main`, the engineering team must execute the automated test suite (`tests/synthesis/test_pillar_tier1.py`) verifying the following invariants:

1. **Word Count Boundary Enforcement:**
   - Feed a mock LLM response of 140 words into `PillarForensicSynthesizer.synthesize_pillar`.
   - Assert `SemanticGatekeeper` raises `SemanticQualityError` and triggers a retry with the exact word deficit injected into `user_prompt`.
2. **Contamination Rejection (`T9` Workplace Isolation):**
   - Feed a mock `T9` narrative containing `"El entorno de escritorio depende de un servidor físico conectado a una SAN NetApp vía BGP."` where input evidence is empty.
   - Assert `SemanticGatekeeper` rejects the payload and explicitly lists `'bgp'`, `'netapp'`, `'san'`, `'servidor físico'` in the rejection feedback.
3. **Evidence Whitelist Bypass:**
   - If the raw evidence for `T9` explicitly states `"VDI hosted on NetApp SAN"`, assert that `"NetApp"` and `"SAN"` do **not** trigger a `SemanticQualityError`.
4. **Concurrency & Isolation:**
   - Run `UniversalTowerSynthesizer.synthesize_tower` with 6 mock pillars and `MAX_CONCURRENT_PILLARS = 5`. Verify via timestamps that batching respects the semaphore and produces 6 independent `PillarSynthesisResult` objects with zero shared mutable state.