---
status: Verified
owner: docs-governance
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
### 1. Executive Verdict

**VERDICT: PASS (Score: 9.8 / 10.0)**

Phase 5 (`TowerPayloadHydrator` ontological quarantine & atomic persistence) and Phase 6 (`OntologicalPromptScoper`) demonstrate exceptional engineering discipline, architectural purity, and strict adherence to all three governance mandates. 

* **Mandate 1 (100% Technical English / Zero Spanish):** **100% Compliant.** Every variable identifier, docstring, comment, log message, prompt template string, and test fixture across all four artifacts is written in clear, idiomatic Technical English. Zero Spanish tokens were detected.
* **Mandate 2 (Zero Hardcoding & Vertical/Topology Agnosticism):** **100% Compliant.** The subsystems support arbitrary domain identifiers (`D_FAC`, `D_CMP`, `T1`, custom slugs), hierarchical sub-pillar identifiers (`P4.1`), heterogeneous KPI schema structures, and dynamic financial scales.
* **Mandate 3 (Hexagonal & Clean Architecture Purity):** **100% Compliant.** `ontological_prompt_scoper.py` resides in the Domain layer (`assessment_engine.domain.prompts`) and depends strictly on pure domain ports (`TaxonomyRegistryPort`, `PillarOntologyProfile`). Unit tests use an in-memory test double (`InMemoryTaxonomyRegistry`) with zero infrastructure leakage.

---

### 2. Forensic Inventory of Findings & Edge Cases

While no blocking defects exist, a brutally adversarial inspection reveals three minor edge cases that can be hardened for maximum enterprise resilience:

#### Finding 2.1: Multi-Line Markdown Prefix Stripping in `_sanitize_prompt_fragment` (Low Severity / Edge Case)
* **Location:** `src/assessment_engine/domain/prompts/ontological_prompt_scoper.py` (Lines 23–43)
* **Analysis:**
  `_MARKDOWN_PREFIX_RE = re.compile(r"^(?:#+\s*|[\*\->+]\s+|[`~|]+\s*)")` is applied to each line before `_UNSAFE_DELIMITERS_RE = re.compile(r"[`\[\]\<\>\x00-\x1f\x7f]+")` strips unsafe characters.
  If an input string begins with leading unsafe brackets or control characters before a markdown prefix—for example, `"[# Heading]"` or `"> > Nested quote"`—`_MARKDOWN_PREFIX_RE` runs only once before `_UNSAFE_DELIMITERS_RE`, leaving residual markdown tokens (`"# Heading"` or `"> Nested quote"`).
* **Remediation:** Strip `_UNSAFE_DELIMITERS_RE` first, and allow `_MARKDOWN_PREFIX_RE` to repeat (`+`) so nested blockquotes (`> > `) or bracket-wrapped headers (`[# Header]`) are completely sanitized while still preserving signed technical notation (`-48V DC`, `*nix`).

#### Finding 2.2: Whitespace-Only `tower_id` Argument Shadowing Fallback Resolution (Low Severity / Edge Case)
* **Location:** `src/assessment_engine/domain/prompts/ontological_prompt_scoper.py` (Lines 199–205)
* **Analysis:**
  In `build_pillar_scoping_directive`:
  ```python
  norm_tower_id = _sanitize_prompt_fragment(
      tower_id
      or tower_definition.get("tower_id")
      or tower_definition.get("tower_code")
      or tower_definition.get("domain_id")
      or ""
  ).upper()
  ```
  If a caller passes a whitespace-only string `tower_id="   "`, Python evaluates `"   "` as truthy in the `or` chain, short-circuiting `tower_definition.get("tower_id")` and evaluating `norm_tower_id` to `""`.
* **Remediation:** Sanitize/strip `tower_id` prior to evaluating the fallback chain so whitespace-only arguments fall back gracefully to `tower_definition`.

#### Finding 2.3: Duplicate Pillar ID Deduplication in `build_pillar_scoping_directive` (Low Severity / Edge Case)
* **Location:** `src/assessment_engine/domain/prompts/ontological_prompt_scoper.py` (Lines 222–245)
* **Analysis:**
  If a malformed upstream `tower_definition` contains duplicate pillar entries (e.g., both `"P4"` and `"D_FAC.P4"` resolving to `canonical_p_id = "D_FAC.P4"`), the scoper emits duplicate `#### PILLAR [D_FAC.P4]` blocks into the LLM prompt, wasting context tokens.
* **Remediation:** Track `seen_canonical_pillars: Set[str]` during directive compilation to guarantee idempotency.

---

### 3. Production-Grade Hardened Remediation (`ontological_prompt_scoper.py`)

Below is the drop-in hardened version of `src/assessment_engine/domain/prompts/ontological_prompt_scoper.py` incorporating all three edge-case improvements:

```python
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
    lines: List[str] = []
    for raw_line in re.split(r"[\r\n]+", text):
        cleaned_delims = _UNSAFE_DELIMITERS_RE.sub("", raw_line).strip()
        stripped_md = _MARKDOWN_PREFIX_RE.sub("", cleaned_delims).strip()
        if stripped_md:
            lines.append(stripped_md)
    flattened = " ".join(lines)
    return " ".join(flattened.split())


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

    def build_pillar_scoping_directive(
        self,
        tower_id: str,
        tower_definition: Mapping[str, Any],
        max_forbidden_terms_per_pillar: int = DEFAULT_MAX_FORBIDDEN_TERMS_PER_PILLAR,
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

            # 1. Official KPI Rubrics
            kpis = p.get("kpis") or p.get("evaluation_dimensions") or []
            if kpis and isinstance(kpis, Sequence) and not isinstance(kpis, (str, bytes)):
                kpi_lines = [
                    line for line in (self._extract_kpi_line(k) for k in kpis) if line
                ]
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

        return "\n".join(sections)
```