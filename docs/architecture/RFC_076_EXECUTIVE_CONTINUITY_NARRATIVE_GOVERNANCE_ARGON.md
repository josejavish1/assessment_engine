# RFC 076: Executive Narrative Realism & Operational Continuity Governance

**Status:** APPROVED FOR IMMEDIATE IMPLEMENTATION  
**Target Release:** Assessment Engine v4.8 (Consolidated AS-IS Diagnostic — Volume 1)  
**Author:** Chief Corporate Governance Advisor & Executive Editorial Director  
**Scope:** Chapter 1 Executive Summary (`tomo_asis_ast_compiler.py`, `locales.json`, Quality Gate Suite)  
**Compliance Invariants:** 100% Technical English Codebase | Zero Hardcoding | Multi-Tenant Industry Agnosticism | 6-Locale Mathematical Symmetry  

---

## 1. Executive Verdict & Editorial Flaw Analysis

### 1.1 The Boardroom Standard (McKinsey / Gartner Editorial Doctrine)
Chapter 1 of the Consolidated AS-IS Diagnostic (*Executive Summary*) is engineered for the Board of Directors, Chief Executive Officer (CEO), Chief Financial Officer (CFO), and Chief Information Officer (CIO). At this governance tier, narrative pacing must be strictly **thesis-driven, risk-oriented, and strategically actionable**. 

When a C-suite executive reads the opening synthesis of a diagnostic, they require immediate visibility into **structural vulnerabilities that threaten revenue generation, operational fulfillment, and enterprise continuity**. They do not read the Executive Summary to audit the mathematical mechanics of the simulation engine.

### 1.2 Forensic Diagnosis of the Editorial Defect
The legacy implementation of Bullet 1 (`tomo_ch1_continuity_bullet_body`) committed four critical governance and editorial violations:

1. **Methodological Noise in the C-Suite Synthesis:**  
   Phrases such as *"el modelo distingue dos umbrales de impacto horario"* expose the internal plumbing of the actuarial engine inside an executive narrative. Explaining how the software model categorizes thresholds turns a strategic board memo into a software user manual.
2. **False Precision & Cognitive Friction:**  
   Quoting unrounded, cents-level figures (`13.061,29 €/h` vs. `5.000 €/h`) in the opening executive thesis creates immediate cognitive friction. Instead of internalizing the operational vulnerability, the CFO is derailed into questioning the exact decimal derivation before reaching the financial chapter.
3. **Structural Misplacement (Violation of Pyramid Principle):**  
   Granular hourly outage rates (Local Facility Outage vs. Consolidated Core Downtime) belong exclusively in **Chapter 3 (Section 3.1: The Cost of Inaction & Financial Exposure)** and the **Technical Domain Annexes**, where actuarial formulas, Monte Carlo bounds, and sensitivity tables provide the necessary context.
4. **Omission of the Core Operational Thesis:**  
   By focusing on rate definitions, the bullet failed to articulate the actual business risk: **operational asymmetry**. While central corporate systems often receive primary governance attention, distributed operational sites and peripheral branches remain reliant on legacy single points of failure (unredounded communication links, end-of-support infrastructure, manual fallback bottlenecks), where a localized technical fault immediately halts physical or transactional operations and severs revenue capture.

---

## 2. Refactored Localization Dictionaries (6-Locale Symmetry)

The refactored narrative eliminates all financial rate mechanics and dynamic currency interpolations from Bullet 1, focusing strictly on **Operational Asymmetry, Distributed Single Points of Failure, and Revenue Fulfillment Vulnerability**. The terminology is 100% vertical-agnostic, applying seamlessly to manufacturing plants, logistics hubs, retail networks, financial branches, or utility substations.

### 2.1 JSON Payload Specification (`locales.json`)

