"""Linguistic Quality Guardrail for Target-Aware Architecture Deliverables (RFC-022).

Enforces strict language purity and detects language contagion or drift
in generated narrative fields before compilation into customer-facing deliverables.
Operates deterministically across target locales without third-party cloud dependencies.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


class UnsupportedLanguageVerificationError(ValueError):
    """Raised when attempting linguistic verification for an unsupported locale."""


# High-frequency linguistic markers and stop-word footprints for space-segmented languages
_LANGUAGE_MARKERS: dict[str, set[str]] = {
    "en": {
        "the", "and", "is", "of", "to", "in", "for", "with", "that", "this",
        "lack", "lacks", "lacking", "absence", "which", "resulting", "across",
        "without", "failure", "causes", "leading", "severe", "due", "management",
        "are", "from", "by", "not", "have", "has", "been", "between", "system",
    },
    "es": {
        "el", "la", "los", "las", "un", "una", "de", "del", "en", "para", "por",
        "con", "que", "carencia", "ausencia", "debido", "provocando", "riesgo",
        "gestion", "falta", "elevada", "critica", "operativo", "servicios",
        "como", "sin", "sobre", "entre", "hacia", "mediante", "desde", "este",
    },
    "de": {
        "der", "die", "das", "und", "in", "den", "von", "zu", "mit", "fur", "für",
        "auf", "nicht", "eine", "einer", "durch", "fehlen", "mangel", "sowie",
        "oder", "bei", "nach", "aus", "dem", "des", "einem", "werden", "sind",
    },
    "fr": {
        "le", "la", "les", "et", "de", "des", "en", "du", "un", "une", "pour",
        "dans", "avec", "qui", "par", "manque", "absence", "risque", "sur",
        "plus", "aux", "sont", "cette", "sans", "entre", "comme", "tout",
    },
    "pt": {
        "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
        "em", "no", "na", "para", "por", "com", "que", "ausencia", "falta",
        "devido", "risco", "gestao", "servicos", "operacional", "como", "sem",
        "entre", "pela", "pelo", "nao", "mais", "sobre", "sistema",
    },
    "it": {
        "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "a",
        "da", "in", "con", "su", "per", "tra", "fra", "che", "non", "del",
        "della", "dei", "delle", "nel", "nella", "mancanza", "assenza", "rischio",
        "sistema", "gestione", "servizi", "come", "senza", "sono",
    },
    "ar": {
        "في", "من", "على", "إلى", "عن", "مع", "هذا", "هذه", "التي", "الذي",
        "أن", "إن", "كان", "كانت", "ما", "لا", "لم", "لن", "كل", "بين",
        "أو", "ثم", "بل", "حتى", "عدم", "نقص", "مخاطر", "إدارة", "بسبب",
    },
}

# Bound-morpheme, particle, and functional character signatures for non-Latin / unsegmented scripts
_BOUND_MORPHEME_SIGNATURES: dict[str, set[str]] = {
    "ja": {
        "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ",
        "ある", "いる", "も", "する", "から", "な", "こと", "として", "い", "や",
        "れる", "など", "なっ", "ない", "この", "ため", "その", "あっ", "よう",
    },
    "zh": {
        "的", "一", "是", "在", "不", "了", "有", "和", "人", "这", "中", "大",
        "为", "上", "个", "国", "我", "以", "要", "他", "时", "来", "用", "们",
        "生", "到", "作", "地", "于", "出", "就", "分", "对", "成", "会", "可",
        "缺乏", "导致", "风险", "管理", "系统", "由于", "没有",
    },
    "ko": {
        "이", "가", "은", "는", "을", "를", "의", "에", "에서", "로", "으로", "과",
        "와", "도", "만", "부터", "까지", "보다", "처럼", "같이", "하고", "이며",
        "있는", "없는", "하는", "되는", "대한", "위해", "통해", "따라", "인한",
    },
    "ar": {
        "ال", "في", "من", "على", "إلى", "عن", "مع", "أن", "إن", "لا", "ما",
        "ب", "ل", "ك", "و", "ف", "ة", "ات", "ين", "ون", "ها", "هم",
    },
}

# Standard Unicode code point block definitions per target language
_SCRIPT_UNICODE_RANGES: dict[str, tuple[tuple[int, int], ...]] = {
    "ar": (
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
        (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
        (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    ),
    "ja": (
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs (Kanji)
        (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
        (0xFF66, 0xFF9F),  # Halfwidth Katakana
    ),
    "zh": (
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
        (0xF900, 0xFAFF),  # CJK Compatibility Ideographs
    ),
    "ko": (
        (0xAC00, 0xD7AF),  # Hangul Syllables
        (0x1100, 0x11FF),  # Hangul Jamo
        (0x3130, 0x318F),  # Hangul Compatibility Jamo
        (0x4E00, 0x9FFF),  # Hanja (CJK Unified Ideographs)
    ),
    "en": ((0x0041, 0x024F), (0x1E00, 0x1EFF)),
    "es": ((0x0041, 0x024F), (0x1E00, 0x1EFF)),
    "de": ((0x0041, 0x024F), (0x1E00, 0x1EFF)),
    "fr": ((0x0041, 0x024F), (0x1E00, 0x1EFF)),
    "pt": ((0x0041, 0x024F), (0x1E00, 0x1EFF)),
    "it": ((0x0041, 0x024F), (0x1E00, 0x1EFF)),
}

_SUPPORTED_LOCALES: frozenset[str] = frozenset(_SCRIPT_UNICODE_RANGES.keys())
_MIN_EXPECTED_SCRIPT_RATIO: float = 0.55
_CJK_PATTERN = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]")


def _normalize_locale(target_locale: str) -> str:
    """Extract normalized ISO 639-1 base language code and fail closed if unsupported."""
    if not target_locale or not str(target_locale).strip():
        raise UnsupportedLanguageVerificationError(
            "Target locale must be a non-empty language identifier."
        )
    base_loc = str(target_locale).strip().lower().split("_")[0].split("-")[0]
    if base_loc not in _SUPPORTED_LOCALES:
        raise UnsupportedLanguageVerificationError(
            f"Unsupported target locale '{target_locale}' (normalized: '{base_loc}'). "
            f"Supported locales: {sorted(_SUPPORTED_LOCALES)}"
        )
    return base_loc


def _compute_script_block_ratio(text: str, base_loc: str) -> tuple[float, int]:
    """Compute ratio of alphabetic/ideographic characters matching expected Unicode ranges."""
    ranges = _SCRIPT_UNICODE_RANGES[base_loc]
    total_letters = 0
    matching_letters = 0

    for ch in text:
        cat = unicodedata.category(ch)
        if cat.startswith("L"):
            total_letters += 1
            cp = ord(ch)
            if any(start <= cp <= end for start, end in ranges):
                matching_letters += 1

    if total_letters == 0:
        return 1.0, 0
    return matching_letters / total_letters, total_letters


def _evaluate_bound_morpheme_signature(text: str, base_loc: str) -> tuple[bool, float]:
    """Evaluate bound-morpheme and particle frequency signatures for segmented/unsegmented scripts."""
    signatures = _BOUND_MORPHEME_SIGNATURES.get(base_loc)
    if not signatures:
        return True, 1.0

    hits = sum(text.count(marker) for marker in signatures)
    letter_count = sum(1 for ch in text if unicodedata.category(ch).startswith("L"))
    if letter_count == 0:
        return False, 0.0

    density = hits / letter_count

    # Japanese text must contain Hiragana grammatical particles/inflections, not pure Kanji/Latin
    if base_loc == "ja":
        hiragana_count = sum(1 for ch in text if 0x3040 <= ord(ch) <= 0x309F)
        if hiragana_count == 0 or hits == 0:
            return False, density

    return hits > 0 and density >= 0.02, density


def verify_language_consistency_strict(
    text: str,
    target_locale: str,
    contamination_threshold: float = 0.15,
    min_script_ratio: float = _MIN_EXPECTED_SCRIPT_RATIO,
) -> tuple[bool, str]:
    """Strictly verify that text conforms to target_locale script and morphological signatures.

    Enforces:
    1. Fail-closed validation on unsupported locales (raises UnsupportedLanguageVerificationError).
    2. Unicode Script Block Ratio Analysis: requires >= 55% (or min_script_ratio) of letter
       code points to reside within the target locale's canonical Unicode script blocks.
    3. Bound-morpheme and particle frequency signature verification for CJK and Arabic scripts.
    4. Stop-word and functional marker contagion analysis for space-segmented languages.

    Args:
        text: Narrative text to verify.
        target_locale: Expected language locale code (e.g. 'en', 'es', 'ar', 'ja', 'zh', 'pt').
        contamination_threshold: Maximum permissible foreign marker ratio.
        min_script_ratio: Minimum required Unicode script block ratio (default 0.55).

    Returns:
        Tuple of (is_valid: bool, diagnostic_reason: str).
    """
    base_loc = _normalize_locale(target_locale)

    if not text or not text.strip():
        return True, "Empty text segment bypassed."

    stripped = text.strip()

    # Step 1: Unicode Script Block Ratio Analysis
    script_ratio, total_letters = _compute_script_block_ratio(stripped, base_loc)
    if total_letters == 0:
        return True, "No alphabetic or ideographic characters present."

    if script_ratio < min_script_ratio:
        return False, (
            f"Unicode script block ratio violation for target '{base_loc}': "
            f"expected >= {min_script_ratio:.1%} target script characters, "
            f"observed {script_ratio:.1%} across {total_letters} linguistic code points."
        )

    # Step 2: Non-Latin script bound-morpheme & particle verification (ar, ja, zh, ko)
    if base_loc in ("ar", "ja", "zh", "ko"):
        if total_letters >= 10:
            has_morphemes, density = _evaluate_bound_morpheme_signature(stripped, base_loc)
            if not has_morphemes:
                return False, (
                    f"Bound-morpheme signature verification failed for '{base_loc}': "
                    f"insufficient native particles/morphemes (density={density:.1%})."
                )

        # Also check for excessive embedded English stop-word contagion in mixed-script text
        latin_words = [w.lower() for w in re.findall(r"[a-zA-Z]{2,}", stripped)]
        if len(latin_words) >= 6:
            en_markers = _LANGUAGE_MARKERS["en"]
            en_hits = [w for w in latin_words if w in en_markers]
            if len(en_hits) >= 3 or (len(en_hits) / max(len(latin_words), 1)) >= 0.30:
                return False, (
                    f"Foreign Latin stop-word contagion detected inside '{base_loc}' text: "
                    f"{len(en_hits)} English stop-words found."
                )

        return True, f"Native '{base_loc}' script ({script_ratio:.1%}) and morpheme signatures verified."

    # Step 3: Space-segmented Latin script languages (en, es, de, fr, pt, it)
    words = LinguisticQualityGuardrail._tokenize(stripped)
    if len(words) < 6:
        return True, "Insufficient tokens for statistical marker evaluation."

    expected_markers = _LANGUAGE_MARKERS.get(base_loc)
    if not expected_markers:
        raise UnsupportedLanguageVerificationError(
            f"No linguistic marker profile configured for locale '{base_loc}'."
        )

    target_hits = [w for w in words if w in expected_markers]
    target_ratio = len(target_hits) / len(words)

    foreign_hits_by_lang: dict[str, int] = {}
    for lang_code, markers in _LANGUAGE_MARKERS.items():
        if lang_code == base_loc or lang_code == "ar":
            continue
        # Count hits that are in the foreign language marker set but NOT shared with target
        exclusive_foreign = markers - expected_markers
        hits = sum(1 for w in words if w in exclusive_foreign)
        if hits > 0:
            foreign_hits_by_lang[lang_code] = hits

    max_foreign_lang = ""
    max_foreign_hits = 0
    if foreign_hits_by_lang:
        max_foreign_lang, max_foreign_hits = max(
            foreign_hits_by_lang.items(), key=lambda item: item[1]
        )
    max_foreign_ratio = max_foreign_hits / len(words)

    if max_foreign_ratio >= contamination_threshold and max_foreign_ratio > target_ratio:
        return False, (
            f"Language contagion detected for target '{base_loc}': "
            f"{max_foreign_hits} '{max_foreign_lang}' markers ({max_foreign_ratio:.1%}) "
            f"exceeding target '{base_loc}' markers ({target_ratio:.1%})."
        )

    if len(words) >= 12 and target_ratio == 0.0:
        return False, (
            f"Zero target language markers found for '{base_loc}' across {len(words)} words."
        )

    return True, "Linguistic purity verified."


class LinguisticQualityGuardrail:
    """Deterministic guardrail validating linguistic purity against target locale."""

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Extract lowercase alphabetical words from text across Unicode scripts."""
        if not text:
            return []
        return [w.lower() for w in re.findall(r"[^\W\d_]+", text, flags=re.UNICODE)]

    @classmethod
    def verify_language_consistency_strict(
        cls,
        text: str,
        target_locale: str,
        contamination_threshold: float = 0.15,
        min_script_ratio: float = _MIN_EXPECTED_SCRIPT_RATIO,
    ) -> tuple[bool, str]:
        """Class-level delegate for strict script-aware language consistency verification."""
        return verify_language_consistency_strict(
            text=text,
            target_locale=target_locale,
            contamination_threshold=contamination_threshold,
            min_script_ratio=min_script_ratio,
        )

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
            target_locale: Expected client language code ('es', 'en', 'de', 'fr', 'ja', 'ar', etc.).
            contamination_threshold: Ratio of foreign stop-words triggering a violation.

        Returns:
            Tuple of (has_drift: bool, reason: str).

        Raises:
            UnsupportedLanguageVerificationError: If target_locale is unsupported.
        """
        base_loc = _normalize_locale(target_locale)

        if not text or len(text.strip()) < 20:
            return False, "Text too short to evaluate drift."

        is_valid, reason = verify_language_consistency_strict(
            text=text,
            target_locale=base_loc,
            contamination_threshold=contamination_threshold,
            min_script_ratio=_MIN_EXPECTED_SCRIPT_RATIO,
        )
        return not is_valid, reason

    @classmethod
    def audit_blueprint_payload(
        cls,
        payload: dict[str, Any],
        target_locale: str,
    ) -> list[str]:
        """Audit all narrative fields across a blueprint payload for language contagion.

        Returns:
            List of diagnostic violation messages. Empty list indicates 100% compliance.

        Raises:
            UnsupportedLanguageVerificationError: If target_locale is unsupported.
        """
        violations: list[str] = []
        base_loc = _normalize_locale(target_locale)

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
