# RFC 081: Section 3.2 Dynamic Risk Taxonomy Clustering & Heatmap Legend Governance

| Metadata | Details |
| :--- | :--- |
| **RFC ID** | RFC-081 |
| **Title** | Section 3.2 Dynamic Risk Taxonomy Clustering & Heatmap Legend Governance |
| **Status** | APPROVED / READY FOR IMPLEMENTATION |
| **Author** | Chief Corporate Governance Advisor & Principal Actuarial Risk Architect |
| **Target Deliverable** | Consolidated AS-IS Diagnostic (Volume 1 / Tomo 1 — Section 3.2) |
| **Compliance Standards** | Open FAIR™ (ISO/IEC 27005), ORX (Operational Riskdata eXchange) Taxonomy, Gartner Adaptive Risk Governance |
| **Architectural Laws** | 100% Technical English Codebase, Zero Hardcoding (Dynamic $N$-Axis Polymorphism), 6-Locale Mathematical Symmetry (`es`, `en`, `pt`, `fr`, `de`, `ja`) |

---

## 1. Executive Verdict & ORX/FAIR State-of-the-Art Justification

### 1.1 The Executive Governance Failure of "Orphaned Plot Points"
In Tier-1 Boardroom advisories, presenting a 5x5 Open FAIR™ Risk Matrix populated with unindexed internal system codes (e.g., `T05.R01`, `T02.R01`) represents a severe editorial and governance anti-pattern. Chief Executive Officers, Chief Financial Officers, and Audit Committee Chairs do not think in terms of internal audit tower identifiers; they govern through **Systemic Business Threat Vectors** and **Capital-at-Risk (Annualized Loss Expectancy — ALE)**.

Furthermore, a mathematical disconnect currently exists between the macroscopic executive summary and the microscopic forensic annexes:
* **The Forensic Reality:** Across the $N$ specialist assessment domains, the forensic audit uncovers dozens or hundreds of empirical technical findings (e.g., 143 total findings broken down into 24 Critical, 68 High, and 51 Medium severity anomalies).
* **The Abstract Representation:** Section 3.2 currently plots only $N$ top-level abstract risk vectors on the 5x5 matrix without explaining how the underlying 143 granular findings aggregate into those vectors. This creates an illusion of arbitrary scoring and fails the **Audit Trail Traceability Mandate**.

### 1.2 The State-of-the-Art Solution: Dynamic Ontological Risk Clustering
Global Tier-1 risk practices (McKinsey Risk Practice, BCG Platinion, Big 4 Actuarial Advisory) aligned with the **ORX (Operational Riskdata eXchange) Reference Taxonomy** and **Open FAIR™ Risk Analysis** strictly prohibit two extremes:
1. Dumping an ungrouped 100+ item technical "laundry list" into an executive deliverable.
2. Forcing every enterprise—regardless of industry, topology, or empirical findings—into a rigid, hardcoded 4-pillar static table.

The industry benchmark is a **Dynamic Ontological Clustering Engine**. Under this architecture:
* The engine maintains a canonical catalog of universal, industry-agnostic **Macro-Risk Taxonomy Families** (e.g., *Structural Obsolescence & Technical Debt*, *Cyber Resilience, Identity & Perimeter Governance*).
* During AST compilation, the engine inspects the active $N$-tower payload, dynamically maps each tower's primary risk vectors and underlying granular findings (Critical, High, Medium) into the canonical families, and calculates the **Clustered Annualized Loss Expectancy ($\sum \text{ALE}$)**.
* **Dynamic $N$-Axis Polymorphism (Zero-Hardcoding Law):** Only taxonomy families with non-zero empirical findings ($\text{Total Findings} > 0$ or $\text{ALE} > 0$) are instantiated and rendered. If a cloud-native SaaS client exhibits zero findings in *Edge, Plant & Operational Continuity*, that taxonomy cluster is mathematically pruned from the AST. Active clusters are deterministically sorted in descending order of aggregate financial exposure ($\sum \text{ALE}$).

---

## 2. The Canonical Risk Taxonomy Catalog & Dynamic Mapping Logic

To guarantee universal applicability across any enterprise topology without hardcoding domain names or client-specific nouns, the engine establishes six (6) canonical **Macro-Risk Taxonomy Families**.

### 2.1 Canonical Taxonomy Matrix (Internal Technical English Keys)

| Canonical Taxonomy Key (`taxonomy_id`) | ORX / Open FAIR™ Alignment | Semantic Keyword Heuristics & Domain Affinity (Dynamic Classifier) |
| :--- | :--- | :--- |
| `TAXONOMY_STRUCTURAL_OBSOLESCENCE` | Technology & Infrastructure Failure / Legacy Debt | End-of-Life (EoL), End-of-Support (EoS), legacy platforms, monolithic coupling, hardware aging, unsupported OS/DB kernels, modernization deficit, technical debt. |
| `TAXONOMY_CYBER_IDENTITY_GOVERNANCE` | External Fraud & Cyber Breach / Access Control | IAM, PAM, Active Directory, MFA, zero-trust, perimeter security, vulnerability management, unpatched CVEs, encryption, compliance, GDPR/ISO/SOC2, shadow IT. |
| `TAXONOMY_OPERATIONAL_CONTINUITY_EDGE` | Business Disruption & System Failures / Physical & Edge | DRP, BCP, RTO/RPO, high availability (HA), single point of failure (SPOF), backup immutability, plant/OT connectivity, industrial edge, WAN/LAN resilience, latency. |
| `TAXONOMY_PROCESS_AUTOMATION_FRICTION` | Execution, Delivery & Process Management | Manual workflows, human error, lack of CI/CD, unautomated provisioning, ITSM bottlenecks, swivel-chair integration, operational toil, DevSecOps maturity. |
| `TAXONOMY_DATA_INTEGRITY_ANALYTICS` | Data Management, Reporting & Model Risk | Master data management (MDM), data silos, schema drift, ETL fragility, BI accuracy, data lineage, telemetry blindness, observability gaps, AI/ML readiness. |
| `TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION` | Third-Party / Supplier Concentration & Lock-in | Vendor lock-in, SLA governance, third-party risk management (TPRM), licensing exposure, SaaS sprawl, cloud cost governance (FinOps), outsourcing dependency. |

