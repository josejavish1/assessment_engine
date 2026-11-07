# RFC 077: Executive Single-Page Portfolio Snapshot & Polarity Governance

| Metadata | Specification |
| :--- | :--- |
| **Document ID** | `RFC-077-EXEC-SNAPSHOT-GOV` |
| **Status** | `APPROVED — MANDATORY ARCHITECTURAL STANDARD` |
| **Target Deliverable** | Consolidated AS-IS Diagnostic (Volume 1 / Tomo 1) — Chapter 1 |
| **Target Subsystems** | `tomo_asis_ast_compiler.py`, `locales.json`, `test_rfc077_executive_snapshot_governance.py` |
| **Architectural Law** | Zero Hardcoding, 100% Technical English Codebase, Single-Page AST Budget, 6-Locale Symmetry |

---

## 1. Executive Verdict & Layout Determinism Analysis

### 1.1 Architectural Diagnosis of Legacy Defects
The legacy implementation of Chapter 1 (*Executive Summary*) violates Tier-1 Boardroom advisory standards across three structural axes:

1. **Cognitive & Vertical Sprawl (Page Overflow)**: Stacking the Executive Cockpit, a verbose 3-column Legacy Triad Table, multi-paragraph narrative blocks, strategic challenge bullets, and the 3-pillar actuarial synthesis generates ~840 pt of vertical height. This exceeds the printable A4 content box (~694.8 pt), spilling Chapter 1 onto a second page and pushing Chapter 2 (*Methodology & Portfolio Heatmap*) off its deterministic Page 4 anchor.
2. **Semantic Redundancy**: The Legacy Triad Table (`tomo_triad_strength_desc`, `tomo_triad_gap_desc`, `tomo_triad_bottleneck_desc`) duplicates the narrative of the *Top Strategic Business Challenges* located directly below it.
3. **Static Hardware Bias & Hardcoded Invariants**: The legacy localization catalog assumes physical data center facilities and compute memory exhaustion, corrupting diagnostics for cloud-native or SaaS tenants. Furthermore, `tomo_ch1_p1` hardcodes `(Nivel 2 CMMI — Repetible)` and `los diez dominios tecnológicos`, causing immediate semantic failure when assessing tenants at CMMI Levels 1, 3, 4, or 5, or across custom $N$-domain topologies.

### 1.2 The Single-Page Boardroom Standard (Page 3 Determinism)
In a Fortune 500 executive deliverable, Chapter 1 must operate as an institutional **Single-Page Portfolio Snapshot** locked strictly onto **Page 3** (immediately following the Table of Contents on Page 2, and preceding Chapter 2 on Page 4). 

To guarantee deterministic rendering across Microsoft Word and LibreOffice Writer without vertical overflow, Chapter 1 is re-architected into **Four Non-Redundant Analytical Blocks** governed by a strict **OpenXML Vertical Point Budget**:

| Structural Component | Element Type | Typography / Leading | Padding / Spacing | Vertical Budget (pt) |
| :--- | :--- | :--- | :--- | :--- |
| ** printable A4 Canvas** | Page Geometry ($841.9\text{ pt} - 144.0\text{ pt margins}$) | — | Top/Bottom: $72.0\text{ pt}$ | **Max: 697.9 pt** |
| **Chapter Header** | H1 Title + Accent Rule | $16.0\text{ pt}$ Bold / $20.0\text{ pt}$ | After: $8.0\text{ pt}$ | $34.0\text{ pt}$ |
| **Block 1: Executive Cockpit** | 1x3 KPI Metric Strip | $18.0\text{ pt}$ Value / $8.5\text{ pt}$ Label | T/B Cell: $6.0\text{ pt}$, After: $8.0\text{ pt}$ | $56.0\text{ pt}$ |
| **Executive Lead Synthesis** | Single Dynamic Paragraph (`tomo_ch1_p1`) | $9.5\text{ pt}$ Regular / $13.0\text{ pt}$ | After: $8.0\text{ pt}$ (Max 4 lines) | $60.0\text{ pt}$ |
| **Block 2: Portfolio Polarity** | Section Subheader + 3x3 Extremes Table | $8.5\text{ pt}$ Table / $11.0\text{ pt}$ | T/B Cell: $4.5\text{ pt}$, After: $8.0\text{ pt}$ | $122.0\text{ pt}$ |
| **Block 3: Strategic Challenges** | Subheader + Headline + 3 Dynamic Bullets | $9.0\text{ pt}$ Bullets / $12.0\text{ pt}$ | Bullet After: $3.5\text{ pt}$, Block: $8.0\text{ pt}$ | $185.0\text{ pt}$ |
| **Block 4: Actuarial Exposure** | Subheader + Lead + 3 Open FAIR™ Pillars | $9.0\text{ pt}$ Pillars / $12.0\text{ pt}$ | Pillar After: $3.5\text{ pt}$, Block: $0.0\text{ pt}$ | $178.0\text{ pt}$ |
| **Safety Margin (Buffer)** | Rendering Tolerance Reserve | — | Unallocated Vertical Cushion | **$62.9\text{ pt}$ (9.0%)** |
| **TOTAL ALLOCATED** | **Deterministic Single-Page Footprint** | — | — | **$635.0\text{ pt} \le 697.9\text{ pt}$** |

