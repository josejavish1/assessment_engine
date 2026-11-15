```markdown
# ARGON-4 ARCHITECTURE BLUEPRINT: PHASE 10 (ITERATION 7)
**Document Reference:** `docs/architecture/ARGON_PHASE10_ITERATION7_MASTER_PLAN.md`  
**Author:** Gemini-4-Argon (Chief Systems Architect, Actuarial Fellow & Global Managing Partner)  
**Target Release:** Engine v10.7.0-Enterprise  
**Audit Baseline:** `Revision_Profunda_Torre_2_Iteracion_7.txt` (Current Score: 8.0/10 $\rightarrow$ Target: 9.5+/10 Tier-1 World-Class)  
**Classification:** STRICTLY CONFIDENTIAL – INTERNAL ENGINEERING & ACTUARIAL ARCHITECTURE

---

## 1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO

### 1.1 The Epistemic Leap from 8.0 to 9.5+
Iteration 6 successfully stabilized the actuarial and typographic foundations of the Argon Engine. Our forensic auditor formally validated that our deterministic mathematical engine operates at Tier-1 perfection: pillar weights sum precisely to $100\%$, the global weighted score locks at $1.85 / 5.00$, the Factor Analysis of Information Risk (FAIR) Monte Carlo distributions align seamlessly with the executive summary ($13,750\text{ EUR} - 27,000\text{ EUR}$ VaR exposure), dynamic heatmaps reflect calibrated realities, and the WeasyPrint rendering pipeline produces a clean, orphaned-header-free 15-page executive dossier.

However, achieving a certified **9.5+/10 World-Class M&A Due Diligence standard** requires transcending mere mathematical consistency. At the Managing Partner level, a due diligence dossier is a legally defensible epistemic instrument. When presenting to Private Equity Investment Committees or C-Suite boards of $100B+ conglomerates, **semantic precision, regulatory non-repudiation, and empirical parsimony** are paramount. 

An 8.0/10 system computes the right numbers; a 9.5+/10 system ensures that every single word surrounding those numbers is forensically unimpeachable, devoid of generative inflation, balanced in its recognition of operational resilience, and strictly aligned with the latest global governance frameworks (e.g., CMMI® V3.0).

### 1.2 Core Architectural Invariants
To bridge the remaining 1.5-point gap without introducing regressions across our 47 existing architecture and actuarial unit tests, all engineering modifications must adhere to three immutable invariants:

1. **100% Technical English Codebase:** Every variable, class name, Pydantic model, docstring, log entry, and LLM system prompt instruction must be written in rigorous Technical English. Target output localization (e.g., `es_ES`, `en_US`) is handled exclusively via the `LocalizationManager` and dynamic locale injection at runtime.
2. **Zero Hardcoding & Universal Enterprise Scaling:** No client-specific strings, tower-specific patches, or ad-hoc regex replacements are permitted in the core pipeline. All prompt directives and AST (Abstract Syntax Tree) transformations must be universally parameterized, scaling seamlessly from a $50M mid-market single-site firm to a $100B multi-cloud global conglomerate.
3. **Strict Epistemic Grounding (Anti-Hallucination):** The LLM is an analytical synthesizer, not a creative writer. Generative prompts must enforce **Parsimonious Factual Precision**—forbidding the extrapolation of single-node edge workloads into enterprise clusters, outlawing the invention of unverified network protocols, and mandating KPI-level audit trails whenever human self-assessments are algorithmically overridden.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

```
+-----------------------------------------------------------------------------------+
|                        ARGON ENGINE v10.7.0 PIPELINE                              |
+-----------------------------------------------------------------------------------+
                                         |
 [Phase 1: Locale Catalog]               v
 (CMMI V3.0, FinOps Orthography,  ---> +--------------------------------------------+
  Automation Domain Alignment)         | LocalizationManager & Config Loader        |
                                       +--------------------------------------------+
                                         |
 [Phase 2: Epistemic & Legal]            v
 (AssessmentScopeMetadata,        ---> +--------------------------------------------+
  NIS2/DORA Operational Shielding)     | AST Methodology & Executive Summary Builder|
                                       +--------------------------------------------+
                                         |
 [Phase 3 & 4: Prompt Engine]            v
 (Parsimonious Grounding,         ---> +--------------------------------------------+
  Scale Invariance, Positive Evidence) | LLM Intelligence Synthesizer (Zero-Inflate)|
                                       +--------------------------------------------+
                                         |
 [Phase 5: Micro-Calibration]            v
 (KPI-by-KPI Rebuttal Matrix,     ---> +--------------------------------------------+
  Raw vs. Calibrated Delta Vector)     | Actuarial Calibration & AST Table Renderer |
                                       +--------------------------------------------+
