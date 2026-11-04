"""Dynamic Loss Magnitude (LM) scale calibrator for universal multi-tenant currencies and enterprise scales.

Eliminates static EUR/USD hardcoded thresholds in Open FAIR 5x5 Heatmaps:
1. Anchors LM 1..5 thresholds dynamically to tenant operational downtime cost or annual turnover.
2. Applies static currency parity multipliers for zero-decimal and high-denomination currencies (e.g., JPY, KRW).
3. Hardens against IEEE-754 NaN/inf, clamps micro-revenue baselines, and enforces Clean Architecture immutability.
4. Unifies discrete scale resolution (1..5) across AST and document compilers, eradicating split-brains.
"""

from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from types import MappingProxyType
from typing import Any, Callable, Dict, Final, Mapping, Tuple

# Heatmap Matrix Cell Severity Thresholds (TEF 1..5 * LM 1..5)
HEATMAP_SEVERITY_HIGH_THRESHOLD: Final[int] = 15
HEATMAP_SEVERITY_MED_THRESHOLD: Final[int] = 8

# MCDA, DII & TEF Narrative Thresholds
MCDA_EXTREME_THRESHOLD: Final[float] = 80.0
MCDA_HIGH_THRESHOLD: Final[float] = 50.0
MCDA_FEASIBILITY_FAVORABLE_THRESHOLD: Final[float] = 60.0
DII_HIGH_STABILITY_THRESHOLD: Final[float] = 15.0
DII_MODERATE_STABILITY_THRESHOLD: Final[float] = 30.0
TEF_RESILIENCE_HIGH_THRESHOLD: Final[float] = 4.0
TEF_RESILIENCE_MED_THRESHOLD: Final[float] = 2.5

# Baseline Monetary Units in EUR for zero-telemetry canonical engagements
BASE_UNIT_STANDARD_EUR: Final[float] = 1000.0
BASE_UNIT_CRITICAL_EUR: Final[float] = 2500.0

# Minimum Absolute Threshold Floors to prevent micro-revenue collapse
MIN_FLOOR_STANDARD_EUR: Final[float] = 100.0
MIN_FLOOR_CRITICAL_EUR: Final[float] = 250.0

# Actuarial Scaling Factors anchored to Corporate Turnover
REVENUE_SCALE_FACTOR_STANDARD: Final[float] = 0.00001  # 0.001% of annual turnover
REVENUE_SCALE_FACTOR_CRITICAL: Final[float] = 0.00005  # 0.005% of annual turnover

# Operational Downtime Burn Multipliers
DOWNTIME_BURN_MULTIPLIER_STANDARD: Final[float] = 1.0  # 1 hour of operational burn
DOWNTIME_BURN_MULTIPLIER_CRITICAL: Final[float] = 2.0  # 2 hours of operational burn

# Discrete Tier Multipliers (Geometric progression across LM 1..5 tiers)
LM_PROGRESSION_STANDARD: Final[Tuple[float, float, float, float]] = (1.0, 4.0, 16.0, 64.0)
LM_PROGRESSION_CRITICAL: Final[Tuple[float, float, float, float]] = (1.0, 5.0, 25.0, 100.0)

# Canonical Open FAIR Discrete Thresholds
CANONICAL_TEF_THRESHOLDS: Final[Tuple[float, float, float, float]] = (0.1, 0.5, 2.0, 10.0)
CANONICAL_LM_STANDARD_THRESHOLDS: Final[Tuple[float, float, float, float]] = (1000.0, 4000.0, 16000.0, 64000.0)
CANONICAL_LM_CRITICAL_THRESHOLDS: Final[Tuple[float, float, float, float]] = (2500.0, 12500.0, 62500.0, 250000.0)

# Error Propagation Index (ERC) Thresholds
ERC_HIGH_THRESHOLD: Final[float] = 0.50
ERC_MEDIUM_THRESHOLD: Final[float] = 0.20

