# RFC 074: Executive Actuarial Realism, Single-Incident Transparency & Chapter 1/3 Governance

| Metadata | Specification Details |
| :--- | :--- |
| **Document ID** | `RFC-074-ACTUARIAL-REALISM` |
| **Target Subsystem** | `reporting_engine.compilers.tomo_asis_ast_compiler` & `engine_config.locales` |
| **Status** | **APPROVED FOR IMMEDIATE IMPLEMENTATION** |
| **Compliance Standards** | Open FAIR™ Risk Standard, Basel III (OpRisk VaR), Solvency II (SCR Sub-additivity) |
| **Architectural Invariants** | 100% Technical English Codebase, Zero Hardcoding, Multi-Tenant Scalability, 6-Locale Symmetry |

---

## 1. Executive Verdict & Actuarial Problem Analysis

### 1.1 The Actuarial Summation Fallacy (Why Summing Percentiles Fails CFO Scrutiny)
In quantitative operational risk frameworks (Open FAIR™, Basel III Advanced Measurement Approaches, and Solvency II Standard Formula), **Value-at-Risk (VaR) and Single Loss Expectancy (SLE) upper-bound percentiles cannot be summed linearly across risk domains**.

Mathematically, for a portfolio of $N$ risk domains with loss random variables $L_1, L_2, \dots, L_N$, the linear sum of individual domain $q$-quantiles ($VaR_q$) satisfies the sub-additivity and co-monotonicity bound:

$$\text{VaR}_q\left(\sum_{i=1}^{N} L_i\right) \le \sum_{i=1}^{N} \text{VaR}_q(L_i)$$

Equality holds **if and only if** the random variables are perfectly co-monotonic (i.e., Pearson linear correlation $\rho_{i,j} = 1.0$ across all domain pairs, or coupled via the upper Fréchet–Hoeffding bound copula $C(u_1, \dots, u_n) = \min(u_1, \dots, u_n)$).

When Table 3 previously displayed a `TOTAL` row summing all 10 domain severe incident costs into a single aggregate figure, it asserted to the CFO and Audit Committee that every single technological domain—from ERP financial ledgers to shop-floor industrial OT, identity directories, and edge networks—will suffer its worst-case multi-day catastrophic collapse **simultaneously on the exact same day**. 

To a seasoned Chief Risk Officer (CRO) or CFO, this linear summation is an immediate red flag indicating methodological amateurism or intentional risk inflation designed to coerce capital allocation.

### 1.2 The Three Distinct Financial Risk Dimensions
To command undisputed boardroom credibility, the Assessment Engine must separate operational risk into three mathematically orthogonal metrics across Chapters 1 and 3:

1. **Annual Average Exposure ($\text{ALE}_{\text{Portfolio}}$ — Expected Loss):**
   * *Mathematical Property:* Strictly linear and additive by the Linearity of Expectation: $\mathbb{E}\left[\sum L_i\right] = \sum \mathbb{E}[L_i]$.
   * *Executive Meaning:* The recurring annual operational friction, uncontracted overtime, SLA penalties, and routine downtime absorbed by the P&L during a typical operating year.
2. **Single Major Incident Outage ($\max_i(\text{SLE}_{i, \text{severe}})$ — Maximum Single Event):**
   * *Mathematical Property:* A supremum operator over the active domain vector: $L_{\text{max\_event}} = \max_{i \in D} (\text{SevereIncidentCost}_i)$.
   * *Executive Meaning:* The direct financial shock to working capital and production continuity if the organization's most vulnerable critical domain suffers a standalone major outage.
3. **Adverse Annual Crisis Scenario ($\text{VaR}_{0.90}(\text{Annual Portfolio})$ — Tail Risk):**
   * *Mathematical Property:* Derived via Monte Carlo convolution of annual frequency and severity distributions across all domains, incorporating realistic cross-domain dependency copulas.
   * *Executive Meaning:* The 1-in-10 year adverse fiscal impact when multiple severe incidents materialize across different platforms within the same 12-month fiscal cycle.