```

---

### PHASE 1: Locale Baseline Rectification (Descriptions, CMMI V3.0, Orthography)

#### 1.1 Forensic Root Cause Analysis
The audit identified three lexicographical defects in `engine_config/locales.json` that undermine the authority of the document:
1. **Cross-Domain Contamination:** The `automation_orchestration` pillar description in `es_ES` inherited a copy-paste artifact from Tower 4 (Cybersecurity), referencing *"medidas de protección y respuesta"* instead of Infrastructure-as-Code (IaC), CI/CD pipelines, and configuration management.
2. **Framework Obsolescence:** The methodology narrative cites *"CMMI v2.0"*. ISACA officially sunset V2.0 in favor of **CMMI® V3.0**, which introduces specific domain practice areas critical to modern infrastructure governance.
3. **Orthographic Defect:** Under the Cloud & FinOps taxonomy section, the string *"taxonomóa FinOps"* contains an acute accent on the wrong vowel (should be *"taxonomía FinOps"*).

#### 1.2 Architectural Solution & JSON Schema Patch
We will execute a surgical update to `engine_config/locales.json` and enforce a schema validation gate in `src/config/localization_manager.py`.

**Target File:** `engine_config/locales.json`

```json
{
  "es_ES": {
    "methodology": {
      "framework_reference": "El modelo de madurez se fundamenta en los principios de CMMI® V3.0 (adaptación a Infraestructura y Operaciones), integrando marcos de referencia como ITIL® 4, ISO/IEC 20000-1 y la taxonomía FinOps Foundation.",
      "validation_state_label": "Estado de Validación Epistémica",
      "validation_state_exploratory": "Exploratorio (Fast Assessment - Basado en muestreo documental y entrevistas técnicas sin auditoría forense en vivo de consolas)"
    },
    "pillars": {
      "automation_orchestration": {
        "title": "Automatización, Orquestación e IaC",
        "description": "Evalúa el grado de estandarización programática del ciclo de vida de la infraestructura, abarcando el aprovisionamiento mediante Infraestructura como Código (IaC), la gestión declarativa de configuraciones, la integración de pipelines CI/CD operativos y la eliminación de tareas manuales repetitivas (Toil)."
      },
      "cloud_finops": {
        "title": "Adopción Cloud y Gobierno FinOps",
        "description": "Analiza la arquitectura de cargas de trabajo en nube pública/híbrida y la madurez financiera operativa bajo la taxonomía FinOps (visibilidad de costes, etiquetado estricto, optimización de recursos y responsabilidad presupuestaria distribuida)."
      }
    }
  },
  "en_US": {
    "methodology": {
      "framework_reference": "The maturity model is grounded in CMMI® V3.0 principles (adapted for Infrastructure and Operations), integrating reference frameworks such as ITIL® 4, ISO/IEC 20000-1, and the FinOps Foundation taxonomy.",
      "validation_state_label": "Epistemic Validation State",
      "validation_state_exploratory": "Exploratory (Fast Assessment - Based on documentary sampling and technical interviews without live forensic console auditing)"
    },
    "pillars": {
      "automation_orchestration": {
        "title": "Automation, Orchestration & IaC",
        "description": "Evaluates the programmatic standardization of the infrastructure lifecycle, encompassing Infrastructure as Code (IaC) provisioning, declarative configuration management, operational CI/CD pipeline integration, and the systematic elimination of manual operational toil."
      },
      "cloud_finops": {
        "title": "Cloud Adoption & FinOps Governance",
        "description": "Analyzes public/hybrid cloud workload architecture and operational financial maturity under the FinOps taxonomy (cost visibility, strict tagging governance, resource right-sizing, and distributed budgetary accountability)."
      }
    }
  }
}
```

---

### PHASE 2: Epistemic Validation State & Regulatory Shielding

#### 2.1 Forensic Root Cause Analysis
Two structural contradictions exposed the consultancy to legal and methodological friction:
1. **Missing Epistemic State:** The document does not explicitly declare the depth of its evidentiary verification. In M&A due diligence, an auditor must distinguish between a *Forensic Deep-Dive* (direct read-only API access to AWS/vCenter/Kubernetes clusters) and an *Exploratory Fast Assessment* (relying on client-provided architecture diagrams, questionnaire responses, and discovery interviews).
2. **Regulatory Contradiction (The NIS2 Trap):** In the Executive Summary KPI cards and Risk Tables, the engine outputs categorical legal conclusions such as `"Incumplimiento Alto (Directiva NIS2)"` (High Breach - NIS2 Directive). This directly violates our own Legal Disclaimer on Page 2, which states that regulatory mentions are purely technical/illustrative and not formal legal opinions (which belong exclusively to Tower 6 - Legal & Compliance).

#### 2.2 Architectural Solution: `AssessmentScopeMetadata` & Regulatory Softening
We will introduce an explicit `EpistemicValidationState` enumeration in the domain model and refactor the regulatory risk mapping layer to emit operational resilience postures rather than legal breach verdicts.

**Target File:** `src/domain/models/assessment_metadata.py`

```python
"""
Domain models for epistemic validation state and regulatory posture shielding.
Ensures strict separation between technical resilience assessments and formal legal opinions.
"""