# Static baseline currency parity factors relative to 1.0 EUR/USD (macro purchasing power / unit scale)
CURRENCY_SCALE_PARITY: Final[Mapping[str, float]] = MappingProxyType({
    # Americas
    "USD": 1.0,
    "$": 1.0,
    "CAD": 1.45,
    "CA$": 1.45,
    "BRL": 5.5,
    "R$": 5.5,
    "MXN": 18.0,
    "ARS": 1000.0,
    "CLP": 950.0,
    "COP": 4000.0,
    "PEN": 3.8,
    # Europe
    "EUR": 1.0,
    "€": 1.0,
    "GBP": 0.85,
    "£": 0.85,
    "CHF": 0.95,
    "SFR": 0.95,
    "FR.": 0.95,
    "SFR.": 0.95,
    "SEK": 11.0,
    "KR": 11.0,
    "KR.": 11.0,
    "NOK": 11.0,
    "DKK": 7.5,
    "ISK": 140.0,
    "PLN": 4.3,
    "ZŁ": 4.3,
    "HUF": 395.0,
    "CZK": 25.0,
    "TRY": 34.0,
    # Asia-Pacific
    "JPY": 160.0,
    "¥": 160.0,
    "CNY": 7.2,
    "RMB": 7.2,
    "CNH": 7.2,
    "KRW": 1400.0,
    "₩": 1400.0,
    "AUD": 1.6,
    "A$": 1.6,
    "NZD": 1.65,
    "NZ$": 1.65,
    "SGD": 1.45,
    "S$": 1.45,
    "HKD": 8.0,
    "HK$": 8.0,
    "TWD": 32.0,
    "NT$": 32.0,
    "THB": 35.0,
    "IDR": 16000.0,
    "VND": 25000.0,
    "₫": 25000.0,
    "MYR": 4.5,
    "PHP": 56.0,
    "INR": 90.0,
    "₹": 90.0,
    "KZT": 500.0,
    "PKR": 300.0,
    # Middle East & Africa
    "AED": 3.67,
    "SAR": 3.75,
    "QAR": 3.65,
    "KWD": 0.33,
    "BHD": 0.40,
    "OMR": 0.42,
    "JOD": 0.78,
    "ILS": 3.7,
    "₪": 3.7,
    "EGP": 52.0,
    "NGN": 1650.0,
    "ZAR": 18.5,
    "R": 18.5,
})

_DOT_THOUSANDS_LOCALES: Final[frozenset[str]] = frozenset(
    {"es", "de", "pt", "it", "nl", "da", "tr", "id", "vi", "pl", "ro", "el"}
)
_SPACE_THOUSANDS_LOCALES: Final[frozenset[str]] = frozenset(
    {"fr", "sv", "no", "nb", "nn", "fi", "ru", "cs", "hu", "sk", "uk"}
)
_APOSTROPHE_THOUSANDS_LOCALES: Final[frozenset[str]] = frozenset(
    {"de-ch", "fr-ch", "it-ch", "rm-ch"}
)

# Minimum monetary value threshold in 'lm' field to distinguish raw currency SLE from 1..10 scale scores
MIN_MONETARY_LM_CUTOFF: Final[float] = 25.0
MONETARY_CUTOFF_SCALE_RATIO: Final[float] = 0.1
MAX_MONETARY_LM_CUTOFF: Final[float] = 100.0
MAX_SAFE_BASE_THRESHOLD: Final[float] = 1e290

_STRICT_DOT_THOUSANDS_GROUP_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[+-]?[1-9]\d{0,2}(?:\.\d{3})+(?:,\d+)?$"
)
_STRICT_COMMA_THOUSANDS_GROUP_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[+-]?[1-9]\d{0,2}(?:,\d{3})+$"
)