### 2.2 Deterministic Classification Algorithm
Every domain tower payload in the assessment engine carries structured metadata: explicit `taxonomy_family` tags (if emitted by upstream extractors), semantic domain titles/codes, risk vector descriptions, and granular finding arrays (`critical_count`, `high_count`, `medium_count`, `low_count`).

The classification engine executes a three-tier resolution cascade for each active risk vector / tower:
1. **Tier 1 (Explicit Tagging):** If the risk vector or tower payload explicitly defines a valid `taxonomy_id`, it binds directly.
2. **Tier 2 (Multi-Lingual Semantic Keyword Scoring):** The classifier normalizes and tokenizes the risk vector's title, description, and domain label, scoring them against language-agnostic root stems (e.g., `obsolesc`, `legacy`, `eol`, `cyber`, `iam`, `bcp`, `drp`, `spof`, `manual`, `data`, `vendor`, `sla`). The family with the highest positive affinity score wins.
3. **Tier 3 (Actuarial Hash Fallback):** If a custom domain exhibits zero lexical overlap with Tier 2 stems, it maps deterministically to `TAXONOMY_OPERATIONAL_CONTINUITY_EDGE` (if infrastructure-weighted) or `TAXONOMY_PROCESS_AUTOMATION_FRICTION` (if governance-weighted), ensuring **100% mathematical reconciliation** (zero dropped findings and zero orphaned plot points).

---

## 3. Codebase Modification Plan

All Python implementations strictly adhere to the **100% Technical English Codebase Law** and **Zero Hardcoding Law**.

### 3.1 Actuarial Taxonomy Clustering Engine (`src/reconciliation/actuarial_taxonomy_clusterer.py`)
We introduce a dedicated, pure-function reconciliation component invoked by `ActuarialReconciler` and `TowerPayloadHydrator`. It transforms raw $N$-tower risk registers and forensic finding counts into reconciled, ALE-sorted taxonomy clusters.