from enum import Enum
from pydantic import BaseModel, Field


class EpistemicValidationState(str, Enum):
    EXPLORATORY_FAST_ASSESSMENT = "EXPLORATORY_FAST_ASSESSMENT"
    EVIDENCE_SAMPLED_AUDIT = "EVIDENCE_SAMPLED_AUDIT"
    FORENSIC_LIVE_VERIFICATION = "FORENSIC_LIVE_VERIFICATION"


class RegulatoryPostureLevel(str, Enum):
    PRIORITY_ATTENTION = "PRIORITY_ATTENTION"
    MODERATE_OBSERVATION = "MODERATE_OBSERVATION"
    ALIGNED_RESILIENCE = "ALIGNED_RESILIENCE"


class AssessmentScopeMetadata(BaseModel):
    """
    Defines the epistemic boundaries and legal shielding parameters for the assessment run.
    """
    validation_state: EpistemicValidationState = Field(
        default=EpistemicValidationState.EXPLORATORY_FAST_ASSESSMENT,
        description="Defines the depth of empirical verification performed during due diligence."
    )
    enforce_regulatory_shielding: bool = Field(
        default=True,
        description="When True, transforms categorical legal breach claims into technical resilience postures."
    )
    delegated_legal_tower_ref: str = Field(
        default="Legal / T6",
        description="Reference identifier for the legal compliance workstream."
    )

    def format_regulatory_posture(
        self, 
        framework_name: str, 
        severity_score: float, 
        locale_dict: dict
    ) -> str:
        """
        Maps a numerical technical severity score to a legally shielded regulatory posture string.
        Prevents categorical claims of statutory breach in technical towers.
        """
        if not self.enforce_regulatory_shielding:
            return f"{framework_name} (Score: {severity_score:.2f})"

        if severity_score >= 3.5:
            template = locale_dict.get(
                "reg_posture_priority",
                "Atención Prioritaria (Principios de Resiliencia {fw} - sujeto a validación {legal})"
            )
        elif severity_score >= 2.0:
            template = locale_dict.get(
                "reg_posture_moderate",
                "Observación Moderada (Alineamiento Técnico {fw} - sujeto a validación {legal})"
            )
        else:
            template = locale_dict.get(
                "reg_posture_aligned",
                "Resiliencia Alineada (Controles Técnicos {fw})"
            )

        return template.format(fw=framework_name, legal=self.delegated_legal_tower_ref)