def _extract_bcp47_lang_and_region(locale: str | None) -> Tuple[str, str, str]:
    """Extracts normalized (norm_loc, lang_code, region_code) from any BCP-47 locale tag."""
    norm_loc = str(locale or "").strip().replace("_", "-").lower()
    loc_parts = [p for p in norm_loc.split("-") if p]
    if not loc_parts:
        return "", "", ""
    lang_code = loc_parts[0]
    region_code = ""
    for part in loc_parts[1:]:
        # ISO 3166-1 alpha-2 (2 letters) or UN M.49 (3 digits)
        if (len(part) == 2 and part.isalpha()) or (len(part) == 3 and part.isdigit()):
            region_code = part
            break
    return norm_loc, lang_code, region_code


_AMBIGUOUS_SYMBOL_LOCALE_MAP: Final[Mapping[Tuple[str, str], str]] = MappingProxyType({
    ("¥", "zh-hk"): "HKD",
    ("¥", "zh-hant-hk"): "HKD",
    ("¥", "hk"): "HKD",
    ("¥", "zh-tw"): "TWD",
    ("¥", "zh-hant-tw"): "TWD",
    ("¥", "tw"): "TWD",
    ("¥", "zh"): "CNY",
    ("$", "pt-br"): "BRL",
    ("$", "br"): "BRL",
    ("$", "es-mx"): "MXN",
    ("$", "mx"): "MXN",
    ("$", "es-ar"): "ARS",
    ("$", "ar"): "ARS",
    ("$", "es-cl"): "CLP",
    ("$", "cl"): "CLP",
    ("$", "es-co"): "COP",
    ("$", "co"): "COP",
    ("$", "es-pe"): "PEN",
    ("$", "pe"): "PEN",
    ("$", "en-ca"): "CAD",
    ("$", "fr-ca"): "CAD",
    ("$", "ca"): "CAD",
    ("$", "en-au"): "AUD",
    ("$", "au"): "AUD",
    ("$", "en-nz"): "NZD",
    ("$", "nz"): "NZD",
    ("$", "en-sg"): "SGD",
    ("$", "sg"): "SGD",
    ("$", "zh-hk"): "HKD",
    ("$", "zh-hant-hk"): "HKD",
    ("$", "hk"): "HKD",
    ("$", "zh-tw"): "TWD",
    ("$", "zh-hant-tw"): "TWD",
    ("$", "tw"): "TWD",
})