```json
{
  "tomo_ch1_continuity_bullet_title": {
    "es": "Exposición de Continuidad Operativa y Asimetría en Centros Distribuidos: ",
    "en": "Operational Continuity Exposure and Distributed Site Asymmetry: ",
    "pt": "Exposição de Continuidade Operacional e Assimetria em Unidades Distribuídas: ",
    "fr": "Exposition de la Continuité Opérationnelle et Asymétrie des Sites Distribués : ",
    "de": "Exposition der Betriebskontinuität und Asymmetrie verteilter Standorte: ",
    "ja": "事業継続性のリスク露出と分散拠点における非対称性："
  },
  "tomo_ch1_continuity_bullet_body": {
    "es": "La arquitectura actual presenta una vulnerabilidad estructural entre la resiliencia de los sistemas corporativos centrales y la fragilidad de las sedes operativas distribuidas. La persistencia de puntos únicos de fallo en enlaces de comunicaciones, infraestructura local en fin de soporte y procesos sin contingencia automatizada expone a la organización a interrupciones inmediatas en la ejecución operativa, facturación y atención al cliente ante cualquier incidencia técnica local o pérdida de conectividad con el núcleo central.",
    "en": "The current architecture exhibits a structural vulnerability between the resilience of central corporate systems and the fragility of distributed operational sites. The persistence of single points of failure across communication links, end-of-support local infrastructure, and processes lacking automated failover exposes the organization to immediate disruptions in operational fulfillment, billing, and customer service upon any localized technical incident or loss of connectivity to the central core.",
    "pt": "A arquitetura atual apresenta uma vulnerabilidade estrutural entre a resiliência dos sistemas corporativos centrais e a fragilidade das unidades operacionais distribuídas. A persistência de pontos únicos de falha em links de comunicação, infraestrutura local em fim de suporte e processos sem contingência automatizada expõe a organização a interrupções imediatas na execução operacional, faturamento e atendimento ao cliente diante de qualquer incidente técnico local ou perda de conectividade com o núcleo central.",
    "fr": "L'architecture actuelle présente une vulnérabilité structurelle entre la résilience des systèmes centraux de l'entreprise et la fragilité des sites opérationnels distribués. La persistance de points de défaillance uniques sur les liaisons de communication, les infrastructures locales en fin de support et les processus dépourvus de basculement automatisé expose l'organisation à des interruptions immédiates de l'exécution opérationnelle, de la facturation et du service client lors de tout incident technique local ou perte de connectivité avec le cœur central.",
    "de": "Die aktuelle Architektur weist eine strukturelle Verwundbarkeit zwischen der Resilienz zentraler Unternehmenssysteme und der Fragilität verteilter Betriebsstandorte auf. Das Fortbestehen einzelner Ausfallpunkte (Single Points of Failure) bei Kommunikationsverbindungen, lokaler Infrastruktur am Ende des Supportzyklus und Prozessen ohne automatisiertes Failover setzt die Organisation unmittelbaren Unterbrechungen in der Betriebsausführung, Abrechnung und Kundenbetreuung bei jedem lokalen technischen Vorfall oder Verbindungsabbruch zum zentralen Kern aus.",
    "ja": "現在のアーキテクチャは、中央のコーポレートシステムの回復力と分散された事業拠点の脆弱性の間に構造的なギャップを抱えています。通信リンクにおける単一障害点（SPOF）の残存、サポート終了（EOS）を迎えたローカルインフラ、および自動フェイルオーバーを欠いた業務プロセスにより、局所的な技術障害や中央コアとの接続喪失が発生した際、業務遂行、請求処理、および顧客サービスが即座に停止するリスクに晒されています。"
  }
}
```

### 2.2 Parameter Signature Invariant
* **Previous Signature:** `{local_rate_fmt}`, `{consolidated_rate_fmt}`
* **New Signature:** `None` (Zero dynamic interpolation tokens).  
* **Architectural Benefit:** Eliminates coupling between Chapter 1's qualitative strategic risk synthesis and Chapter 3's actuarial rate formatting variables, while preserving exact mathematical token symmetry (`set() == set()`) across all 6 languages.

---

## 3. Codebase Modification Plan

All Python source code, comments, and docstrings strictly adhere to the **100% Technical English Invariant**.

### 3.1 File: `src/reporting/tomo_asis_ast_compiler.py`

In the Chapter 1 AST compilation routine (`_compile_chapter_1_executive_summary` or equivalent builder method), remove the formatting arguments passed to `tomo_ch1_continuity_bullet_body` and clean up any unused local rate formatting variables if they are not consumed elsewhere in the same scope.

#### Diff Specification:

```python
# BEFORE (Legacy Implementation with Methodological Noise)
b1_title = self._t("tomo_ch1_continuity_bullet_title")
b1_body = self._t(
    "tomo_ch1_continuity_bullet_body",
    local_rate_fmt=local_hourly_str,
    consolidated_rate_fmt=consolidated_hourly_str,
)
```

```python
# AFTER (RFC 076 Compliant — Pure Executive Continuity Governance Narrative)
# RFC 076: Bullet 1 focuses strictly on operational continuity and distributed site
# asymmetry without exposing internal simulation rate thresholds in Chapter 1.
b1_title = self._t("tomo_ch1_continuity_bullet_title")
b1_body = self._t("tomo_ch1_continuity_bullet_body")
```

