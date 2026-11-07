# RFC 078: Executive Editorial Simplification & Value Diagnosis Governance

**Status:** APPROVED FOR IMMEDIATE IMPLEMENTATION  
**Author:** Chief Corporate Governance Advisor & Executive Editorial Director  
**Target Release:** Assessment Engine v4.8 (Volume 1 / Consolidated AS-IS Diagnostic)  
**Architectural Invariants:** 100% Technical English Codebase | Zero Hardcoding | 6-Locale Mathematical Symmetry (`es`, `en`, `pt`, `fr`, `de`, `ja`) | Strict Page 3 Budget Preservation  

---

## 1. Executive Verdict & Heading Simplification Catalog

### 1.1 Executive Editorial Diagnosis
Board members, CEOs, CFOs, and CIOs read diagnostic deliverables to understand **operational risk, financial exposure, and capital allocation priorities**. They do not read board reports to decode internal software engineering acronyms (such as `SSOT`) or academic phrasing ("Radiografía de Polaridad", "Cuantificación Actuarial").

Furthermore, mixing minor residual financial risk figures (e.g., `30.242 € / año`) into the narrative of the portfolio's strongest maturity leader creates cognitive dissonance. When highlighting a benchmark domain, the executive takeaway must focus exclusively on **why** it is resilient (redundancy, vendor support, standardization)—not its residual actuarial noise. Conversely, financial loss figures belong strictly where they drive urgency: in the primary risk concentration vector.

### 1.2 Document-Wide Heading Simplification Catalog (Volume 1)

All verbose, academic, or developer-centric headings across Volume 1 (`consolidated_asis`) are hereby standardized to direct, high-impact executive titles across all 6 supported locales.

| Locale Key (`consolidated_asis.*`) | Legacy Verbose / Jargon Text (`es` reference) | New Executive-Grade Text (`es`) | New Executive-Grade Text (`en`) |
| :--- | :--- | :--- | :--- |
| `ch1_sec1_title` | `1.1. Radiografía de Polaridad y Extremos del Portafolio` | `1.1. Áreas Clave: Fortalezas y Puntos Críticos` | `1.1. Key Areas: Strengths & Critical Bottlenecks` |
| `ch1_polarity_col_axis` | `Eje de Polaridad del Portafolio` | `Indicador Clave` | `Key Indicator` |
| `ch1_polarity_col_domain` | `Dominio Identificado (SSOT)` | `Dominio Tecnológico` | `Technology Domain` |
| `ch1_polarity_col_telemetry` | `Telemetría e Impacto de Gobernanza` | `Diagnóstico y Consecuencia de Negocio` | `Executive Diagnosis & Business Impact` |
| `ch1_sec2_title` | `1.2. Síntesis de Posicionamiento Estratégico` | `1.2. Conclusiones Ejecutivas del Diagnóstico` | `1.2. Executive Diagnostic Conclusions` |
| `ch1_sec3_title` | `1.3. Cuantificación Actuarial de Exposición Financiera (Open FAIR™)` | `1.3. Impacto Económico Estimado del Riesgo` | `1.3. Estimated Economic Risk Impact` |
| `ch3_title` | `3. Evaluación Multidimensional de Madurez y Gobernanza` | `3. Evaluación de Madurez por Dominio Tecnológico` | `3. Maturity Assessment by Technology Domain` |
| `ch4_title` | `4. Modelado Actuarial de Riesgo Tecnológico (Open FAIR™)` | `4. Análisis de Riesgo Operativo y Financiero` | `4. Operational & Financial Risk Analysis` |
| `ch5_title` | `5. Deuda Técnica, Obsolescencia y Fragilidad Operativa` | `5. Obsolescencia Tecnológica y Vulnerabilidades` | `5. Technology Obsolescence & Vulnerabilities` |

#### Complete 6-Locale Heading Mapping Matrix (`pt`, `fr`, `de`, `ja`)

