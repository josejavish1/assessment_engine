"""Ontological Prompt Scoper Domain Service (Phase 6).

Dynamically compiles strict ontological boundary directives and official KPI rubrics
into LLM synthesis prompts, preventing cross-pillar semantic drift and topic contamination
at the point of generative inception.
Strictly 100% Technical English, zero hardcoding, multi-tenant and topology-agnostic.
"""

from __future__ import annotations

import logging
import re
from typing import Any, List, Mapping, Sequence, Set

from assessment_engine.domain.ontology.models import (
    PillarOntologyProfile,
    TaxonomyRegistryPort,
)

logger = logging.getLogger(__name__)

DEFAULT_MAX_FORBIDDEN_TERMS_PER_PILLAR: int = 12

_MARKDOWN_PREFIX_RE = re.compile(r"^(?:\s*(?:#+\s*|[\*\->+]\s+|[`~|]+\s*))+")
_UNSAFE_DELIMITERS_RE = re.compile(r"[`\[\]\<\>\x00-\x1f\x7f]+")


def _sanitize_prompt_fragment(raw: Any) -> str:
    """Sanitizes text by stripping markdown prefixes, control characters, and line breaks

    without corrupting signed technical notation (e.g., -48V DC, *nix).
    """
    if raw is None:
        return ""
    text = str(raw).strip()
    if not text:
        return ""
    lines = [
        _MARKDOWN_PREFIX_RE.sub("", line).strip()
        for line in re.split(r"[\r\n]+", text)
    ]
    flattened = " ".join(line for line in lines if line)
    clean = _UNSAFE_DELIMITERS_RE.sub("", flattened)
    return " ".join(clean.split())


# Public API alias
sanitize_prompt_injected_claim = _sanitize_prompt_fragment


def _canonicalize_pillar_id(raw_p_id: str, norm_tower_id: str) -> str:
    """Canonicalizes a pillar ID, respecting pre-qualified delimiters (., :, -) without duplication."""
    if not raw_p_id:
        return ""
    clean_raw = str(raw_p_id).strip().upper()
    clean_tower = str(norm_tower_id or "").strip().upper()

    if not clean_tower or clean_raw == clean_tower:
        return clean_raw

    for sep in (".", ":", "-"):
        if clean_raw.startswith(f"{clean_tower}{sep}"):
            return clean_raw

    return f"{clean_tower}.{clean_raw}"