_ACCOUNTING_NEGATIVE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\(\s*[\d.,'_\u2019\u00a0\u202f]+\s*\)|[\d.,'_\u2019\u00a0\u202f]+\s*-$"
)
_PRE_CURRENCY_NEGATIVE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[+-]\s*[^\deE\s.,'_\u2019\u00a0\u202f]+\s*\d|[^\deE\s.,'_\u2019\u00a0\u202f]+\s*-\s*\d"
)
_EXPLICIT_NEGATIVE_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\d.eE])-\s*(?:[^\d\s.,'_\u2019\u00a0\u202f]+\s*)?\d"
)
_NUMERIC_CLEAN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\d.+-])([+-])?\s*(\d(?:[\d.,'_\u2019\u00a0\u202f]*\d)?)((?:[eE][+-]?\d+)?)"
)


def safe_float(
    val: Any,
    locale: str | None = None,
    allow_zero: bool = False,
) -> float | None:
    """Safely extracts a finite positive (or non-negative if allow_zero=True) float from arbitrary inputs."""
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, str):
        stripped = val.strip()
        # Allow explicit float strings like 'inf' or 'nan' to be caught safely
        if stripped.lower() in ("inf", "+inf", "-inf", "infinity", "+infinity", "-infinity", "nan"):
            return None

        # Reject accounting negative notation e.g. "(1,500.00)", "($1,500)", "1,500-" and negative currency prefixes
        if (
            _ACCOUNTING_NEGATIVE_PATTERN.search(stripped)
            or _PRE_CURRENCY_NEGATIVE_PATTERN.search(stripped)
            or _EXPLICIT_NEGATIVE_PREFIX_PATTERN.search(stripped)
        ):
            return None

        match = _NUMERIC_CLEAN_PATTERN.search(stripped)
        if match:
            sign = match.group(1) or ""
            mantissa = match.group(2)
            exponent = match.group(3) or ""
            clean = sign + mantissa
        else:
            return None
        clean = "".join(clean.split()).replace("_", "").replace("'", "").replace("\u2019", "")

        norm_loc, lang_code, region_code = _extract_bcp47_lang_and_region(locale)
        is_swiss_locale = norm_loc in _APOSTROPHE_THOUSANDS_LOCALES or region_code == "ch"
        is_comma_decimal_locale = (
            is_swiss_locale
            or lang_code in _DOT_THOUSANDS_LOCALES
            or lang_code in _SPACE_THOUSANDS_LOCALES
        ) and not (lang_code == "es" and region_code in ("mx", "us", "pr"))
        is_dot_thousands_locale = (
            lang_code in _DOT_THOUSANDS_LOCALES
            and not is_swiss_locale
            and not (lang_code == "es" and region_code in ("mx", "us", "pr"))
        )

        # Resilient European string formatting: 50.000.000,00 -> 50000000.00
        if "." in clean and "," in clean:
            if clean.rfind(",") > clean.rfind("."):
                clean = clean.replace(".", "").replace(",", ".")
            else:
                clean = clean.replace(",", "")
        elif "," in clean:
            parts = clean.split(",")
            if len(parts) == 2:
                # Treat comma as decimal separator if:
                # 1. Explicit comma-decimal locale is active, OR
                # 2. Fractional part is not exactly 3 digits, OR
                # 3. Leading integer part is '0', '+0', or '-0' (e.g. '0,125')
                if (
                    is_comma_decimal_locale
                    or len(parts[1]) != 3
                    or parts[0] in ("0", "+0", "-0")
                ):
                    clean = clean.replace(",", ".")
                else:
                    clean = clean.replace(",", "")
            elif _STRICT_COMMA_THOUSANDS_GROUP_PATTERN.match(clean):
                clean = clean.replace(",", "")
            else:
                return None
        elif clean.count(".") > 1:
            if _STRICT_DOT_THOUSANDS_GROUP_PATTERN.match(clean):
                clean = clean.replace(".", "")
            else:
                return None
        elif is_dot_thousands_locale and clean.count(".") == 1 and not exponent:
            dot_parts = clean.split(".")
            unsigned_int = dot_parts[0].lstrip("+-")
            # In dot-thousands locales without a decimal comma, a single dot followed by
            # exactly 3 digits is ONLY stripped as integer thousands if the trailing
            # group is strictly '000' (e.g. '1.000', '10.000', '250.000').
            # If the fractional part contains non-zero digits (e.g. '1.500', '10.500',
            # '12.300', '0.125'), it represents a fractional float and the dot is preserved.
            if (
                unsigned_int.isdigit()
                and not (len(unsigned_int) > 1 and unsigned_int.startswith("0"))
                and int(unsigned_int) > 0
                and _STRICT_DOT_THOUSANDS_GROUP_PATTERN.match(clean)
                and dot_parts[1] == "000"
            ):
                clean = clean.replace(".", "")
        val = clean + exponent
    try:
        f_val = float(val)
        if not math.isfinite(f_val):
            return None
        return f_val if (f_val >= 0.0 if allow_zero else f_val > 0.0) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _validate_thresholds(
    thresholds: Tuple[float, float, float, float] | Any,
    fallback: Tuple[float, float, float, float],
) -> Tuple[float, float, float, float]:
    """Ensures threshold tuple is a strictly ascending 4-tuple of positive finite floats."""
    try:
        if (
            thresholds is not None
            and len(thresholds) == 4
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0.0 for x in thresholds)
            and thresholds[0] < thresholds[1] < thresholds[2] < thresholds[3]
        ):
            return (float(thresholds[0]), float(thresholds[1]), float(thresholds[2]), float(thresholds[3]))
    except (TypeError, ValueError, IndexError):
        pass
    return fallback


