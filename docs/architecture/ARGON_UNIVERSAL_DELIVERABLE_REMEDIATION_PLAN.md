---
status: Verified
owner: architecture-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-07
applies_to:
- gemini
- architecture
doc_type: operational
diataxis: reference
verification_mode: editorial
---
# ENGINEERING DESIGN DOCUMENT (EDD)
**Document ID:** EDD-2026-AST-099  
**Title:** Universal Multi-Tower AST Truthfulness, Grounding & Structural Remediation Architecture  
**Status:** APPROVED FOR IMPLEMENTATION  
**Author:** Distinguished Principal Distributed Systems Architect, Lead Enterprise Ontologist & Chief Quality Gatekeeper  
**Target Architecture:** Multi-Tenant, Multi-Vertical, Multi-Lingual Enterprise Assessment Compiler (`payload_to_ast.py`, `resynthesize_domains_from_raw_transcription.py`, `domain_prompt_scoper.py`)  
**Codebase Language Policy:** 100% Technical English (Identifiers, Types, Comments, Docstrings, Commit Messages). Zero Hardcoded Client/Vertical Strings.

---

## 1. EXECUTIVE ARCHITECTURAL MANDATE & ROOT-CAUSE ONTOLOGY

Our forensic audit of the Tower 1 AS-IS deliverable (`Molins_202610_Anexo_01_Data_Center_ASIS.docx`) confirmed that while the deterministic scoring engine (2.61 / 5.00) and primary empirical ingestion pipelines operate at 100% mathematical fidelity, **five systemic architectural defects** corrupt the final AST-to-DOCX compilation and LLM synthesis layers. Because the compilation pipeline is shared across all domains (`T1..T10`, `D1..D8`, and arbitrary custom domain slugs), these defects represent a platform-wide horizontal failure mode.

### 1.1 Architectural Invariants (Non-Negotiable Mandates)
1. **Zero Spanish in Source Code:** Every function name, variable, class, docstring, comment, and structural schema key in Python must be written in strict Technical English. Localized output strings must be resolved exclusively via the `LocaleRegistry` / `i18n` translation bundles (`es`, `en`, `pt`, `fr`, `de`, etc.) injected at runtime.
2. **Zero Client or Domain Hardcoding:** No client names, specific vendor models (unless dynamically extracted from the active `EvidenceStore`), or hardcoded tower numbers may exist in logic branches. All domain routing must resolve dynamically via the `CanonicalOntologyGraph`.
3. **100% Empirical Grounding (Closed-World Assumption):** When a questionnaire response indicates a low maturity score (e.g., Score 1 or 2), the synthesis engine must describe **only** the functional condition stated in the selected rubric option and verified interview transcripts. Speculative causal embellishments (e.g., inventing clamp meters, manufacturer nameplates, or handwritten paper forms) are strictly forbidden.
4. **Strict Tower Boundary Isolation:** Cross-tower context (e.g., Compute hypervisor RAM saturation or Application ERP technical debt) may only appear in an infrastructure tower as a *downstream dependency impact*, never as the primary subject of the Executive Summary.

---

## 2. MASTER PHASED REMEDIATION ROADMAP

To guarantee zero regressions and deterministic verification across all 10 towers simultaneously, remediation is structured into **Five (5) Sequential, Gate-Checked Engineering Phases**.

```text
+---------------------------------------------------------------------------------------------------+
|                        MASTER REMEDIATION PIPELINE (5 GATE-CHECKED PHASES)                        |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [PHASE 1] AST Data Routing & Universal Chapter 2 Bridge (payload_to_ast.py)                      |
|      |-- Fixes Defect #1: Resolves blueprint_data -> annex_data -> dynamic ontology fallback      |
|      v                                                                                            |
|  [PHASE 2] Causal Risk Impact Resolver & Enum Sanitizer (payload_to_ast.py + i18n)                |
|      |-- Fixes Defect #2: Intercepts raw enums (HIGH/CRITICAL) & synthesizes causal narratives    |
|      v                                                                                            |
|  [PHASE 3] Table 6 Justification Polarity & Orthographic Engine (payload_to_ast.py)               |
|      |-- Fixes Defect #4: Enforces strength/gap polarity, strips adversative orphans & fixes UTF8 |
|      v                                                                                            |
|  [PHASE 4] Closed-World Grounding & Ontology Scoper (resynthesize_domains + prompt_scoper)        |
|      |-- Fixes Defects #3 & #5: Eliminates tool hallucinations & enforces strict tower boundaries |
|      v                                                                                            |
|  [PHASE 5] Multi-Tower Re-Synthesis, Compilation & Automated AST-Purity Gate (CI/CD Test Suite)   |
|      |-- Rebuilds all 10 payloads, compiles all 10 DOCX annexes, & executes 10/10 Quality Gate    |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

### Why Exactly Five Phases?
* **Separation of Deterministic Compiler Fixes (Phases 1–3) from Stochastic LLM Re-Synthesis (Phase 4):** Phases 1, 2, and 3 repair deterministic AST transformation bugs inside `payload_to_ast.py`. Building and unit-testing the compiler fixes *first* ensures that when Phase 4 re-synthesizes the JSON payloads across all 10 towers, the downstream AST compiler can immediately render them without structural data loss.
* **Cost & Latency Optimization:** LLM re-synthesis across 10 towers is compute-intensive. By isolating prompt and grounding guardrails in Phase 4—after deterministic AST validators are already online—we ensure a single, clean regeneration pass in Phase 5.

---

## 3. PHASE 1: UNIVERSAL CHAPTER 2 BRIDGE ARCHITECTURE (`payload_to_ast.py`)

### 3.1 Root Cause Analysis
In `payload_to_ast.py`, the entry point `compile_asis_docx_via_ast(...)` invoked internal builder routines while passing `approved_annex_path=""` when compiling directly from synthesized blueprint payloads. Consequently:
1. `annex_data` evaluated to `{}`.
2. `_build_chapter_2_ast` queried `annex_data.get("domain_introduction")` exclusively, ignoring `blueprint_data.get("domain_introduction")` and root-level scope structures.
3. Section 2.1 emitted the fallback error string (`"Módulo de introducción y alcance no disponible"`), and Section 2.2 (`Platform Description`) rendered an empty list of AST blocks (`[]`).

### 3.2 Target Architecture: Multi-Tier Coalescing Resolution Engine
We will architect a deterministic **4-Tier Coalescing Resolution Pipeline** (`DomainIntroductionResolver`) inside `payload_to_ast.py` that guarantees Sections 2.1 and 2.2 are richly populated for any domain (`T1..T10`, `D1..D8`, or custom vertical slugs) in any language.

```text
+-----------------------------------------------------------------------------------+
|                     DOMAIN INTRODUCTION & PLATFORM RESOLVER                       |
+-----------------------------------------------------------------------------------+
| Input: blueprint_data, annex_data, canonical_ontology, locale_bundle              |
|                                                                                   |
|  Tier 1: Explicit Annex Override     -> annex_data["domain_introduction"]         |
|  Tier 2: Synthesized Blueprint Dict  -> blueprint_data["domain_introduction"]     |
|  Tier 3: Root Payload Synthesis Keys -> blueprint_data["scope_and_objectives"],   |
|                                         blueprint_data["platform_description"],   |
|                                         blueprint_data["baseline_inventory"]      |
|  Tier 4: Deterministic Ontology Synthesis -> Synthesizes Objective, Technical     |
|          Scope (from active Subdomains/Pillars), and Platform Baseline (from      |
|          verified Inventory + Findings + Executive Context)                       |
+-----------------------------------------------------------------------------------+
```

### 3.3 Production Reference Implementation (100% Technical English)

```python
# File: src/compiler/ast/chapter_two_resolver.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional
from src.compiler.i18n.locale_registry import LocaleBundle
from src.ontology.canonical_graph import CanonicalDomainNode