### 1.3 Remediation of Table 3 and Executive Summary Tone
* **Header Purification:** The column header in Table 3 removes the conflicting `(P95)` technical tag, standardizing on clean executive nomenclature (`Severe Incident Cost`).
* **Total Row Replacement:** In the summary row of Table 3, the column for Severe Incident Cost no longer sums the column vector. Instead, it applies the `MAX()` operator across active domains, explicitly labeled with a `(Max.)` qualifier, and appends an actuarial governance footnote below the table explaining non-additivity and pointing to the worst-case single domain exposure.
* **Tone Calibration:** Chapter 1 replaces colloquial metaphors (such as "constant dripping" / *"goteo"*) with sober, institutional financial terminology suitable for Board Risk Committees and external auditors.

---

## 2. Production Code Blueprint: `tomo_asis_ast_compiler.py`

All Python source code strictly adheres to **Architectural Invariant #1 (100% Technical English Codebase)** and **Invariant #2 (Zero Hardcoding)**. Tenant-specific domain codes, domain names, currencies, and loss magnitudes are resolved dynamically at runtime from the Single Source of Truth (SSOT) telemetry payload.

```python
# File: reporting_engine/compilers/tomo_asis_ast_compiler.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SingleIncidentPeakMetrics:
    """Immutable container for the highest single-domain severe incident exposure."""
    domain_code: str
    domain_name: str
    severe_incident_cost: float
    formatted_cost: str


class TomoAsisAstCompiler:
    """
    AST Compiler for Deliverable Tomo 1 (Consolidated AS-IS Executive Diagnostic).
    Enforces Open FAIR actuarial invariants and multi-tenant localization symmetry.
    """

    def __init__(self, ssot_payload: Dict[str, Any], locale_catalog: Dict[str, Any], locale_code: str = "es"):
        self.ssot = ssot_payload
        self.locale_code = locale_code
        self.t = locale_catalog.get(locale_code, locale_catalog.get("en", {}))

    def _format_currency(self, amount: float) -> str:
        """
        Formats monetary values dynamically according to tenant currency and locale rules.
        Zero hardcoded currency symbols or separators.
        """
        currency_symbol = self.ssot.get("financial_context", {}).get("currency_symbol", "€")
        symbol_position = self.ssot.get("financial_context", {}).get("currency_position", "suffix")
        
        rounded_val = int(round(amount))
        if self.locale_code in ("en", "ja"):
            num_str = f"{rounded_val:,}"
        elif self.locale_code == "fr":
            num_str = f"{rounded_val:,}".replace(",", " ")
        else:
            # Default European continental formatting (es, pt, de)
            num_str = f"{rounded_val:,}".replace(",", ".")

        if symbol_position == "prefix":
            return f"{currency_symbol}{num_str}"
        return f"{num_str} {currency_symbol}"

    def _compute_peak_single_incident(
        self, active_domains: List[Dict[str, Any]]
    ) -> SingleIncidentPeakMetrics:
        """
        Dynamically computes the maximum single-incident exposure across all active domains.
        Prevents linear summation fallacy of tail percentiles in executive tables.
        """
        if not active_domains:
            logger.warning("No active domains found in SSOT topology for peak incident computation.")
            return SingleIncidentPeakMetrics(
                domain_code="N/A",
                domain_name="N/A",
                severe_incident_cost=0.0,
                formatted_cost=self._format_currency(0.0),
            )

        peak_domain = max(
            active_domains,
            key=lambda d: float(d.get("financial_metrics", {}).get("severe_incident_cost_p95", 0.0)),
        )

        raw_cost = float(peak_domain.get("financial_metrics", {}).get("severe_incident_cost_p95", 0.0))
        domain_code = str(peak_domain.get("domain_code", "UNK")).strip()
        domain_name = str(peak_domain.get("domain_name", domain_code)).strip()

        return SingleIncidentPeakMetrics(
            domain_code=domain_code,
            domain_name=domain_name,
            severe_incident_cost=raw_cost,
            formatted_cost=self._format_currency(raw_cost),
        )

    def compile_chapter_1_executive_summary(self) -> List[Dict[str, Any]]:
        """
        Compiles the Chapter 1 Executive Summary narrative nodes, differentiating:
        1. Annual Expected Loss (ALE)
        2. Single Major Domain Outage (Max SLE)
        3. Adverse Annual Portfolio Crisis (Monte Carlo P90)
        """
        active_domains = self.ssot.get("domain_topology", {}).get("active_domains", [])
        portfolio_metrics = self.ssot.get("portfolio_simulation", {})

        ale_total = float(portfolio_metrics.get("annual_expected_loss_ale", 0.0))
        p90_annual = float(portfolio_metrics.get("annual_p90_loss_var", 0.0))
        peak_incident = self._compute_peak_single_incident(active_domains)

        ch1_strings = self.t.get("tomo1_chapter1_exec_summary", {})

        narrative_text = ch1_strings.get("actuarial_three_dimensions_body", "").format(
            ale_formatted=self._format_currency(ale_total),
            worst_incident_cost=peak_incident.formatted_cost,
            worst_incident_code=peak_incident.domain_code,
            worst_incident_domain=peak_incident.domain_name,
            p90_annual_formatted=self._format_currency(p90_annual),
        )

        return [
            {
                "node_type": "heading",
                "level": 2,
                "text": ch1_strings.get("actuarial_section_title", ""),
            },
            {
                "node_type": "paragraph",
                "style": "executive_body",
                "text": narrative_text,
            },
        ]

    def compile_chapter_3_domain_exposure_table(self) -> List[Dict[str, Any]]:
        """
        Compiles Table 3 (Domain Exposure & Severe Event Table) and its actuarial footnote.
        Enforces non-additivity on the Severe Incident Cost column by rendering the maximum
        single-domain event in the summary row rather than a linear column sum.
        """
        active_domains = self.ssot.get("domain_topology", {}).get("active_domains", [])
        portfolio_metrics = self.ssot.get("portfolio_simulation", {})
        table_strings = self.t.get("tomo1_table3_domain_exposure", {})

        headers = [
            table_strings.get("col_domain", "Domain"),
            table_strings.get("col_maturity", "Maturity"),
            table_strings.get("col_ale", "Annual Expected Exposure (ALE)"),
            table_strings.get("col_severe_incident", "Severe Incident Cost"),
            table_strings.get("col_risk_share", "% of Annual Risk"),
        ]

        rows: List[List[str]] = []
        total_ale = 0.0

        for domain in active_domains:
            d_code = str(domain.get("domain_code", ""))
            d_name = str(domain.get("domain_name", ""))
            maturity = f"{float(domain.get('maturity_score', 0.0)):.2f}"
            
            fin = domain.get("financial_metrics", {})
            d_ale = float(fin.get("annual_expected_loss_ale", 0.0))
            d_severe = float(fin.get("severe_incident_cost_p95", 0.0))
            d_share = float(fin.get("portfolio_ale_share_pct", 0.0))

            total_ale += d_ale

            rows.append([
                f"{d_code} - {d_name}",
                maturity,
                self._format_currency(d_ale),
                self._format_currency(d_severe),
                f"{d_share:.1f}%",
            ])

        # Compute peak single incident dynamically (Actuarial Supremum Operator)
        peak_incident = self._compute_peak_single_incident(active_domains)
        avg_maturity = float(portfolio_metrics.get("weighted_maturity_score", 0.0))

        # Construct Summary Row: ALE sums linearly; Severe Incident displays MAX()
        max_qualifier = table_strings.get("max_qualifier_tag", "(Max.)")
        total_row = [
            table_strings.get("row_total_label", "TOTAL PORTFOLIO"),
            f"{avg_maturity:.2f}",
            self._format_currency(total_ale),
            f"{peak_incident.formatted_cost} {max_qualifier}",
            "100.0%",
        ]

        footnote_text = table_strings.get("actuarial_non_additivity_footnote", "").format(
            worst_incident_cost=peak_incident.formatted_cost,
            worst_incident_code=peak_incident.domain_code,
            worst_incident_domain=peak_incident.domain_name,
        )

        return [
            {
                "node_type": "table",
                "table_id": "table_3_domain_financial_exposure",
                "headers": headers,
                "rows": rows,
                "summary_row": total_row,
            },
            {
                "node_type": "footnote",
                "style": "actuarial_caption",
                "text": footnote_text,
            },
        ]
```