def _is_positive_infinity(val: Any) -> bool:
    """Detects positive infinity in both float and string forms while rejecting negative infinity."""
    if val is None or isinstance(val, bool):
        return False
    try:
        f_val = float(val)
        return math.isinf(f_val) and f_val > 0.0
    except (TypeError, ValueError, OverflowError):
        return False


def clamp_scale_level(val: Any, default: int = 1, locale: str | None = None) -> int:
    """Safely converts and clamps an arbitrary scale level input to discrete 1..5."""
    if _is_positive_infinity(val):
        return 5
    clean = safe_float(val, locale=locale)
    if clean is None:
        return default
    try:
        return min(5, max(1, math.floor(clean + 0.5)))
    except (TypeError, ValueError, OverflowError):
        return default


def _snap_to_clean_step(val: float) -> float:
    """Snaps a positive float value to a clean executive round number with 2 significant digits."""
    if not math.isfinite(val) or val <= 0.0:
        return 1.0
    try:
        dec_val = Decimal(str(val))
        exponent = dec_val.adjusted()
        step_exp = max(0, exponent - 1) if dec_val >= Decimal("10") else 0
        dec_step = Decimal(f"1e{step_exp}")
        units = (dec_val / dec_step).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return float(max(units * dec_step, dec_step))
    except (InvalidOperation, ValueError, OverflowError):
        exponent_f = math.floor(math.log10(val))
        step_exp_f = max(0, exponent_f - 1) if val >= 10.0 else 0
        step = 10.0 ** step_exp_f
        units_f = math.floor(val / step + 0.5)
        return float(max(units_f * step, step))


def resolve_currency_parity(currency: str = "EUR", locale: str | None = None) -> float:
    """Resolves the macro purchasing-power parity multiplier for any currency code or symbol."""
    clean_currency = str(currency or "EUR").strip().upper()
    parity = float(CURRENCY_SCALE_PARITY.get(clean_currency, 1.0))

    norm_loc, lang_code, region_code = _extract_bcp47_lang_and_region(locale)

    mapped_iso = (
        _AMBIGUOUS_SYMBOL_LOCALE_MAP.get((clean_currency, norm_loc))
        or (_AMBIGUOUS_SYMBOL_LOCALE_MAP.get((clean_currency, region_code)) if region_code else None)
        or (_AMBIGUOUS_SYMBOL_LOCALE_MAP.get((clean_currency, lang_code)) if lang_code else None)
    )
    if not mapped_iso:
        for (sym, prefix), iso in _AMBIGUOUS_SYMBOL_LOCALE_MAP.items():
            if sym == clean_currency and (norm_loc == prefix or norm_loc.startswith(f"{prefix}-")):
                mapped_iso = iso
                break

    if mapped_iso:
        parity = float(CURRENCY_SCALE_PARITY.get(mapped_iso, parity))
    elif clean_currency in ("KR", "KR."):
        if lang_code == "da" or norm_loc == "dk" or region_code == "dk":
            parity = float(CURRENCY_SCALE_PARITY.get("DKK", 7.5))
        elif lang_code == "is" or region_code == "is":
            parity = float(CURRENCY_SCALE_PARITY.get("ISK", 140.0))
        elif lang_code in ("no", "nb", "nn") or region_code == "no":
            parity = float(CURRENCY_SCALE_PARITY.get("NOK", 11.0))
        else:
            parity = float(CURRENCY_SCALE_PARITY.get("SEK", 11.0))

    return parity