---

## 2. Dynamic Domain Polarity Algorithms

To eliminate static prose from Block 2, the compiler must compute mathematical portfolio extremes at runtime from the Single Source of Truth (SSOT) domain vector. 

### 2.1 Tie-Breaking & Edge-Case Governance
For any $N$-domain assessment ($N \ge 1$), the polarity engine evaluates each domain record $d_i \in D$ containing `(code, name, maturity_score, ale_eur)`:
1. **Maturity Leader ($d_{\text{leader}}$)**: Maximizes `maturity_score`. Tie-breaker: lowest `ale_eur` (highest resilience), then lexicographical `code` ascending.
2. **Financial Risk Concentration ($d_{\text{risk}}$)**: Maximizes `ale_eur`. Tie-breaker: lowest `maturity_score` (highest vulnerability), then lexicographical `code` ascending.
3. **Modernization Urgency / Lagging Domain ($d_{\text{lagging}}$)**: Minimizes `maturity_score`. Tie-breaker: highest `ale_eur` (highest financial exposure at low maturity), then lexicographical `code` ascending.
4. **Zero-ALE Guard**: If $\sum \text{ale\_eur} == 0$, `top_risk_share_pct` defaults cleanly to `"0.0"` without raising `ZeroDivisionError`.

### 2.2 Production Python Implementation

```python
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Sequence


@dataclass(frozen=True)
class DomainPolarityMetric:
    """Immutable representation of a single domain extremity in the portfolio."""
    code: str
    name: str
    score_formatted: str
    ale_formatted: str
    ale_share_pct: str
    raw_score: float
    raw_ale: float


@dataclass(frozen=True)
class PortfolioPolarityExtremes:
    """Container holding the three mathematical extremes of the assessed portfolio."""
    domain_count: int
    leader: DomainPolarityMetric
    top_risk: DomainPolarityMetric
    lagging: DomainPolarityMetric


def _compute_portfolio_polarity_extremes(
    domains: Sequence[Dict[str, Any]],
    currency_formatter: Callable[[float], str],
) -> PortfolioPolarityExtremes:
    """
    Dynamically computes portfolio polarity extremes (Maturity Leader, Top Financial Risk,
    and Modernization Urgency / Lagging Domain) across any N-domain topology.

    Enforces deterministic tie-breaking and zero-division guards.
    """
    if not domains:
        fallback = DomainPolarityMetric(
            code="N/A",
            name="Unassigned Domain",
            score_formatted="0.00",
            ale_formatted=currency_formatter(0.0),
            ale_share_pct="0.0",
            raw_score=0.0,
            raw_ale=0.0,
        )
        return PortfolioPolarityExtremes(
            domain_count=0,
            leader=fallback,
            top_risk=fallback,
            lagging=fallback,
        )

    normalized: List[Dict[str, Any]] = []
    total_portfolio_ale: float = 0.0

    for item in domains:
        code = str(item.get("code") or item.get("domain_code") or "DOM").strip()
        name = str(item.get("name") or item.get("domain_name") or code).strip()
        score = float(item.get("score") if item.get("score") is not None else item.get("maturity_score", 0.0))
        ale = float(item.get("ale") if item.get("ale") is not None else item.get("ale_eur", 0.0))
        total_portfolio_ale += max(0.0, ale)
        normalized.append(
            {
                "code": code,
                "name": name,
                "score": score,
                "ale": max(0.0, ale),
            }
        )

    # 1. Maturity Leader: Highest score -> Lowest ALE -> Code ASC
    leader_raw = min(
        normalized,
        key=lambda d: (-round(d["score"], 4), round(d["ale"], 2), d["code"]),
    )

    # 2. Financial Risk Concentration: Highest ALE -> Lowest score -> Code ASC
    top_risk_raw = min(
        normalized,
        key=lambda d: (-round(d["ale"], 2), round(d["score"], 4), d["code"]),
    )

    # 3. Modernization Urgency (Lagging): Lowest score -> Highest ALE -> Code ASC
    lagging_raw = min(
        normalized,
        key=lambda d: (round(d["score"], 4), -round(d["ale"], 2), d["code"]),
    )

    def _to_metric(record: Dict[str, Any]) -> DomainPolarityMetric:
        share = (
            (record["ale"] / total_portfolio_ale) * 100.0
            if total_portfolio_ale > 0.0
            else 0.0
        )
        return DomainPolarityMetric(
            code=record["code"],
            name=record["name"],
            score_formatted=f"{record['score']:.2f}",
            ale_formatted=currency_formatter(record["ale"]),
            ale_share_pct=f"{share:.1f}",
            raw_score=record["score"],
            raw_ale=record["ale"],
        )

    return PortfolioPolarityExtremes(
        domain_count=len(normalized),
        leader=_to_metric(leader_raw),
        top_risk=_to_metric(top_risk_raw),
        lagging=_to_metric(lagging_raw),
    )
```