| Locale Key | `pt` (Portuguese) | `fr` (French) | `de` (German) | `ja` (Japanese) |
| :--- | :--- | :--- | :--- | :--- |
| `ch1_sec1_title` | `1.1. Áreas-Chave: Pontos Fortes e Críticos` | `1.1. Domaines Clés : Forces et Points Critiques` | `1.1. Kernbereiche: Stärken und Kritische Engpässe` | `1.1. 重要領域：強みと主要なボトルネック` |
| `ch1_polarity_col_axis` | `Indicador-Chave` | `Indicateur Clé` | `Schlüsselindikator` | `主要指標` |
| `ch1_polarity_col_domain` | `Domínio Tecnológico` | `Domaine Technologique` | `Technologiedomäne` | `技術ドメイン` |
| `ch1_polarity_col_telemetry` | `Diagnóstico e Impacto no Negócio` | `Diagnostic et Impact Métier` | `Diagnose und Geschäftsauswirkung` | `エグゼクティブ診断とビジネス影響` |
| `ch1_sec2_title` | `1.2. Conclusões Executivas do Diagnóstico` | `1.2. Conclusions Exécutives du Diagnostic` | `1.2. Wichtigste Ergebnisse der Diagnose` | `1.2. 診断のエグゼクティブ結論` |
| `ch1_sec3_title` | `1.3. Impacto Econômico Estimado do Risco` | `1.3. Impact Économique Estimé du Risque` | `1.3. Geschätzte Wirtschaftliche Risikoauswirkung` | `1.3. リスクの推定経済的影響` |
| `ch3_title` | `3. Avaliação de Maturidade por Domínio Tecnológico` | `3. Évaluation de la Maturité par Domaine Technologique` | `3. Reifegradbewertung nach Technologiedomäne` | `3. 技術ドメイン別の成熟度評価` |
| `ch4_title` | `4. Análise de Risco Operacional e Financeiro` | `4. Analyse des Risques Opérationnels et Financiers` | `4. Operationelle und Finanzielle Risikoanalyse` | `4. 運用および財務リスク分析` |
| `ch5_title` | `5. Obsolescência Tecnológica e Vulnerabilidades` | `5. Obsolescence Technologique et Vulnérabilités` | `5. Technologische Veralterung und Schwachstellen` | `5. 技術の老朽化と脆弱性` |

---

## 2. Refactored Table 1.1 Specification

### 2.1 Parameter Signature Modernization
To eliminate confusing metric cross-contamination while maintaining strict multi-tenant universality, the template token signatures for Table 1.1 rows in `locales.json` are refactored as follows:

1. **Row 1: Maturity Leader (`ch1_polarity_leader_desc`)**
   - **Removed Token:** `{ale}` (Residual Annualized Loss Expectancy is stripped from the leader row to prevent executive distraction).
   - **Retained Token:** `{score}` (Formatted maturity score, e.g., `3,30`).
   - **Strategic Narrative:** Highlights architectural standardization, active vendor support, redundancy, and its role as the internal governance reference model.
2. **Row 2: Primary Risk Concentration (`ch1_polarity_exposure_desc`)**
   - **Retained Tokens:** `{ale}` (Formatted currency exposure) and `{share}` (Percentage of total portfolio risk).
   - **Strategic Narrative:** Translates actuarial concentration into direct business consequence: service interruption in this domain halts core operational workflows and revenue execution.
3. **Row 3: Modernization Urgency (`ch1_polarity_laggard_desc`)**
   - **Retained Token:** `{score}` (Formatted lowest maturity score, e.g., `1,50`).
   - **Strategic Narrative:** Highlights structural vulnerability caused by manual operational workarounds, obsolete components, and absence of automated recovery mechanisms.

### 2.2 Symmetrical 6-Locale Template Catalog for Table 1.1

All templates below are **100% industry-agnostic** (zero hardcoded vertical nouns, company names, or domain codes) and strictly constrained in character length to preserve the **Single-Page Budget of Chapter 1 (Page 3)**.