_UNAMBIGUOUS_SYMBOL_TO_ISO: Final[Mapping[str, str]] = MappingProxyType({
    "€": "EUR",
    "$": "USD",
    "£": "GBP",
    "¥": "JPY",
    "R$": "BRL",
    "CA$": "CAD",
    "A$": "AUD",
    "NZ$": "NZD",
    "S$": "SGD",
    "HK$": "HKD",
    "NT$": "TWD",
    "₹": "INR",
    "₩": "KRW",
    "₫": "VND",
    "₪": "ILS",
    "ZŁ": "PLN",
    "KR": "SEK",
    "KR.": "DKK",
    "R": "ZAR",
    "CHF": "CHF",
    "SFR": "CHF",
    "FR.": "CHF",
    "SFR.": "CHF",
})


def resolve_iso_currency_code(currency_token: str = "EUR", locale: str | None = None) -> str:
    """Resolves a currency symbol or code into an authoritative ISO 4217 code respecting locale."""
    clean_curr = str(currency_token or "EUR").strip()
    clean_upper = clean_curr.upper()
    norm_loc, lang_code, region_code = _extract_bcp47_lang_and_region(locale)

    mapped_iso = (
        _AMBIGUOUS_SYMBOL_LOCALE_MAP.get((clean_upper, norm_loc))
        or (_AMBIGUOUS_SYMBOL_LOCALE_MAP.get((clean_upper, region_code)) if region_code else None)
        or (_AMBIGUOUS_SYMBOL_LOCALE_MAP.get((clean_upper, lang_code)) if lang_code else None)
    )
    if not mapped_iso:
        for (sym, prefix), iso in _AMBIGUOUS_SYMBOL_LOCALE_MAP.items():
            if sym == clean_upper and (norm_loc == prefix or norm_loc.startswith(f"{prefix}-")):
                mapped_iso = iso
                break
    if mapped_iso:
        return mapped_iso

    if clean_upper in ("KR", "KR."):
        if lang_code == "da" or norm_loc == "dk" or region_code == "dk":
            return "DKK"
        if lang_code == "is" or region_code == "is":
            return "ISK"
        if lang_code in ("no", "nb", "nn") or region_code == "no":
            return "NOK"
        return "SEK"

    return _UNAMBIGUOUS_SYMBOL_TO_ISO.get(clean_curr, _UNAMBIGUOUS_SYMBOL_TO_ISO.get(clean_upper, clean_upper))


def compute_dynamic_lm_thresholds(
    currency: str = "EUR",
    annual_revenue: float | None = None,
    hourly_downtime_cost: float | None = None,
    is_critical_tier: bool = False,
    locale: str | None = None,
) -> Tuple[float, float, float, float]:
    """Computes the 4 boundary thresholds dividing Loss Magnitude into 5 discrete tiers (LM 1..5).

    Returns:
        Tuple of 4 ascending float thresholds: (t1, t2, t3, t4)
        LM 1: < t1
        LM 2: t1 <= val < t2
        LM 3: t2 <= val < t3
        LM 4: t3 <= val < t4
        LM 5: >= t4
    """
    parity = resolve_currency_parity(currency=currency, locale=locale)
    min_floor = (MIN_FLOOR_CRITICAL_EUR if is_critical_tier else MIN_FLOOR_STANDARD_EUR) * parity

    # 1. Anchor base threshold (t1) prioritizing hourly operational downtime burn
    burn_val = safe_float(hourly_downtime_cost, locale=locale)
    rev_val = safe_float(annual_revenue, locale=locale)

    if burn_val is not None:
        mult = DOWNTIME_BURN_MULTIPLIER_CRITICAL if is_critical_tier else DOWNTIME_BURN_MULTIPLIER_STANDARD
        base_unit = max(burn_val * mult, min_floor)
        clean_base = _snap_to_clean_step(base_unit)
    elif rev_val is not None:
        rev_factor = REVENUE_SCALE_FACTOR_CRITICAL if is_critical_tier else REVENUE_SCALE_FACTOR_STANDARD
        base_unit = max(rev_val * rev_factor, min_floor)
        clean_base = _snap_to_clean_step(base_unit)
    else:
        # Exact canonical base unit scaled by static currency parity and cleanly rounded
        canonical_base = BASE_UNIT_CRITICAL_EUR if is_critical_tier else BASE_UNIT_STANDARD_EUR
        clean_base = _snap_to_clean_step(canonical_base * parity)

    clean_base = min(clean_base, MAX_SAFE_BASE_THRESHOLD)
    progression = LM_PROGRESSION_CRITICAL if is_critical_tier else LM_PROGRESSION_STANDARD
    t1, t2, t3, t4 = [float(clean_base * m) for m in progression]
    return (t1, t2, t3, t4)


