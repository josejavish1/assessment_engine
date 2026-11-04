# RFC 068: Canonical Maturity Scale Unification & Elimination of Chapter 2 Semantic Split-Brain

**Status:** APPROVED — MANDATORY ENFORCEMENT  
**Author:** Principal Enterprise Systems Architect & Lead Ontologist  
**Domain:** Assessment Engine (`domain/maturity_band.py`, `engine_config/locales.json`, `tomo_compiler.py`)  
**Compliance:** 100% Technical English Codebase | 6-Locale Symmetry (`es`, `en`, `pt`, `fr`, `de`, `ja`) | Zero Hardcoding  

---

## 1. Ontological Audit & Theoretical Justification

### 1.1 The Mathematical Fallacy of the Naive Integer-Floor Scale (`1.0–1.9`, `2.0–2.9`, …, `5.00`)
The legacy prose in `tomo_ch2_intro` described a naive integer-truncation scale where Levels 1 through 4 each occupied a `1.00`-point interval (`[1.0, 2.0)`, `[2.0, 3.0)`, `[3.0, 4.0)`, `[4.0, 5.0)`) and Level 5 was compressed into a mathematical singularity (`5.00`). 

From an psychometric and enterprise ontology standpoint, this is a severe anti-pattern:
1. **Degenerate Top Tier (Zero-Measure Interval):** On a continuous domain $[1.00, 5.00]$ of total length $L = 4.00$, assigning Level 5 only to $5.00$ gives it Lebesgue measure $0.00$. In composite weighted aggregations across 20 technological annexes, achieving a perfect $5.00$ across every underlying vector is statistically impossible in production environments, rendering Level 5 (Optimized) unattainable.
2. **Semantic Split-Brain:** While the prose in `tomo_ch2_intro` claimed an integer-floor scale, the deterministic calculation engine (`domain/maturity_band.py` via `ANNEX_MATURITY_BANDS`) and all analytical tables classified capabilities using uniform **Equidistant Quintile Partitioning**.

### 1.2 The Authoritative Equidistant Quintile Scale ($\Delta = 0.80$)
The Assessment Engine evaluates maturity across a closed continuous interval $[1.00, 5.00]$. Partitioning a range of $4.00$ into $5$ equiprobable maturity tiers yields an exact step interval of:

$$\Delta = \frac{5.00 - 1.00}{5} = 0.80$$

| CMMI / COBIT Tier | Canonical `band_key` | Mathematical Interval | English Label | Spanish Label | Operational Ontology |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Level 1** | `level_1` | $[1.00, 1.79]$ | Initial | Inicial | Ad-hoc, unstandardized, heroic individual effort. |
| **Level 2** | `level_2` | $[1.80, 2.59]$ | Repeatable | Repetible | Basic operational hygiene, reactive discipline, localized repeatability. |
| **Level 3** | `level_3` | $[2.60, 3.39]$ | Defined | Definido | Standardized, documented, proactive governance across towers. |
| **Level 4** | `level_4` | $[3.40, 4.19]$ | Managed | Gestionado | Quantitatively measured, SLA/SLO-driven, predictable performance. |
| **Level 5** | `level_5` | $[4.20, 5.00]$ | Optimized | Optimizado | Autonomous self-healing, continuous innovation, FinOps/AIOps excellence. |

### 1.3 Resolution of Executive Score Contradictions
By enforcing the SSOT across all narrative templates:
* **Global Composite Score (`2.55`):** Strictly resolves to **Level 2 (Repeatable / Repetible)** (`1.80 – 2.59`), sitting just $0.05$ points below the threshold of Level 3 (`2.60`).
* **Tower 1 Score (`2.60`):** Strictly resolves to the entry boundary of **Level 3 (Defined / Definido)** (`2.60 – 3.39`), matching Table 2 and the Executive Cockpit.
* **Sector Benchmark (`3.50`):** Strictly resolves to **Level 4 (Managed / Gestionado)** (`3.40 – 4.19`), matching the quantitative target tier across all charts and tables.

---

## 2. Canonical Text Rewrites (`engine_config/locales.json`)

To eliminate hardcoding of numerical boundaries in prose, `tomo_ch2_intro` must dynamically interpolate the localized boundary strings or use the exact canonical ranges synced with `ANNEX_MATURITY_BANDS`. Below are the authoritative 6-locale definitions for `engine_config/locales.json`.