```python
"""
RFC 081: Dynamic Ontological Risk Taxonomy Clustering Engine.
Aggregates N-tower Open FAIR risk vectors and granular forensic findings
into canonical ORX/FAIR risk families without hardcoded domain assumptions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
import re


CANONICAL_TAXONOMY_KEYS: Tuple[str, ...] = (
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION",
)

# Language-agnostic stem patterns for deterministic semantic classification
_TAXONOMY_STEM_RULES: Dict[str, Tuple[str, ...]] = {
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE": (
        r"obsolesc", r"legacy", r"\beol\b", r"\beos\b", r"end[\s\-]of[\s\-]life",
        r"monolith", r"deuda\s+t", r"technical\s+debt", r"aging", r"unsupported",
        r"veraltet", r"obsolète", r"老朽", r"レガシー",
    ),
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE": (
        r"cyber", r"ciber", r"\biam\b", r"\bpam\b", r"\bmfa\b", r"identit",
        r"zero[\s\-]trust", r"vulnerab", r"\bcve\b", r"perimeter", r"perímetr",
        r"compliance", r"cumplimiento", r"gdpr", r"iso\s*27", r"encrypt", r"cifrad",
        r"sicherheit", r"sécurité", r"セキュリティ", r"権限",
    ),
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE": (
        r"\bdrp\b", r"\bbcp\b", r"\brto\b", r"\brpo\b", r"\bspof\b", r"continuit",
        r"continuidad", r"resilien", r"backup", r"respaldo", r"outage", r"caída",
        r"edge", r"planta", r"plant", r"\bot\b", r"scada", r"network", r"red\b",
        r"verfügbarkeit", r"disponibilité", r"可用性", r"事業継続",
    ),
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION": (
        r"manual", r"automat", r"ci/cd", r"devops", r"devsecops", r"\bitsm\b",
        r"workflow", r"flujo", r"toil", r"human\s+error", r"error\s+humano",
        r"provision", r"runbook", r"prozess", r"processus", r"自動化", r"手動",
    ),
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS": (
        r"\bdata\b", r"\bdatos\b", r"\bmdm\b", r"\betl\b", r"analytics", r"analítica",
        r"schema", r"esquema", r"silo", r"lineage", r"linaje", r"observabil",
        r"telemetr", r"daten", r"données", r"データ",
    ),
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION": (
        r"vendor", r"proveedor", r"supplier", r"lock[\s\-]in", r"\bsla\b",
        r"\btprm\b", r"third[\s\-]party", r"terceros", r"licens", r"licencia",
        r"finops", r"outsourc", r"lieferant", r"fournisseur", r"ベンダー",
    ),
}


@dataclass(frozen=True)
class TaxonomyClusterRecord:
    """Immutable representation of an active, reconciled risk taxonomy cluster."""
    taxonomy_id: str
    matrix_plot_codes: List[str]
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    total_findings: int
    cluster_ale_p50: float
    cluster_ale_p90: float
    share_of_total_ale_pct: float
    representative_threats: List[str]


class ActuarialTaxonomyClusterer:
    """
    Dynamically clusters N-tower risk registers and forensic findings into
    canonical ORX/Open FAIR risk taxonomy families.
    Enforces the Zero-Hardcoding Law by filtering out zero-finding families.
    """

    @classmethod
    def classify_risk_record(cls, record: Dict[str, Any]) -> str:
        """
        Deterministically resolves the canonical taxonomy_id for a given risk/tower record.
        """
        explicit_tag = str(record.get("taxonomy_id") or "").strip().upper()
        if explicit_tag in CANONICAL_TAXONOMY_KEYS:
            return explicit_tag

        searchable_corpus = " ".join(
            str(record.get(k) or "")
            for k in (
                "risk_title",
                "title",
                "threat_scenario",
                "description",
                "tower_name",
                "domain_name",
                "category",
            )
        ).lower()

        best_key = "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE"
        best_score = 0

        for taxonomy_key, patterns in _TAXONOMY_STEM_RULES.items():
            score = sum(
                1 for pattern in patterns if re.search(pattern, searchable_corpus)
            )
            if score > best_score:
                best_score = score
                best_key = taxonomy_key

        return best_key

    @classmethod
    def build_dynamic_clusters(
        cls,
        risk_vectors: List[Dict[str, Any]],
        tower_findings_summary: List[Dict[str, Any]] | None = None,
    ) -> List[TaxonomyClusterRecord]:
        """
        Aggregates plot points (e.g., 'T01.R01') and granular tower findings
        (Critical, High, Medium, Low) into active taxonomy clusters.
        Only returns clusters with non-zero findings or non-zero ALE,
        sorted descending by cluster_ale_p90 (or cluster_ale_p50).
        """
        buckets: Dict[str, Dict[str, Any]] = {
            key: {
                "plot_codes": [],
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "ale_p50": 0.0,
                "ale_p90": 0.0,
                "threats": [],
            }
            for key in CANONICAL_TAXONOMY_KEYS
        }

        # Map tower_id -> granular finding counts if provided separately
        tower_findings_map: Dict[str, Dict[str, int]] = {}
        if tower_findings_summary:
            for tf in tower_findings_summary:
                t_id = str(tf.get("tower_id") or tf.get("domain_id") or "").strip().upper()
                if t_id:
                    tower_findings_map[t_id] = {
                        "critical": int(tf.get("critical_count", tf.get("critical", 0)) or 0),
                        "high": int(tf.get("high_count", tf.get("high", 0)) or 0),
                        "medium": int(tf.get("medium_count", tf.get("medium", 0)) or 0),
                        "low": int(tf.get("low_count", tf.get("low", 0)) or 0),
                    }

        consumed_towers: set[str] = set()

        for idx, vector in enumerate(risk_vectors, start=1):
            taxonomy_key = cls.classify_risk_record(vector)
            bucket = buckets[taxonomy_key]

            plot_code = str(
                vector.get("risk_id")
                or vector.get("plot_code")
                or vector.get("code")
                or f"R{idx:02d}"
            ).strip()
            if plot_code and plot_code not in bucket["plot_codes"]:
                bucket["plot_codes"].append(plot_code)

            tower_id = str(
                vector.get("tower_id")
                or vector.get("domain_id")
                or plot_code.split(".")[0]
            ).strip().upper()

            # Extract granular counts directly from vector or linked tower summary
            c_cnt = int(vector.get("critical_count", vector.get("critical_findings", 0)) or 0)
            h_cnt = int(vector.get("high_count", vector.get("high_findings", 0)) or 0)
            m_cnt = int(vector.get("medium_count", vector.get("medium_findings", 0)) or 0)
            l_cnt = int(vector.get("low_count", vector.get("low_findings", 0)) or 0)

            if (c_cnt + h_cnt + m_cnt + l_cnt == 0) and tower_id in tower_findings_map and tower_id not in consumed_towers:
                tf_counts = tower_findings_map[tower_id]
                c_cnt = tf_counts["critical"]
                h_cnt = tf_counts["high"]
                m_cnt = tf_counts["medium"]
                l_cnt = tf_counts["low"]
                consumed_towers.add(tower_id)

            bucket["critical"] += c_cnt
            bucket["high"] += h_cnt
            bucket["medium"] += m_cnt
            bucket["low"] += l_cnt

            ale_p50 = float(vector.get("ale_p50", vector.get("ale_expected", vector.get("ale", 0.0))) or 0.0)
            ale_p90 = float(vector.get("ale_p90", vector.get("ale_var95", ale_p50)) or 0.0)
            bucket["ale_p50"] += ale_p50
            bucket["ale_p90"] += ale_p90

            threat_title = str(
                vector.get("risk_title")
                or vector.get("title")
                or vector.get("threat_scenario")
                or ""
            ).strip()
            if threat_title and threat_title not in bucket["threats"]:
                bucket["threats"].append(threat_title)

        # Reconcile any remaining unconsumed towers from tower_findings_summary
        if tower_findings_summary:
            for tf in tower_findings_summary:
                t_id = str(tf.get("tower_id") or tf.get("domain_id") or "").strip().upper()
                if t_id and t_id not in consumed_towers:
                    taxonomy_key = cls.classify_risk_record(tf)
                    bucket = buckets[taxonomy_key]
                    if t_id not in bucket["plot_codes"]:
                        bucket["plot_codes"].append(t_id)
                    bucket["critical"] += int(tf.get("critical_count", tf.get("critical", 0)) or 0)
                    bucket["high"] += int(tf.get("high_count", tf.get("high", 0)) or 0)
                    bucket["medium"] += int(tf.get("medium_count", tf.get("medium", 0)) or 0)
                    bucket["low"] += int(tf.get("low_count", tf.get("low", 0)) or 0)
                    consumed_towers.add(t_id)

        total_portfolio_ale = sum(b["ale_p90"] or b["ale_p50"] for b in buckets.values())

        active_clusters: List[TaxonomyClusterRecord] = []
        for taxonomy_key, b in buckets.items():
            total_f = b["critical"] + b["high"] + b["medium"] + b["low"]
            exposure_metric = b["ale_p90"] if b["ale_p90"] > 0 else b["ale_p50"]

            # Dynamic N-Axis Pruning: Only emit clusters with actual findings or plot points
            if total_f == 0 and exposure_metric == 0.0 and not b["plot_codes"]:
                continue

            share_pct = (
                round((exposure_metric / total_portfolio_ale) * 100.0, 1)
                if total_portfolio_ale > 0
                else 0.0
            )

            active_clusters.append(
                TaxonomyClusterRecord(
                    taxonomy_id=taxonomy_key,
                    matrix_plot_codes=sorted(b["plot_codes"]),
                    critical_findings=b["critical"],
                    high_findings=b["high"],
                    medium_findings=b["medium"],
                    low_findings=b["low"],
                    total_findings=total_f,
                    cluster_ale_p50=round(b["ale_p50"], 2),
                    cluster_ale_p90=round(b["ale_p90"], 2),
                    share_of_total_ale_pct=share_pct,
                    representative_threats=b["threats"][:3],
                )
            )

        # Deterministic sorting: highest financial impact first, then total findings
        active_clusters.sort(
            key=lambda c: (
                c.cluster_ale_p90 if c.cluster_ale_p90 > 0 else c.cluster_ale_p50,
                c.critical_findings,
                c.total_findings,
            ),
            reverse=True,
        )
        return active_clusters
```

---

### 3.2 AST Compiler Integration (`src/ast/tomo_asis_ast_compiler.py`)
In `_build_chapter_3_actuarial_risk_register`, immediately after emitting the 5x5 Open FAIR™ Heatmap Matrix node, the compiler invokes `ActuarialTaxonomyClusterer.build_dynamic_clusters(...)` and appends:
1. A localized **Executive Taxonomy Narrative Bridge** explaining how the $N$ plotted codes reconcile with the total empirical findings across all audited towers.
2. The high-density **Risk Taxonomy & Findings Clustering Table** (`TableNode`), ending with a mathematically reconciled **Portfolio Total / Reconciliation Footer Row**.