```json
{
  "es": {
    "ch1_polarity_leader_axis": "Referente de Madurez",
    "ch1_polarity_leader_desc": "Nivel más alto de control ({score} / 5.00). Cuenta con soporte vigente, redundancia operativa y sirve como modelo interno de estandarización.",
    "ch1_polarity_exposure_axis": "Mayor Exposición Económica",
    "ch1_polarity_exposure_desc": "Concentra el {share}% del riesgo económico total ({ale} / año). Una caída en este ámbito detiene procesos críticos de operación y facturación.",
    "ch1_polarity_laggard_axis": "Prioridad de Modernización",
    "ch1_polarity_laggard_desc": "Nivel más bajo de madurez ({score} / 5.00). Opera con alta dependencia de tareas manuales y sin capacidad de recuperación automática ante fallos."
  },
  "en": {
    "ch1_polarity_leader_axis": "Maturity Benchmark",
    "ch1_polarity_leader_desc": "Highest control posture ({score} / 5.00). Backed by active support and operational redundancy, serving as the internal standardization model.",
    "ch1_polarity_exposure_axis": "Highest Economic Exposure",
    "ch1_polarity_exposure_desc": "Concentrates {share}% of total financial risk ({ale} / year). Outages in this domain directly halt critical operational and billing workflows.",
    "ch1_polarity_laggard_axis": "Modernization Priority",
    "ch1_polarity_laggard_desc": "Lowest maturity level ({score} / 5.00). Operates with heavy reliance on manual intervention and lacks automated failover recovery."
  },
  "pt": {
    "ch1_polarity_leader_axis": "Referência de Maturidade",
    "ch1_polarity_leader_desc": "Maior nível de controle ({score} / 5.00). Conta com suporte ativo, redundância operacional e serve como modelo interno de padronização.",
    "ch1_polarity_exposure_axis": "Maior Exposição Econômica",
    "ch1_polarity_exposure_desc": "Concentra {share}% do risco financeiro total ({ale} / ano). Uma falha neste domínio interrompe processos críticos de operação e faturamento.",
    "ch1_polarity_laggard_axis": "Prioridade de Modernização",
    "ch1_polarity_laggard_desc": "Menor nível de maturidade ({score} / 5.00). Opera com forte dependência de tarefas manuais e sem recuperação automática contra falhas."
  },
  "fr": {
    "ch1_polarity_leader_axis": "Référence de Maturité",
    "ch1_polarity_leader_desc": "Plus haut niveau de contrôle ({score} / 5.00). Bénéficie d'un support actif, d'une redondance opérationnelle et sert de modèle interne.",
    "ch1_polarity_exposure_axis": "Exposition Économique Maximale",
    "ch1_polarity_exposure_desc": "Concentre {share}% du risque financier total ({ale} / an). Une panne dans ce domaine bloque les processus critiques d'exploitation et de facturation.",
    "ch1_polarity_laggard_axis": "Priorité de Modernisation",
    "ch1_polarity_laggard_desc": "Plus faible niveau de maturité ({score} / 5.00). Fonctionne avec une forte dépendance manuelle sans capacité de reprise automatique."
  },
  "de": {
    "ch1_polarity_leader_axis": "Reifegrad-Referenz",
    "ch1_polarity_leader_desc": "Höchstes Kontrollniveau ({score} / 5.00). Verfügt über aktiven Support sowie Redundanz und dient als internes Standardisierungsmodell.",
    "ch1_polarity_exposure_axis": "Höchstes Wirtschaftliches Risiko",
    "ch1_polarity_exposure_desc": "Vereint {share}% des gesamten Finanzrisikos ({ale} / Jahr). Ein Ausfall in diesem Bereich stoppt kritische Betriebs- und Abrechnungsprozesse.",
    "ch1_polarity_laggard_axis": "Modernisierungspriorität",
    "ch1_polarity_laggard_desc": "Niedrigster Reifegrad ({score} / 5.00). Arbeitet mit hoher Abhängigkeit von manuellen Eingriffen ohne automatische Wiederherstellung."
  },
  "ja": {
    "ch1_polarity_leader_axis": "成熟度ベンチマーク",
    "ch1_polarity_leader_desc": "最高水準の管理体制（{score} / 5.00）。有効なサポートと運用冗長性を備え、社内標準化のモデルとして機能しています。",
    "ch1_polarity_exposure_axis": "最大経済的リスク領域",
    "ch1_polarity_exposure_desc": "全財務リスクの {share}%（年間 {ale}）が集中。この領域の停止は、基幹業務および請求プロセスを直接中断させます。",
    "ch1_polarity_laggard_axis": "近代化の最優先領域",
    "ch1_polarity_laggard_desc": "最低水準の成熟度（{score} / 5.00）。手作業への依存度が高く、障害発生時の自動復旧機能が欠如しています。"
  }
}
```