```json
{
  "cmmi_level_1_name": {
    "es": "Inicial",
    "en": "Initial",
    "pt": "Inicial",
    "fr": "Initial",
    "de": "Initial",
    "ja": "初期"
  },
  "cmmi_level_2_name": {
    "es": "Repetible",
    "en": "Repeatable",
    "pt": "Repetível",
    "fr": "Répétable",
    "de": "Wiederholbar",
    "ja": "反復可能"
  },
  "cmmi_level_3_name": {
    "es": "Definido",
    "en": "Defined",
    "pt": "Definido",
    "fr": "Défini",
    "de": "Definiert",
    "ja": "定義済み"
  },
  "cmmi_level_4_name": {
    "es": "Gestionado",
    "en": "Managed",
    "pt": "Gerenciado",
    "fr": "Géré",
    "de": "Gesteuert",
    "ja": "管理された"
  },
  "cmmi_level_5_name": {
    "es": "Optimizado",
    "en": "Optimized",
    "pt": "Otimizado",
    "fr": "Optimisé",
    "de": "Optimiert",
    "ja": "最適化された"
  },
  "tomo_ch2_intro": {
    "es": "La evaluación de capacidades de infraestructura y operaciones se rige por el estándar internacional CMMI (Capability Maturity Model Integration) y el marco COBIT, estructurados en una escala continua de cinco niveles equidistantes: Nivel 1 (Inicial / Ad-Hoc: {l1_range}), Nivel 2 (Repetible / Reactivo: {l2_range}), Nivel 3 (Definido / Proactivo: {l3_range}), Nivel 4 (Gestionado / Medido Cuantitativamente: {l4_range}) y Nivel 5 (Optimizado / Mejora Continua: {l5_range}). Bajo esta taxonomía canónica, la organización registra un índice de madurez global de {overall_score} ({overall_band_label}), situándose a {gap_to_benchmark} puntos del benchmark sectorial de {benchmark_score} ({benchmark_band_label}).",
    "en": "The infrastructure and operations capability assessment is governed by the international CMMI (Capability Maturity Model Integration) standard and the COBIT framework, structured across a continuous five-tier equidistant scale: Level 1 (Initial / Ad-Hoc: {l1_range}), Level 2 (Repeatable / Reactive: {l2_range}), Level 3 (Defined / Proactive: {l3_range}), Level 4 (Managed / Quantitatively Measured: {l4_range}), and Level 5 (Optimized / Continuous Improvement: {l5_range}). Under this canonical taxonomy, the organization records an overall maturity index of {overall_score} ({overall_band_label}), standing {gap_to_benchmark} points below the sector benchmark of {benchmark_score} ({benchmark_band_label}).",
    "pt": "A avaliação de capacidades de infraestrutura e operações é regida pelo padrão internacional CMMI (Capability Maturity Model Integration) e pelo framework COBIT, estruturados em uma escala contínua de cinco níveis equidistantes: Nível 1 (Inicial / Ad-Hoc: {l1_range}), Nível 2 (Repetível / Reativo: {l2_range}), Nível 3 (Definido / Proativo: {l3_range}), Nível 4 (Gerenciado / Medido Quantitativamente: {l4_range}) e Nível 5 (Otimizado / Melhoria Contínua: {l5_range}). Sob esta taxonomia canônica, a organização registra um índice de maturidade global de {overall_score} ({overall_band_label}), situando-se a {gap_to_benchmark} pontos do benchmark setorial de {benchmark_score} ({benchmark_band_label}).",
    "fr": "L'évaluation des capacités d'infrastructure et d'opérations est régie par la norme internationale CMMI (Capability Maturity Model Integration) et le référentiel COBIT, structurés sur une échelle continue à cinq niveaux équidistants : Niveau 1 (Initial / Ad-Hoc : {l1_range}), Niveau 2 (Répétable / Réactif : {l2_range}), Niveau 3 (Défini / Proactif : {l3_range}), Niveau 4 (Géré / Mesuré Quantitativement : {l4_range}) et Niveau 5 (Optimisé / Amélioration Continue : {l5_range}). Selon cette taxonomie canonique, l'organisation enregistre un indice de maturité global de {overall_score} ({overall_band_label}), se situant à {gap_to_benchmark} points de l'indice de référence sectoriel de {benchmark_score} ({benchmark_band_label}).",
    "de": "Die Bewertung der Infrastruktur- und Betriebsfähigkeiten richtet sich nach dem internationalen CMMI-Standard (Capability Maturity Model Integration) und dem COBIT-Rahmenwerk, strukturiert auf einer kontinuierlichen fünfstufigen äquidistanten Skala: Stufe 1 (Initial / Ad-Hoc: {l1_range}), Stufe 2 (Wiederholbar / Reaktiv: {l2_range}), Stufe 3 (Definiert / Proaktiv: {l3_range}), Stufe 4 (Gesteuert / Quantitativ Gemessen: {l4_range}) und Stufe 5 (Optimiert / Kontinuierliche Verbesserung: {l5_range}). Gemäß dieser kanonischen Taxonomie verzeichnet die Organisation einen Gesamtreifegradindex von {overall_score} ({overall_band_label}) und liegt damit {gap_to_benchmark} Punkte unter dem Branchen-Benchmark von {benchmark_score} ({benchmark_band_label}).",
    "ja": "インフラストラクチャおよび運用能力の評価は、国際標準であるCMMI（能力成熟度モデル統合）およびCOBITフレームワークに準拠し、5段階の等間隔連続スケールで構成されています：レベル1（初期／アドホック：{l1_range}）、レベル2（反復可能／リアクティブ：{l2_range}）、レベル3（定義済み／プロアクティブ：{l3_range}）、レベル4（管理された／定量的測定：{l4_range}）、レベル5（最適化された／継続的改善：{l5_range}）。この正規分類に基づき、組織の総合成熟度指数は {overall_score}（{overall_band_label}）であり、業界ベンチマークである {benchmark_score}（{benchmark_band_label}）から {gap_to_benchmark} ポイントの乖離があります。"
  }
}
```