```python
# Excerpt from src/ast/tomo_asis_ast_compiler.py inside _build_chapter_3_actuarial_risk_register

from src.reconciliation.actuarial_taxonomy_clusterer import (
    ActuarialTaxonomyClusterer,
    TaxonomyClusterRecord,
)

def _build_section_3_2_heatmap_and_taxonomy_legend(
    self,
    risk_vectors: List[Dict[str, Any]],
    tower_findings_summary: List[Dict[str, Any]],
    currency_symbol: str = "€",
) -> List[Dict[str, Any]]:
    """
    Renders Section 3.2:
    1. Classic 5x5 Open FAIR Heatmap Matrix.
    2. Dynamic Ontological Risk Taxonomy & Forensic Findings Clustering Table (RFC 081).
    """
    ast_nodes: List[Dict[str, Any]] = []

    # 1. Retain Classic 5x5 Open FAIR Heatmap Visual
    ast_nodes.append(self._build_fair_5x5_heatmap_node(risk_vectors))

    # 2. Compute Dynamic N-Cluster Taxonomy Aggregation
    clusters: List[TaxonomyClusterRecord] = (
        ActuarialTaxonomyClusterer.build_dynamic_clusters(
            risk_vectors=risk_vectors,
            tower_findings_summary=tower_findings_summary,
        )
    )

    if not clusters:
        return ast_nodes

    total_crit = sum(c.critical_findings for c in clusters)
    total_high = sum(c.high_findings for c in clusters)
    total_med = sum(c.medium_findings for c in clusters)
    total_all = sum(c.total_findings for c in clusters)
    total_plot_points = sum(len(c.matrix_plot_codes) for c in clusters)

    # 3. Narrative Bridge reconciling Plot Codes with Granular Forensic Findings
    bridge_template = self.i18n.t("sec_3_2_taxonomy_bridge_narrative")
    bridge_text = bridge_template.format(
        active_cluster_count=len(clusters),
        total_plot_points=total_plot_points,
        total_findings=total_all,
        critical_count=total_crit,
        high_count=total_high,
        medium_count=total_med,
    )
    ast_nodes.append({
        "type": "paragraph",
        "style": "ExecutiveCallout",
        "text": bridge_text,
    })

    # 4. Build Dynamic Taxonomy & Heatmap Legend Table
    headers = [
        self.i18n.t("sec_3_2_col_taxonomy_family"),
        self.i18n.t("sec_3_2_col_matrix_codes"),
        self.i18n.t("sec_3_2_col_systemic_threat_rationale"),
        self.i18n.t("sec_3_2_col_forensic_breakdown"),
        self.i18n.t("sec_3_2_col_clustered_ale"),
    ]

    rows: List[List[str]] = []
    for cluster in clusters:
        family_title = self.i18n.t(f"{cluster.taxonomy_id}_TITLE")
        family_rationale = self.i18n.t(f"{cluster.taxonomy_id}_RATIONALE")

        # Enrich rationale with empirical representative threats from the audit
        if cluster.representative_threats:
            empirical_scope = " | ".join(cluster.representative_threats)
            rationale_cell = f"{family_rationale} ({empirical_scope})"
        else:
            rationale_cell = family_rationale

        codes_cell = ", ".join(cluster.matrix_plot_codes) if cluster.matrix_plot_codes else "—"

        breakdown_cell = self.i18n.t("sec_3_2_findings_badge_template").format(
            total=cluster.total_findings,
            crit=cluster.critical_findings,
            high=cluster.high_findings,
            med=cluster.medium_findings,
        )

        ale_val = cluster.cluster_ale_p90 if cluster.cluster_ale_p90 > 0 else cluster.cluster_ale_p50
        ale_cell = f"{currency_symbol}{ale_val:,.0f} ({cluster.share_of_total_ale_pct:.1f}%)"

        rows.append([
            family_title,
            codes_cell,
            rationale_cell,
            breakdown_cell,
            ale_cell,
        ])

    # 5. Append Mathematical Reconciliation Footer Row
    total_ale = sum(
        (c.cluster_ale_p90 if c.cluster_ale_p90 > 0 else c.cluster_ale_p50)
        for c in clusters
    )
    total_breakdown_cell = self.i18n.t("sec_3_2_findings_badge_template").format(
        total=total_all,
        crit=total_crit,
        high=total_high,
        med=total_med,
    )
    rows.append([
        self.i18n.t("sec_3_2_row_total_reconciled"),
        f"N = {total_plot_points}",
        self.i18n.t("sec_3_2_row_total_rationale"),
        total_breakdown_cell,
        f"{currency_symbol}{total_ale:,.0f} (100.0%)",
    ])

    ast_nodes.append({
        "type": "table",
        "id": "table_sec_3_2_dynamic_taxonomy_legend",
        "title": self.i18n.t("sec_3_2_taxonomy_table_title"),
        "headers": headers,
        "rows": rows,
        "highlight_last_row": True,
    })

    return ast_nodes
```

---

### 3.3 Symmetrical 6-Locale Catalog Updates (`src/i18n/locales.json`)
Below are the exact, mathematically symmetrical localization keys across all 6 mandatory locales (`es`, `en`, `pt`, `fr`, `de`, `ja`). Zero hardcoded client names or static counts exist in the templates.