```

**AST Integration (`src/presentation/ast_builders/methodology_builder.py`):**
The `MethodologySectionBuilder` will inject a prominent callout box immediately below the CMMI® V3.0 framework declaration rendering the `validation_state_label` and `validation_state_exploratory` strings from `locales.json`.

---

### PHASE 3: Hallucination Catalyst Removal & Parsimonious Grounding Engine

#### 3.1 Forensic Root Cause Analysis
In Iteration 6, to prevent overly brief executive narratives, the prompt engineering layer included a length-expansion directive: *"Expand analytical depth and narrative length by 50%."*
In Large Language Models, unconditional length expansion directives act as **Hallucination Catalysts**. Forced to generate more tokens from a finite set of discovery facts, the LLM engaged in two dangerous behaviors:
1. **Scale Extrapolation (Architectural Inflation):** It took a localized finding—a single legacy physical host running local database instances at an edge site—and extrapolated it into *"clústeres de bases de datos departamentales distribuidos"* (distributed departmental database clusters).
2. **Protocol Invention:** To sound deeply technical while filling token quotas, it hallucinated unverified networking and cloud constructs not present in the raw telemetry (e.g., citing lack of *Bidirectional Forwarding Detection [BFD]* on routers and *flat AWS multi-account topologies* when the client only provided basic VPN and single-account sandbox evidence).

#### 3.2 Architectural Solution: The Parsimonious Factual Precision Engine
We will purge all percentage-based expansion directives from `src/intelligence/prompts/system_directives.py` and replace them with the **Parsimonious Factual Precision & Scale Invariance Protocol**.

**Target File:** `src/intelligence/prompts/system_directives.py`

```python
"""
System prompt directives governing LLM narrative synthesis.
Enforces strict epistemic parsimony, scale invariance, and zero protocol hallucination.
"""

PARSIMONIOUS_GROUNDING_DIRECTIVE = """
### CRITICAL EPISTEMIC DIRECTIVE: PARSIMONIOUS FACTUAL PRECISION & SCALE INVARIANCE

You are writing a legally defensible M&A / Enterprise Due Diligence technical dossier. 
Your narrative authority derives from surgical precision, NOT verbose extrapolation.

1. ABOLITION OF ARTIFICIAL EXPANSION:
   - Do NOT pad, inflate, or artificially lengthen paragraphs to meet arbitrary word counts.
   - Every sentence must convey a distinct, verifiable architectural fact, actuarial metric, or governance implication derived directly from the `verified_evidence_payload`.

2. STRICT SCALE INVARIANCE (NO ARCHITECTURAL INFLATION):
   - Preserve the exact topological scale of the source evidence.
   - If the evidence describes a single server, a standalone VM, a specific edge site, or a localized instance, you MUST refer to it at that exact scale (e.g., "the standalone legacy database host", "the specific edge workload").
   - NEVER pluralize or upgrade single nodes into "departmental clusters", "enterprise-wide server farms", or "distributed data planes" unless explicit multi-node clustering is documented in the input payload.

3. ZERO PROTOCOL OR TOPOLOGY HALLUCINATION:
   - Mention ONLY technologies, network protocols, cloud account structures, and software versions explicitly present in the `verified_evidence_payload`.
   - When explaining why a maturity score is low, cite the absence of general functional capabilities (e.g., "absence of automated dynamic routing failover" or "lack of centralized cloud cost governance"), NEVER the absence of ultra-specific protocols (e.g., do NOT invent references to BFD, OSPF timers, BGP communities, or flat AWS Organization hierarchies) unless those exact terms appear in the raw evidence.
"""
```

---

### PHASE 4: Positive Resilience Recognition (Balanced Assessment Framework)

#### 4.1 Forensic Root Cause Analysis
When a client exhibits a low global maturity score ($1.85 / 5.00$), naive prompt chains suffer from **Negative Sentiment Monopolization**. The LLM focuses 100% of its narrative energy on bashing the infrastructure's flaws (e.g., 91% storage saturation, manual provisioning). 
Consequently, the engine completely omitted a critical piece of positive empirical evidence present in the discovery payload: **the client successfully executed a verified 15-minute High Availability (HA) failover test on their primary virtualization/firewall cluster.**
Omitting proven operational successes alienates the client's engineering leadership, destroys the credibility of the assessor, and presents a skewed risk profile to the Investment Committee.

#### 4.2 Architectural Solution: Dialectical Resilience Synthesis
We will upgrade the `PillarNarrativeContext` Pydantic model and the prompt template in `src/intelligence/prompts/pillar_synthesis_prompt.py` to enforce a **Dialectical Assessment Structure** (Operational Strengths vs. Structural Vulnerabilities).

**Target File:** `src/domain/models/intelligence_payload.py`

```python
from typing import List
from pydantic import BaseModel, Field