---

## 3. Chapter 1 & Chapter 2 Narrative Harmony Specification

### 3.1 Domain SSOT Enforcement (`domain/maturity_band.py`)
All compiler modules must resolve maturity band metadata exclusively through `resolve_maturity_band(score)` in `domain/maturity_band.py`. No template or compiler method may compute maturity tiers using `int(score)` or ad-hoc `if/else` branching.

```python
# domain/maturity_band.py
from dataclasses import dataclass
from typing import Tuple, Callable


@dataclass(frozen=True)
class MaturityBandSpec:
    level: int
    band_key: str
    name_locale_key: str
    range_locale_key: str
    min_score: float
    max_score: float


ANNEX_MATURITY_BANDS: Tuple[MaturityBandSpec, ...] = (
    MaturityBandSpec(1, "level_1", "cmmi_level_1_name", "cmmi_level_1_range", 1.00, 1.79),
    MaturityBandSpec(2, "level_2", "cmmi_level_2_name", "cmmi_level_2_range", 1.80, 2.59),
    MaturityBandSpec(3, "level_3", "cmmi_level_3_name", "cmmi_level_3_range", 2.60, 3.39),
    MaturityBandSpec(4, "level_4", "cmmi_level_4_name", "cmmi_level_4_range", 3.40, 4.19),
    MaturityBandSpec(5, "level_5", "cmmi_level_5_name", "cmmi_level_5_range", 4.20, 5.00),
)


def resolve_maturity_band(score: float) -> MaturityBandSpec:
    """Resolve a continuous maturity score [1.00, 5.00] to its canonical CMMI band."""
    rounded = round(float(score), 2)
    for band in ANNEX_MATURITY_BANDS:
        if band.min_score <= rounded <= band.max_score:
            return band
    if rounded < 1.00:
        return ANNEX_MATURITY_BANDS[0]
    return ANNEX_MATURITY_BANDS[-1]


def format_band_range(band: MaturityBandSpec, format_number: Callable[[float, int], str]) -> str:
    """Format band min/max boundaries using the active locale's numeric formatter."""
    return f"{format_number(band.min_score, 2)} - {format_number(band.max_score, 2)}"
```

