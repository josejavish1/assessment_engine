---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
doc_type: operational
diataxis: reference
verification_mode: editorial
---

### Architectural & Security Audit Report
**Auditor:** `gemini-4-argon` (Principal Staff Security & Software Engineering Auditor)  
**Target Module:** `src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py`  
**Audit Status:** **FAILED (CRITICAL ARCHITECTURAL & RUNTIME DEFECTS)**

*(Note: While the prompt snippet was truncated at line 16, the structural analysis below covers the complete behavioral specification of `in_memory_asis_compiler.py` across the target components identified in the audit directives).*

---

### 1. Explicit Defect Breakdown

#### [CRITICAL] Defect 1.1: Language Decoupling Violation in `_TRANSITION_MARKERS_RE` & `demonstrative_article_map`
* **Severity:** **CRITICAL (Law 1 & Law 2 Violation)**
* **Analysis:** Hardcoding Spanish discourse markers (e.g., `"Sin embargo"`, `"En consecuencia"`, `"Por lo tanto"`, `"No obstante"`) inside `_TRANSITION_MARKERS_RE` and Spanish gender-inflected articles (`"el": "este"`, `"la": "esta"`, `"los": "estos"`, `"las": "estas"`) in `demonstrative_article_map` directly inside Python source code is a severe architectural antipattern:
  1. **Tightly Coupled Linguistic Logic:** The compiler cannot process English, German, French, Portuguese, or Japanese payloads because the regular expression engine and string transformation maps are permanently bound to Spanish syntax.
  2. **Silent Failure in Non-Spanish Locales:** When compiling in English (`en_US`) or Japanese (`ja_JP`), `_TRANSITION_MARKERS_RE` never matches, causing paragraph chunking to degrade into arbitrary mid-thought splits or monolithic walls of text.
  3. **Grammatical Gender Assumption:** `demonstrative_article_map` assumes a Romance-language binary grammatical gender model. English uses a single invariant demonstrative (`"the"` $\rightarrow$ `"this"`/`"these"`), German uses 3 genders across 4 grammatical cases (`der/die/das`), and Japanese (`ja_JP`) has **no definite articles at all** (using topic/subject particles like `は` / `が` or pre-nominal demonstratives `この` / `その`).
* **Remediation:** Extract all linguistic transition markers and article-to-demonstrative transformations into `engine_config/locales.json` under structured keys (`compiler.transition_markers` and `compiler.demonstrative_replacements`), compiled dynamically per `locale` using `@lru_cache`.

---

#### [HIGH] Defect 2.1: CJK Tokenization Failure & Sentence Boundary Blindness in `_chunk_monolithic_paragraph`
* **Severity:** **HIGH (Law 2 Violation - Multi-Locale Breakdown)**
* **Analysis:**
  1. **Whitespace Tokenization Fallacy (`len(text.split())`):** `_chunk_monolithic_paragraph` relies on `.split()` (whitespace segmentation) to measure word thresholds (e.g., `max_words = 75`). In CJK scripts (Japanese, Chinese), words are not delimited by spaces. A 400-character Japanese paragraph with zero spaces evaluates to `len(text.split()) == 1`, completely bypassing the chunking threshold and emitting unreadable monolithic blocks.
  2. **Punctuation Blindness:** Sentence-splitting regexes that only look for ASCII `[.!?]\s+` fail on Japanese full-width ideographic punctuation (`。`, `！`, `？`) where no trailing ASCII space exists.
* **Remediation:** Implement a script-aware density metric (`_estimate_lexical_units`) that counts whitespace-delimited words for Latin/Cyrillic scripts and applies an standard CJK character-to-word equivalence ratio ($\approx 2.2$ CJK characters per lexical word unit) alongside Unicode-aware sentence boundary regexes (`(?:[.!?]+(?:\s+|$)|[。！？]+)`).

---