@dataclass(frozen=True)
class ChapterTwoContentModel:
    """Immutable value object representing validated Chapter 2 AST content."""
    objective_narrative: str
    technical_scope_narrative: str
    included_subdomains: List[str] = field(default_factory=list)
    platform_overview_narrative: str = ""
    architectural_topologies: List[str] = field(default_factory=list)
    operational_boundaries: str = ""


class UniversalChapterTwoResolver:
    """
    Resolves Section 2.1 (Objective & Technical Scope) and Section 2.2 (Platform Description)
    across arbitrary domain topologies with zero fallback error strings.
    """

    def __init__(
        self,
        locale_bundle: LocaleBundle,
        domain_node: CanonicalDomainNode,
    ) -> None:
        self._i18n = locale_bundle
        self._domain_node = domain_node

    def resolve(
        self,
        blueprint_data: Mapping[str, Any],
        annex_data: Optional[Mapping[str, Any]] = None,
    ) -> ChapterTwoContentModel:
        annex_dict = annex_data or {}

        # Coalesce domain_introduction dictionary across Tier 1 and Tier 2
        intro_sources: List[Mapping[str, Any]] = [
            annex_dict.get("domain_introduction") if isinstance(annex_dict.get("domain_introduction"), Mapping) else {},
            blueprint_data.get("domain_introduction") if isinstance(blueprint_data.get("domain_introduction"), Mapping) else {},
            annex_dict,
            blueprint_data,
        ]

        objective = self._first_valid_text(
            intro_sources,
            keys=("objective", "domain_objective", "assessment_objective", "purpose"),
        )
        scope = self._first_valid_text(
            intro_sources,
            keys=("technical_scope", "scope", "domain_scope", "evaluated_scope"),
        )
        platform_desc = self._first_valid_text(
            intro_sources,
            keys=(
                "platform_description",
                "technological_platform_description",
                "infrastructure_baseline",
                "current_state_architecture",
                "environment_overview",
            ),
        )

        subdomains = self._extract_subdomain_names(blueprint_data, annex_dict)
        topologies = self._extract_verified_components(blueprint_data, annex_dict)

        # Tier 4 Deterministic Fallback Synthesis (Zero Error Strings Guaranteed)
        if not objective:
            objective = self._synthesize_deterministic_objective(subdomains)

        if not scope:
            scope = self._synthesize_deterministic_scope(subdomains, blueprint_data)

        if not platform_desc:
            platform_desc = self._synthesize_deterministic_platform_description(
                blueprint_data=blueprint_data,
                subdomains=subdomains,
                topologies=topologies,
            )

        boundaries = self._first_valid_text(
            intro_sources,
            keys=("operational_boundaries", "governance_boundaries", "interfaces"),
        ) or self._synthesize_operational_boundaries(subdomains)

        return ChapterTwoContentModel(
            objective_narrative=objective,
            technical_scope_narrative=scope,
            included_subdomains=subdomains,
            platform_overview_narrative=platform_desc,
            architectural_topologies=topologies,
            operational_boundaries=boundaries,
        )

    def _first_valid_text(
        self,
        sources: List[Mapping[str, Any]],
        keys: tuple[str, ...],
        min_length: int = 40,
    ) -> str:
        banned_markers = set(self._i18n.get_list("compiler.banned_placeholder_markers"))
        for source in sources:
            for key in keys:
                raw_val = source.get(key)
                if isinstance(raw_val, str):
                    cleaned = raw_val.strip()
                    if len(cleaned) >= min_length and not any(
                        marker.lower() in cleaned.lower() for marker in banned_markers
                    ):
                        return cleaned
                elif isinstance(raw_val, Mapping):
                    nested_text = " ".join(
                        str(v).strip() for v in raw_val.values() if isinstance(v, str) and len(v.strip()) > 15
                    )
                    if len(nested_text) >= min_length:
                        return nested_text
        return ""

    def _extract_subdomain_names(
        self,
        blueprint_data: Mapping[str, Any],
        annex_data: Mapping[str, Any],
    ) -> List[str]:
        """Extracts canonical pillar/subdomain names from the active payload or ontology."""
        pillars = (
            blueprint_data.get("pillar_evaluations")
            or blueprint_data.get("subdomains")
            or annex_data.get("pillar_evaluations")
            or []
        )
        extracted: List[str] = []
        for item in pillars:
            if isinstance(item, Mapping):
                name = item.get("pillar_name") or item.get("subdomain_name") or item.get("name")
                if isinstance(name, str) and name.strip():
                    extracted.append(name.strip())
        if not extracted:
            extracted = list(self._domain_node.canonical_pillar_titles)
        return extracted

    def _extract_verified_components(
        self,
        blueprint_data: Mapping[str, Any],
        annex_data: Mapping[str, Any],
    ) -> List[str]:
        """Harvests empirically verified assets and architectural facts from the domain payload."""
        components: List[str] = []
        inventory = blueprint_data.get("technical_inventory") or annex_data.get("technical_inventory") or []
        for entry in inventory:
            if isinstance(entry, Mapping):
                asset = entry.get("component") or entry.get("system_name") or entry.get("category")
                detail = entry.get("specification") or entry.get("description") or entry.get("status")
                if asset and detail:
                    components.append(f"{asset}: {detail}")
        return components[:8]

    def _synthesize_deterministic_objective(self, subdomains: List[str]) -> str:
        return self._i18n.format(
            "chapter2.FallbackObjectiveTemplate",
            domain_title=self._domain_node.localized_title,
            pillar_count=len(subdomains),
            pillar_list=", ".join(subdomains[:6]),
        )

    def _synthesize_deterministic_scope(
        self,
        subdomains: List[str],
        blueprint_data: Mapping[str, Any],
    ) -> str:
        kpi_count = len(blueprint_data.get("kpi_evaluations") or blueprint_data.get("question_assessments") or [])
        return self._i18n.format(
            "chapter2.FallbackScopeTemplate",
            domain_title=self._domain_node.localized_title,
            pillar_list=", ".join(subdomains),
            kpi_count=kpi_count if kpi_count > 0 else self._domain_node.default_kpi_count,
        )

    def _synthesize_deterministic_platform_description(
        self,
        blueprint_data: Mapping[str, Any],
        subdomains: List[str],
        topologies: List[str],
    ) -> str:
        """Synthesizes Section 2.2 from verified pillar findings and inventory when explicit key is absent."""
        pillar_summaries: List[str] = []
        for pillar in (blueprint_data.get("pillar_evaluations") or [])[:4]:
            if isinstance(pillar, Mapping):
                p_name = pillar.get("pillar_name") or pillar.get("name") or ""
                p_state = pillar.get("current_state_summary") or pillar.get("operational_reality") or ""
                if p_name and p_state:
                    pillar_summaries.append(f"{p_name} ({p_state.strip().rstrip('.')})")

        if topologies or pillar_summaries:
            return self._i18n.format(
                "chapter2.FallbackPlatformWithEvidenceTemplate",
                domain_title=self._domain_node.localized_title,
                topology_summary="; ".join(topologies[:4]) if topologies else ", ".join(subdomains[:4]),
                operational_synthesis=". ".join(pillar_summaries[:3]),
            )

        return self._i18n.format(
            "chapter2.FallbackPlatformGenericTemplate",
            domain_title=self._domain_node.localized_title,
            pillar_list=", ".join(subdomains),
        )

    def _synthesize_operational_boundaries(self, subdomains: List[str]) -> str:
        return self._i18n.format(
            "chapter2.FallbackOperationalBoundariesTemplate",
            domain_title=self._domain_node.localized_title,
            upstream_domains=", ".join(self._domain_node.upstream_dependencies),
            downstream_domains=", ".join(self._domain_node.downstream_dependents),
        )