### 3.2 Dynamic Context Binding in the Compiler
When rendering Chapter 1 (`tomo_ch1_*`) and Chapter 2 (`tomo_ch2_*`), the compiler must bind all range strings and score labels dynamically via `resolve_maturity_band` and `format_number`:

```python
def build_ch2_intro_context(
    overall_score: float,
    benchmark_score: float,
    translate: Callable[[str], str],
    format_number: Callable[[float, int], str],
) -> dict[str, str]:
    """Build locale-aware interpolation context for Chapter 2 introduction."""
    overall_band = resolve_maturity_band(overall_score)
    benchmark_band = resolve_maturity_band(benchmark_score)
    gap = round(benchmark_score - overall_score, 2)

    range_map = {
        f"l{band.level}_range": format_band_range(band, format_number)
        for band in ANNEX_MATURITY_BANDS
    }

    return {
        **range_map,
        "overall_score": format_number(overall_score, 2),
        "overall_band_label": f"{translate(f'cmmi_level_{overall_band.level}_prefix')} {translate(overall_band.name_locale_key)}",
        "benchmark_score": format_number(benchmark_score, 2),
        "benchmark_band_label": f"{translate(f'cmmi_level_{benchmark_band.level}_prefix')} {translate(benchmark_band.name_locale_key)}",
        "gap_to_benchmark": format_number(gap, 2),
    }
```

---

## 4. Test Oracle & Verification Suite (`tests/test_rfc068_maturity_unification.py`)

The following pytest suite serves as the mandatory gate in CI/CD to prevent any regression or semantic split-brain across all 6 locales.

```python
import re
import pytest
from domain.maturity_band import ANNEX_MATURITY_BANDS, resolve_maturity_band, format_band_range

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")

FORBIDDEN_LEGACY_RANGES = (
    r"1[.,]0\s*-\s*1[.,]9\b",
    r"2[.,]0\s*-\s*2[.,]9\b",
    r"3[.,]0\s*-\s*3[.,]9\b",
    r"4[.,]0\s*-\s*4[.,]9\b",
)


def test_equidistant_band_partitioning_invariants():
    """Verify the 5 canonical bands cover [1.00, 5.00] with exact 0.79/0.80 step continuity."""
    assert len(ANNEX_MATURITY_BANDS) == 5
    expected_bounds = [
        (1, "level_1", 1.00, 1.79),
        (2, "level_2", 1.80, 2.59),
        (3, "level_3", 2.60, 3.39),
        (4, "level_4", 3.40, 4.19),
        (5, "level_5", 4.20, 5.00),
    ]
    for band, (lvl, key, low, high) in zip(ANNEX_MATURITY_BANDS, expected_bounds):
        assert band.level == lvl
        assert band.band_key == key
        assert band.min_score == low
        assert band.max_score == high


@pytest.mark.parametrize(
    "score,expected_level,expected_key",
    [
        (1.00, 1, "level_1"),
        (1.79, 1, "level_1"),
        (1.80, 2, "level_2"),
        (2.55, 2, "level_2"),  # Global Composite Score -> Level 2 (Repeatable)
        (2.59, 2, "level_2"),
        (2.60, 3, "level_3"),  # Tower 1 Score -> Level 3 (Defined)
        (3.39, 3, "level_3"),
        (3.40, 4, "level_4"),
        (3.50, 4, "level_4"),  # Sector Benchmark -> Level 4 (Managed)
        (4.19, 4, "level_4"),
        (4.20, 5, "level_5"),
        (5.00, 5, "level_5"),
    ],
)
def test_canonical_score_resolution(score: float, expected_level: int, expected_key: str):
    """Certify boundary and executive reference scores resolve to exact SSOT tiers."""
    band = resolve_maturity_band(score)
    assert band.level == expected_level
    assert band.band_key == expected_key


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_no_legacy_ranges_in_locales_json(locale: str, locales_config: dict):
    """Ensure no locale string in engine_config/locales.json contains legacy integer-floor ranges."""
    for key, translations in locales_config.items():
        assert locale in translations, f"Missing locale '{locale}' in key '{key}'"
        text = str(translations[locale])
        for pattern in FORBIDDEN_LEGACY_RANGES:
            assert not re.search(pattern, text), (
                f"Forbidden legacy CMMI range matching '{pattern}' found in {key}[{locale}]"
            )
```