class OntologicalPromptScoper:
    """Constructs prompt boundary constraints and KPI scoping directives

    for arbitrary enterprise domain topologies and industry verticals.
    """

    def __init__(self, taxonomy_registry: TaxonomyRegistryPort) -> None:
        self._registry = taxonomy_registry

    @staticmethod
    def _select_balanced_forbidden_terms(
        negative_exclusion_map: Mapping[str, Set[str] | Sequence[str]],
        max_terms: int,
    ) -> List[str]:
        """Selects up to `max_terms` unique forbidden concepts using deterministic

        round-robin sampling across all foreign domains to prevent alphabetical starvation.
        """
        if max_terms <= 0 or not isinstance(negative_exclusion_map, Mapping) or not negative_exclusion_map:
            return []

        sorted_domains = sorted(
            negative_exclusion_map.keys(),
            key=lambda x: (str(x).strip().lower(), str(x).strip()),
        )
        domain_queues: List[List[str]] = []

        for dom in sorted_domains:
            raw_terms = negative_exclusion_map.get(dom)
            if not raw_terms:
                continue
            if isinstance(raw_terms, (str, bytes)):
                iterable_terms: Sequence[Any] = (raw_terms,)
            elif isinstance(raw_terms, (Set, Sequence)):
                iterable_terms = tuple(raw_terms)
            else:
                continue

            seen_dom: Set[str] = set()
            cleaned: List[str] = []
            sorted_candidates = sorted(
                (str(term).strip() for term in iterable_terms if term is not None and str(term).strip()),
                key=lambda x: (x.lower(), x),
            )
            for t in sorted_candidates:
                t_clean = _sanitize_prompt_fragment(t).replace("'", "")
                t_lower = t_clean.lower()
                if t_clean and t_lower not in seen_dom:
                    seen_dom.add(t_lower)
                    cleaned.append(t_clean)
            if cleaned:
                domain_queues.append(cleaned)

        if not domain_queues:
            return []

        selected: List[str] = []
        seen: Set[str] = set()
        idx = 0

        while len(selected) < max_terms:
            progressed = False
            for queue in domain_queues:
                if idx < len(queue):
                    progressed = True
                    candidate = queue[idx]
                    candidate_lower = candidate.lower()
                    if candidate_lower not in seen:
                        seen.add(candidate_lower)
                        selected.append(candidate)
                        if len(selected) >= max_terms:
                            break
            if not progressed:
                break
            idx += 1

        return selected

    @staticmethod
    def _extract_kpi_line(kpi_entry: Any) -> str:
        """Extracts a sanitized, normalized KPI rubric line from heterogeneous schema formats."""
        if isinstance(kpi_entry, str):
            clean_str = _sanitize_prompt_fragment(kpi_entry)
            return f"    * {clean_str}" if clean_str else ""

        if not isinstance(kpi_entry, Mapping):
            return ""

        k_id = _sanitize_prompt_fragment(
            kpi_entry.get("kpi_id")
            or kpi_entry.get("id")
            or kpi_entry.get("code")
            or ""
        )
        k_name = _sanitize_prompt_fragment(
            kpi_entry.get("kpi_name")
            or kpi_entry.get("name")
            or kpi_entry.get("title")
            or ""
        )
        k_desc = _sanitize_prompt_fragment(
            kpi_entry.get("description")
            or kpi_entry.get("rubric")
            or kpi_entry.get("criteria")
            or ""
        )

        if k_id and k_name:
            header = f"{k_id}: {k_name}"
        elif k_name:
            header = k_name
        elif k_id:
            header = k_id
        else:
            return ""

        if k_desc:
            return f"    * {header} ({k_desc})"
        return f"    * {header}"

    def _build_isolation_invariant(
        self,
        canonical_p_id: str,
        pillar_label: str,
        profile: PillarOntologyProfile | None,
    ) -> str:
        """Builds a vertical-agnostic isolation invariant dynamically tailored to the ontology."""
        foreign_domains: List[str] = []
        if profile and getattr(profile, "negative_exclusion_map", None):
            foreign_domains = sorted(
                {
                    _sanitize_prompt_fragment(d)
                    for d in profile.negative_exclusion_map.keys()
                    if _sanitize_prompt_fragment(d)
                },
                key=lambda x: (x.lower(), x),
            )

        if foreign_domains:
            foreign_list_str = ", ".join(foreign_domains)
            return (
                f"  - ISOLATION INVARIANT: All findings for [{canonical_p_id}] must strictly "
                f"relate to {pillar_label}. Never cross-contaminate with foreign domains "
                f"({foreign_list_str}) unless specifically mandated by its assigned KPIs.\n"
            )

        return (
            f"  - ISOLATION INVARIANT: All findings for [{canonical_p_id}] must strictly "
            f"relate to {pillar_label} and its assigned KPIs. Never cross-contaminate with "
            "unrelated architectural or operational domains.\n"
        )

    def build_closed_world_grounding_directive(
        self,
        client_name: str,
        domain_name: str,
    ) -> str:
        """Compiles strict epistemic closed-world grounding instructions forbidding ungrounded tools and embellishments."""
        clean_client = _sanitize_prompt_fragment(client_name) or "the enterprise"
        clean_domain = _sanitize_prompt_fragment(domain_name) or "the target infrastructure domain"

        return (
            "### CLOSED-WORLD EPISTEMIC GROUNDING MANDATE (ZERO UNGROUNDED EMBELLISHMENTS):\n"
            f"1. STRICT GROUNDING IN EVALUATION DIMENSIONS:\n"
            f"   All technical observations, diagnosed breaches, and architectural descriptions for {clean_client}'s {clean_domain} "
            "MUST derive strictly from verified facts in the evidence corpus and the client's explicit questionnaire answers.\n"
            "2. PROHIBITION OF INVENTED INSTRUMENTATION OR MEASURING TOOLS:\n"
            "   If a KPI or control evaluates to a low maturity level (Level 1 or Level 2), you are strictly FORBIDDEN from inventing "
            "hypothetical measurement instruments (e.g. claiming staff performs ad-hoc measurements with clamp meters, handheld thermal cameras, "
            "multimeters, or physical logbooks) unless explicitly recorded in the interview transcript.\n"
            "3. PROHIBITION OF INVENTED MANUAL PROCEDURES:\n"
            "   If the client selected 'no formal control' or 'not tracked', report the gap as the factual absence of the control. "
            "DO NOT invent that tasks are tracked via paper forms, handwritten signatures, physical binders, or informal spreadsheets "
            "unless explicitly stated in the primary source text.\n"
            "4. FACTUAL CAUSALITY IN RESILIENCE BREACHES:\n"
            "   Every diagnosed breach must state the direct business and operational exposure arising from the missing control, "
            "without exaggerating or manufacturing fictional operational rituals.\n"
        )

    def build_executive_summary_scoping_directive(
        self,
        tower_id: str,
        tower_name: str,
        domain_archetype: str,
    ) -> str:
        """Compiles strict executive summary scoping instructions enforcing primary domain headline isolation."""
        clean_tower_id = _sanitize_prompt_fragment(tower_id).upper() or "DOMAIN"
        clean_tower_name = _sanitize_prompt_fragment(tower_name) or "Target Infrastructure"
        clean_archetype = _sanitize_prompt_fragment(domain_archetype) or "ENTERPRISE_SYSTEMS"

        return (
            f"### EXECUTIVE SUMMARY SCOPING & DOMAIN ISOLATION MANDATE FOR [{clean_tower_id}]:\n"
            f"1. PRIMARY DOMAIN HEADLINE:\n"
            f"   The Executive Summary for [{clean_tower_id}: {clean_tower_name}] must maintain 100% of its spotlight on the core capabilities, "
            f"infrastructure assets, and risks belonging to the [{clean_archetype}] domain perimeter.\n"
            "2. CROSS-DOMAIN DEPENDENCIES AS SECONDARY CONTEXT ONLY:\n"
            "   You may reference platforms from other technical domains (such as virtual machine hypervisors, databases, or enterprise applications) "
            f"SOLELY as downstream consumers or upstream dependencies (e.g., as workloads driving physical power and cooling requirements). "
            f"You are strictly FORBIDDEN from making foreign domain issues the primary headline risk of [{clean_tower_id}].\n"
            "3. STRATEGIC BOTTOM LINE:\n"
            f"   The executive bottom line must synthesize the operational posture, single points of failure, and actionable priorities "
            f"specifically within the [{clean_tower_name}] perimeter.\n"
        )

    def build_pillar_scoping_directive(
        self,
        tower_id: str,
        tower_definition: Mapping[str, Any],
        max_forbidden_terms_per_pillar: int = DEFAULT_MAX_FORBIDDEN_TERMS_PER_PILLAR,
        questionnaire_answers: Optional[Mapping[str, Any]] = None,
        score_scale_max: Optional[int] = 5,
    ) -> str:
        """Compiles a deterministic, structured Markdown directive constraining the LLM

        to the official pillars, evaluated KPIs, and negative foreign exclusions of the target domain.
        """
        if not isinstance(tower_definition, Mapping):
            return ""

        norm_tower_id = (
            _sanitize_prompt_fragment(tower_id)
            or _sanitize_prompt_fragment(tower_definition.get("tower_id"))
            or _sanitize_prompt_fragment(tower_definition.get("tower_code"))
            or _sanitize_prompt_fragment(tower_definition.get("domain_id"))
        ).upper()

        pillars = (
            tower_definition.get("pillars")
            or tower_definition.get("pillars_analysis")
            or []
        )
        if not pillars or not isinstance(pillars, Sequence) or isinstance(pillars, (str, bytes)):
            return ""

        sections: List[str] = [
            "### MANDATORY ONTOLOGICAL BOUNDARIES & KPI SCOPING PER PILLAR:",
            "To guarantee 100% architectural precision and eliminate semantic contamination, "
            "each pillar's technical description, capability analysis, and health check findings "
            "MUST strictly evaluate its assigned KPIs. You are strictly FORBIDDEN from reporting "
            "issues belonging to foreign domains inside this pillar.\n",
        ]

        valid_pillar_count = 0
        seen_canonical_pillars: Set[str] = set()

        for p in pillars:
            if not isinstance(p, Mapping):
                continue
            raw_p_id = _sanitize_prompt_fragment(
                p.get("pillar_id") or p.get("id") or p.get("code") or ""
            ).upper()
            if not raw_p_id:
                continue

            candidate_p_id = _canonicalize_pillar_id(raw_p_id, norm_tower_id)

            profile = self._registry.get_profile(candidate_p_id, tower_id=norm_tower_id)
            if profile is None and candidate_p_id != raw_p_id:
                profile = self._registry.get_profile(raw_p_id, tower_id=norm_tower_id)

            canonical_p_id = (
                _sanitize_prompt_fragment(profile.pillar_id).upper()
                if (profile and getattr(profile, "pillar_id", None))
                else candidate_p_id
            )

            if canonical_p_id in seen_canonical_pillars:
                continue
            seen_canonical_pillars.add(canonical_p_id)

            p_name = _sanitize_prompt_fragment(
                p.get("pillar_name")
                or p.get("name")
                or (profile.pillar_name if profile else "")
                or canonical_p_id
            )

            valid_pillar_count += 1
            sections.append(f"#### PILLAR [{canonical_p_id}]: {p_name}")

            # 1. Official KPI Rubrics & Client Grounding Answers
            kpis = p.get("kpis") or p.get("evaluation_dimensions") or []
            if kpis and isinstance(kpis, Sequence) and not isinstance(kpis, (str, bytes)):
                kpi_lines: List[str] = []
                scale_suffix = f"/{score_scale_max}" if score_scale_max is not None else ""
                for k in kpis:
                    base_line = self._extract_kpi_line(k)
                    if not base_line:
                        continue
                    k_id = _sanitize_prompt_fragment(
                        (k.get("kpi_id") or k.get("id") or k.get("code") or "") if isinstance(k, Mapping) else ""
                    ).upper()
                    if questionnaire_answers and k_id in questionnaire_answers:
                        ans_data = questionnaire_answers[k_id]
                        if isinstance(ans_data, Mapping):
                            score_val = (
                                ans_data.get("score")
                                if ans_data.get("score") is not None
                                else ans_data.get("rating")
                            )
                            statement = _sanitize_prompt_fragment(
                                ans_data.get("response_text") or ans_data.get("answer") or ans_data.get("statement") or ""
                            )
                            if score_val is not None and statement:
                                base_line += f" | Client Declared Score: {score_val}{scale_suffix} | Client Factual Statement: \"{statement}\""
                            elif score_val is not None:
                                base_line += f" | Client Declared Score: {score_val}{scale_suffix}"
                            elif statement:
                                base_line += f" | Client Factual Statement: \"{statement}\""
                        elif isinstance(ans_data, (int, float, str)):
                            base_line += f" | Client Declared Score: {ans_data}{scale_suffix}"
                    kpi_lines.append(base_line)

                if kpi_lines:
                    sections.append("  - OFFICIAL EVALUATION DIMENSIONS (KPIs):")
                    sections.extend(kpi_lines)

            # 2. Negative Exclusion Directives (Balanced Round-Robin across Foreign Domains)
            if profile and profile.negative_exclusion_map and max_forbidden_terms_per_pillar > 0:
                balanced_forbidden = self._select_balanced_forbidden_terms(
                    profile.negative_exclusion_map,
                    max_terms=max_forbidden_terms_per_pillar,
                )
                if balanced_forbidden:
                    forbidden_str = ", ".join(f"'{t}'" for t in balanced_forbidden)
                    sections.append(
                        "  - STRICTLY FORBIDDEN CONCEPTS (belong to foreign domains, DO NOT REPORT HERE): "
                        f"[{forbidden_str}]."
                    )

            # 3. Dynamic Vertical-Agnostic Isolation Invariant
            sections.append(
                self._build_isolation_invariant(canonical_p_id, p_name, profile)
            )

        if valid_pillar_count == 0:
            return ""

        sections.append(
            self.build_closed_world_grounding_directive(
                client_name=str(tower_definition.get("client_name") or ""),
                domain_name=str(tower_definition.get("tower_name") or norm_tower_id),
            )
        )

        return "\n".join(sections)