class EmpiricalEvidenceItem(BaseModel):
    evidence_id: str
    description: str
    is_positive_resilience_indicator: bool = Field(
        default=False,
        description="True if this evidence represents a verified operational success, working control, or met SLA/RTO."
    )
    verified_metric: str | None = Field(
        default=None,
        description="Exact quantitative metric associated with the evidence (e.g., '15-minute RTO failover', '91% disk capacity')."
    )
```

**Target File:** `src/intelligence/prompts/pillar_synthesis_prompt.py`

```python
BALANCED_RESILIENCE_PROMPT_BLOCK = """
### DIALECTICAL ASSESSMENT MANDATE: POSITIVE RESILIENCE RECOGNITION

Even in low-maturity environments (Score < 2.0), engineering teams often maintain pockets of functional tactical resilience. A Tier-1 audit must be rigorously fair and balanced.

1. MANDATORY INCLUSION OF POSITIVE EVIDENCE:
   - Inspect the `empirical_evidence_items` where `is_positive_resilience_indicator == True`.
   - You MUST explicitly weave these verified operational successes and exact metrics (e.g., proven failover execution times, functional backup restorations, localized high-availability clusters) into the narrative BEFORE or ALONGSIDE your critique of structural deficits.

2. DIALECTICAL CONTRAST STRUCTURE:
   - Frame the analysis using professional consulting dialectic: acknowledge the proven tactical capability (e.g., "While the infrastructure demonstrates localized tactical resilience—evidenced by verified high-availability failover transitions within exact target windows..."), and immediately contrast it with the systemic or capacity risks that threaten its sustainability (e.g., "...this capability is severely jeopardized by critical storage saturation and the absence of automated capacity management.").
"""
```

**Automated Pre-Synthesis Extraction (`src/intelligence/extractors/evidence_classifier.py`):**
We will implement a deterministic rule-based classifier that scans raw discovery notes for positive quantitative patterns (e.g., regex matching `RTO`, `failover`, ` exitoso`, `successful`, ` HA `, `< \d+ min`) and flags `is_positive_resilience_indicator = True` prior to LLM invocation, guaranteeing that tactical successes cannot be ignored by attention mechanisms.

---

### PHASE 5: KPI-by-KPI Micro-Calibration Traceability

#### 5.1 Forensic Root Cause Analysis
This is the most critical actuarial enhancement in Iteration 7. In our current deliverable, when the client self-assesses **Containers & Kubernetes** at an aspirational **4.25 / 5.00** (inputting scores of `4, 4, 5, 4` across its four constituent KPIs) and the Argon Calibration Engine overrides it down to **1.00 / 5.00** (a massive $-3.25$ delta), the report provides only a macro-level paragraph explaining that Kubernetes is in an incipient lab state.

A forensic auditor or an aggrieved CTO reading the report will challenge a $-3.25$ penalty unless every single overridden KPI is systematically dismantled and contrasted against empirical reality.

#### 5.2 Architectural Solution: The Micro-Calibration Rebuttal Matrix
We will architect a universal, threshold-triggered **KPI Micro-Calibration Traceability Engine**. Whenever any domain or sub-domain experiences an algorithmic calibration delta where $|\Delta_{\text{score}}| \ge 1.50$, the engine will construct a structured `KPICalibrationRebuttal` vector and render a dedicated micro-audit table in the AST presentation layer.

**Target File:** `src/actuarial/calibration/kpi_traceability.py`

```python
"""
KPI-by-KPI Micro-Calibration Traceability Engine.
Provides deterministic audit trails whenever human self-assessments diverge significantly
from empirical telemetry and evidence-based scoring.
"""

from typing import List
from pydantic import BaseModel, Field


class KPICalibrationRecord(BaseModel):
    kpi_id: str = Field(..., description="Unique identifier of the KPI from the master catalog.")
    kpi_name: str = Field(..., description="Localized human-readable title of the KPI.")
    raw_self_assessment_score: float = Field(..., ge=1.0, le=5.0, description="Unverified client score.")
    calibrated_empirical_score: float = Field(..., ge=1.0, le=5.0, description="Auditor-verified score.")
    calibration_delta: float = Field(..., description="Mathematical delta (Calibrated - Raw).")
    self_assessment_claim_summary: str = Field(
        ..., description="What the raw score implies according to CMMI V3.0 rubrics."
    )
    empirical_rebuttal_evidence: str = Field(
        ..., description="Specific factual evidence justifying the downward/upward calibration."
    )