*Note on Variable Hygiene:* If `local_hourly_str` and `consolidated_hourly_str` were computed exclusively for `b1_body` inside the Chapter 1 method scope, remove their declarations in that method to prevent linter warnings (`F841: local variable is assigned to but never used`). Ensure their primary computation in Chapter 3 (`_compile_chapter_3_financial_impact`) remains completely intact.

---

## 4. Automated Quality Gate Test Specification

File path: `tests/unit/test_rfc076_executive_continuity_narrative.py`

This test suite enforces:
1. **6-Locale Presence & Non-Empty Invariant** for both title and body keys.
2. **Zero Placeholder Symmetry** (confirming `{local_rate_fmt}` and `{consolidated_rate_fmt}` are eradicated).
3. **Anti-Regression Guardrails** against methodological phrasing (`"el modelo distingue"`, `"umbrales"`, currency symbols) and hardcoded client/industry nouns.

```python
"""
Unit tests for RFC 076: Executive Narrative Realism & Operational Continuity Governance.

Verifies that Chapter 1 Bullet 1 (Operational Continuity) adheres to C-suite
editorial standards across all 6 supported locales, free from simulation mechanics,
hourly rate figures, and industry-specific hardcoding.
"""

import json
import re
from pathlib import Path
import pytest


SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")
LOCALES_PATH = Path(__file__).resolve().parents[2] / "src" / "resources" / "locales.json"

FORBIDDEN_METHODOLOGICAL_PATTERNS = (
    r"local_rate_fmt",
    r"consolidated_rate_fmt",
    r"€/h",
    r"\$/h",
    r"el modelo distingue",
    r"the model distinguishes",
    r"dos umbrales",
    r"two thresholds",
    r"13\.061",
    r"5\.000",
)

FORBIDDEN_INDUSTRY_HARDCODING = (
    r"\bmolins\b",
    r"\bcemento\b",
    r"\bcement\b",
    r"\bbásculas\b",
    r"\bcamiones\b",
)


@pytest.fixture(scope="module")
def locales_data() -> dict:
    """Load the master localization dictionary."""
    with open(LOCALES_PATH, mode="r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def test_rfc076_continuity_keys_exist_across_all_locales(locales_data: dict) -> None:
    """Ensure title and body keys exist and are non-empty across all 6 locales."""
    for key in ("tomo_ch1_continuity_bullet_title", "tomo_ch1_continuity_bullet_body"):
        assert key in locales_data, f"Missing mandatory localization key: {key}"
        translations = locales_data[key]
        for locale in SUPPORTED_LOCALES:
            assert locale in translations, f"Missing locale '{locale}' in key '{key}'"
            text = translations[locale].strip()
            assert len(text) > 15, f"Translation too short for '{key}' in locale '{locale}'"


def test_rfc076_zero_interpolation_placeholders(locales_data: dict) -> None:
    """Verify that rate placeholders have been completely removed from Bullet 1."""
    placeholder_regex = re.compile(r"\{([a-zA-Z0-9_]+)\}")
    for key in ("tomo_ch1_continuity_bullet_title", "tomo_ch1_continuity_bullet_body"):
        for locale in SUPPORTED_LOCALES:
            text = locales_data[key][locale]
            matches = placeholder_regex.findall(text)
            assert matches == [], (
                f"Unexpected interpolation placeholders {matches} found in "
                f"'{key}' for locale '{locale}'. Chapter 1 Bullet 1 must be purely strategic."
            )


def test_rfc076_no_methodological_noise_or_hourly_rates(locales_data: dict) -> None:
    """Ensure simulation mechanics and literal hourly rates do not leak into Bullet 1."""
    body_translations = locales_data["tomo_ch1_continuity_bullet_body"]
    for locale in SUPPORTED_LOCALES:
        text = body_translations[locale]
        for pattern in FORBIDDEN_METHODOLOGICAL_PATTERNS:
            assert not re.search(pattern, text, re.IGNORECASE), (
                f"Forbidden methodological/rate pattern '{pattern}' detected in "
                f"locale '{locale}': {text}"
            )


def test_rfc076_universal_multi_tenant_agnosticism(locales_data: dict) -> None:
    """Verify zero hardcoding of client names or vertical-specific nouns."""
    for key in ("tomo_ch1_continuity_bullet_title", "tomo_ch1_continuity_bullet_body"):
        for locale in SUPPORTED_LOCALES:
            text = locales_data[key][locale]
            for pattern in FORBIDDEN_INDUSTRY_HARDCODING:
                assert not re.search(pattern, text, re.IGNORECASE), (
                    f"Forbidden tenant/industry-specific term '{pattern}' detected in "
                    f"'{key}' ({locale}). Narrative must remain 100% vertical-agnostic."
                )
```