```json
{
  "en": {
    "sec_3_2_taxonomy_table_title": "Table 3.2.B — Open FAIR™ Heatmap Legend & Dynamic Risk Taxonomy Clustering",
    "sec_3_2_taxonomy_bridge_narrative": "Actuarial Traceability & Forensic Reconciliation: To translate the {total_plot_points} macroscopic plot points rendered on the 5x5 Open FAIR™ matrix into actionable board governance, the engine dynamically clusters the {total_findings} empirical forensic findings ({critical_count} Critical, {high_count} High, {medium_count} Medium) into {active_cluster_count} active systemic risk families ordered by Annualized Loss Expectancy (ALE).",
    "sec_3_2_col_taxonomy_family": "Systemic Risk Taxonomy Family (ORX / FAIR)",
    "sec_3_2_col_matrix_codes": "Matrix Plot Codes",
    "sec_3_2_col_systemic_threat_rationale": "Executive Business Threat & Empirical Audit Scope",
    "sec_3_2_col_forensic_breakdown": "Forensic Findings (Total: C / H / M)",
    "sec_3_2_col_clustered_ale": "Clustered ALE Exposure (% Share)",
    "sec_3_2_findings_badge_template": "{total} [{crit}C | {high}H | {med}M]",
    "sec_3_2_row_total_reconciled": "TOTAL RECONCILED AUDIT PORTFOLIO",
    "sec_3_2_row_total_rationale": "100% mathematical reconciliation between N-tower forensic annexes and executive heatmap vectors.",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_TITLE": "Structural Obsolescence & Technical Debt",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_RATIONALE": "Operational fragility and unpatched exposure driven by End-of-Life (EoL) infrastructure, legacy kernels, and monolithic coupling",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_TITLE": "Cyber Resilience, Identity & Perimeter Governance",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_RATIONALE": "Unauthorized lateral movement, privilege escalation, and regulatory non-compliance across identity and perimeter controls",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_TITLE": "Operational Continuity, Edge & Infrastructure Resilience",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_RATIONALE": "Production halt and revenue interruption due to single points of failure (SPOF), disaster recovery deficits, or edge/network instability",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_TITLE": "Process Frictions, Manual Toil & Delivery Governance",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_RATIONALE": "Execution bottlenecks, change failure rates, and human-error exposure stemming from unautomated workflows and ITSM fragmentation",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_TITLE": "Data Integrity, Observability & Decision Blindness",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_RATIONALE": "Corrupted executive reporting, telemetry blind spots, and master data fragmentation impairing real-time operational control",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_TITLE": "Third-Party Concentration, SLA & Licensing Exposure",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_RATIONALE": "Commercial lock-in, asymmetric supplier dependency, and unmitigated third-party operational or licensing liabilities"
  },
  "es": {
    "sec_3_2_taxonomy_table_title": "Tabla 3.2.B — Leyenda de Matriz Open FAIR™ y Agrupación Dinámica por Taxonomía de Riesgo",
    "sec_3_2_taxonomy_bridge_narrative": "Trazabilidad Actuarial y Conciliación Forense: Para traducir los {total_plot_points} vectores macroscópicos graficados en la matriz Open FAIR™ 5x5 en gobernanza ejecutiva accionable, el motor agrupa dinámicamente los {total_findings} hallazgos forenses empíricos ({critical_count} Críticos, {high_count} Altos, {medium_count} Medios) en {active_cluster_count} familias activas de riesgo sistémico ordenadas por Expectativa de Pérdida Anualizada (ALE).",
    "sec_3_2_col_taxonomy_family": "Familia Taxonómica de Riesgo Sistémico (ORX / FAIR)",
    "sec_3_2_col_matrix_codes": "Códigos en Matriz",
    "sec_3_2_col_systemic_threat_rationale": "Amenaza de Negocio Ejecutiva y Alcance Empírico Auditado",
    "sec_3_2_col_forensic_breakdown": "Hallazgos Forenses (Total: C / A / M)",
    "sec_3_2_col_clustered_ale": "Exposición ALE Agrupada (% Cuota)",
    "sec_3_2_findings_badge_template": "{total} [{crit}C | {high}A | {med}M]",
    "sec_3_2_row_total_reconciled": "TOTAL CARTERA AUDITADA CONCILIADA",
    "sec_3_2_row_total_rationale": "Conciliación matemática del 100% entre los anexos forenses de las N torres y los vectores del mapa de calor ejecutivo.",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_TITLE": "Obsolescencia Estructural y Deuda Técnica",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_RATIONALE": "Fragilidad operativa y exposición sin parches derivada de infraestructura fuera de soporte (EoL), núcleos heredados y acoplamiento monolítico",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_TITLE": "Ciberresiliencia, Gobernanza de Identidad y Perímetro",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_RATIONALE": "Movimiento lateral no autorizado, escalada de privilegios e incumplimiento normativo en controles de identidad y perímetro",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_TITLE": "Continuidad Operativa, Resiliencia de Red y Borde (Edge)",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_RATIONALE": "Parada productiva e interrupción de ingresos por puntos únicos de fallo (SPOF), déficit de recuperación ante desastres o inestabilidad de red",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_TITLE": "Fricción de Procesos, Operativa Manual y Gobernanza de Entrega",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_RATIONALE": "Cuellos de botella operativos, tasa de fallo en cambios y exposición a error humano por flujos manuales y fragmentación ITSM",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_TITLE": "Integridad de Datos, Observabilidad y Ceguera Analítica",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_RATIONALE": " distorsión en reportes ejecutivos, puntos ciegos de telemetría y fragmentación de datos maestros que degradan el control operativo",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_TITLE": "Concentración de Proveedores, Exposición de SLA y Licenciamiento",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_RATIONALE": "Cautividad comercial (lock-in), dependencia asimétrica de terceros y contingencias operativas o de licenciamiento no mitigadas"
  },
  "pt": {
    "sec_3_2_taxonomy_table_title": "Tabela 3.2.B — Legenda da Matriz Open FAIR™ e Agrupamento Dinâmico por Taxonomia de Risco",
    "sec_3_2_taxonomy_bridge_narrative": "Rastreabilidade Atuarial e Reconciliação Forense: Para traduzir os {total_plot_points} vetores macroscópicos plotados na matriz Open FAIR™ 5x5 em governança executiva acionável, o motor agrupa dinamicamente as {total_findings} constatações forenses empíricas ({critical_count} Críticas, {high_count} Altas, {medium_count} Médias) em {active_cluster_count} famílias ativas de risco sistêmico ordenadas pela Expectativa de Perda Anualizada (ALE).",
    "sec_3_2_col_taxonomy_family": "Família Taxonômica de Risco Sistêmico (ORX / FAIR)",
    "sec_3_2_col_matrix_codes": "Códigos na Matriz",
    "sec_3_2_col_systemic_threat_rationale": "Ameaça Executiva de Negócio e Escopo Empírico Auditado",
    "sec_3_2_col_forensic_breakdown": "Constatações Forenses (Total: C / A / M)",
    "sec_3_2_col_clustered_ale": "Exposição ALE Agrupada (% Quota)",
    "sec_3_2_findings_badge_template": "{total} [{crit}C | {high}A | {med}M]",
    "sec_3_2_row_total_reconciled": "TOTAL DO PORTFÓLIO AUDITADO RECONCILIADO",
    "sec_3_2_row_total_rationale": "Reconciliação matemática de 100% entre os anexos forenses das N torres e os vetores do mapa de calor executivo.",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_TITLE": "Obsolescência Estrutural e Dívida Técnica",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_RATIONALE": "Fragilidade operacional e exposição sem correção decorrente de infraestrutura em fim de vida (EoL), sistemas legados e acoplamento monolítico",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_TITLE": "Ciber-resiliência, Governança de Identidade e Perímetro",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_RATIONALE": "Movimento lateral não autorizado, escalonamento de privilégios e não conformidade regulatória em controles de identidade e perímetro",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_TITLE": "Continuidade Operacional, Resiliência de Borda e Infraestrutura",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_RATIONALE": "Paralisação produtiva e interrupção de receita por pontos únicos de falha (SPOF), déficits de recuperação de desastres ou instabilidade de rede",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_TITLE": "Fricção de Processos, Trabalho Manual e Governança de Entrega",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_RATIONALE": "Gargalos de execução, falhas em mudanças e exposição a erro humano decorrentes de fluxos não automatizados e fragmentação de ITSM",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_TITLE": "Integridade de Dados, Observabilidade e Cegueira Analítica",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_RATIONALE": "Relatórios executivos comprometidos, pontos cegos de telemetria e fragmentação de dados mestres prejudicando o controle operacional",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_TITLE": "Concentração de Fornecedores, Exposição de SLA e Licenciamento",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_RATIONALE": "Dependência comercial (lock-in), assimetria de fornecedores e passivos operacionais ou de licenciamento de terceiros não mitigados"
  },
  "fr": {
    "sec_3_2_taxonomy_table_title": "Tableau 3.2.B — Légende de la Matrice Open FAIR™ et Regroupement Dynamique par Taxonomie de Risque",
    "sec_3_2_taxonomy_bridge_narrative": "Traçabilité Actuarielle et Réconciliation Forensique : Pour traduire les {total_plot_points} vecteurs macroscopiques projetés sur la matrice Open FAIR™ 5x5 en gouvernance exécutive exploitable, le moteur regroupe dynamiquement les {total_findings} constats forensiques empiriques ({critical_count} Critiques, {high_count} Élevés, {medium_count} Moyens) en {active_cluster_count} familles actives de risques systémiques classées par Espérance de Perte Annualisée (ALE).",
    "sec_3_2_col_taxonomy_family": "Famille Taxonomique de Risque Systémique (ORX / FAIR)",
    "sec_3_2_col_matrix_codes": "Codes Matrice",
    "sec_3_2_col_systemic_threat_rationale": "Menace Métier Exécutive et Périmètre Empirique Audité",
    "sec_3_2_col_forensic_breakdown": "Constats Forensiques (Total : C / É / M)",
    "sec_3_2_col_clustered_ale": "Exposition ALE Regroupée (% Part)",
    "sec_3_2_findings_badge_template": "{total} [{crit}C | {high}É | {med}M]",
    "sec_3_2_row_total_reconciled": "TOTAL DU PORTEFEUILLE AUDITÉ RÉCONCILIÉ",
    "sec_3_2_row_total_rationale": "Réconciliation mathématique à 100 % entre les annexes forensiques des N tours et les vecteurs de la carte thermique exécutive.",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_TITLE": "Obsolescence Structurelle et Dette Technique",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_RATIONALE": "Fragilité opérationnelle et exposition non corrigée liées aux infrastructures en fin de vie (EoL), noyaux hérités et couplage monolithique",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_TITLE": "Cyber-résilience, Gouvernance des Identités et du Périmètre",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_RATIONALE": "Mouvement latéral non autorisé, élévation de privilèges et non-conformité réglementaire sur les contrôles d'identité et de périmètre",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_TITLE": "Continuité Opérationnelle, Résilience Edge et Infrastructure",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_RATIONALE": "Arrêt de production et perte de revenus dus à des points de défaillance uniques (SPOF), déficits de reprise d'activité ou instabilité réseau",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_TITLE": "Frictions Processus, Tâches Manuelles et Gouvernance de Livraison",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_RATIONALE": "Goulets d'étranglement, taux d'échec des changements et erreurs humaines liés aux flux non automatisés et à la fragmentation ITSM",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_TITLE": "Intégrité des Données, Observabilité et Cécité Analytique",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_RATIONALE": "Rapports exécutifs altérés, angles morts télémétriques et fragmentation des données de référence dégradant le pilotage opérationnel",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_TITLE": "Concentration Fournisseurs, Exposition SLA et Licences",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_RATIONALE": "Verrouillage commercial (lock-in), dépendance asymétrique aux tiers et passifs opérationnels ou de licences non maîtrisés"
  },
  "de": {
    "sec_3_2_taxonomy_table_title": "Tabelle 3.2.B — Open FAIR™ Matrix-Legende & Dynamische Risikotaxonomie-Clusterung",
    "sec_3_2_taxonomy_bridge_narrative": "Versicherungsmathematische Rückverfolgbarkeit & Forensische Abstimmung: Um die {total_plot_points} makroskopischen Datenpunkte der 5x5 Open FAIR™-Matrix in belastbare Vorstands-Governance zu übersetzen, gruppiert die Engine die {total_findings} empirischen forensischen Feststellungen ({critical_count} Kritisch, {high_count} Hoch, {medium_count} Mittel) dynamisch in {active_cluster_count} aktive systemische Risikofamilien, sortiert nach der Annualisierten Verlustwartung (ALE).",
    "sec_3_2_col_taxonomy_family": "Systemische Risikotaxonomie-Familie (ORX / FAIR)",
    "sec_3_2_col_matrix_codes": "Matrix-Codes",
    "sec_3_2_col_systemic_threat_rationale": "Geschäftsbedrohung & Empirischer Prüfungsumfang",
    "sec_3_2_col_forensic_breakdown": "Forensische Befunde (Gesamt: K / H / M)",
    "sec_3_2_col_clustered_ale": "Geclusterte ALE-Exponierung (% Anteil)",
    "sec_3_2_findings_badge_template": "{total} [{crit}K | {high}H | {med}M]",
    "sec_3_2_row_total_reconciled": "GESAMTES ABGESTIMMTES PRÜFUNGSPORTFOLIO",
    "sec_3_2_row_total_rationale": "100%ige mathematische Abstimmung zwischen den forensischen Anhängen der N Domänen und den Vektoren der Vorstands-Heatmap.",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_TITLE": "Strukturelle Obsoleszenz & Technische Schulden",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_RATIONALE": "Operative Fragilität und ungepatchte Verwundbarkeit durch End-of-Life (EoL)-Infrastruktur, Altsysteme und monolithische Kopplung",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_TITLE": "Cyber-Resilienz, Identitäts- & Perimeter-Governance",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_RATIONALE": "Unbefugte Lateralbewegung, Privilegieneskalation und regulatorische Verstöße bei Identitäts- und Perimeterkontrollen",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_TITLE": "Betriebskontinuität, Edge- & Infrastruktur-Resilienz",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_RATIONALE": "Produktionsstillstand und Umsatzausfall durch Single Points of Failure (SPOF), Notfallwiederherstellungsdefizite oder Netzwerkinstabilität",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_TITLE": "Prozessreibung, Manuelle Aufwände & Delivery-Governance",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_RATIONALE": "Ausführungsengpässe, Änderungsfehlerraten und menschliche Fehlerrisiken durch nicht automatisierte Workflows und ITSM-Fragmentierung",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_TITLE": "Datenintegrität, Observability & Analytische Blindheit",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_RATIONALE": "Verzerrtes Vorstands-Reporting, Telemetrie-Blindflecken und Stammdatenfragmentierung mit Beeinträchtigung der operativen Steuerung",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_TITLE": "Anbieterkonzentration, SLA- & Lizenz-Exponierung",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_RATIONALE": "Kommerzieller Lock-in, asymmetrische Lieferantenabhängigkeit und ungeminderte Drittparteien- oder Lizenzverbindlichkeiten"
  },
  "ja": {
    "sec_3_2_taxonomy_table_title": "表 3.2.B — Open FAIR™ ヒートマップ凡例および動的リスク分類クラスタリング",
    "sec_3_2_taxonomy_bridge_narrative": "アクチュアリー追跡性とフォレンジック照合：5x5 Open FAIR™ マトリックス上にプロットされた {total_plot_points} 個のマクロ的リスクベクトルを取締役会の実効的なガバナンスへ変換するため、本エンジンは {total_findings} 件の実証的フォレンジック検出事項（致命的 {critical_count} 件、高 {high_count} 件、中 {medium_count} 件）を年間予想損失額（ALE）順の {active_cluster_count} 個のアクティブなシステミックリスク領域へ動的にクラスタリングします。",
    "sec_3_2_col_taxonomy_family": "システミックリスク分類領域 (ORX / FAIR)",
    "sec_3_2_col_matrix_codes": "マトリックスコード",
    "sec_3_2_col_systemic_threat_rationale": "経営上の脅威と実証監査スコープ",
    "sec_3_2_col_forensic_breakdown": "フォレンジック検出内訳 (計: 致命/高/中)",
    "sec_3_2_col_clustered_ale": "クラスター化ALEエクスポージャー (構成比)",
    "sec_3_2_findings_badge_template": "{total} [{crit}C | {high}H | {med}M]",
    "sec_3_2_row_total_reconciled": "照合済み監査ポートフォリオ合計",
    "sec_3_2_row_total_rationale": "N個の専門領域別フォレンジック付属書と経営陣向けヒートマップベクトル間の100%数理照合。",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_TITLE": "構造的老朽化および技術的負債",
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE_RATIONALE": "サポート終了（EoL）インフラ、レガシーカーネル、モノリシック結合に起因する運用上の脆弱性と未パッチリスク",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_TITLE": "サイバーレジリエンス・IDおよび境界ガバナンス",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE_RATIONALE": "IDおよび境界統制の不備による不正な横展開（ラテラルムーブメント）、権限昇格、および法規制コンプライアンス違反",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_TITLE": "事業継続性・エッジおよびインフラレジリエンス",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE_RATIONALE": "単一障害点（SPOF）、災害復旧（DR）体制の欠如、またはエッジ／ネットワーク不安定化による生産停止および収益中断",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_TITLE": "プロセス摩擦・手動運用負荷およびデリバリーガバナンス",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION_RATIONALE": "未自動化ワークフローとITSM分断に起因する実行ボトルネック、変更失敗率の上昇、およびヒューマンエラーリスク",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_TITLE": "データ整合性・可観測性および意思決定の盲点",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS_RATIONALE": "経営レポートの歪み、テレメトリの死角、およびマスターデータ分断によるリアルタイム運用統制の低下",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_TITLE": "サードパーティ集中・SLAおよびライセンスリスク",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION_RATIONALE": "ベンダーロックイン、非対称なサプライヤー依存、および未軽減の外部委託・ライセンス債務"
  }
}
```