---

## 3. Full Localization Catalog Dictionaries (`engine_config/locales.json`)

In compliance with **Architectural Invariant #4 (Mathematical Symmetry)**, the following JSON localization blocks must be updated across all 6 supported locales (`es`, `en`, `pt`, `fr`, `de`, `ja`). All dynamic runtime interpolation tokens (`{ale_formatted}`, `{worst_incident_cost}`, `{worst_incident_code}`, `{worst_incident_domain}`, `{p90_annual_formatted}`) are strictly identical across every language.

```json
{
  "es": {
    "tomo1_chapter1_exec_summary": {
      "actuarial_section_title": "Síntesis de Exposición Financiera y Dimensionamiento Actuarial",
      "actuarial_three_dimensions_body": "El diagnóstico cuantitativo estructura el riesgo operacional tecnológico en tres dimensiones financieras diferenciadas: (1) Exposición Anual Promedio (ALE) de {ale_formatted}, que representa la fricción operativa recurrente, horas extra no planificadas y micro-interrupciones absorbidas anualmente por la cuenta de resultados; (2) Impacto por Incidente Grave Único de hasta {worst_incident_cost}, correspondiente al coste directo de parada operativa en el dominio más expuesto ({worst_incident_code} - {worst_incident_domain}) ante un evento crítico aislado; y (3) Escenario de Crisis Anual Acumulada (P90) de {p90_annual_formatted}, que modela el riesgo extremo de cola si convergen múltiples incidentes severos en distintas plataformas a lo largo de un ejercicio fiscal adverso."
    },
    "tomo1_table3_domain_exposure": {
      "col_domain": "Dominio Tecnológico",
      "col_maturity": "Nivel de Madurez",
      "col_ale": "Exposición Media Anual (ALE)",
      "col_severe_incident": "Coste ante Incidente Grave",
      "col_risk_share": "% del Riesgo Anual",
      "row_total_label": "TOTAL CARTERA / MÁX. EVENTO",
      "max_qualifier_tag": "(Máx.)",
      "actuarial_non_additivity_footnote": "* Nota Metodológica Actuarial: A diferencia de la Exposición Media Anual (ALE), que es linealmente aditiva, los costes ante incidentes graves representan eventos extremos aislados por dominio y no pueden sumarse linealmente (asumir su suma implicaría la caída catastrófica simultánea de los 10 dominios el mismo día). La fila de síntesis refleja el impacto máximo de un único incidente severo en el dominio de mayor exposición ({worst_incident_cost} en {worst_incident_code} - {worst_incident_domain})."
    }
  },
  "en": {
    "tomo1_chapter1_exec_summary": {
      "actuarial_section_title": "Financial Exposure Synthesis & Actuarial Risk Sizing",
      "actuarial_three_dimensions_body": "The quantitative diagnostic structures technology operational risk across three distinct financial dimensions: (1) Annual Expected Exposure (ALE) of {ale_formatted}, representing baseline operational friction, unplanned overtime, and routine service disruptions absorbed annually by the income statement; (2) Single Major Incident Outage of up to {worst_incident_cost}, reflecting the direct operational outage cost in the most exposed domain ({worst_incident_code} - {worst_incident_domain}) during an isolated critical event; and (3) Adverse Annual Crisis Scenario (Portfolio P90) of {p90_annual_formatted}, modeling the cumulative annual tail risk should multiple severe incidents materialize across different platforms within a difficult fiscal year."
    },
    "tomo1_table3_domain_exposure": {
      "col_domain": "Technology Domain",
      "col_maturity": "Maturity Level",
      "col_ale": "Annual Expected Exposure (ALE)",
      "col_severe_incident": "Severe Incident Cost",
      "col_risk_share": "% of Annual Risk",
      "row_total_label": "TOTAL PORTFOLIO / MAX EVENT",
      "max_qualifier_tag": "(Max.)",
      "actuarial_non_additivity_footnote": "* Actuarial Methodology Note: Unlike Annual Expected Exposure (ALE), which is linearly additive, severe incident costs represent isolated tail events per domain and cannot be summed linearly (linear summation would imply the simultaneous catastrophic collapse of all domains on the exact same day). The summary row reflects the maximum single-incident impact in the most exposed domain ({worst_incident_cost} in {worst_incident_code} - {worst_incident_domain})."
    }
  },
  "pt": {
    "tomo1_chapter1_exec_summary": {
      "actuarial_section_title": "Síntese de Exposição Financeira e Dimensionamento Atuarial",
      "actuarial_three_dimensions_body": "O diagnóstico quantitativo estrutura o risco operacional tecnológico em três dimensões financeiras distintas: (1) Exposição Média Anual (ALE) de {ale_formatted}, que representa o atrito operacional recorrente, horas extras não planeadas e interrupções de rotina absorvidas anualmente pela demonstração de resultados; (2) Impacto de Incidente Grave Único de até {worst_incident_cost}, refletindo o custo direto de paralisação operacional no domínio mais exposto ({worst_incident_code} - {worst_incident_domain}) durante um evento crítico isolado; e (3) Cenário de Crise Anual Acumulada (P90) de {p90_annual_formatted}, que modela o risco extremo de cauda caso múltiplos incidentes severos ocorram em diferentes plataformas ao longo de um ano fiscal adverso."
    },
    "tomo1_table3_domain_exposure": {
      "col_domain": "Domínio Tecnológico",
      "col_maturity": "Nível de Maturidade",
      "col_ale": "Exposição Média Anual (ALE)",
      "col_severe_incident": "Custo de Incidente Grave",
      "col_risk_share": "% do Risco Anual",
      "row_total_label": "TOTAL CARTEIRA / MÁX. EVENTO",
      "max_qualifier_tag": "(Máx.)",
      "actuarial_non_additivity_footnote": "* Nota Metodológica Atuarial: Ao contrário da Exposição Média Anual (ALE), que é linearmente aditiva, os custos de incidentes graves representam eventos extremos isolados por domínio e não podem ser somados linearmente (a soma linear implicaria o colapso catastrófico simultâneo de todos os domínios no mesmo dia). A linha de síntese reflete o impacto máximo de um único incidente severo no domínio de maior exposição ({worst_incident_cost} em {worst_incident_code} - {worst_incident_domain})."
    }
  },
  "fr": {
    "tomo1_chapter1_exec_summary": {
      "actuarial_section_title": "Synthèse de l'Exposition Financière et Dimensionnement Actuariel",
      "actuarial_three_dimensions_body": "Le diagnostic quantitatif structure le risque opérationnel technologique selon trois dimensions financières distinctes : (1) l'Exposition Annuelle Moyenne (ALE) de {ale_formatted}, représentant la friction opérationnelle récurrente, les heures supplémentaires non planifiées et les perturbations courantes absorbées annuellement par le compte de résultat ; (2) le Coût d'un Incident Majeur Unique pouvant atteindre {worst_incident_cost}, reflétant le coût direct d'arrêt d'exploitation dans le domaine le plus exposé ({worst_incident_code} - {worst_incident_domain}) lors d'un sinistre critique isolé ; et (3) le Scénario de Crise Annuelle Cumulée (P90) de {p90_annual_formatted}, modélisant le risque extrême de queue si plusieurs incidents graves surviennent sur différentes plateformes au cours d'un exercice défavorable."
    },
    "tomo1_table3_domain_exposure": {
      "col_domain": "Domaine Technologique",
      "col_maturity": "Niveau de Maturité",
      "col_ale": "Exposition Annuelle Moyenne (ALE)",
      "col_severe_incident": "Coût d'Incident Grave",
      "col_risk_share": "% du Risque Annuel",
      "row_total_label": "TOTAL PORTEFEUILLE / ÉVÉN. MAX.",
      "max_qualifier_tag": "(Max.)",
      "actuarial_non_additivity_footnote": "* Note Méthodologique Actuarielle : Contrairement à l'Exposition Annuelle Moyenne (ALE) qui est linéairement additive, les coûts d'incidents graves représentent des sinistres extrêmes isolés par domaine et ne peuvent être additionnés linéairement (les sommer impliquerait l'effondrement catastrophique simultané de tous les domaines le même jour). La ligne de synthèse indique l'impact maximal d'un incident grave unique dans le domaine le plus exposé ({worst_incident_cost} sur {worst_incident_code} - {worst_incident_domain})."
    }
  },
  "de": {
    "tomo1_chapter1_exec_summary": {
      "actuarial_section_title": "Synthese des Finanziellen Risikos und Versicherungsmathematische Dimensionierung",
      "actuarial_three_dimensions_body": "Die quantitative Diagnose gliedert das technologische Betriebsrisiko in drei klar abgegrenzte Finanzdimensionen: (1) den Jährlichen Erwartungsschaden (ALE) von {ale_formatted}, der laufende Reibungsverluste, ungeplante Überstunden und routinemäßige Betriebsunterbrechungen abbildet, die jährlich die Gewinn- und Verlustrechnung belasten; (2) den Einzelausfall durch einen Schwerwiegenden Störfall von bis zu {worst_incident_cost}, der die direkten Stillstandskosten im am stärksten exponierten Bereich ({worst_incident_code} - {worst_incident_domain}) bei einem isolierten Großereignis beziffert; sowie (3) das Kumulierte Jährliche Krisenszenario (Portfolio-P90) von {p90_annual_formatted}, welches das extreme Tail-Risiko modelliert, falls in einem schwierigen Geschäftsjahr mehrere schwere Vorfälle über verschiedene Plattformen hinweg zusammentreffen."
    },
    "tomo1_table3_domain_exposure": {
      "col_domain": "Technologiedomäne",
      "col_maturity": "Reifegrad",
      "col_ale": "Jährlicher Erwartungsschaden (ALE)",
      "col_severe_incident": "Kosten bei Schwerem Störfall",
      "col_risk_share": "% des Jahresrisikos",
      "row_total_label": "GESAMTPORTFOLIO / MAX. EREIGNIS",
      "max_qualifier_tag": "(Max.)",
      "actuarial_non_additivity_footnote": "* Versicherungsmathematischer Methodikhinweis: Im Gegensatz zum Jährlichen Erwartungsschaden (ALE), der linear additiv ist, stellen die Kosten schwerer Störfälle isolierte Extremereignisse je Domäne dar und dürfen nicht linear summiert werden (eine lineare Addition würde den gleichzeitigen katastrophalen Totalausfall aller Domänen am selben Tag voraussetzen). Die Summenzeile weist den maximalen Einzelschaden in der am stärksten exponierten Domäne aus ({worst_incident_cost} in {worst_incident_code} - {worst_incident_domain})."
    }
  },
  "ja": {
    "tomo1_chapter1_exec_summary": {
      "actuarial_section_title": "財務エクスポージャーの統合評価およびアクチュアリーリスク算定",
      "actuarial_three_dimensions_body": "本定量診断では、テクノロジーのオペレーショナルリスクを3つの明確に異なる財務次元に構造化しています。(1) 年間平均予想損失額（ALE）{ale_formatted}：日常的な業務摩擦、計画外の残業、および損益計算書で毎年吸収される定常的な小規模障害コストを表します。(2) 単一重大インシデント最大損失額 {worst_incident_cost}：最もリスク露出度の高いドメイン（{worst_incident_code} - {worst_incident_domain}）において単独の致命的障害が発生した際の直接的な業務停止コストを反映します。(3) 年間累積危機シナリオ（ポートフォリオP90）{p90_annual_formatted}：厳しい会計年度内に複数の異なるプラットフォームで重大なインシデントが連鎖・累積した場合の年間テールリスクをモデル化したものです。"
    },
    "tomo1_table3_domain_exposure": {
      "col_domain": "テクノロジードメイン",
      "col_maturity": "成熟度レベル",
      "col_ale": "年間平均予想損失 (ALE)",
      "col_severe_incident": "重大インシデント発生時コスト",
      "col_risk_share": "年間リスク構成比 (%)",
      "row_total_label": "ポートフォリオ合計 / 最大単一事象",
      "max_qualifier_tag": "(最大)",
      "actuarial_non_additivity_footnote": "* アクチュアリー手法に関する注記：線形加算が可能な年間平均予想損失（ALE）とは異なり、重大インシデント発生時コストは各ドメインにおける個別の極端事象を表すため、単純合算することはできません（単純合算は、全ドメインが同日に同時多発的に完全崩壊するという非現実的な仮定を意味します）。合計行には、最も露出度の高いドメインにおける単一重大インシデントの最大影響額（{worst_incident_code} - {worst_incident_domain} における {worst_incident_cost}）を表示しています。"
    }
  }
}
```