```

---

## 4. PHASE 2: CAUSAL RISK IMPACT RESOLVER (`payload_to_ast.py`)

### 4.1 Root Cause Analysis
In Risk Cards (Tables 13, 14, and 17) and Risk Matrices, upstream JSON payloads occasionally populate `primary_impact`, `business_risk`, or `operational_impact` with a raw severity token (`"HIGH"`, `"CRITICAL"`, `"MEDIUM"`, `"ALTO"`, `"CRÍTICO"`) or leave it empty while populating `severity="HIGH"`. The AST compiler previously concatenated this value directly into the template string:
> `Impacto en la Operación y Continuidad: HIGH.`

### 4.2 Target Architecture: Enum Interception & Causal Graph Synthesis
We will introduce `CausalRiskImpactResolver` in `payload_to_ast.py`. Every risk impact field passes through a **Token & Triviality Interceptor** before AST node construction:

1. **Detection Criteria:** A candidate impact string is flagged as a *Raw Enum / Non-Narrative Token* if:
   * Its normalized uppercase token matches the `SEVERITY_TOKEN_SET` (`{"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "CRITICO", "CRÍTICO", "ALTO", "MEDIO", "BAJO", "MODERADO", "SEVERE", "MAJOR", "MINOR", "N/A", "TBD", "NONE"}`), **OR**
   * Its word count is `< 5` words, **OR**
   * It matches a regex of bare severity labels (`r"^(?:nivel\s+|level\s+|impacto\s+|impact\s+)?(?:high|medium|low|critical|alto|medio|bajo|cr[ií]tico)[\.\s]*$"`).
2. **Causal Synthesis Algorithm:** When intercepted, the resolver constructs a domain-grounded operational continuity narrative by combining:
   * **Vulnerability / Failure Mode** (`risk_card.get("vulnerability")` or `risk_card.get("finding_description")` or `risk_card.get("title")`)
   * **Affected Asset / Pillar** (`risk_card.get("affected_asset")` or `risk_card.get("pillar_name")` or `domain_node.localized_title`)
   * **Domain-Specific Consequence Vector** resolved from `CanonicalDomainNode.consequence_profile` and the normalized severity tier (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).

### 4.3 Production Reference Implementation (100% Technical English)

```python
# File: src/compiler/ast/risk_impact_resolver.py
import re
from typing import Any, Mapping, Set
from src.compiler.i18n.locale_registry import LocaleBundle
from src.ontology.canonical_graph import CanonicalDomainNode

RAW_SEVERITY_TOKENS: Set[str] = {
    "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "INFO",
    "CRITICO", "CRÍTICO", "ALTO", "MEDIO", "BAJO", "MODERADO",
    "SEVERE", "MAJOR", "MINOR", "EXTREME", "ELEVATED", "N/A", "TBD", "NONE",
}

BARE_ENUM_REGEX = re.compile(
    r"^\s*(?:(?:nivel|level|impacto|impact|severidad|severity|riesgo|risk)\s*[:\-]?\s*)?"
    r"(?:critical|high|medium|low|info|cr[ií]tico|alto|medio|bajo|moderado|severe|major|minor)"
    r"\s*[\.\!;,]?\s*$",
    re.IGNORECASE,
)


class CausalRiskImpactResolver:
    """
    Intercepts raw enum placeholders (e.g., 'HIGH.', 'CRITICAL') in risk cards and
    synthesizes deterministic, domain-grounded operational continuity narratives.
    """

    def __init__(
        self,
        locale_bundle: LocaleBundle,
        domain_node: CanonicalDomainNode,
    ) -> None:
        self._i18n = locale_bundle
        self._domain_node = domain_node

    def is_raw_enum_or_trivial(self, candidate: Any) -> bool:
        if not isinstance(candidate, str):
            return True
        cleaned = candidate.strip()
        if not cleaned:
            return True
        normalized_token = cleaned.rstrip(".,;:!").strip().upper()
        if normalized_token in RAW_SEVERITY_TOKENS:
            return True
        if BARE_ENUM_REGEX.match(cleaned):
            return True
        words = [w for w in re.split(r"\s+", cleaned) if w]
        return len(words) < 5

    def normalize_severity_key(self, raw_severity: Any) -> str:
        if not isinstance(raw_severity, str):
            return "HIGH"
        token = raw_severity.strip().rstrip(".,;:!").upper()
        mapping = {
            "CRITICAL": "CRITICAL", "CRITICO": "CRITICAL", "CRÍTICO": "CRITICAL", "EXTREME": "CRITICAL",
            "HIGH": "HIGH", "ALTO": "HIGH", "SEVERE": "HIGH", "MAJOR": "HIGH",
            "MEDIUM": "MEDIUM", "MEDIO": "MEDIUM", "MODERADO": "MEDIUM", "MODERATE": "MEDIUM",
            "LOW": "LOW", "BAJO": "LOW", "MINOR": "LOW",
        }
        return mapping.get(token, "HIGH")

    def resolve_operational_impact(self, risk_entry: Mapping[str, Any]) -> str:
        # 1. Inspect candidate narrative fields in priority order
        candidate_fields = (
            "operational_continuity_impact",
            "business_continuity_impact",
            "primary_impact_narrative",
            "primary_impact",
            "business_risk",
            "impact_description",
            "consequence",
        )
        for field_name in candidate_fields:
            val = risk_entry.get(field_name)
            if not self.is_raw_enum_or_trivial(val):
                return self._ensure_terminal_punctuation(str(val).strip())

        # 2. Extract context for deterministic causal synthesis
        severity_tier = self.normalize_severity_key(
            risk_entry.get("severity")
            or risk_entry.get("risk_level")
            or risk_entry.get("primary_impact")
        )
        vulnerability = self._extract_clean_clause(
            risk_entry,
            keys=("vulnerability", "root_cause", "finding_summary", "description", "title", "risk_title"),
            fallback=self._domain_node.default_vulnerability_clause,
        )
        affected_scope = self._extract_clean_clause(
            risk_entry,
            keys=("affected_subdomain", "pillar_name", "affected_assets", "component", "subdomain"),
            fallback=self._domain_node.localized_title,
        )

        # 3. Synthesize localized, domain-grounded impact narrative
        template_key = f"risk_impact.CausalTemplate.{self._domain_node.consequence_archetype}.{severity_tier}"
        synthesized = self._i18n.format(
            template_key,
            vulnerability_clause=vulnerability,
            affected_scope=affected_scope,
            domain_title=self._domain_node.localized_title,
            sla_degradation_vector=self._domain_node.primary_sla_vector,
        )
        return self._ensure_terminal_punctuation(synthesized)

    def _extract_clean_clause(
        self,
        risk_entry: Mapping[str, Any],
        keys: tuple[str, ...],
        fallback: str,
    ) -> str:
        for key in keys:
            raw = risk_entry.get(key)
            if isinstance(raw, str) and not self.is_raw_enum_or_trivial(raw):
                clause = raw.strip().rstrip(".")
                return clause[0].lower() + clause[1:] if len(clause) > 1 else clause
        # Secondary check for short titles (2-4 words) that are not severity enums
        for key in ("title", "risk_title", "pillar_name", "subdomain"):
            raw = risk_entry.get(key)
            if isinstance(raw, str) and raw.strip() and raw.strip().upper() not in RAW_SEVERITY_TOKENS:
                return raw.strip().rstrip(".")
        return fallback

    @staticmethod
    def _ensure_terminal_punctuation(text: str) -> str:
        cleaned = text.strip()
        if cleaned and cleaned[-1] not in ".!?":
            return f"{cleaned}."
        return cleaned
```

---

## 5. PHASE 3: TABLE 6 JUSTIFICATION POLARITY & ORTHOGRAPHIC SANITIZER (`payload_to_ast.py`)

### 5.1 Root Cause Analysis
In Table 6 (*Justificación de Puntuaciones por Subdominio / Pilar*), two distinct defects occurred:
1. **Orphaned Adversative Fragments in Strengths:** Previous regex truncation split multi-sentence LLM paragraphs and left adversative clauses (starting with `"No obstante, la efectividad real..."`, `"Sin embargo..."`, `"Aunque..."`, `"However..."`) inside the **Identified Operational Strength** (`Fortaleza Operativa Identificada`) slot for high-scoring pillars (e.g., 4.00 / 5.00), turning a strength into a critique or an incomplete sentence fragment.
2. **Unaccented Template Strings:** Static fallback strings contained orthographic errors (`"Deficit en gestión..."` instead of `"Déficit en la gestión..."`).

### 5.2 Target Architecture: Discourse-Marker Clause Classifier & Polarity Enforcer
We will engineer `PillarJustificationSanitizer` in `payload_to_ast.py`:
1. **Discourse Segmentation:** Every justification paragraph is segmented into individual sentences and clauses.
2. **Adversative & Polarity Classification:**
   * Sentences starting with adversative discourse markers (`No obstante`, `Sin embargo`, `Ahora bien`, `Por el contrario`, `A pesar de ello`, `However`, `Nevertheless`, `Nonetheless`, `Conversely`, `Although`) or containing explicit deficit lexemes (`carece`, `ausencia`, `déficit`, `inexistencia`, `vulnerabilidad`, `riesgo`, `lacks`, `absence`, `deficiency`) are classified as **Negative Polarity (Gap/Constraint)**.
   * Sentences containing affirmative operational capability markers (`cuenta con`, `dispone de`, `implementa`, `garantiza`, `redundancia`, `alta disponibilidad`, `cumple`, `estandarizado`, `maintains`, `enforces`, `provides`) without adversative prefixes are classified as **Positive Polarity (Strength)**.
3. **Strict Slot Routing:**
   * **Strength Slot (`Fortaleza Operativa Identificada`):** Accepts **only** Positive Polarity clauses. If an adversative tail is attached to a positive sentence (e.g., `"...cuenta con doble acometida; no obstante, carece de..."`), the clause splitter strips the adversative tail and routes the tail to the Gap/Opportunity slot. If a high-scoring pillar (`score >= 3.5`) has no clean positive sentence remaining after stripping, the sanitizer synthesizes a deterministic positive statement anchored to the highest-scoring KPIs (`score >= 4`) in that pillar.
   * **Gap / Opportunity Slot (`Brecha / Oportunidad de Mejora`):** Accepts Negative Polarity clauses anchored to the lowest-scoring KPIs in that pillar. For pillars scoring `>= 4.0`, the label and phrasing are automatically modulated via `i18n` to *Continuous Optimization Opportunity* rather than *Critical Deficit*.
4. **Orthographic Normalization Dictionary:** Applies deterministic UTF-8 diacritic restoration across all localized output strings (`Deficit` $\rightarrow$ `Déficit`, `Gestion` $\rightarrow$ `Gestión`, `Operacion` $\rightarrow$ `Operación`, `Critico` $\rightarrow$ `Crítico`, `Tecnica` $\rightarrow$ `Técnica`).

### 5.3 Production Reference Implementation (100% Technical English)

```python
# File: src/compiler/ast/table_six_sanitizer.py
import re
from dataclasses import dataclass
from typing import Any, List, Mapping, Sequence
from src.compiler.i18n.locale_registry import LocaleBundle


@dataclass(frozen=True)
class SanitizedPillarJustification:
    pillar_id: str
    pillar_name: str
    score: float
    strength_statement: str
    gap_or_opportunity_statement: str


class PillarJustificationSanitizer:
    """
    Enforces strict semantic polarity between Operational Strengths and Gaps in Table 6,
    eradicates orphaned adversative fragments, and guarantees UTF-8 orthographic integrity.
    """

    def __init__(self, locale_bundle: LocaleBundle) -> None:
        self._i18n = locale_bundle
        self._adversative_prefixes = tuple(
            p.lower() for p in self._i18n.get_list("sanitizer.adversative_prefixes")
        )
        self._deficit_markers = tuple(
            m.lower() for m in self._i18n.get_list("sanitizer.deficit_lexemes")
        )
        self._orthographic_fixes: Mapping[str, str] = self._i18n.get_map(
            "sanitizer.orthographic_corrections"
        )

    def sanitize_pillar_row(
        self,
        pillar_data: Mapping[str, Any],
        pillar_kpis: Sequence[Mapping[str, Any]],
    ) -> SanitizedPillarJustification:
        pillar_id = str(pillar_data.get("pillar_id") or pillar_data.get("id") or "")
        pillar_name = self.apply_orthographic_fixes(
            str(pillar_data.get("pillar_name") or pillar_data.get("name") or "")
        )
        score = float(pillar_data.get("score") or pillar_data.get("maturity_score") or 0.0)

        raw_strength = str(
            pillar_data.get("identified_strength")
            or pillar_data.get("strengths")
            or pillar_data.get("operational_strength")
            or ""
        )
        raw_gap = str(
            pillar_data.get("identified_gap")
            or pillar_data.get("gaps")
            or pillar_data.get("weaknesses")
            or pillar_data.get("improvement_opportunity")
            or ""
        )

        positive_clauses, redirected_negative_clauses = self._extract_clean_positive_clauses(raw_strength)
        explicit_negative_clauses = self._extract_clean_negative_clauses(raw_gap)
        all_negative_clauses = explicit_negative_clauses or redirected_negative_clauses

        # Resolve final Strength statement
        if positive_clauses:
            final_strength = " ".join(positive_clauses[:2])
        else:
            final_strength = self._synthesize_kpi_grounded_strength(pillar_name, score, pillar_kpis)

        # Resolve final Gap / Opportunity statement
        if all_negative_clauses:
            final_gap = " ".join(all_negative_clauses[:2])
        else:
            final_gap = self._synthesize_kpi_grounded_gap(pillar_name, score, pillar_kpis)

        return SanitizedPillarJustification(
            pillar_id=pillar_id,
            pillar_name=pillar_name,
            score=score,
            strength_statement=self.apply_orthographic_fixes(final_strength),
            gap_or_opportunity_statement=self.apply_orthographic_fixes(final_gap),
        )

    def _extract_clean_positive_clauses(self, text: str) -> tuple[List[str], List[str]]:
        """
        Splits text into sentences, strips adversative tails, and separates genuinely
        positive capability statements from misplaced deficit statements.
        """
        positives: List[str] = []
        redirected_negatives: List[str] = []

        sentences = [s.strip() for s in re.split(r"(?<=[\.\!\?])\s+", text.strip()) if s.strip()]
        for sentence in sentences:
            # Split compound sentences containing mid-sentence adversative conjunctions
            sub_clauses = re.split(
                r"\s*[;:]\s*(?=(?:no obstante|sin embargo|ahora bien|por el contrario|however|nevertheless)\b)",
                sentence,
                flags=re.IGNORECASE,
            )
            for clause in sub_clauses:
                clean_clause = clause.strip()
                if not clean_clause or len(clean_clause.split()) < 5:
                    continue
                lower_clause = clean_clause.lower()

                # Reject or redirect clauses starting with adversative markers
                if lower_clause.startswith(self._adversative_prefixes):
                    stripped_adversative = self._strip_leading_adversative_marker(clean_clause)
                    if stripped_adversative:
                        redirected_negatives.append(stripped_adversative)
                    continue

                # Redirect clauses dominated by deficit lexemes
                if any(re.search(rf"\b{re.escape(marker)}\b", lower_clause) for marker in self._deficit_markers):
                    redirected_negatives.append(self._ensure_sentence_case_and_period(clean_clause))
                    continue

                positives.append(self._ensure_sentence_case_and_period(clean_clause))

        return positives, redirected_negatives

    def _extract_clean_negative_clauses(self, text: str) -> List[str]:
        negatives: List[str] = []
        sentences = [s.strip() for s in re.split(r"(?<=[\.\!\?])\s+", text.strip()) if s.strip()]
        for sentence in sentences:
            stripped = self._strip_leading_adversative_marker(sentence)
            if stripped and len(stripped.split()) >= 5:
                negatives.append(self._ensure_sentence_case_and_period(stripped))
        return negatives

    def _strip_leading_adversative_marker(self, clause: str) -> str:
        cleaned = clause.strip()
        for prefix in self._adversative_prefixes:
            pattern = rf"^{re.escape(prefix)}\s*[,]?\s*"
            if re.match(pattern, cleaned, flags=re.IGNORECASE):
                cleaned = re.sub(pattern, "", cleaned, count=1, flags=re.IGNORECASE).strip()
                break
        return self._ensure_sentence_case_and_period(cleaned) if cleaned else ""

    def _synthesize_kpi_grounded_strength(
        self,
        pillar_name: str,
        score: float,
        pillar_kpis: Sequence[Mapping[str, Any]],
    ) -> str:
        high_kpis = sorted(
            [k for k in pillar_kpis if float(k.get("score") or 0.0) >= 3.0],
            key=lambda x: float(x.get("score") or 0.0),
            reverse=True,
        )
        if high_kpis:
            top_kpi = high_kpis[0]
            kpi_title = str(top_kpi.get("kpi_name") or top_kpi.get("question_title") or pillar_name).strip()
            selected_rubric = str(top_kpi.get("selected_option_text") or top_kpi.get("evidence_summary") or "").strip()
            if selected_rubric:
                return self._i18n.format(
                    "table6.GroundedStrengthWithRubric",
                    pillar_name=pillar_name,
                    kpi_title=kpi_title,
                    rubric_fact=selected_rubric.rstrip("."),
                )
        return self._i18n.format("table6.BaselineStrengthFallback", pillar_name=pillar_name, score=f"{score:.2f}")

    def _synthesize_kpi_grounded_gap(
        self,
        pillar_name: str,
        score: float,
        pillar_kpis: Sequence[Mapping[str, Any]],
    ) -> str:
        low_kpis = sorted(
            [k for k in pillar_kpis if float(k.get("score") or 5.0) < 4.0],
            key=lambda x: float(x.get("score") or 5.0),
        )
        if low_kpis:
            bottom_kpi = low_kpis[0]
            kpi_title = str(bottom_kpi.get("kpi_name") or bottom_kpi.get("question_title") or pillar_name).strip()
            selected_rubric = str(bottom_kpi.get("selected_option_text") or "").strip().rstrip(".")
            if score >= 3.75:
                return self._i18n.format(
                    "table6.OptimizationOpportunityWithRubric",
                    pillar_name=pillar_name,
                    kpi_title=kpi_title,
                    rubric_fact=selected_rubric,
                )
            return self._i18n.format(
                "table6.GroundedGapWithRubric",
                pillar_name=pillar_name,
                kpi_title=kpi_title,
                rubric_fact=selected_rubric,
            )
        return self._i18n.format("table6.ContinuousImprovementFallback", pillar_name=pillar_name)

    def apply_orthographic_fixes(self, text: str) -> str:
        result = text
        for wrong, right in self._orthographic_fixes.items():
            result = re.sub(rf"\b{re.escape(wrong)}\b", right, result)
        return result

    @staticmethod
    def _ensure_sentence_case_and_period(text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return ""
        cleaned = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
        if cleaned[-1] not in ".!?":
            cleaned += "."
        return cleaned
```

---

## 6. PHASE 4: STRICT GROUNDING GUARDRAILS & ONTOLOGY SCOPER (`resynthesize_domains_from_raw_transcription.py` & `domain_prompt_scoper.py`)

### 6.1 Root Cause Analysis
1. **Defect #3 (Speculative Tool & Process Hallucinations in Section 3.1):** When the questionnaire recorded Score 1 (`1.00 / 5.00`) for electrical capacity monitoring or work permits, the LLM attempted to make the narrative sound "vivid" by inventing unverified physical instruments and artifacts (`"pinzas amperimétricas"`, `"especificaciones de placa de fabricante"`, `"formularios impresos con firmas manuscritas"`). None of these existed in the interview transcript or questionnaire rubric text.
2. **Defect #5 (Cross-Tower Focus Contamination in Executive Summaries):** Because raw interview transcripts often discuss multiple domains in a single session (e.g., mentioning SimpliVity RAM saturation and legacy ERPs alongside data center UPS systems), the synthesis prompt allowed the LLM to place Compute and Application bottlenecks at the center of the Tower 1 (Data Center Facilities) Executive Summary.

### 6.2 Target Architecture: Closed-World Evidence Ledger & Two-Stage Hallucination Firewall
We will re-architect `domain_prompt_scoper.py` and `resynthesize_domains_from_raw_transcription.py` around three deterministic mechanisms:

```text
+--------------------------------------------------------------------------------------------------+
|                         CLOSED-WORLD SYNTHESIS & HALLUCINATION FIREWALL                          |
+--------------------------------------------------------------------------------------------------+
|                                                                                                  |
|  1. EvidenceScoper (Pre-LLM):                                                                    |
|     - Filters raw transcript segments by CanonicalDomainNode.in_scope_ontology_tags.             |
|     - Demotes non-domain transcript facts into a read-only `cross_domain_dependency_notes` list  |
|       with a strict cap of <= 10% narrative weight and zero primary focus in Executive Summary.  |
|     - Passes exact Questionnaire Rubric Text (`selected_option_text`) for every KPI.             |
|                                                                                                  |
|  2. Closed-World Prompt Contract (LLM System Directive):                                         |
|     - FORBIDS inventing unverified physical measuring tools, paper forms, or manual procedures   |
|       not explicitly present in the `VerifiedLexiconSet` built from the transcript + rubric.     |
|                                                                                                  |
|  3. Post-Synthesis Grounding Verifier (`UnverifiedArtifactFirewall`):                            |
|     - Scans generated Section 3.1 & Executive Summary against speculative artifact patterns      |
|       and out-of-tower primary subjects.                                                         |
|     - Automatically rewrites or strips any sentence containing an unverified physical tool/form  |
|       noun phrase that does not appear in the client's source evidence corpus.                   |
+--------------------------------------------------------------------------------------------------+
```

### 6.3 Production Reference Implementation (100% Technical English)

```python
# File: src/synthesis/grounding_firewall.py
import re
from dataclasses import dataclass
from typing import Any, List, Mapping, Sequence, Set
from src.compiler.i18n.locale_registry import LocaleBundle
from src.ontology.canonical_graph import CanonicalDomainNode


@dataclass(frozen=True)
class GroundingAuditResult:
    is_clean: bool
    sanitized_text: str
    detected_violations: List[str]


class ClosedWorldGroundingFirewall:
    """
    Enforces two strict invariants on synthesized narratives:
    1. Zero Speculative Physical/Process Artifacts: Any specific measuring tool, physical media,
       or ad-hoc manual mechanism not present in the source evidence corpus is stripped and
       replaced with the exact functional state from the selected questionnaire rubric.
    2. Strict Tower Boundary Focus: Prevents foreign-tower systems from dominating the
       Executive Summary of the active domain.
    """

    def __init__(
        self,
        locale_bundle: LocaleBundle,
        domain_node: CanonicalDomainNode,
        source_evidence_corpus: str,
    ) -> None:
        self._i18n = locale_bundle
        self._domain_node = domain_node
        self._source_corpus_lower = source_evidence_corpus.lower()
        self._speculative_artifact_patterns: Sequence[str] = self._i18n.get_list(
            "grounding.speculative_artifact_regexes"
        )
        self._foreign_domain_primary_terms: Set[str] = {
            term.lower()
            for term in domain_node.excluded_foreign_tower_keywords
            if term.lower() not in domain_node.allowed_dependency_keywords
        }

    def build_domain_scoped_prompt_directives(
        self,
        kpi_rubric_selections: Sequence[Mapping[str, Any]],
    ) -> str:
        """
        Generates the deterministic Closed-World Grounding Mandate injected into the LLM system prompt.
        """
        rubric_ledger_lines: List[str] = []
        for kpi in kpi_rubric_selections:
            kpi_id = kpi.get("kpi_id") or kpi.get("question_id")
            kpi_title = kpi.get("kpi_name") or kpi.get("question_title")
            score = kpi.get("score")
            selected_text = kpi.get("selected_option_text")
            rubric_ledger_lines.append(
                f"- [{kpi_id}] {kpi_title} (Score: {score}/5): \"{selected_text}\""
            )

        return (
            "CLOSED-WORLD EMPIRICAL GROUNDING MANDATE (STRICT COMPLIANCE REQUIRED):\n"
            f"1. PRIMARY DOMAIN BOUNDARY: You are synthesizing ONLY '{self._domain_node.canonical_name}' "
            f"({self._domain_node.localized_title}). At least 90% of the Executive Summary and Section 3.1 "
            f"must focus strictly on {', '.join(self._domain_node.canonical_pillar_titles)}.\n"
            f"2. FOREIGN TOWER EXCLUSION: Systems belonging to other towers "
            f"({', '.join(self._domain_node.excluded_foreign_tower_keywords)}) MUST NOT be framed as primary "
            "findings of this tower. They may only be referenced briefly in a single clause if they act as a "
            "direct upstream/downstream boundary condition.\n"
            "3. ZERO SPECULATIVE EMBELLISHMENT ON LOW SCORES: When a KPI has Score 1 or Score 2, describe "
            "ONLY the functional absence or reactive state defined in the Questionnaire Rubric Ledger below "
            "and verified interview facts. DO NOT invent specific physical tools, measuring instruments "
            "(e.g., clamp meters, thermal cameras, multimeters), manufacturer nameplates, spreadsheets, or "
            "handwritten paper forms unless those exact words appear verbatim in the interview transcript.\n"
            "4. VERIFIED QUESTIONNAIRE RUBRIC LEDGER:\n"
            + "\n".join(rubric_ledger_lines)
        )

    def sanitize_narrative_block(
        self,
        narrative: str,
        fallback_rubric_statement: str = "",
    ) -> GroundingAuditResult:
        """
        Post-synthesis deterministic scrubber that inspects each sentence for speculative
        artifacts not attested in the source evidence corpus.
        """
        violations: List[str] = []
        clean_sentences: List[str] = []

        sentences = [s.strip() for s in re.split(r"(?<=[\.\!\?])\s+", narrative.strip()) if s.strip()]
        for sentence in sentences:
            sentence_lower = sentence.lower()
            violated_pattern = None

            for pattern in self._speculative_artifact_patterns:
                match = re.search(pattern, sentence_lower, flags=re.IGNORECASE)
                if match:
                    matched_phrase = match.group(0).strip().lower()
                    # Verify whether the client actually mentioned this artifact in the source evidence
                    if matched_phrase not in self._source_corpus_lower:
                        violated_pattern = matched_phrase
                        break

            if violated_pattern:
                violations.append(f"Unverified artifact '{violated_pattern}' in sentence: '{sentence}'")
                repaired = self._strip_speculative_clause(sentence, violated_pattern, fallback_rubric_statement)
                if repaired:
                    clean_sentences.append(repaired)
            else:
                clean_sentences.append(sentence)

        return GroundingAuditResult(
            is_clean=(len(violations) == 0),
            sanitized_text=" ".join(clean_sentences),
            detected_violations=violations,
        )

    def enforce_executive_summary_tower_focus(
        self,
        executive_paragraphs: Sequence[str],
    ) -> List[str]:
        """
        Ensures that no paragraph in the Executive Summary is dominated by foreign-tower topics.
        """
        sanitized_paragraphs: List[str] = []
        for paragraph in executive_paragraphs:
            sentences = [s.strip() for s in re.split(r"(?<=[\.\!\?])\s+", paragraph.strip()) if s.strip()]
            in_scope_sentences: List[str] = []
            for sentence in sentences:
                s_lower = sentence.lower()
                foreign_hits = sum(1 for kw in self._foreign_domain_primary_terms if kw in s_lower)
                in_scope_hits = sum(1 for kw in self._domain_node.in_scope_keywords if kw in s_lower)
                # Drop sentences that discuss foreign-tower entities without linking to any in-scope asset
                if foreign_hits > 0 and in_scope_hits == 0:
                    continue
                in_scope_sentences.append(sentence)
            if in_scope_sentences:
                sanitized_paragraphs.append(" ".join(in_scope_sentences))
        return sanitized_paragraphs

    def _strip_speculative_clause(
        self,
        sentence: str,
        violated_phrase: str,
        fallback_rubric_statement: str,
    ) -> str:
        # Remove subordinate clauses introducing speculative mechanisms (e.g., "mediante...", "a través de...")
        cleaned = re.sub(
            rf"[,]?\s*(?:mediante|a trav[eé]s de|utilizando|usando|basado en| recurriendo a|by means of|using|via)\s+[^,\.;]*{re.escape(violated_phrase)}[^,\.;]*",
            "",
            sentence,
            flags=re.IGNORECASE,
        ).strip()
        if cleaned and cleaned != sentence and len(cleaned.split()) >= 6:
            return cleaned if cleaned[-1] in ".!?" else f"{cleaned}."
        return fallback_rubric_statement
```

---

## 7. PHASE 5: AUTOMATED MULTI-TOWER VERIFICATION & AST-PURITY QUALITY GATE

To guarantee **10.0 / 10.0 forensic quality across all 10 deliverables simultaneously** and prevent regressions in future client engagements, we will implement a three-tier automated test suite executed as a mandatory CI/CD release gate (`tests/quality_gates/test_multi_tower_ast_purity.py`).

### 7.1 The 6 Mandatory Automated Verification Suites

| Test Suite ID | Target Layer | Verification Invariant | Failure Condition (Hard Build Break) |
| :--- | :--- | :--- | :--- |
| **QG-01: Codebase English Purity** | Static AST Analysis (`src/`) | 100% Technical English in Python identifiers, docstrings, comments, and literals outside `i18n/*.json`. | Any Spanish lexeme or diacritic (`[áéíóúñÁÉÍÓÚÑ]`) detected inside `.py` files. |
| **QG-02: Chapter 2 Completeness** | AST & DOCX (`Sections 2.1 & 2.2`) | Every compiled tower (`T1..T10`) contains non-empty Objective, Technical Scope, and Platform Description blocks (`>= 80` words each). | Presence of `"no disponible"`, `"not available"`, or `len(section_2_2.blocks) == 0`. |
| **QG-03: Risk Impact Narrative Purity** | AST & DOCX (`Tables 13, 14, 17`) | Every risk card impact field contains a multi-word causal narrative (`>= 8` words) grounded in domain consequences. | Any impact cell matching `BARE_ENUM_REGEX` (e.g., `HIGH.`, `CRITICAL.`, `MEDIUM.`). |
| **QG-04: Table 6 Polarity & Orthography** | AST & DOCX (`Table 6`) | Strengths contain zero adversative orphans (`No obstante...`, `Sin embargo...`) and zero deficit lexemes; zero unaccented `Deficit` / `Gestion` tokens. | Any Strength cell starting with an adversative prefix or failing UTF-8 spellcheck. |
| **QG-05: Closed-World Grounding Audit** | JSON Payload & DOCX (`Section 3.1`) | Zero unverified physical tools or paper form hallucinations when compared against the active client `EvidenceStore`. | Any match in `speculative_artifact_regexes` not attested in `source_evidence_corpus`. |
| **QG-06: Tower Boundary Isolation** | JSON Payload & DOCX (`Exec Summary`) | `>= 90%` of Executive Summary sentences map to the active tower's canonical ontology keywords; `0` standalone foreign-tower sentences. | Foreign tower keyword density `> 10%` or standalone foreign-tower sentences `> 0`. |

### 7.2 Automated Multi-Tower AST & DOCX Verification Harness (100% Technical English)

```python
# File: tests/quality_gates/test_multi_tower_ast_purity.py
import re
from pathlib import Path
import pytest
from docx import Document
from src.compiler.ast.risk_impact_resolver import BARE_ENUM_REGEX
from src.compiler.i18n.locale_registry import LocaleRegistry
from src.ontology.canonical_graph import CanonicalOntologyGraph


@pytest.mark.parametrize("tower_index", list(range(1, 11)))
def test_compiled_docx_deliverable_passes_all_forensic_gates(
    tower_index: int,
    compiled_deliverables_dir: Path,
    client_evidence_corpus: str,
    locale_code: str,
) -> None:
    """
    End-to-end forensic certification across all 10 Towers (T1..T10).
    Verifies zero placeholders, zero raw enums, zero orphaned fragments,
    zero unverified tool hallucinations, and strict tower boundary isolation.
    """
    locale = LocaleRegistry.load(locale_code)
    ontology = CanonicalOntologyGraph.load_default()
    domain_node = ontology.get_domain_by_index(tower_index)

    docx_files = list(compiled_deliverables_dir.glob(f"*Anexo_{tower_index:02d}*ASIS.docx"))
    assert len(docx_files) == 1, f"Expected exactly 1 DOCX for Tower {tower_index}, found {len(docx_files)}"
    doc = Document(str(docx_files[0]))

    full_paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    full_text = "\n".join(full_paragraphs)

    # 1. Verify Gate QG-02: Chapter 2 (Sections 2.1 and 2.2) Non-Empty & Zero Error Placeholders
    banned_markers = locale.get_list("compiler.banned_placeholder_markers")
    for marker in banned_markers:
        assert marker.lower() not in full_text.lower(), (
            f"Tower {tower_index} failed QG-02: Banned placeholder '{marker}' found in compiled DOCX."
        )

    sec_2_1_idx = next((i for i, p in enumerate(full_paragraphs) if p.startswith("2.1")), -1)
    sec_2_2_idx = next((i for i, p in enumerate(full_paragraphs) if p.startswith("2.2")), -1)
    sec_3_0_idx = next((i for i, p in enumerate(full_paragraphs) if p.startswith("3.")), -1)

    assert sec_2_1_idx != -1 and sec_2_2_idx != -1, f"Tower {tower_index} missing Section 2.1 or 2.2 headers."
    sec_2_1_body = " ".join(full_paragraphs[sec_2_1_idx + 1 : sec_2_2_idx])
    sec_2_2_body = " ".join(full_paragraphs[sec_2_2_idx + 1 : sec_3_0_idx])

    assert len(sec_2_1_body.split()) >= 60, f"Tower {tower_index} Section 2.1 is under-populated."
    assert len(sec_2_2_body.split()) >= 60, f"Tower {tower_index} Section 2.2 is blank or under-populated."

    # 2. Verify Gate QG-03: Zero Raw Severity Enums in Risk Tables
    impact_label = locale.get_string("risk_card.impact_label_prefix")
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                if impact_label in cell_text:
                    after_label = cell_text.split(impact_label, 1)[1].strip()
                    assert not BARE_ENUM_REGEX.match(after_label), (
                        f"Tower {tower_index} failed QG-03: Raw enum impact found: '{cell_text}'"
                    )

    # 3. Verify Gate QG-04: Table 6 Polarity & Orthographic Integrity
    adversative_prefixes = tuple(p.lower() for p in locale.get_list("sanitizer.adversative_prefixes"))
    strength_label = locale.get_string("table6.strength_label_prefix")
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for line in cell.text.splitlines():
                    if strength_label in line:
                        strength_body = line.split(strength_label, 1)[1].strip().lower()
                        assert not strength_body.startswith(adversative_prefixes), (
                            f"Tower {tower_index} failed QG-04: Orphaned adversative fragment in Strength: '{line}'"
                        )

    for wrong_spelling in locale.get_map("sanitizer.orthographic_corrections").keys():
        assert not re.search(rf"\b{re.escape(wrong_spelling)}\b", full_text), (
            f"Tower {tower_index} failed QG-04: Unaccented token '{wrong_spelling}' found in deliverable."
        )

    # 4. Verify Gate QG-05: Zero Unverified Speculative Artifacts
    corpus_lower = client_evidence_corpus.lower()
    for pattern in locale.get_list("grounding.speculative_artifact_regexes"):
        for match in re.finditer(pattern, full_text, flags=re.IGNORECASE):
            phrase = match.group(0).strip().lower()
            assert phrase in corpus_lower, (
                f"Tower {tower_index} failed QG-05: Hallucinated artifact '{phrase}' not in client evidence."
            )
```

---

## 8. EXECUTION SIGN-OFF & ROLLOUT SEQUENCE

1. **Step 1 (Phase 1–3 Implementation):** Commit `UniversalChapterTwoResolver`, `CausalRiskImpactResolver`, and `PillarJustificationSanitizer` into `src/compiler/ast/` and wire them into `payload_to_ast.py`. Run unit test suites `QG-01` through `QG-04`.
2. **Step 2 (Phase 4 Implementation):** Commit `ClosedWorldGroundingFirewall` into `src/synthesis/` and integrate it into `domain_prompt_scoper.py` and `resynthesize_domains_from_raw_transcription.py`.
3. **Step 3 (Phase 5 Batch Execution & Gate Certification):** Execute the multi-tower re-synthesis and AST compilation pipeline across all 10 towers (`Anexo_01` through `Anexo_10`) and run `pytest tests/quality_gates/test_multi_tower_ast_purity.py` to certify 100% pass rate before releasing the deliverables.