class DomainCalibrationAuditTrail(BaseModel):
    domain_id: str
    domain_name: str
    aggregate_raw_score: float
    aggregate_calibrated_score: float
    aggregate_delta: float
    requires_micro_rebuttal: bool
    kpi_records: List[KPICalibrationRecord] = Field(default_factory=list)

    @classmethod
    def build_from_evaluation(
        cls,
        domain_eval: dict,
        catalog_rubrics: dict,
        delta_threshold: float = 1.50
    ) -> "DomainCalibrationAuditTrail":
        """
        Constructs a complete KPI-by-KPI traceability matrix for any domain exceeding
        the calibration divergence threshold. Universally applicable across all towers.
        """
        raw_agg = domain_eval["raw_score"]
        cal_agg = domain_eval["calibrated_score"]
        delta_agg = round(cal_agg - raw_agg, 2)
        requires_rebuttal = abs(delta_agg) >= delta_threshold

        records: List[KPICalibrationRecord] = []
        if requires_rebuttal:
            for kpi in domain_eval.get("kpis", []):
                k_id = kpi["id"]
                k_raw = float(kpi["raw_score"])
                k_cal = float(kpi["calibrated_score"])
                k_delta = round(k_cal - k_raw, 2)

                rubric_level_claim = catalog_rubrics.get(k_id, {}).get(
                    f"level_{int(round(k_raw))}_descriptor",
                    "Declaración de madurez avanzada / optimizada sin respaldo documental."
                )

                records.append(
                    KPICalibrationRecord(
                        kpi_id=k_id,
                        kpi_name=kpi["name"],
                        raw_self_assessment_score=k_raw,
                        calibrated_empirical_score=k_cal,
                        calibration_delta=k_delta,
                        self_assessment_claim_summary=rubric_level_claim,
                        empirical_rebuttal_evidence=kpi.get(
                            "auditor_rebuttal_note",
                            domain_eval.get("macro_calibration_rationale", "")
                        )
                    )
                )

        return cls(
            domain_id=domain_eval["id"],
            domain_name=domain_eval["name"],
            aggregate_raw_score=raw_agg,
            aggregate_calibrated_score=cal_agg,
            aggregate_delta=delta_agg,
            requires_micro_rebuttal=requires_rebuttal,
            kpi_records=records
        )
```

#### 5.3 LLM Prompt Directive for KPI-Specific Rebuttal Synthesis
When `requires_micro_rebuttal == True`, the intelligence layer executes a specialized structured-output call to populate `empirical_rebuttal_evidence` for each KPI in the domain, translating the macro discovery notes into KPI-specific technical rebuttals.

For example, in a universal scenario where a client rates **Container Orchestration** KPIs at `4 / 4 / 5 / 4` (Raw: $4.25$) while only having an isolated sandbox test environment, the engine will automatically generate and render the following AST table in the Calibration Appendix / Section:

| KPI Code & Domain Metric | Raw Self-Assessment | Calibrated Score | Delta ($\Delta$) | Implied Rubric Claim (Raw) | Empirical Forensic Rebuttal (Calibrated Reality) |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **KPI-CONT-01**<br>*Cluster Architecture & Multi-Zone HA* | 4.00 | 1.00 | **-3.00** | Production multi-master HA control plane across availability zones. | No production clusters exist. Workload is confined to non-critical, isolated laboratory testing without HA topology. |
| **KPI-CONT-02**<br>*Automated Deployment & GitOps* | 4.00 | 1.00 | **-3.00** | Declarative CI/CD GitOps pipelines with automated rollback. | Deployments in the test environment are manual/imperative; zero integration with production release pipelines. |
| **KPI-CONT-03**<br>*Container Security & Runtime Policy* | 5.00 | 1.00 | **-4.00** | Zero-trust service mesh, automated image scanning, and runtime eBPF admission control. | Aspirational scoring. No runtime security policies, admission controllers, or registry scanning are active in production. |
| **KPI-CONT-04**<br>*Observability & Auto-Scaling (HPA/VPA)* | 4.00 | 1.00 | **-3.00** | Dynamic metric-driven horizontal/vertical pod auto-scaling and full Prometheus/Grafana telemetry. | Incipient adoption phase; production core applications remain monolithic/VM-based without container auto-scaling. |
| **DOMAIN AGGREGATE** | **4.25** | **1.00** | **-3.25** | *Managed / Optimizing* | *Initial / Incipient (Isolated Lab Scope)* |

#### 5.4 AST & WeasyPrint Pagination Preservation
To ensure this new traceability table does not break our validated **15-page layout**, we will apply compact CSS styling (`font-size: 7.5pt; line-height: 1.15; padding: 3px 5px;`) to `.micro-calibration-table` in `assets/styles/enterprise_report.css`, embedding it directly within the existing Calibration Justification block on Page 6/7 where generous whitespace currently exists.

---

## 3. QUALITY GATES & VERIFICATION ORACLES

Before any PDF compilation is triggered in Iteration 7, the codebase must pass all 47 existing tests plus **5 new deterministic verification oracles** located in `tests/iteration7_world_class_verification/test_phase10_iter7_gates.py`.

**Target File:** `tests/iteration7_world_class_verification/test_phase10_iter7_gates.py`

```python
"""
Deterministic Verification Oracles for Phase 10 - Iteration 7 (9.5+/10 World-Class Target).
Validates locale integrity, epistemic states, regulatory shielding, anti-hallucination prompts,
and KPI-by-KPI micro-calibration traceability.
"""