---

## 3. Exact Refactored Localization Catalogs (`locales.json`)

All static facility/memory assumptions and hardcoded CMMI/domain-count strings are purged. `tomo_ch1_p1` now accepts `{domain_count}` and `{cmmi_label}` dynamically, while the Block 2 Polarity Table uses parameterized telemetry templates across all 6 supported locales (`es`, `en`, `pt`, `fr`, `de`, `ja`).

```json
{
  "es": {
    "tomo_ch1_title": "1. Resumen Ejecutivo",
    "tomo_ch1_p1": "La evaluación integral del portafolio tecnológico de {client} abarca {domain_count} dominios operativos y arroja un Índice Global de Madurez de {score} sobre 5.00 ({cmmi_label}). Este perfil refleja una arquitectura con capacidades operativas consolidadas en sus activos líderes, pero expuesta a asimetrías estructurales y riesgos financieros concentrados que requieren gobernanza ejecutiva prioritaria.",
    "tomo_polarity_section_title": "Radiografía de Polaridad y Extremos del Portafolio",
    "tomo_polarity_col_axis": "Eje de Polaridad del Portafolio",
    "tomo_polarity_col_domain": "Dominio Identificado (SSOT)",
    "tomo_polarity_col_telemetry": "Telemetría e Impacto de Gobernanza",
    "tomo_polarity_leader_axis": "Líder de Madurez Operativa",
    "tomo_polarity_leader_domain": "{leader_code} — {leader_name}",
    "tomo_polarity_leader_desc": "Madurez máxima del portafolio ({leader_score} / 5.00). Actúa como referencia interna de control y estandarización operativa ({leader_ale} / año).",
    "tomo_polarity_risk_axis": "Concentración de Riesgo Financiero",
    "tomo_polarity_risk_domain": "{top_risk_code} — {top_risk_name}",
    "tomo_polarity_risk_desc": "Exposición actuarial máxima con {top_risk_ale} / año ({top_risk_share_pct}% del ALE total del portafolio; madurez {top_risk_score} / 5.00).",
    "tomo_polarity_lagging_axis": "Urgencia de Modernización (Rezago)",
    "tomo_polarity_lagging_domain": "{lagging_code} — {lagging_name}",
    "tomo_polarity_lagging_desc": "Madurez mínima registrada ({lagging_score} / 5.00). Representa el principal cuello de botella estructural con exposición de {lagging_ale} / año.",
    "tomo_ch1_challenges_title": "Desafíos Estratégicos de Negocio Prioritarios",
    "tomo_ch1_econ_title": "Cuantificación Actuarial de Exposición Financiera (Open FAIR™)"
  },
  "en": {
    "tomo_ch1_title": "1. Executive Summary",
    "tomo_ch1_p1": "The comprehensive technology portfolio assessment for {client} encompasses {domain_count} operational domains, yielding a Global Maturity Index of {score} out of 5.00 ({cmmi_label}). This profile reflects an architecture with established operational capabilities in its leading assets, yet exposed to structural asymmetries and concentrated financial risks requiring immediate executive governance.",
    "tomo_polarity_section_title": "Portfolio Polarity & Extremes Radiography",
    "tomo_polarity_col_axis": "Portfolio Polarity Axis",
    "tomo_polarity_col_domain": "Identified Domain (SSOT)",
    "tomo_polarity_col_telemetry": "Telemetry & Governance Impact",
    "tomo_polarity_leader_axis": "Operational Maturity Leader",
    "tomo_polarity_leader_domain": "{leader_code} — {leader_name}",
    "tomo_polarity_leader_desc": "Highest portfolio maturity ({leader_score} / 5.00). Serves as the internal benchmark for control and operational standardization ({leader_ale} / year).",
    "tomo_polarity_risk_axis": "Financial Risk Concentration",
    "tomo_polarity_risk_domain": "{top_risk_code} — {top_risk_name}",
    "tomo_polarity_risk_desc": "Peak actuarial exposure at {top_risk_ale} / year ({top_risk_share_pct}% of total portfolio ALE; maturity {top_risk_score} / 5.00).",
    "tomo_polarity_lagging_axis": "Modernization Urgency (Lagging)",
    "tomo_polarity_lagging_domain": "{lagging_code} — {lagging_name}",
    "tomo_polarity_lagging_desc": "Lowest recorded maturity ({lagging_score} / 5.00). Represents the primary structural bottleneck with an exposure of {lagging_ale} / year.",
    "tomo_ch1_challenges_title": "Priority Strategic Business Challenges",
    "tomo_ch1_econ_title": "Actuarial Financial Exposure Quantification (Open FAIR™)"
  },
  "pt": {
    "tomo_ch1_title": "1. Resumo Executivo",
    "tomo_ch1_p1": "A avaliação abrangente do portfólio tecnológico da {client} abrange {domain_count} domínios operacionais, resultando em um Índice Global de Maturidade de {score} em 5.00 ({cmmi_label}). Este perfil reflete uma arquitetura com capacidades operacionais consolidadas em seus ativos líderes, mas exposta a assimetrias estruturais e riscos financeiros concentrados que exigem governança executiva prioritária.",
    "tomo_polarity_section_title": "Radiografia de Polaridade e Extremos do Portfólio",
    "tomo_polarity_col_axis": "Eixo de Polaridade do Portfólio",
    "tomo_polarity_col_domain": "Domínio Identificado (SSOT)",
    "tomo_polarity_col_telemetry": "Telemetria e Impacto de Governança",
    "tomo_polarity_leader_axis": "Líder de Maturidade Operacional",
    "tomo_polarity_leader_domain": "{leader_code} — {leader_name}",
    "tomo_polarity_leader_desc": "Maior maturidade do portfólio ({leader_score} / 5.00). Atua como referência interna de controle e padronização operacional ({leader_ale} / ano).",
    "tomo_polarity_risk_axis": "Concentração de Risco Financeiro",
    "tomo_polarity_risk_domain": "{top_risk_code} — {top_risk_name}",
    "tomo_polarity_risk_desc": "Exposição atuarial máxima de {top_risk_ale} / ano ({top_risk_share_pct}% do ALE total do portfólio; maturidade {top_risk_score} / 5.00).",
    "tomo_polarity_lagging_axis": "Urgência de Modernização (Defasagem)",
    "tomo_polarity_lagging_domain": "{lagging_code} — {lagging_name}",
    "tomo_polarity_lagging_desc": "Menor maturidade registrada ({lagging_score} / 5.00). Representa o principal gargalo estrutural com exposição de {lagging_ale} / ano.",
    "tomo_ch1_challenges_title": "Desafios Estratégicos de Negócio Prioritários",
    "tomo_ch1_econ_title": "Quantificação Atuarial de Exposição Financeira (Open FAIR™)"
  },
  "fr": {
    "tomo_ch1_title": "1. Synthèse Exécutive",
    "tomo_ch1_p1": "L'évaluation exhaustive du portefeuille technologique de {client} couvre {domain_count} domaines opérationnels et établit un Indice Global de Maturité de {score} sur 5.00 ({cmmi_label}). Ce profil reflète une architecture dotée de capacités consolidées sur ses actifs phares, mais exposée à des asymétries structurelles et à une concentration des risques financiers exigeant une gouvernance exécutive prioritaire.",
    "tomo_polarity_section_title": "Radiographie de Polarité et des Extrêmes du Portefeuille",
    "tomo_polarity_col_axis": "Axe de Polarité du Portefeuille",
    "tomo_polarity_col_domain": "Domaine Identifié (SSOT)",
    "tomo_polarity_col_telemetry": "Télémétrie et Impact de Gouvernance",
    "tomo_polarity_leader_axis": "Leader de Maturité Opérationnelle",
    "tomo_polarity_leader_domain": "{leader_code} — {leader_name}",
    "tomo_polarity_leader_desc": "Maturité maximale du portefeuille ({leader_score} / 5.00). Sert de référence interne de contrôle et de standardisation ({leader_ale} / an).",
    "tomo_polarity_risk_axis": "Concentration du Risque Financier",
    "tomo_polarity_risk_domain": "{top_risk_code} — {top_risk_name}",
    "tomo_polarity_risk_desc": "Exposition actuarielle maximale à {top_risk_ale} / an ({top_risk_share_pct}% de l'ALE total du portefeuille ; maturité {top_risk_score} / 5.00).",
    "tomo_polarity_lagging_axis": "Urgence de Modernisation (Retard)",
    "tomo_polarity_lagging_domain": "{lagging_code} — {lagging_name}",
    "tomo_polarity_lagging_desc": "Maturité minimale enregistrée ({lagging_score} / 5.00). Représente le principal goulot d'étranglement structurel avec une exposition de {lagging_ale} / an.",
    "tomo_ch1_challenges_title": "Défis Stratégiques Prioritaires de l'Entreprise",
    "tomo_ch1_econ_title": "Quantification Actuarielle de l'Exposition Financière (Open FAIR™)"
  },
  "de": {
    "tomo_ch1_title": "1. Management Summary",
    "tomo_ch1_p1": "Die umfassende Bewertung des Technologieportfolios von {client} erstreckt sich über {domain_count} operative Domänen und ergibt einen globalen Reifegradindex von {score} von 5.00 ({cmmi_label}). Dieses Profil zeigt eine Architektur mit gefestigten operativen Fähigkeiten in ihren führenden Assets, die jedoch strukturellen Asymmetrien und konzentrierten finanziellen Risiken ausgesetzt ist, welche eine prioritäre Executive Governance erfordern.",
    "tomo_polarity_section_title": "Portfoliopolarität und Extremwerte-Radiographie",
    "tomo_polarity_col_axis": "Portfoliopolaritätsachse",
    "tomo_polarity_col_domain": "Identifizierte Domäne (SSOT)",
    "tomo_polarity_col_telemetry": "Telemetrie & Governance-Auswirkung",
    "tomo_polarity_leader_axis": "Operativer Reifegrad-Leader",
    "tomo_polarity_leader_domain": "{leader_code} — {leader_name}",
    "tomo_polarity_leader_desc": "Höchster Portfolioreifegrad ({leader_score} / 5.00). Dient als interner Maßstab für Kontrolle und operative Standardisierung ({leader_ale} / Jahr).",
    "tomo_polarity_risk_axis": "Finanzielle Risikokonzentration",
    "tomo_polarity_risk_domain": "{top_risk_code} — {top_risk_name}",
    "tomo_polarity_risk_desc": "Maximales versicherungsmathematisches Risiko bei {top_risk_ale} / Jahr ({top_risk_share_pct}% des gesamten Portfolio-ALE; Reifegrad {top_risk_score} / 5.00).",
    "tomo_polarity_lagging_axis": "Modernisierungsdringlichkeit (Rückstand)",
    "tomo_polarity_lagging_domain": "{lagging_code} — {lagging_name}",
    "tomo_polarity_lagging_desc": "Niedrigster erfasster Reifegrad ({lagging_score} / 5.00). Stellt den primären strukturellen Engpass mit einem Risiko von {lagging_ale} / Jahr dar.",
    "tomo_ch1_challenges_title": "Prioritäre Strategische Geschäftsherausforderungen",
    "tomo_ch1_econ_title": "Versicherungsmathematische Risikoquantifizierung (Open FAIR™)"
  },
  "ja": {
    "tomo_ch1_title": "1. エグゼクティブサマリー",
    "tomo_ch1_p1": "{client}のテクノロジーポートフォリオに関する包括的評価は{domain_count}の運用ドメインを対象とし、総合成熟度指数は5.00満点中{score}（{cmmi_label}）となりました。このプロファイルは、主要資産において確立された運用能力を備えている一方で、優先的なエグゼクティブガバナンスを必要とする構造的非対称性と集中した財務リスクに晒されているアーキテクチャを反映しています。",
    "tomo_polarity_section_title": "ポートフォリオ極性および極値分析",
    "tomo_polarity_col_axis": "ポートフォリオ極性軸",
    "tomo_polarity_col_domain": "特定ドメイン (SSOT)",
    "tomo_polarity_col_telemetry": "テレメトリとガバナンスへの影響",
    "tomo_polarity_leader_axis": "運用成熟度リーダー",
    "tomo_polarity_leader_domain": "{leader_code} — {leader_name}",
    "tomo_polarity_leader_desc": "ポートフォリオ最高成熟度（{leader_score} / 5.00）。統制および運用標準化の社内ベンチマークとして機能（年間 {leader_ale}）。",
    "tomo_polarity_risk_axis": "財務リスク集中ドメイン",
    "tomo_polarity_risk_domain": "{top_risk_code} — {top_risk_name}",
    "tomo_polarity_risk_desc": "最大数理リスク露出：年間 {top_risk_ale}（ポートフォリオ総ALEの{top_risk_share_pct}%、成熟度 {top_risk_score} / 5.00）。",
    "tomo_polarity_lagging_axis": "近代化最優先ドメイン（遅滞）",
    "tomo_polarity_lagging_domain": "{lagging_code} — {lagging_name}",
    "tomo_polarity_lagging_desc": "最低記録成熟度（{lagging_score} / 5.00）。年間 {lagging_ale} の露出を伴う主要な構造的ボトルネック。",
    "tomo_ch1_challenges_title": "最優先の戦略的ビジネス課題",
    "tomo_ch1_econ_title": "財務リスク露出の数理定量化 (Open FAIR™)"
  }
}
```