def resolve_dynamic_lm_scale_level(
    sle_amount: float | Any,
    thresholds: Tuple[float, float, float, float],
    locale: str | None = None,
) -> int:
    """Maps single loss expectancy (SLE) to discrete 1..5 LM scale level given dynamic thresholds."""
    if _is_positive_infinity(sle_amount):
        return 5

    val = safe_float(sle_amount, locale=locale)
    if val is None:
        return 1

    clean_bounds = _validate_thresholds(
        thresholds,
        CANONICAL_LM_STANDARD_THRESHOLDS,
    )

    if val < clean_bounds[0]:
        return 1
    if val < clean_bounds[1]:
        return 2
    if val < clean_bounds[2]:
        return 3
    if val < clean_bounds[3]:
        return 4
    return 5


def resolve_dynamic_tef_scale_level(
    lef_annual: float | Any,
    thresholds: Tuple[float, float, float, float] = CANONICAL_TEF_THRESHOLDS,
    locale: str | None = None,
) -> int:
    """Maps continuous Loss Event Frequency (events/year) to discrete 1..5 TEF scale level."""
    if _is_positive_infinity(lef_annual):
        return 5

    val = safe_float(lef_annual, locale=locale)
    if val is None:
        return 1

    clean_bounds = _validate_thresholds(thresholds, CANONICAL_TEF_THRESHOLDS)

    if val < clean_bounds[0]:
        return 1
    if val < clean_bounds[1]:
        return 2
    if val < clean_bounds[2]:
        return 3
    if val <= clean_bounds[3]:
        return 4
    return 5


def resolve_risk_matrix_coordinates(
    risk_entry: Mapping[str, Any],
    lm_thresholds: Tuple[float, float, float, float],
    tef_thresholds: Tuple[float, float, float, float] = CANONICAL_TEF_THRESHOLDS,
    locale: str | None = None,
) -> Tuple[int, int]:
    """Resolves discrete (tef_level, lm_level) coordinates for a risk item given dynamic thresholds.

    Decouples TEF and LM axes independently so partial telemetry is never discarded.
    """
    raw_lef = risk_entry.get("lef") if risk_entry.get("lef") is not None else risk_entry.get("tef_annual")
    if _is_positive_infinity(raw_lef):
        r_tef = 5
    else:
        f_lef = safe_float(raw_lef, locale=locale)
        if f_lef is not None:
            r_tef = resolve_dynamic_tef_scale_level(f_lef, tef_thresholds, locale=locale)
        elif "tef_scale_level" in risk_entry and risk_entry.get("tef_scale_level") is not None:
            r_tef = clamp_scale_level(risk_entry.get("tef_scale_level"), default=1, locale=locale)
        else:
            r_tef = clamp_scale_level(risk_entry.get("tef"), default=1, locale=locale)

    raw_sle = risk_entry.get("sle") if risk_entry.get("sle") is not None else risk_entry.get("effective_sle")
    if _is_positive_infinity(raw_sle):
        r_lm = 5
    else:
        f_sle = safe_float(raw_sle, locale=locale)
        if f_sle is not None:
            r_lm = resolve_dynamic_lm_scale_level(f_sle, lm_thresholds, locale=locale)
        elif "lm_scale_level" in risk_entry and risk_entry.get("lm_scale_level") is not None:
            r_lm = clamp_scale_level(risk_entry.get("lm_scale_level"), default=1, locale=locale)
        else:
            raw_lm_field = risk_entry.get("lm")
            f_lm = safe_float(raw_lm_field, locale=locale, allow_zero=True)
            clean_lm_bounds = _validate_thresholds(lm_thresholds, CANONICAL_LM_STANDARD_THRESHOLDS)
            monetary_cutoff = max(
                MIN_MONETARY_LM_CUTOFF,
                min(clean_lm_bounds[0] * MONETARY_CUTOFF_SCALE_RATIO, MAX_MONETARY_LM_CUTOFF),
            )
            if f_lm is not None and f_lm >= monetary_cutoff:
                r_lm = resolve_dynamic_lm_scale_level(f_lm, clean_lm_bounds, locale=locale)
            else:
                r_lm = clamp_scale_level(raw_lm_field, default=1, locale=locale)

    return (r_tef, r_lm)