import json
import pathlib
import pytest

from src.domain.models.assessment_metadata import (
    AssessmentScopeMetadata,
    EpistemicValidationState,
)
from src.actuarial.calibration.kpi_traceability import DomainCalibrationAuditTrail
from src.intelligence.prompts import system_directives, pillar_synthesis_prompt


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
LOCALES_PATH = PROJECT_ROOT / "engine_config" / "locales.json"


def test_gate1_locale_catalog_integrity_and_cmmi_v3():
    """
    Oracle 1: Verifies that locales.json contains zero orthographic typos ('taxonomóa'),
    references CMMI® V3.0, and purges cybersecurity copy-paste artifacts from Automation.
    """
    raw_content = LOCALES_PATH.read_text(encoding="utf-8")
    
    # 1. Orthographic check
    assert "taxonomóa" not in raw_content, "Orthographic defect 'taxonomóa' still present in locales.json"
    assert "taxonomía FinOps" in raw_content, "Corrected 'taxonomía FinOps' missing from locales.json"

    locales = json.loads(raw_content)
    es_locale = locales["es_ES"]

    # 2. CMMI V3.0 verification
    fw_ref = es_locale["methodology"]["framework_reference"]
    assert "CMMI® V3.0" in fw_ref, "Framework reference must explicitly cite CMMI® V3.0"
    assert "CMMI v2.0" not in raw_content, "Legacy CMMI v2.0 reference must be completely purged"

    # 3. Automation domain purity check
    auto_desc = es_locale["pillars"]["automation_orchestration"]["description"].lower()
    assert "protección y respuesta" not in auto_desc, (
        "Cybersecurity copy-paste artifact detected in Automation pillar description"
    )
    assert "infraestructura como código" in auto_desc or "iac" in auto_desc


def test_gate2_epistemic_validation_state_and_regulatory_shielding():
    """
    Oracle 2: Verifies that regulatory posture formatting avoids categorical legal breach claims
    and delegates statutory validation to Legal / T6.
    """
    metadata = AssessmentScopeMetadata(
        validation_state=EpistemicValidationState.EXPLORATORY_FAST_ASSESSMENT,
        enforce_regulatory_shielding=True,
        delegated_legal_tower_ref="Legal / T6",
    )

    mock_locale = {
        "reg_posture_priority": "Atención Prioritaria (Principios de Resiliencia {fw} - sujeto a validación {legal})"
    }

    posture_output = metadata.format_regulatory_posture(
        framework_name="NIS2", severity_score=4.2, locale_dict=mock_locale
    )

    assert "Incumplimiento" not in posture_output, "Categorical legal breach claim ('Incumplimiento') is forbidden"
    assert "Atención Prioritaria" in posture_output
    assert "Principios de Resiliencia NIS2" in posture_output
    assert "sujeto a validación Legal / T6" in posture_output


def test_gate3_prompt_hallucination_catalyst_removal():
    """
    Oracle 3: Verifies that 'Expand 50%' directives are purged and replaced with
    Parsimonious Factual Precision and Scale Invariance rules.
    """
    directive_text = system_directives.PARSIMONIOUS_GROUNDING_DIRECTIVE.lower()

    assert "expand" not in directive_text or "do not pad" in directive_text
    assert "50%" not in directive_text, "Length expansion percentage catalyst must be removed"
    assert "scale invariance" in directive_text
    assert "zero protocol or topology hallucination" in directive_text