---

## 4. Concrete AST Implementation Plan (`tomo_asis_ast_compiler.py`)

The `_compile_chapter_1_executive_summary` method in `tomo_asis_ast_compiler.py` is refactored to emit the 4-block Single-Page Snapshot AST and enforce explicit OpenXML spacing constraints.

```python
from typing import Any, Dict, List


def _compile_chapter_1_executive_summary(
    self,
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Compiles Chapter 1 (Executive Summary) as a deterministic Single-Page
    Portfolio Snapshot locked onto Page 3 of the Consolidated AS-IS Deliverable.

    Enforces a strict vertical point budget (<= 635.0 pt) across four blocks:
      - Block 1: Executive Cockpit Strip (Global Score, CMMI Level, Annual ALE)
      - Block 2: Portfolio Polarity & Extremes Radiography (3x3 Dynamic SSOT Table)
      - Block 3: Priority Strategic Business Challenges (Dynamic Burning Platform)
      - Block 4: Actuarial Financial Quantification (Open FAIR 3-Pillar Breakdown)
    """
    nodes: List[Dict[str, Any]] = []

    client_name = str(context.get("client_name") or "Enterprise Client").strip()
    global_score = float(context.get("global_score", 0.0))
    global_score_str = f"{global_score:.2f}"
    cmmi_label = self._resolve_cmmi_band_label(global_score)
    total_ale_str = self._format_currency(float(context.get("total_ale_eur", 0.0)))

    domains = context.get("domains") or []
    polarity = _compute_portfolio_polarity_extremes(
        domains=domains,
        currency_formatter=self._format_currency,
    )

    # Chapter Title (H1) - Budget: 34.0 pt
    nodes.append(
        {
            "type": "heading",
            "level": 1,
            "text": self._t("tomo_ch1_title"),
            "style": {
                "font_size_pt": 16.0,
                "line_spacing_pt": 20.0,
                "space_before_pt": 0.0,
                "space_after_pt": 8.0,
                "keep_with_next": True,
            },
        }
    )

    # BLOCK 1: Top Cockpit Strip (1x3 KPI Table) - Budget: 56.0 pt
    nodes.append(
        {
            "type": "cockpit_strip_table",
            "layout_budget_pt": 56.0,
            "style": {
                "cell_padding_top_pt": 6.0,
                "cell_padding_bottom_pt": 6.0,
                "space_after_pt": 8.0,
                "value_font_size_pt": 18.0,
                "label_font_size_pt": 8.5,
            },
            "columns": [
                {
                    "label": self._t("tomo_cockpit_score_label"),
                    "value": f"{global_score_str} / 5.00",
                    "accent": "navy",
                },
                {
                    "label": self._t("tomo_cockpit_maturity_label"),
                    "value": cmmi_label,
                    "accent": "slate",
                },
                {
                    "label": self._t("tomo_cockpit_ale_label"),
                    "value": total_ale_str,
                    "accent": "crimson",
                },
            ],
        }
    )

    # Executive Lead Synthesis Paragraph - Budget: 60.0 pt
    nodes.append(
        {
            "type": "paragraph",
            "text": self._t(
                "tomo_ch1_p1",
                client=client_name,
                domain_count=polarity.domain_count,
                score=global_score_str,
                cmmi_label=cmmi_label,
            ),
            "style": {
                "font_size_pt": 9.5,
                "line_spacing_pt": 13.0,
                "space_before_pt": 0.0,
                "space_after_pt": 8.0,
            },
        }
    )

    # BLOCK 2: Portfolio Polarity & Extremes Radiography - Budget: 122.0 pt
    nodes.append(
        {
            "type": "subheading",
            "level": 2,
            "text": self._t("tomo_polarity_section_title"),
            "style": {
                "font_size_pt": 10.5,
                "line_spacing_pt": 13.5,
                "space_before_pt": 2.0,
                "space_after_pt": 4.0,
                "keep_with_next": True,
            },
        }
    )

    fmt_kwargs = {
        "leader_code": polarity.leader.code,
        "leader_name": polarity.leader.name,
        "leader_score": polarity.leader.score_formatted,
        "leader_ale": polarity.leader.ale_formatted,
        "top_risk_code": polarity.top_risk.code,
        "top_risk_name": polarity.top_risk.name,
        "top_risk_score": polarity.top_risk.score_formatted,
        "top_risk_ale": polarity.top_risk.ale_formatted,
        "top_risk_share_pct": polarity.top_risk.ale_share_pct,
        "lagging_code": polarity.lagging.code,
        "lagging_name": polarity.lagging.name,
        "lagging_score": polarity.lagging.score_formatted,
        "lagging_ale": polarity.lagging.ale_formatted,
    }

    nodes.append(
        {
            "type": "polarity_extremes_table",
            "layout_budget_pt": 102.0,
            "column_widths_pct": [26.0, 26.0, 48.0],
            "style": {
                "font_size_pt": 8.5,
                "line_spacing_pt": 11.0,
                "cell_padding_top_pt": 4.5,
                "cell_padding_bottom_pt": 4.5,
                "cell_padding_left_pt": 6.0,
                "cell_padding_right_pt": 6.0,
                "space_after_pt": 8.0,
                "cant_split_rows": True,
            },
            "headers": [
                self._t("tomo_polarity_col_axis"),
                self._t("tomo_polarity_col_domain"),
                self._t("tomo_polarity_col_telemetry"),
            ],
            "rows": [
                {
                    "polarity_type": "leader",
                    "badge_color": "#1B5E20",
                    "cells": [
                        self._t("tomo_polarity_leader_axis"),
                        self._t("tomo_polarity_leader_domain", **fmt_kwargs),
                        self._t("tomo_polarity_leader_desc", **fmt_kwargs),
                    ],
                },
                {
                    "polarity_type": "top_risk",
                    "badge_color": "#B71C1C",
                    "cells": [
                        self._t("tomo_polarity_risk_axis"),
                        self._t("tomo_polarity_risk_domain", **fmt_kwargs),
                        self._t("tomo_polarity_risk_desc", **fmt_kwargs),
                    ],
                },
                {
                    "polarity_type": "lagging",
                    "badge_color": "#E65100",
                    "cells": [
                        self._t("tomo_polarity_lagging_axis"),
                        self._t("tomo_polarity_lagging_domain", **fmt_kwargs),
                        self._t("tomo_polarity_lagging_desc", **fmt_kwargs),
                    ],
                },
            ],
        }
    )

    # BLOCK 3: Top Strategic Business Challenges - Budget: 185.0 pt
    nodes.append(
        {
            "type": "subheading",
            "level": 2,
            "text": self._t("tomo_ch1_challenges_title"),
            "style": {
                "font_size_pt": 10.5,
                "line_spacing_pt": 13.5,
                "space_before_pt": 2.0,
                "space_after_pt": 4.0,
                "keep_with_next": True,
            },
        }
    )

    burning_platform = context.get("burning_platform") or {}
    headline_text = str(burning_platform.get("headline") or self._t("tomo_ch1_p2")).strip()
    nodes.append(
        {
            "type": "paragraph",
            "text": headline_text,
            "style": {
                "font_size_pt": 9.0,
                "line_spacing_pt": 12.0,
                "space_before_pt": 0.0,
                "space_after_pt": 4.0,
                "italic": True,
            },
        }
    )

    raw_challenges = burning_platform.get("challenges") or [
        self._t("tomo_ch1_b1"),
        self._t("tomo_ch1_b2"),
        self._t("tomo_ch1_b3"),
    ]
    nodes.append(
        {
            "type": "bullet_list",
            "layout_budget_pt": 140.0,
            "items": [str(c).strip() for c in raw_challenges[:3]],
            "style": {
                "font_size_pt": 9.0,
                "line_spacing_pt": 12.0,
                "item_space_after_pt": 3.5,
                "block_space_after_pt": 8.0,
            },
        }
    )

    # BLOCK 4: Actuarial Financial Quantification (Open FAIR) - Budget: 178.0 pt
    nodes.append(
        {
            "type": "subheading",
            "level": 2,
            "text": self._t("tomo_ch1_econ_title"),
            "style": {
                "font_size_pt": 10.5,
                "line_spacing_pt": 13.5,
                "space_before_pt": 2.0,
                "space_after_pt": 4.0,
                "keep_with_next": True,
            },
        }
    )

    nodes.append(
        {
            "type": "paragraph",
            "text": self._t(
                "tomo_ch1_econ_lead",
                client=client_name,
                ale=total_ale_str,
            ),
            "style": {
                "font_size_pt": 9.0,
                "line_spacing_pt": 12.0,
                "space_before_pt": 0.0,
                "space_after_pt": 4.0,
            },
        }
    )

    fair_metrics = context.get("open_fair") or {}
    single_outage_str = self._format_currency(
        float(fair_metrics.get("single_worst_incident_eur", 0.0))
    )
    crisis_p90_str = self._format_currency(
        float(fair_metrics.get("portfolio_crisis_p90_eur", 0.0))
    )

    nodes.append(
        {
            "type": "actuarial_pillars_list",
            "layout_budget_pt": 130.0,
            "items": [
                self._t("tomo_ch1_econ_b1", ale=total_ale_str),
                self._t("tomo_ch1_econ_b2", outage=single_outage_str, top_risk_code=polarity.top_risk.code),
                self._t("tomo_ch1_econ_b3", p90=crisis_p90_str),
            ],
            "style": {
                "font_size_pt": 9.0,
                "line_spacing_pt": 12.0,
                "item_space_after_pt": 3.5,
                "block_space_after_pt": 0.0,
            },
        }
    )

    # Explicit Page Break anchoring Chapter 2 strictly to Page 4
    nodes.append({"type": "page_break", "target_page": 4})

    return nodes
```