---

## 3. Codebase Modification Plan

### 3.1 `src/reporting/tomo_asis_ast_compiler.py`
All Python source code, variable names, docstrings, and inline comments remain strictly in **100% Technical English**.

In the Chapter 1 polarity table builder method (`_build_chapter_1_polarity_table` or equivalent AST node builder inside `TomoAsisAstCompiler`), update the formatting call for `ch1_polarity_leader_desc` so it passes only `score=leader_score_str`, omitting the `ale` argument:

```python
# Inside TomoAsisAstCompiler._build_chapter_1_executive_synthesis(...)

leader_desc = self._t(
    "consolidated_asis.ch1_polarity_leader_desc",
    score=self._format_score(leader_domain.maturity_score),
)

exposure_desc = self._t(
    "consolidated_asis.ch1_polarity_exposure_desc",
    share=self._format_percentage(top_risk_domain.ale_share_pct),
    ale=self._format_currency(top_risk_domain.ale_expected),
)

laggard_desc = self._t(
    "consolidated_asis.ch1_polarity_laggard_desc",
    score=self._format_score(laggard_domain.maturity_score),
)
```

> **Note on Backward-Safe Formatting:** Because Python's `str.format(**kwargs)` silently ignores extra keyword arguments if not referenced in the format string, removing `{ale}` from `ch1_polarity_leader_desc` in `locales.json` is immediately safe even if legacy callers pass `ale=...`. However, cleaning up the keyword argument in `tomo_asis_ast_compiler.py` ensures zero dead telemetry computation in the AST compiler.

### 3.2 `src/i18n/locales.json`
Update the `consolidated_asis` namespace across all 6 top-level locale keys (`es`, `en`, `pt`, `fr`, `de`, `ja`) with the exact strings defined in Sections 1.2 and 2.2.

---

## 4. Automated Quality Gate Test Specification

Create `tests/unit/test_rfc078_executive_editorial_simplification.py` to enforce 6-locale mathematical symmetry, ban developer jargon (`SSOT`), verify removal of `{ale}` from the maturity leader description, and guarantee zero hardcoded client/vertical leakage.