---

## 4. Validation & Quality Gates (`tests/test_rfc074_actuarial_governance.py`)

The following automated test suite enforces all architectural invariants in CI/CD pipelines, guaranteeing zero hardcoded tenant strings, 6-locale dictionary symmetry, header sanitation, and mathematical non-additivity in Table 3.

```python
# File: tests/test_rfc074_actuarial_governance.py

import inspect
import json
import re
from pathlib import Path
from typing import Any, Dict

import pytest
from reporting_engine.compilers.tomo_asis_ast_compiler import TomoAsisAstCompiler

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")
REQUIRED_INTERPOLATION_VARS_CH1 = {
    "ale_formatted",
    "worst_incident_cost",
    "worst_incident_code",
    "worst_incident_domain",
    "p90_annual_formatted",
}
REQUIRED_INTERPOLATION_VARS_FOOTNOTE = {
    "worst_incident_cost",
    "worst_incident_code",
    "worst_incident_domain",
}


@pytest.fixture
def sample_multi_tenant_ssot() -> Dict[str, Any]:
    """Provides a synthetic multi-tenant SSOT payload to verify dynamic computation."""
    return {
        "financial_context": {
            "currency_symbol": "€",
            "currency_position": "suffix",
        },
        "portfolio_simulation": {
            "annual_expected_loss_ale": 642850.0,
            "annual_p90_loss_var": 1480000.0,
            "weighted_maturity_score": 2.15,
        },
        "domain_topology": {
            "active_domains": [
                {
                    "domain_code": "D1",
                    "domain_name": "Core ERP & Financial Ledgers",
                    "maturity_score": 2.40,
                    "financial_metrics": {
                        "annual_expected_loss_ale": 120000.0,
                        "severe_incident_cost_p95": 310000.0,
                        "portfolio_ale_share_pct": 18.7,
                    },
                },
                {
                    "domain_code": "D5",
                    "domain_name": "Industrial OT & Plant Execution",
                    "maturity_score": 1.65,
                    "financial_metrics": {
                        "annual_expected_loss_ale": 340000.0,
                        "severe_incident_cost_p95": 515485.0,
                        "portfolio_ale_share_pct": 52.9,
                    },
                },
                {
                    "domain_code": "D8",
                    "domain_name": "Identity & Access Governance",
                    "maturity_score": 2.40,
                    "financial_metrics": {
                        "annual_expected_loss_ale": 182850.0,
                        "severe_incident_cost_p95": 290000.0,
                        "portfolio_ale_share_pct": 28.4,
                    },
                },
            ]
        },
    }


def test_invariant_1_and_2_zero_hardcoding_in_compiler_source():
    """
    Gate 1: Asserts that no client names, domain codes, or static monetary figures
    are hardcoded inside tomo_asis_ast_compiler.py.
    """
    source_code = inspect.getsource(TomoAsisAstCompiler)
    forbidden_literals = [
        "MOLINS",
        "515.485",
        "2.291.040",
        "goteo",
        "(P95)",
        "T5",
    ]
    for literal in forbidden_literals:
        assert literal not in source_code, (
            f"Architectural Violation: Forbidden hardcoded literal '{literal}' "
            f"detected in TomoAsisAstCompiler source code."
        )


def test_invariant_4_locale_catalog_mathematical_symmetry(locales_dict: Dict[str, Any]):
    """
    Gate 2: Verifies that all 6 locales contain identical keys and identical
    string formatting placeholders for Chapter 1 and Table 3.
    """
    placeholder_regex = re.compile(r"\{([a-zA-Z0-9_]+)\}")

    for locale in SUPPORTED_LOCALES:
        assert locale in locales_dict, f"Missing mandatory locale '{locale}' in locales.json"
        lang_pack = locales_dict[locale]

        ch1_pack = lang_pack.get("tomo1_chapter1_exec_summary", {})
        t3_pack = lang_pack.get("tomo1_table3_domain_exposure", {})

        # Verify P95 jargon is eradicated from Table 3 header across all languages
        header_severe = t3_pack.get("col_severe_incident", "")
        assert "P95" not in header_severe, (
            f"Jargon Defect: '(P95)' found in Table 3 header for locale '{locale}'."
        )

        # Verify exact placeholder symmetry in Chapter 1 body
        ch1_body = ch1_pack.get("actuarial_three_dimensions_body", "")
        extracted_ch1_vars = set(placeholder_regex.findall(ch1_body))
        assert extracted_ch1_vars == REQUIRED_INTERPOLATION_VARS_CH1, (
            f"Placeholder mismatch in Chapter 1 for locale '{locale}': {extracted_ch1_vars}"
        )

        # Verify exact placeholder symmetry in Table 3 footnote
        footnote = t3_pack.get("actuarial_non_additivity_footnote", "")
        extracted_fn_vars = set(placeholder_regex.findall(footnote))
        assert extracted_fn_vars == REQUIRED_INTERPOLATION_VARS_FOOTNOTE, (
            f"Placeholder mismatch in Table 3 footnote for locale '{locale}': {extracted_fn_vars}"
        )


def test_table_3_non_additivity_and_supremum_computation(
    sample_multi_tenant_ssot: Dict[str, Any], locales_dict: Dict[str, Any]
):
    """
    Gate 3: Verifies that Table 3 computes the MAX single incident cost (515.485 €)
    in the summary row rather than the false linear sum (1.115.485 €).
    """
    compiler = TomoAsisAstCompiler(
        ssot_payload=sample_multi_tenant_ssot,
        locale_catalog=locales_dict,
        locale_code="es",
    )
    ast_nodes = compiler.compile_chapter_3_domain_exposure_table()
    table_node = ast_nodes[0]
    footnote_node = ast_nodes[1]

    summary_row = table_node["summary_row"]
    severe_incident_summary_cell = summary_row[3]

    # Must display the maximum domain value (515.485 €) with the (Máx.) tag, NOT the linear sum
    assert "515.485 € (Máx.)" == severe_incident_summary_cell
    assert "1.115.485" not in severe_incident_summary_cell

    # Footnote must dynamically cite D5 and 515.485 €
    assert "515.485 €" in footnote_node["text"]
    assert "D5 - Industrial OT & Plant Execution" in footnote_node["text"]
```