def _format_integer_with_separator(val: float, thousands_sep: str = ".") -> str:
    """Pure domain numeric formatting with custom thousands separator and exact Decimal half-up rounding."""
    if not math.isfinite(val) or val <= 0.0:
        return "0"
    if val < 1.0:
        decimal_sep = "," if thousands_sep in (".", " ") else "."
        try:
            sub_unit = Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if sub_unit >= Decimal("1.00"):
                return "1"
            if sub_unit <= Decimal("0.00"):
                return "0"
            return f"{sub_unit:.2f}".replace(".", decimal_sep)
        except (InvalidOperation, ValueError, OverflowError):
            return "0"
    try:
        rounded = int(Decimal(str(val)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, OverflowError):
        rounded = 0
    raw = f"{rounded:,}"
    if thousands_sep != ",":
        return raw.replace(",", thousands_sep)
    return raw


def compute_dynamic_lm_brackets(
    currency: str = "EUR",
    locale: str = "en",
    annual_revenue: float | None = None,
    hourly_downtime_cost: float | None = None,
    is_critical_tier: bool = False,
    formatter: Callable[[float], str] | None = None,
    precomputed_thresholds: Tuple[float, float, float, float] | None = None,
) -> Dict[int, str]:
    """Generates localized display strings for Loss Magnitude columns in 5x5 Risk Heatmap headers."""
    valid_precomputed = _validate_thresholds(precomputed_thresholds, (0.0, 0.0, 0.0, 0.0))
    if valid_precomputed != (0.0, 0.0, 0.0, 0.0):
        t1, t2, t3, t4 = valid_precomputed
    else:
        t1, t2, t3, t4 = compute_dynamic_lm_thresholds(
            currency=currency,
            annual_revenue=annual_revenue,
            hourly_downtime_cost=hourly_downtime_cost,
            is_critical_tier=is_critical_tier,
            locale=locale,
        )

    clean_currency = str(currency or "EUR").strip()

    # Robust locale normalization supporting regional and script tags e.g. "es-ES", "es-MX", "zh-Hans-CN"
    raw_locale, lang_code, region_code = _extract_bcp47_lang_and_region(locale)

    if raw_locale in _APOSTROPHE_THOUSANDS_LOCALES or region_code == "ch":
        sep = "'"
    elif region_code in ("mx", "us", "pr") and lang_code == "es":
        sep = ","
    elif lang_code in _DOT_THOUSANDS_LOCALES:
        sep = "."
    elif lang_code in _SPACE_THOUSANDS_LOCALES:
        sep = " "
    else:
        sep = ","

    def default_fmt(val: float) -> str:
        return _format_integer_with_separator(val, thousands_sep=sep)

    fmt = formatter or default_fmt

    return {
        1: f"< {fmt(t1)} {clean_currency}",
        2: f"{fmt(t1)} - {fmt(t2)} {clean_currency}",
        3: f"{fmt(t2)} - {fmt(t3)} {clean_currency}",
        4: f"{fmt(t3)} - {fmt(t4)} {clean_currency}",
        5: f"≥ {fmt(t4)} {clean_currency}",
    }