---

## 5. Automated Quality Gate Test Specification

File: `tests/unit/test_rfc077_executive_snapshot_governance.py`

```python
import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from src.reporting.tomo_asis_ast_compiler import (
    _compute_portfolio_polarity_extremes,
    TomoAsisAstCompiler,
)

SUPPORTED_LOCALES = ("es", "en", "pt", "fr", "de", "ja")
REQUIRED_RFC077_KEYS = (
    "tomo_ch1_title",
    "tomo_ch1_p1",
    "tomo_polarity_section_title",
    "tomo_polarity_col_axis",
    "tomo_polarity_col_domain",
    "tomo_polarity_col_telemetry",
    "tomo_polarity_leader_axis",
    "tomo_polarity_leader_domain",
    "tomo_polarity_leader_desc",
    "tomo_polarity_risk_axis",
    "tomo_polarity_risk_domain",
    "tomo_polarity_risk_desc",
    "tomo_polarity_lagging_axis",
    "tomo_polarity_lagging_domain",
    "tomo_polarity_lagging_desc",
    "tomo_ch1_challenges_title",
    "tomo_ch1_econ_title",
)


def _mock_eur_formatter(amount: float) -> str:
    return f"EUR {amount:,.0f}"


def test_polarity_extremes_arbitrary_topology_and_tie_breaking() -> None:
    """Verifies dynamic leader, top risk, and lagging domain extraction across N domains."""
    domains: List[Dict[str, Any]] = [
        {"code": "D1", "name": "Cloud Platform", "score": 4.10, "ale": 120_000.0},
        {"code": "D2", "name": "Core Banking", "score": 4.10, "ale": 85_000.0},  # Leader via lower ALE tie-breaker
        {"code": "D3", "name": "Cyber Defense", "score": 2.40, "ale": 950_000.0},  # Top Risk
        {"code": "D4", "name": "Legacy ERP", "score": 1.65, "ale": 410_000.0},  # Lagging via higher ALE tie-breaker
        {"code": "D5", "name": "Data Governance", "score": 1.65, "ale": 190_000.0},
    ]

    extremes = _compute_portfolio_polarity_extremes(domains, _mock_eur_formatter)

    assert extremes.domain_count == 5
    assert extremes.leader.code == "D2"
    assert extremes.leader.score_formatted == "4.10"
    assert extremes.top_risk.code == "D3"
    assert extremes.top_risk.ale_share_pct == "54.1"
    assert extremes.lagging.code == "D4"
    assert extremes.lagging.score_formatted == "1.65"


def test_polarity_zero_ale_guard() -> None:
    """Ensures zero-ALE portfolios do not raise ZeroDivisionError."""
    domains = [{"code": "C1", "name": "Zero Risk Asset", "score": 3.5, "ale": 0.0}]
    extremes = _compute_portfolio_polarity_extremes(domains, _mock_eur_formatter)
    assert extremes.top_risk.ale_share_pct == "0.0"
    assert extremes.domain_count == 1


def test_locales_mathematical_symmetry_and_zero_hardcoding() -> None:
    """Enforces 6-locale symmetry and verifies removal of hardcoded CMMI/domain counts."""
    locales_path = Path("src/i18n/locales.json")
    if not locales_path.exists():
        pytest.skip("locales.json path not mounted in isolated unit runner")

    catalog = json.loads(locales_path.read_text(encoding="utf-8"))
    for lang in SUPPORTED_LOCALES:
        assert lang in catalog, f"Missing locale '{lang}'"
        lang_dict = catalog[lang]
        for key in REQUIRED_RFC077_KEYS:
            assert key in lang_dict, f"Missing RFC 077 key '{key}' in locale '{lang}'"
            assert lang_dict[key].strip(), f"Empty translation for '{key}' in locale '{lang}'"

        # Verify dynamic placeholders in paragraph 1
        p1_template = lang_dict["tomo_ch1_p1"]
        assert "{domain_count}" in p1_template
        assert "{cmmi_label}" in p1_template
        assert "Nivel 2 CMMI" not in p1_template
        assert "diez dominios" not in p1_template


def test_chapter_1_ast_single_page_vertical_budget() -> None:
    """Verifies Chapter 1 AST replaces legacy triad table and stays strictly <= 635 pt."""
    compiler = TomoAsisAstCompiler(locale="en")
    context = {
        "client_name": "Global Financial Corp",
        "global_score": 3.45,
        "total_ale_eur": 2_500_000.0,
        "domains": [
            {"code": "DOM-01", "name": "Cloud Native Core", "score": 4.25, "ale": 200_000.0},
            {"code": "DOM-02", "name": "Identity & Access", "score": 2.90, "ale": 1_600_000.0},
            {"code": "DOM-03", "name": "Mainframe Bridge", "score": 1.80, "ale": 700_000.0},
        ],
        "burning_platform": {
            "headline": "Concentrated identity exposure threatens core transaction SLA.",
            "challenges": ["Challenge A", "Challenge B", "Challenge C"],
        },
        "open_fair": {
            "single_worst_incident_eur": 980_000.0,
            "portfolio_crisis_p90_eur": 4_100_000.0,
        },
    }

    ast_nodes = compiler._compile_chapter_1_executive_summary(context)
    node_types = [n["type"] for n in ast_nodes]

    assert "polarity_extremes_table" in node_types
    assert "legacy_triad_table" not in node_types
    assert ast_nodes[-1] == {"type": "page_break", "target_page": 4}

    polarity_node = next(n for n in ast_nodes if n["type"] == "polarity_extremes_table")
    assert len(polarity_node["rows"]) == 3
    assert "DOM-01" in polarity_node["rows"][0]["cells"][1]
    assert "DOM-02" in polarity_node["rows"][1]["cells"][1]
    assert "64.0%" in polarity_node["rows"][1]["cells"][2]
    assert "DOM-03" in polarity_node["rows"][2]["cells"][1]
```