def test_gate4_positive_resilience_dialectic_enforcement():
    """
    Oracle 4: Verifies that the pillar synthesis prompt mandates the inclusion of
    verified positive operational metrics (e.g., successful HA failover tests).
    """
    prompt_text = pillar_synthesis_prompt.BALANCED_RESILIENCE_PROMPT_BLOCK

    assert "is_positive_resilience_indicator" in prompt_text
    assert "MANDATORY INCLUSION OF POSITIVE EVIDENCE" in prompt_text
    assert "DIALECTICAL CONTRAST STRUCTURE" in prompt_text


def test_gate5_kpi_micro_calibration_traceability_matrix():
    """
    Oracle 5: Verifies that any domain with a calibration delta >= 1.50 automatically
    generates a complete KPI-by-KPI rebuttal vector matching raw vs. calibrated scores.
    """
    mock_domain_eval = {
        "id": "containers_k8s",
        "name": "Contenedores y Orquestación (Kubernetes)",
        "raw_score": 4.25,
        "calibrated_score": 1.00,
        "macro_calibration_rationale": "Uso incipiente restringido a laboratorio sin cargas productivas.",
        "kpis": [
            {"id": "k1", "name": "Arquitectura de Clúster HA", "raw_score": 4.0, "calibrated_score": 1.0},
            {"id": "k2", "name": "Despliegue Automatizado GitOps", "raw_score": 4.0, "calibrated_score": 1.0},
            {"id": "k3", "name": "Seguridad Runtime y Políticas", "raw_score": 5.0, "calibrated_score": 1.0},
            {"id": "k4", "name": "Observabilidad y Auto-escalado", "raw_score": 4.0, "calibrated_score": 1.0},
        ],
    }

    audit_trail = DomainCalibrationAuditTrail.build_from_evaluation(
        domain_eval=mock_domain_eval, catalog_rubrics={}, delta_threshold=1.50
    )

    assert audit_trail.requires_micro_rebuttal is True
    assert audit_trail.aggregate_delta == -3.25
    assert len(audit_trail.kpi_records) == 4

    # Verify exact mathematical alignment of individual KPI deltas
    deltas = [r.calibration_delta for r in audit_trail.kpi_records]
    assert deltas == [-3.0, -3.0, -4.0, -3.0]
    assert sum(r.raw_self_assessment_score for r in audit_trail.kpi_records) / 4.0 == 4.25
    assert sum(r.calibrated_empirical_score for r in audit_trail.kpi_records) / 4.0 == 1.00
```

---

## 4. EXECUTION ROADMAP & SIGN-OFF CRITERIA

| Step | Component / Module | Action Item | Verification Metric |
| :--- | :--- | :--- | :--- |
| **Step 1** | `engine_config/locales.json` | Patch Automation description, fix `taxonomía FinOps`, upgrade to `CMMI® V3.0`, add Epistemic State strings. | `pytest -k test_gate1` passes $100\%$. |
| **Step 2** | `src/domain/models/assessment_metadata.py` | Implement `EpistemicValidationState` & `format_regulatory_posture` shielding logic. | `pytest -k test_gate2` passes $100\%$. |
| **Step 3** | `src/intelligence/prompts/` | Replace length expansion catalysts with `PARSIMONIOUS_GROUNDING_DIRECTIVE` & `BALANCED_RESILIENCE_PROMPT_BLOCK`. | `pytest -k "test_gate3 or test_gate4"` passes $100\%$. |
| **Step 4** | `src/actuarial/calibration/kpi_traceability.py` | Implement `DomainCalibrationAuditTrail` and wire into AST Calibration Table renderer. | `pytest -k test_gate5` passes $100\%$. |
| **Step 5** | Full Pipeline Regression | Execute complete test suite (47 legacy tests + 5 new Iteration 7 gates) and compile PDF dossier. | **52/52 tests green**, PDF page count $\le 15$ pages, zero visual overlaps. |

*Blueprint formally approved for immediate engineering execution.*  
**— Gemini-4-Argon, Chief Systems Architect & Actuarial Fellow**
```