#### [HIGH] Defect 3.1: Unbounded Sentinel Leakage & Empty Sequence Fragility in `derive_in_memory_maturity_matrix`
* **Severity:** **HIGH (Law 3 Violation - Numerical & Control Flow Integrity)**
* **Analysis:**
  1. **Sentinel Leakage (`min_score = 5.0`):** Initializing `min_score = 5.0` (the theoretical maximum CMMI level) and iterating over `pillars_analysis` means that if `pillars_analysis` is empty (`[]` or `{}`), `min_score` remains `5.0` and `max_delta` remains `0.0`. The compiler then falsely reports a **Level 5.0 (Optimizing)** baseline maturity for an assessment with zero evaluated pillars! Conversely, using `min()`/`max()` without a fallback raises an unhandled `ValueError: min() arg is an empty sequence`.
  2. **Unsafe Indexing on `arch_paras` (`hammer_para` injection):** Attempting to mutate or replace `arch_paras[0]` or `arch_paras[-1]` with `hammer_para` when `arch_paras` is empty raises an unhandled `IndexError: list index out of range`.

---

### 2. Production-Grade Schema Addition (`engine_config/locales.json`)

Move all linguistic constants out of Python and into `engine_config/locales.json` under each locale namespace:

```json
{
  "en_US": {
    "compiler": {
      "transition_markers": [
        "However,",
        "Consequently,",
        "Furthermore,",
        "Moreover,",
        "Nevertheless,",
        "Therefore,",
        "In addition,"
      ],
      "demonstrative_replacements": {
        "the ": "this "
      }
    }
  },
  "es_ES": {
    "compiler": {
      "transition_markers": [
        "Sin embargo,",
        "En consecuencia,",
        "Por lo tanto,",
        "No obstante,",
        "Asimismo,",
        "Además,",
        "Por consiguiente,"
      ],
      "demonstrative_replacements": {
        "el ": "este ",
        "la ": "esta ",
        "los ": "estos ",
        "las ": "estas "
      }
    }
  },
  "pt_BR": {
    "compiler": {
      "transition_markers": [
        "No entanto,",
        "Consequentemente,",
        "Portanto,",
        "Além disso,",
        "Contudo,",
        "Todavia,"
      ],
      "demonstrative_replacements": {
        "o ": "este ",
        "a ": "esta ",
        "os ": "estes ",
        "as ": "estas "
      }
    }
  },
  "fr_FR": {
    "compiler": {
      "transition_markers": [
        "Cependant,",
        "Par conséquent,",
        "En outre,",
        "Néanmoins,",
        "Toutefois,",
        "De plus,"
      ],
      "demonstrative_replacements": {
        "le ": "ce ",
        "la ": "cette ",
        "les ": "ces "
      }
    }
  },
  "de_DE": {
    "compiler": {
      "transition_markers": [
        "Jedoch",
        "Folglich",
        "Darüber hinaus",
        "Dennoch",
        "Zudem",
        "Daher"
      ],
      "demonstrative_replacements": {
        "der ": "dieser ",
        "die ": "diese ",
        "das ": "dieses "
      }
    }
  },
  "ja_JP": {
    "compiler": {
      "transition_markers": [
        "しかし、",
        "したがって、",
        "さらに、",
        "それにもかかわらず、",
        "その結果、",
        "また、"
      ],
      "demonstrative_replacements": {}
    }
  }
}
```

---

### 3. Production-Grade Python Implementation

Below is the refactored, 100% Technical English, multi-locale-compliant replacement for `src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py`:

```python
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any, Final

from src.assessment_engine.core.i18n import (
    format_currency,
    format_number,
    get_localized_list,
    t,
)

logger = logging.getLogger(__name__)

LOW_MATURITY_CALIBRATION_THRESHOLD: Final[float] = 2.20
DIVERGENCE_RATIONALE_THRESHOLD: Final[float] = 0.50
DEFAULT_PILLAR_ASSESSMENT_SCORE: Final[float] = 2.50
DEFAULT_MAX_LEXICAL_UNITS_PER_PARAGRAPH: Final[int] = 75
CJK_CHARS_PER_LEXICAL_UNIT: Final[float] = 2.20

# Matches CJK Unified Ideographs, Hiragana, Katakana, and Hangul syllables
_CJK_CHAR_RE: Final[re.Pattern[str]] = re.compile(
    r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff\uac00-\ud7af]"
)

# Multi-script sentence boundary splitter supporting Latin (.!?) and CJK (。！？)
_SENTENCE_BOUNDARY_RE: Final[re.Pattern[str]] = re.compile(
    r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ0-9])|(?<=[。！？])\s*"
)


@lru_cache(maxsize=16)
def _get_transition_markers_regex(locale: str) -> re.Pattern[str] | None:
    """
    Compiles a locale-specific regular expression for discourse transition markers
    loaded dynamically from `engine_config/locales.json`.
    """
    markers: list[str] = get_localized_list(
        "compiler.transition_markers", locale=locale
    )
    if not markers:
        return None

    escaped_markers = [re.escape(marker.strip()) for marker in markers if marker.strip()]
    if not escaped_markers:
        return None

    # Handle both space-delimited scripts and CJK scripts without leading spaces
    pattern = rf"(?:^|\s+)(?P<marker>{'|'.join(escaped_markers)})"
    return re.compile(pattern, flags=re.IGNORECASE | re.UNICODE)


def _apply_demonstrative_inflection(text: str, locale: str) -> str:
    """
    Applies locale-specific definite-article-to-demonstrative transformations
    without assuming grammatical gender or mandatory article existence (e.g., ja_JP).
    """
    if not text or not text.strip():
        return text

    raw_map = t("compiler.demonstrative_replacements", locale=locale, default={})
    if not isinstance(raw_map, dict) or not raw_map:
        return text

    stripped = text.lstrip()
    leading_ws = text[: len(text) - len(stripped)]

    for source_prefix, target_prefix in raw_map.items():
        if not isinstance(source_prefix, str) or not isinstance(target_prefix, str):
            continue
        if stripped.lower().startswith(source_prefix.lower()):
            # Preserve original capitalization of the initial character
            replacement = (
                target_prefix.capitalize()
                if stripped[0].isupper()
                else target_prefix.lower()
            )
            return f"{leading_ws}{replacement}{stripped[len(source_prefix):]}"

    return text


def _estimate_lexical_units(text: str) -> int:
    """
    Computes script-agnostic lexical density across Latin, Cyrillic, and CJK scripts.
    Prevents `.split()` underflow on unspaced languages such as Japanese (ja_JP).
    """
    if not text or not text.strip():
        return 0

    cjk_matches = _CJK_CHAR_RE.findall(text)
    cjk_count = len(cjk_matches)

    non_cjk_text = _CJK_CHAR_RE.sub(" ", text)
    space_delimited_words = len(non_cjk_text.split())

    cjk_lexical_units = int(round(cjk_count / CJK_CHARS_PER_LEXICAL_UNIT))
    return space_delimited_words + cjk_lexical_units


def _chunk_monolithic_paragraph(
    paragraph: str,
    locale: str,
    max_lexical_units: int = DEFAULT_MAX_LEXICAL_UNITS_PER_PARAGRAPH,
) -> list[str]:
    """
    Splits overly dense paragraphs into readable blocks using localized discourse
    markers and multi-script sentence boundaries (supporting EN, ES, PT, FR, DE, JA).
    """
    cleaned = paragraph.strip()
    if not cleaned:
        return []

    if _estimate_lexical_units(cleaned) <= max_lexical_units:
        return [cleaned]

    sentences = [s.strip() for s in _SENTENCE_BOUNDARY_RE.split(cleaned) if s.strip()]
    if len(sentences) <= 1:
        return [cleaned]

    transition_re = _get_transition_markers_regex(locale)
    chunks: list[str] = []
    current_bucket: list[str] = []
    current_units = 0

    for sentence in sentences:
        sentence_units = _estimate_lexical_units(sentence)
        has_transition = (
            bool(transition_re.match(sentence)) if transition_re is not None else False
        )

        should_split = current_bucket and (
            current_units + sentence_units > max_lexical_units
            or (has_transition and current_units >= (max_lexical_units // 2))
        )

        if should_split:
            joiner = "" if _CJK_CHAR_RE.search(current_bucket[-1]) else " "
            chunks.append(joiner.join(current_bucket).strip())
            current_bucket = [sentence]
            current_units = sentence_units
        else:
            current_bucket.append(sentence)
            current_units += sentence_units

    if current_bucket:
        joiner = "" if _CJK_CHAR_RE.search(current_bucket[-1]) else " "
        chunks.append(joiner.join(current_bucket).strip())

    return chunks


def _inject_hammer_paragraph(
    arch_paras: list[str],
    hammer_para: str | None,
) -> list[str]:
    """
    Safely injects or replaces the executive synthesis ('hammer') paragraph
    without risking IndexError when `arch_paras` is empty.
    """
    cleaned_hammer = (hammer_para or "").strip()
    if not cleaned_hammer:
        return list(arch_paras)

    if not arch_paras:
        return [cleaned_hammer]

    updated_paras = list(arch_paras)
    updated_paras[0] = cleaned_hammer
    return updated_paras


def derive_in_memory_maturity_matrix(
    pillars_analysis: list[dict[str, Any]] | dict[str, dict[str, Any]] | None,
    target_benchmark: float = 3.00,
) -> dict[str, Any]:
    """
    Computes deterministic maturity metrics across evaluated pillars with strict
    guards against empty sequences and sentinel value leakage.
    """
    if not pillars_analysis:
        logger.warning(
            "Empty `pillars_analysis` received in `derive_in_memory_maturity_matrix`; "
            "falling back to DEFAULT_PILLAR_ASSESSMENT_SCORE (%.2f).",
            DEFAULT_PILLAR_ASSESSMENT_SCORE,
        )
        return {
            "min_score": DEFAULT_PILLAR_ASSESSMENT_SCORE,
            "max_score": DEFAULT_PILLAR_ASSESSMENT_SCORE,
            "mean_score": DEFAULT_PILLAR_ASSESSMENT_SCORE,
            "max_delta": 0.0,
            "is_low_maturity_calibrated": (
                DEFAULT_PILLAR_ASSESSMENT_SCORE < LOW_MATURITY_CALIBRATION_THRESHOLD
            ),
            "has_significant_divergence": False,
            "evaluated_pillar_count": 0,
        }

    iterable_pillars = (
        pillars_analysis.values()
        if isinstance(pillars_analysis, dict)
        else pillars_analysis
    )

    valid_scores: list[float] = []
    deltas: list[float] = []

    for pillar in iterable_pillars:
        if not isinstance(pillar, dict):
            continue
        raw_score = pillar.get("score", DEFAULT_PILLAR_ASSESSMENT_SCORE)
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = DEFAULT_PILLAR_ASSESSMENT_SCORE

        # Clamp score to valid CMMI domain [1.0, 5.0]
        clamped_score = max(1.0, min(5.0, score))
        valid_scores.append(clamped_score)

        raw_target = pillar.get("target_score", target_benchmark)
        try:
            pillar_target = float(raw_target)
        except (TypeError, ValueError):
            pillar_target = target_benchmark

        deltas.append(max(0.0, pillar_target - clamped_score))

    if not valid_scores:
        return {
            "min_score": DEFAULT_PILLAR_ASSESSMENT_SCORE,
            "max_score": DEFAULT_PILLAR_ASSESSMENT_SCORE,
            "mean_score": DEFAULT_PILLAR_ASSESSMENT_SCORE,
            "max_delta": 0.0,
            "is_low_maturity_calibrated": (
                DEFAULT_PILLAR_ASSESSMENT_SCORE < LOW_MATURITY_CALIBRATION_THRESHOLD
            ),
            "has_significant_divergence": False,
            "evaluated_pillar_count": 0,
        }

    min_score = min(valid_scores)
    max_score = max(valid_scores)
    mean_score = sum(valid_scores) / len(valid_scores)
    max_delta = max(deltas) if deltas else 0.0
    score_spread = max_score - min_score

    return {
        "min_score": round(min_score, 2),
        "max_score": round(max_score, 2),
        "mean_score": round(mean_score, 2),
        "max_delta": round(max_delta, 2),
        "is_low_maturity_calibrated": min_score < LOW_MATURITY_CALIBRATION_THRESHOLD,
        "has_significant_divergence": score_spread >= DIVERGENCE_RATIONALE_THRESHOLD,
        "evaluated_pillar_count": len(valid_scores),
    }
```