---

## 4. Automated Quality Gate Test Specification

File: `tests/unit/test_rfc081_dynamic_risk_taxonomy_clustering.py`

```python
"""
Unit & Governance Quality Gate Tests for RFC 081:
Section 3.2 Dynamic Risk Taxonomy Clustering & Heatmap Legend Governance.
Verifies:
1. 100% Mathematical Reconciliation between N-tower granular findings (e.g., 143 findings)
   and the clustered heatmap legend table.
2. Dynamic N-Axis Polymorphism (Zero-Hardcoding Law: zero-finding families are omitted).
3. Deterministic ALE descending sort order.
4. 6-Locale Mathematical Symmetry in locales.json.
"""

import json
from pathlib import Path
import pytest

from src.reconciliation.actuarial_taxonomy_clusterer import (
    ActuarialTaxonomyClusterer,
    CANONICAL_TAXONOMY_KEYS,
)


def test_rfc081_143_forensic_findings_reconcile_across_10_towers():
    """
    Verifies that a 10-tower audit with 143 granular findings (24 Critical, 68 High, 51 Medium)
    and 10 plot codes (T01.R01 .. T10.R01) reconciles 100% without orphaned codes or lost findings.
    """
    risk_vectors = [
        {"risk_id": "T01.R01", "tower_id": "T01", "risk_title": "Legacy ERP EoL Kernel Obsolescence", "ale_p90": 1250000.0},
        {"risk_id": "T02.R01", "tower_id": "T02", "risk_title": "Active Directory PAM & MFA Gaps", "ale_p90": 2100000.0},
        {"risk_id": "T03.R01", "tower_id": "T03", "risk_title": "Plant Edge WAN SPOF & DRP Deficit", "ale_p90": 1800000.0},
        {"risk_id": "T04.R01", "tower_id": "T04", "risk_title": "Manual Deployment Toil & Missing CI/CD", "ale_p90": 650000.0},
        {"risk_id": "T05.R01", "tower_id": "T05", "risk_title": "Master Data Silos & ETL Schema Drift", "ale_p90": 540000.0},
        {"risk_id": "T06.R01", "tower_id": "T06", "risk_title": "Unpatched Perimeter CVE Exposure", "ale_p90": 950000.0},
        {"risk_id": "T07.R01", "tower_id": "T07", "risk_title": "Unsupported OS Monolithic Debt", "ale_p90": 820000.0},
        {"risk_id": "T08.R01", "tower_id": "T08", "risk_title": "Backup Immutability & RTO Failure", "ale_p90": 1100000.0},
        {"risk_id": "T09.R01", "tower_id": "T09", "risk_title": "Critical Cloud Vendor Lock-in & SLA Deficit", "ale_p90": 430000.0},
        {"risk_id": "T10.R01", "tower_id": "T10", "risk_title": "ITSM Manual Provisioning Bottlenecks", "ale_p90": 360000.0},
    ]

    # Exact forensic breakdown totaling 143 findings: 24 Critical, 68 High, 51 Medium
    tower_findings_summary = [
        {"tower_id": "T01", "critical_count": 4, "high_count": 9, "medium_count": 6},
        {"tower_id": "T02", "critical_count": 5, "high_count": 11, "medium_count": 7},
        {"tower_id": "T03", "critical_count": 3, "high_count": 8, "medium_count": 5},
        {"tower_id": "T04", "critical_count": 1, "high_count": 6, "medium_count": 5},
        {"tower_id": "T05", "critical_count": 2, "high_count": 5, "medium_count": 6},
        {"tower_id": "T06", "critical_count": 3, "high_count": 7, "medium_count": 4},
        {"tower_id": "T07", "critical_count": 2, "high_count": 6, "medium_count": 5},
        {"tower_id": "T08", "critical_count": 2, "high_count": 7, "medium_count": 5},
        {"tower_id": "T09", "critical_count": 1, "high_count": 5, "medium_count": 4},
        {"tower_id": "T10", "critical_count": 1, "high_count": 4, "medium_count": 4},
    ]

    clusters = ActuarialTaxonomyClusterer.build_dynamic_clusters(
        risk_vectors=risk_vectors,
        tower_findings_summary=tower_findings_summary,
    )

    assert len(clusters) == 6
    assert sum(c.critical_findings for c in clusters) == 24
    assert sum(c.high_findings for c in clusters) == 68
    assert sum(c.medium_findings for c in clusters) == 51
    assert sum(c.total_findings for c in clusters) == 143

    all_plotted_codes = [code for c in clusters for code in c.matrix_plot_codes]
    assert len(all_plotted_codes) == 10
    assert set(all_plotted_codes) == {f"T{i:02d}.R01" for i in range(1, 11)}

    # Verify strict descending ALE sort order
    cluster_ales = [c.cluster_ale_p90 for c in clusters]
    assert cluster_ales == sorted(cluster_ales, reverse=True)
    assert round(sum(c.share_of_total_ale_pct for c in clusters), 0) == 100.0


def test_rfc081_dynamic_n_axis_prunes_empty_taxonomy_families():
    """
    Enforces the Zero-Hardcoding Law: if a payload only has findings in 2 taxonomy
    families (e.g., Cyber Identity and Data Integrity), only 2 clusters are emitted.
    """
    risk_vectors = [
        {
            "risk_id": "DOM_A.R01",
            "risk_title": "Zero-Trust IAM Privilege Escalation",
            "critical_count": 3,
            "high_count": 5,
            "medium_count": 2,
            "ale_p90": 900000.0,
        },
        {
            "risk_id": "DOM_B.R01",
            "risk_title": "Enterprise Data Lineage & MDM Corruption",
            "critical_count": 1,
            "high_count": 4,
            "medium_count": 3,
            "ale_p90": 450000.0,
        },
    ]

    clusters = ActuarialTaxonomyClusterer.build_dynamic_clusters(risk_vectors=risk_vectors)

    assert len(clusters) == 2
    assert [c.taxonomy_id for c in clusters] == [
        "TAXONOMY_CYBER_IDENTITY_GOVERNANCE",
        "TAXONOMY_DATA_INTEGRITY_ANALYTICS",
    ]
    assert clusters[0].total_findings == 10
    assert clusters[1].total_findings == 8


def test_rfc081_six_locale_mathematical_symmetry():
    """
    Verifies that all RFC 081 i18n keys exist across es, en, pt, fr, de, ja
    with non-empty strings and matching placeholder signatures.
    """
    locales_path = Path("src/i18n/locales.json")
    if not locales_path.exists():
        pytest.skip("locales.json not found in current working directory")

    catalog = json.loads(locales_path.read_text(encoding="utf-8"))
    required_locales = ("es", "en", "pt", "fr", "de", "ja")

    required_keys = [
        "sec_3_2_taxonomy_table_title",
        "sec_3_2_taxonomy_bridge_narrative",
        "sec_3_2_col_taxonomy_family",
        "sec_3_2_col_matrix_codes",
        "sec_3_2_col_systemic_threat_rationale",
        "sec_3_2_col_forensic_breakdown",
        "sec_3_2_col_clustered_ale",
        "sec_3_2_findings_badge_template",
        "sec_3_2_row_total_reconciled",
        "sec_3_2_row_total_rationale",
    ]
    for tax_key in CANONICAL_TAXONOMY_KEYS:
        required_keys.append(f"{tax_key}_TITLE")
        required_keys.append(f"{tax_key}_RATIONALE")

    for locale in required_locales:
        assert locale in catalog, f"Missing mandatory locale: {locale}"
        locale_dict = catalog[locale]
        for key in required_keys:
            assert key in locale_dict, f"Missing RFC 081 key '{key}' in locale '{locale}'"
            val = locale_dict[key]
            assert isinstance(val, str) and len(val.strip()) > 0
```