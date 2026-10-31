"""Linguistic Quality Guardrail for Target-Aware Architecture Deliverables (RFC-022).

Enforces strict language purity and detects language contagion or drift (e.g. Spanglish)
in generated narrative fields before compilation into customer-facing deliverables.
Operates deterministically across target locales without third-party cloud dependencies.
"""

from __future__ import annotations

import re
from typing import Any

# High-frequency linguistic markers and stop-word footprints
_LANGUAGE_MARKERS: dict[str, set[str]] = {
    "en": {
        "the", "and", "is", "of", "to", "in", "for", "with", "that", "this",
        "lack", "lacks", "lacking", "absence", "which", "resulting", "across",
        "without", "failure", "causes", "leading", "severe", "due", "management",
    },
    "es": {
        "el", "la", "los", "las", "un", "una", "de", "del", "en", "para", "por",
        "con", "que", "carencia", "ausencia", "debido", "provocando", "riesgo",
        "gestion", "falta", "elevada", "critica", "operativo", "servicios",
    },
    "de": {
        "der", "die", "das", "und", "in", "den", "von", "zu", "mit", "für",
        "auf", "nicht", "eine", "einer", "durch", "fehlen", "mangel",
    },
    "fr": {
        "le", "la", "les", "et", "de", "des", "en", "du", "un", "une", "pour",
        "dans", "avec", "qui", "par", "manque", "absence", "risque",
    },
}

_CJK_PATTERN = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]")


class LinguisticQualityGuardrail:
    """Deterministic guardrail validating linguistic purity against target locale."""

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Extract lowercase alphabetical words from text across Unicode scripts."""
        if not text:
            return []
        return [w.lower() for w in re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)]

    @classmethod
    def detect_language_drift(
        cls,
        text: str,
        target_locale: str,
        contamination_threshold: float = 0.15,
    ) -> tuple[bool, str]:
        """Detect if text suffers from severe language contagion away from target_locale.

        Args:
            text: Narrative content to evaluate.
            target_locale: Expected client language code ('es', 'en', 'de', 'fr', 'ja', etc.).
            contamination_threshold: Ratio of foreign stop-words triggering a violation.

        Returns:
            Tuple of (has_drift: bool, reason: str).
        """
        if not text or len(text.strip()) < 40:
            return False, "Text too short to evaluate drift."

        base_loc = str(target_locale).strip().lower().split("_")[0].split("-")[0]

        # CJK scripts (Japanese, Chinese, Korean) evaluation
        if base_loc in ("ja", "zh", "ko"):
            has_cjk_glyphs = bool(_CJK_PATTERN.search(text))
            if has_cjk_glyphs:
                return False, "CJK native script verified."
            return True, f"Target is '{base_loc}' but no CJK script characters found in text."

        words = cls._tokenize(text)
        if not words or len(words) < 8:
            return False, "Insufficient tokens for statistical drift evaluation."

        # Case A: Non-English target document contaminated by English
        if base_loc != "en":
            en_markers = _LANGUAGE_MARKERS.get("en", set())
            en_hits = [w for w in words if w in en_markers]
            en_ratio = len(en_hits) / len(words)

            target_markers = _LANGUAGE_MARKERS.get(base_loc, set())
            target_hits = [w for w in words if w in target_markers]
            target_ratio = len(target_hits) / len(words)

            if en_ratio >= contamination_threshold and en_ratio > (target_ratio * 1.5):
                return True, (
                    f"Language contagion detected: {len(en_hits)} English stop-words found "
                    f"({en_ratio:.1%}) exceeding target '{base_loc}' markers ({target_ratio:.1%})."
                )

        # Case B: English target document contaminated by non-English foreign text
        else:
            en_markers = _LANGUAGE_MARKERS.get("en", set())
            en_hits = [w for w in words if w in en_markers]
            en_ratio = len(en_hits) / len(words)

            foreign_hits = []
            for foreign_lang in ("es", "de", "fr"):
                markers = _LANGUAGE_MARKERS.get(foreign_lang, set())
                foreign_hits.extend([w for w in words if w in markers])

            foreign_ratio = len(foreign_hits) / len(words)
            if foreign_ratio >= contamination_threshold and foreign_ratio > (en_ratio * 1.5):
                return True, (
                    f"Foreign language contagion detected: {len(foreign_hits)} foreign markers "
                    f"({foreign_ratio:.1%}) exceeding English markers ({en_ratio:.1%})."
                )

        return False, "Linguistic purity verified."

    @classmethod
    def audit_blueprint_payload(
        cls,
        payload: dict[str, Any],
        target_locale: str,
    ) -> list[str]:
        """Audit all narrative fields across a blueprint payload for language contagion.

        Returns:
            List of diagnostic violation messages. Empty list indicates 100% compliance.
        """
        violations: list[str] = []
        base_loc = str(target_locale).strip().lower().split("_")[0].split("-")[0]

        for p_idx, pillar in enumerate(payload.get("pillars_analysis", [])):
            p_name = pillar.get("pillar_name", f"Pillar_{p_idx}")

            # Check AS-IS description
            asis_desc = pillar.get("asis_architecture_description", "")
            has_drift, reason = cls.detect_language_drift(asis_desc, base_loc)
            if has_drift:
                violations.append(f"[{p_name}] asis_architecture_description: {reason}")

            # Check findings and business risks
            for hc_idx, hc in enumerate(pillar.get("health_check_asis", [])):
                finding_text = hc.get("finding", hc.get("risk_observed", ""))
                has_drift_f, reason_f = cls.detect_language_drift(finding_text, base_loc)
                if has_drift_f:
                    violations.append(f"[{p_name} - Finding {hc_idx + 1}]: {reason_f}")

                risk_text = hc.get("business_risk", hc.get("impact", ""))
                has_drift_r, reason_r = cls.detect_language_drift(risk_text, base_loc)
                if has_drift_r:
                    violations.append(f"[{p_name} - Risk {hc_idx + 1}]: {reason_r}")

        return violations
