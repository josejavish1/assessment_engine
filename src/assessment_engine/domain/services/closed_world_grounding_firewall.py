"""Closed-World Grounding and Hallucination Firewall Domain Service (Phase 4).

Enforces two strict epistemic invariants on synthesized engineering narratives:
1. Zero Speculative Physical / Process Artifacts: Any specific measuring tool, physical media,
   or ad-hoc manual mechanism not present in the source evidence corpus is stripped and
   replaced with the factual absence of the control or the selected questionnaire rubric.
2. Strict Domain Headline Isolation: Prevents foreign-domain topics from dominating the
   Executive Summary or technical chapters of the active domain.

Strictly 100% Technical English, zero hardcoding, multi-tenant and topology-agnostic.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Protocol, Sequence, Set

logger = logging.getLogger(__name__)


class LocalizationPort(Protocol):
    """Protocol for resolving localized string tokens and lists."""

    def get_localized_list(self, key: str, locale: str = "en") -> Sequence[str]:
        """Retrieve localized vocabulary list for epistemic scoper."""
        ...

    def translate(self, key: str, locale: str = "en") -> str:
        """Translate string token according to localized dictionary."""
        ...


_DEFAULT_ENGLISH_SPECULATIVE_ARTIFACTS: Sequence[str] = (
    r"clamp\s+meters?",
    r"thermal\s+cameras?",
    r"multimeters?",
    r"nameplates?",
    r"manufacturer\s+plates?",
    r"printed\s+forms?",
    r"handwritten\s+signatures?",
    r"physical\s+logbooks?",
    r"paper\s+forms?",
)

_DEFAULT_ENGLISH_CLAUSE_PREFIX: str = (
    r"(?:by means of|via|utilizing|using|based on|relying on)\s+[^,\.;:\!\?\u2014\u2013]*"
)

_DEFAULT_ENGLISH_CONJUNCTION: str = r"(?:and|or)"

# Protect against false sentence splits on technical abbreviations (e.g., i.e., vs., fig., st., approx., dept.)
_SENTENCE_BOUNDARY_RE = re.compile(
    r"(?<!\be\.g\.)(?<!\bi\.e\.)(?<!\bvs\.)(?<!\bfig\.)(?<!\bst\.)(?<!\bapprox\.)(?<!\bdept\.)(?<=[\.\!\?])\s+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GroundingAuditResult:
    """Forensic result of a narrative grounding audit."""

    is_clean: bool
    sanitized_text: str
    detected_violations: list[str] = field(default_factory=list)


class ClosedWorldGroundingFirewall:
    """Enforces closed-world epistemic grounding and domain isolation on generative narratives."""

    def __init__(
        self,
        source_evidence_corpus: str = "",
        speculative_artifact_patterns: Optional[Sequence[str]] = None,
        speculative_clause_prefix_regex: Optional[str] = None,
        coordinating_conjunction_regex: Optional[str] = None,
        in_scope_keywords: Optional[Set[str]] = None,
        foreign_domain_primary_terms: Optional[Set[str]] = None,
        allowed_dependency_keywords: Optional[Set[str]] = None,
        doc_lang: str = "en",
        localization_provider: Optional[LocalizationPort] = None,
    ) -> None:
        self._source_corpus_lower = str(source_evidence_corpus or "").lower()
        self._doc_lang = str(doc_lang or "en").strip().lower()
        lang_subtag = self._doc_lang.split("-")[0]

        # Resolve patterns from explicit parameter, injected localization provider, or pure English default
        if speculative_artifact_patterns is not None:
            resolved_patterns = list(speculative_artifact_patterns)
        elif localization_provider is not None:
            localized = localization_provider.get_localized_list(
                "speculative_artifact_regexes", self._doc_lang
            )
            if not localized and "-" in self._doc_lang:
                localized = localization_provider.get_localized_list(
                    "speculative_artifact_regexes", lang_subtag
                )
            resolved_patterns = (
                list(localized)
                if localized
                else list(_DEFAULT_ENGLISH_SPECULATIVE_ARTIFACTS)
            )
        else:
            resolved_patterns = list(_DEFAULT_ENGLISH_SPECULATIVE_ARTIFACTS)

        self._speculative_patterns = tuple(resolved_patterns)
        self._compiled_speculative_regexes = tuple(
            re.compile(p, re.IGNORECASE) for p in self._speculative_patterns
        )

        if speculative_clause_prefix_regex is not None:
            self._clause_prefix_regex_str = speculative_clause_prefix_regex
        elif localization_provider is not None:
            loc_prefix = localization_provider.translate(
                "speculative_clause_prefix_regex", self._doc_lang
            )
            if (not loc_prefix or loc_prefix == "speculative_clause_prefix_regex") and "-" in self._doc_lang:
                loc_prefix = localization_provider.translate(
                    "speculative_clause_prefix_regex", lang_subtag
                )
            self._clause_prefix_regex_str = (
                loc_prefix
                if loc_prefix and loc_prefix != "speculative_clause_prefix_regex"
                else _DEFAULT_ENGLISH_CLAUSE_PREFIX
            )
        else:
            self._clause_prefix_regex_str = _DEFAULT_ENGLISH_CLAUSE_PREFIX

        if coordinating_conjunction_regex is not None:
            self._conjunction_regex_str = coordinating_conjunction_regex
        elif localization_provider is not None:
            conj = localization_provider.translate(
                "coordinating_conjunction_regex", self._doc_lang
            )
            if (not conj or conj == "coordinating_conjunction_regex") and "-" in self._doc_lang:
                conj = localization_provider.translate(
                    "coordinating_conjunction_regex", lang_subtag
                )
            self._conjunction_regex_str = (
                conj
                if conj and conj != "coordinating_conjunction_regex"
                else _DEFAULT_ENGLISH_CONJUNCTION
            )
        else:
            self._conjunction_regex_str = _DEFAULT_ENGLISH_CONJUNCTION

        self._in_scope_keywords = {
            kw.strip().lower() for kw in (in_scope_keywords or set()) if kw.strip()
        }
        allowed_deps = {
            kw.strip().lower() for kw in (allowed_dependency_keywords or set()) if kw.strip()
        }
        self._foreign_domain_primary_terms = {
            term.strip().lower()
            for term in (foreign_domain_primary_terms or set())
            if term.strip().lower() not in allowed_deps
        }

        # Pre-compile boundary-safe regexes to eradicate false-positive substring collisions
        self._in_scope_regexes = tuple(
            re.compile(rf"(?<!\w){re.escape(kw)}(?!\w)", re.IGNORECASE)
            for kw in self._in_scope_keywords
        )
        self._foreign_domain_regexes = tuple(
            re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)
            for term in self._foreign_domain_primary_terms
        )

    def build_domain_scoped_prompt_directives(
        self,
        domain_name: str,
        kpi_rubric_selections: Sequence[Mapping[str, Any]],
        canonical_pillar_titles: Optional[Sequence[str]] = None,
        excluded_foreign_tower_keywords: Optional[Sequence[str]] = None,
        score_scale_max: Optional[int] = None,
    ) -> str:
        """Generates deterministic Closed-World Grounding Mandates for prompt construction."""
        scale_suffix = f"/{score_scale_max}" if score_scale_max is not None else ""
        rubric_ledger_lines: List[str] = []
        for kpi in kpi_rubric_selections:
            kpi_id = kpi.get("kpi_id") or kpi.get("question_id") or kpi.get("id") or ""
            kpi_title = kpi.get("kpi_name") or kpi.get("question_title") or kpi.get("name") or ""
            score = kpi.get("score") if kpi.get("score") is not None else kpi.get("rating")
            selected_text = (
                kpi.get("selected_option_text")
                or kpi.get("response_text")
                or kpi.get("answer")
                or ""
            )
            score_display = f"{score}{scale_suffix}" if score is not None else "N/A"
            rubric_ledger_lines.append(
                f"- [{kpi_id}] {kpi_title} (Score: {score_display}): \"{selected_text}\""
            )

        pillars_str = (
            ", ".join(canonical_pillar_titles)
            if canonical_pillar_titles
            else "the designated pillars"
        )
        foreign_str = (
            ", ".join(excluded_foreign_tower_keywords)
            if excluded_foreign_tower_keywords
            else "unrelated technical domains"
        )

        lines: List[str] = [
            "### CLOSED-WORLD EPISTEMIC GROUNDING MANDATE (STRICT COMPLIANCE REQUIRED):",
            f"1. PRIMARY DOMAIN BOUNDARY: You are evaluating strictly [{domain_name}]. "
            f"The narrative must focus primarily on {pillars_str}.",
            f"2. FOREIGN DOMAIN EXCLUSION: Systems belonging to other towers ({foreign_str}) "
            "MUST NOT be framed as primary findings of this domain. They may only be referenced "
            "as downstream consumers or boundary dependencies.",
            "3. ZERO SPECULATIVE EMBELLISHMENT ON DEFICIENT CONTROLS: When a control is deficient or absent, describe "
            "ONLY the functional absence or reactive state defined in the Verified Questionnaire Rubric Ledger below "
            "and verified interview facts. DO NOT invent specific physical measuring instruments (e.g., clamp meters, "
            "thermal cameras, multimeters), manufacturer nameplates, spreadsheets, or handwritten paper forms unless "
            "those exact terms appear verbatim in the interview transcript.",
            "4. VERIFIED QUESTIONNAIRE RUBRIC LEDGER:",
        ]
        lines.extend(rubric_ledger_lines)
        return "\n".join(lines)

    def sanitize_narrative_block(
        self,
        narrative: str,
        fallback_rubric_statement: str = "",
    ) -> GroundingAuditResult:
        """Scans each sentence in a narrative for unverified speculative artifacts.

        Iteratively strips all unverified speculative artifacts from each sentence.
        If stripping leaves an empty or degenerate clause, substitutes the fallback rubric statement.
        """
        text = str(narrative or "").strip()
        if not text:
            return GroundingAuditResult(is_clean=True, sanitized_text="")

        sentences = [
            s.strip()
            for s in _SENTENCE_BOUNDARY_RE.split(text)
            if s.strip()
        ]
        violations: List[str] = []
        clean_sentences: List[str] = []

        for sentence in sentences:
            current_sentence = sentence
            iteration = 0
            max_iterations = 6

            while iteration < max_iterations:
                iteration += 1
                violated_pattern = None

                for compiled_re in self._compiled_speculative_regexes:
                    match = compiled_re.search(current_sentence)
                    if match:
                        # Check whether the empirical corpus attests this instrument or tool
                        if not compiled_re.search(self._source_corpus_lower):
                            violated_pattern = match.group(0).strip().lower()
                            break

                if not violated_pattern:
                    break

                violations.append(
                    f"Unverified speculative artifact '{violated_pattern}' in: '{current_sentence}'"
                )
                repaired = self._strip_speculative_clause(
                    current_sentence, violated_pattern, fallback_rubric_statement
                )
                if repaired and repaired != current_sentence:
                    current_sentence = repaired
                else:
                    current_sentence = fallback_rubric_statement.strip()
                    break

            if current_sentence:
                clean_sentences.append(current_sentence)

        sanitized = " ".join(clean_sentences)
        return GroundingAuditResult(
            is_clean=(len(violations) == 0),
            sanitized_text=sanitized,
            detected_violations=violations,
        )

    def enforce_executive_summary_tower_focus(
        self,
        executive_paragraphs: Sequence[str],
    ) -> list[str]:
        """Ensures that no paragraph in the Executive Summary is dominated by foreign-domain topics."""
        sanitized_paragraphs: List[str] = []

        for paragraph in executive_paragraphs:
            raw_p = str(paragraph or "").strip()
            if not raw_p:
                continue

            sentences = [
                s.strip()
                for s in _SENTENCE_BOUNDARY_RE.split(raw_p)
                if s.strip()
            ]
            in_scope_sentences: List[str] = []

            for sentence in sentences:
                foreign_hits = sum(
                    1 for r in self._foreign_domain_regexes if r.search(sentence)
                )
                in_scope_hits = sum(
                    1 for r in self._in_scope_regexes if r.search(sentence)
                )

                if foreign_hits > 0 and in_scope_hits == 0:
                    logger.debug(
                        "Dropping out-of-scope sentence from Executive Summary: %s", sentence
                    )
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
        """Removes the subordinate clause introducing the speculative artifact."""
        escaped_phrase = re.escape(violated_phrase)
        pattern = (
            rf"(?:[,]?\s*{self._conjunction_regex_str}\s+|[,]?\s*)"
            rf"{self._clause_prefix_regex_str}{escaped_phrase}[^,\.;:\!\?\u2014\u2013]*"
        )
        cleaned = re.sub(pattern, "", sentence, flags=re.IGNORECASE).strip()

        cleaned = re.sub(r"\s+([,\.;])", r"\1", cleaned).strip()
        cleaned = re.sub(
            rf"\s+{self._conjunction_regex_str}\s*$", "", cleaned, flags=re.IGNORECASE
        ).strip()

        if cleaned and cleaned != sentence and len(cleaned.split()) >= 4:
            return cleaned if cleaned[-1] in ".!?" else f"{cleaned}."

        return fallback_rubric_statement.strip()