```python
"""
Unit tests for RFC 078: Executive Editorial Simplification & Value Diagnosis Governance.

Verifies that:
1. Developer jargon ('SSOT') and pedantic academic headings are purged across all 6 locales.
2. Table 1.1 Maturity Leader description no longer injects residual financial loss ('{ale}').
3. Exact parameter token symmetry holds across all 6 locales ('es', 'en', 'pt', 'fr', 'de', 'ja').
4. Zero client names, domain IDs, or vertical-specific nouns are hardcoded in templates.
"""

import json
import re
from pathlib import Path
import pytest

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")
LOCALES_PATH = Path("src/i18n/locales.json")

FORBIDDEN_JARGON_PATTERNS = (
    r"\bSSOT\b",
    r"Single Source of Truth",
    r"Radiograf[íi]a de Polaridad",
    r"Cuantificaci[óo]n Actuarial",
)

FORBIDDEN_VERTICAL_HARDCODES = (
    r"\bmolins\b",
    r"\bcemento\b",
    r"\bb[áa]sculas\b",
    r"\bcamiones\b",
    r"\bT[1-9]\b",
)

EXPECTED_TOKEN_SIGNATURES = {
    "ch1_sec1_title": set(),
    "ch1_polarity_col_axis": set(),
    "ch1_polarity_col_domain": set(),
    "ch1_polarity_col_telemetry": set(),
    "ch1_polarity_leader_axis": set(),
    "ch1_polarity_leader_desc": {"score"},
    "ch1_polarity_exposure_axis": set(),
    "ch1_polarity_exposure_desc": {"share", "ale"},
    "ch1_polarity_laggard_axis": set(),
    "ch1_polarity_laggard_desc": {"score"},
    "ch1_sec2_title": set(),
    "ch1_sec3_title": set(),
    "ch3_title": set(),
    "ch4_title": set(),
    "ch5_title": set(),
}


@pytest.fixture(scope="module")
def locales_catalog() -> dict:
    """Load the master locales JSON catalog."""
    with LOCALES_PATH.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _extract_tokens(template_str: str) -> set[str]:
    """Extract Python format tokens from a localization template string."""
    return set(re.findall(r"\{([a-zA-Z0-9_]+)\}", template_str))


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
@pytest.mark.parametrize("key,expected_tokens", EXPECTED_TOKEN_SIGNATURES.items())
def test_rfc078_token_symmetry_and_leader_ale_removal(
    locales_catalog: dict, locale: str, key: str, expected_tokens: set[str]
) -> None:
    """Ensure every RFC 078 key exists across all 6 locales with exact token symmetry."""
    asis_section = locales_catalog[locale]["consolidated_asis"]
    assert key in asis_section, f"Missing key '{key}' in locale '{locale}'"

    template_text = asis_section[key]
    assert isinstance(template_text, str) and len(template_text.strip()) > 0

    actual_tokens = _extract_tokens(template_text)
    assert actual_tokens == expected_tokens, (
        f"Token mismatch for '{key}' in locale '{locale}': "
        f"expected {expected_tokens}, got {actual_tokens}"
    )


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
@pytest.mark.parametrize("key", EXPECTED_TOKEN_SIGNATURES.keys())
def test_rfc078_zero_jargon_and_zero_vertical_hardcoding(
    locales_catalog: dict, locale: str, key: str
) -> None:
    """Verify that developer jargon (SSOT) and vertical nouns never appear in templates."""
    template_text = locales_catalog[locale]["consolidated_asis"][key]

    for pattern in FORBIDDEN_JARGON_PATTERNS:
        assert not re.search(pattern, template_text, flags=re.IGNORECASE), (
            f"Forbidden developer/academic jargon '{pattern}' found in "
            f"{locale}.consolidated_asis.{key}: '{template_text}'"
        )

    for pattern in FORBIDDEN_VERTICAL_HARDCODES:
        assert not re.search(pattern, template_text, flags=re.IGNORECASE), (
            f"Forbidden hardcoded vertical/client term '{pattern}' found in "
            f"{locale}.consolidated_asis.{key}: '{template_text}'"
        )


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_rfc078_single_page_budget_character_bounds(
    locales_catalog: dict, locale: str
) -> None:
    """Ensure Table 1.1 descriptions remain concise to preserve Page 3 layout lock."""
    asis_section = locales_catalog[locale]["consolidated_asis"]
    max_len = 95 if locale == "ja" else 185

    for desc_key in (
        "ch1_polarity_leader_desc",
        "ch1_polarity_exposure_desc",
        "ch1_polarity_laggard_desc",
    ):
        text = asis_section[desc_key]
        assert len(text) <= max_len, (
            f"{locale}.consolidated_asis.{desc_key} exceeds single-page budget "
            f"threshold ({len(text)} > {max_len} chars): '{text}'"
        )
```