**RFC 072: Universal TO-BE Architecture & Commercial Pipeline Blueprint**

**Author:** Global Managing Director of Enterprise Architecture & Strategic Advisory
**Status:** Approved for Production Implementation
**Classification:** Highly Confidential - Platform Core Architecture
**Target Deliverables:** Volume 2 (Tomo 2: Target Architecture) & Volume 3 (Tomo 3: Strategic Transformation Roadmap)

---

### 1. Executive Delivery Architecture & Value Proposition

#### 1.1. The Commercial Mandate: Eradicating the 10-Tower Antipattern
Historically, presenting a fragmented 10-tower "TO-BE" architecture triggers a catastrophic commercial anti-pattern:
1.  **Cognitive Overload:** The C-Suite (CIO, CTO, CFO) cannot synthesize 10 disparate technical annexes into a unified business vision.
2.  **Commoditized Procurement:** Fragmented deliverables encourage procurement departments to issue 10 separate, micro-RFPs. This forces NTT DATA into a race-to-the-bottom pricing war against niche, tier-3 vendors on hourly rates.

**The Solution:** The engine will generate a unified, Transversal Target Architecture (Tomo 2) and a programmatic Strategic Transformation Roadmap (Tomo 3). This positions NTT DATA unequivocally as the **Prime Contractor & Strategic Partner**, securing multi-year, end-to-end modernization programs spanning Professional Services (Build) and Managed Services (Run).

#### 1.2. The C-Suite Cognitive Model
The information architecture is engineered to guide executive decision-making:
*   **Volume 2 (Tomo 2 - The "What" & "Why"):** Targets the CIO and CTO. Translates AS-IS technical debt into a highly resilient, scalable, and secure platform ecosystem. 
*   **Volume 3 (Tomo 3 - The "How", "When", & "How Much"):** Targets the CFO and Transformation Office. Quantifies the journey into actionable work packages, resource models, and an actuarially sound Business Case (CAPEX/OPEX/ROI).

#### 1.3. The NTT DATA Commercial Pipeline Engine (Execution Horizons)
All project initiatives derived from the AS-IS diagnostic deficits are dynamically mapped into three sequential execution horizons:
*   **Horizon 1 (H1) - Immediate Stabilization (Months 0-6):** Remediation of critical single-points-of-failure (SPOFs), rapid security patching, basic backup immutability, and landing zone preparation.
*   **Horizon 2 (H2) - Core Modernization & Cloud Convergence (Months 6-18):** Migration to sovereign/hybrid cloud, zero-trust network fabric deployment, identity consolidation, and legacy infrastructure decommissioning.
*   **Horizon 3 (H3) - Platform Innovation & Autonomous Operations (Months 18-36):** Introduction of AIOps, FinOps governance, advanced observability, and fully declarative infrastructure-as-code (IaC).

---

### 2. Data Contract & Domain Schemas (Pydantic)

To guarantee absolute architectural purity, 100% of the codebase, AST, and domain models are written in Technical English. There is zero hardcoding of client names, industry verticals, or specific niche vendor products (e.g., no hardcoded VMware, SimpliVity, etc.).

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

# --- Enums & Core Types ---
class SizingEnum(str, Enum):
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"
    EXTRA_LARGE = "XL"

class HorizonEnum(str, Enum):
    H1 = "H1_STABILIZATION"
    H2 = "H2_MODERNIZATION"
    H3 = "H3_INNOVATION"

class CostModel(BaseModel):
    capex_estimate: float = Field(..., description="Estimated capital expenditure (CAPEX)")
    opex_monthly: float = Field(..., description="Estimated monthly operational expenditure (OPEX)")
    roi_payback_months: int = Field(..., description="Months to achieve return on investment")
    currency: str = Field(default="EUR", description="Dynamic currency ISO code (EUR, USD, JPY, GBP, CHF)")

# --- Tomo 2: Target Architecture Schemas ---
class TargetPlatform(BaseModel):
    platform_id: str = Field(..., description="Platform identifier (e.g., PLATFORM-1)")
    platform_name: str = Field(..., description="Transversal Platform Name")
    strategic_objective: str = Field(..., description="Business value of this platform")
    target_capabilities: List[str] = Field(..., description="List of capabilities provided")
    compliance_controls: List[str] = Field(..., description="Mapped regulatory controls (e.g., DORA, HIPAA)")

class TargetStatePayload(BaseModel):
    version: str = Field(default="1.0.0")
    multi_tenant_scale: str = Field(..., description="Revenue scale definition ($10M to $100B)")
    platforms: List[TargetPlatform] = Field(..., description="The 5 Transversal Enterprise Platforms")
    global_security_posture: str = Field(..., description="Zero Trust and Cyber Defense summary")
    hybrid_topology_summary: str = Field(..., description="Abstracted compute and network topology")

# --- Tomo 3: Transformation Pipeline Schemas ---
class DeliveryResource(BaseModel):
    role: str = Field(..., description="Standardized NTT DATA role (e.g., Lead Architect)")
    fte_allocation: float = Field(..., description="Full-Time Equivalent allocation")

class ProjectInitiative(BaseModel):
    initiative_id: str = Field(..., description="Unique ID (e.g., INIT-H1-001)")
    title: str = Field(..., description="Project Title")
    horizon: HorizonEnum = Field(..., description="Execution Horizon mapping")
    sizing: SizingEnum = Field(..., description="T-shirt sizing for the initiative")
    prerequisites: List[str] = Field(default_factory=list, description="IDs of blocking initiatives")
    wbs_components: List[str] = Field(..., description="Work Breakdown Structure high-level tasks")
    financials: CostModel = Field(..., description="Financial estimates for this initiative")
    delivery_team: List[DeliveryResource] = Field(..., description="NTT DATA staffing model")

class TransformationPipelinePayload(BaseModel):
    version: str = Field(default="1.0.0")
    total_transformation_cost: CostModel = Field(..., description="Aggregated TCO/ROI for entire program")
    strategic_roadmap: List[ProjectInitiative] = Field(..., description="Sorted execution pipeline")
    governance_model: str = Field(..., description="Steering committee and PMO structure")
```

---

### 3. Compiler Architecture Blueprint

The engine will utilize deterministic, high-fidelity OpenXML AST compilers (`Tomo2TargetArchitectureCompiler` and `Tomo3TransformationRoadmapCompiler`) inheriting from the master `OpenXMLASTCompiler`.

#### 3.1. Strict Typography & Layout Invariants
*   **Character Encoding Invariant:** Strict adherence to the short-hyphen (`-`) U+002D. The compiler will intercept and throw a fatal compilation error if an em-dash (`U+2014`) or en-dash (`U+2013`) is detected in the AST pipeline.
*   **Table Autofit Invariant:** All generated WBS and financial tables must inject `<w:tblLayout w:type="autofit"/>`.
*   **Vertical Containment:** Page budgets are strictly enforced. Orphan/widow control (`<w:widowControl/>`) and keep-with-next (`<w:keepNext/>`) attributes must be universally applied to headers and financial summaries to prevent awkward page breaks.

#### 3.2. Volume 2 (Tomo 2) Chapter Specification
1.  **Executive Architecture Synthesis & North Star Vision:** Translating the AS-IS deficits into a unified target state.
2.  **Transversal Enterprise Platforms:**
    *   *Platform 1:* Sovereign Hybrid Cloud & Modern Compute (Landing Zones, K8s).
    *   *Platform 2:* Zero Trust Network Fabric & Distributed Connectivity (SD-WAN, SASE).
    *   *Platform 3:* Data Fabric, Enterprise Storage & Resilience (Immutable Backups).
    *   *Platform 4:* Identity Governance, Modern Workplace & Cyber Defense.
    *   *Platform 5:* Autonomous Operations, Observability & FinOps (OpenTelemetry).
3.  **Multi-Cloud & Hybrid Infrastructure Topology:** Conceptual block diagrams and interconnectivity paradigms.
4.  **Resilient Data & Application Modernization:** Target state for database consistency, backup topologies, and DR.
5.  **Enterprise Security Architecture & Compliance Matrix:** Dynamic mapping to the client's regulatory framework (DORA, HIPAA, NIS2).

#### 3.3. Volume 3 (Tomo 3) Chapter Specification
1.  **Executive Roadmap Memo & Investment Horizon:** C-level summary of transformation velocity and ROI.
2.  **Master Transformation Roadmap:** Gantt-style logical dependency graph (H1 -> H2 -> H3).
3.  **Project Portfolio & Work Breakdown Structure (WBS):** Detailed `ProjectInitiative` printouts, categorized by horizon.
4.  **Comprehensive Business Case, TCO & Actuarial ROI:** Financial breakdowns, Capex vs. Opex shifts, and break-even analysis.
5.  **Governance, Sizing & Delivery Operating Model:** NTT DATA Partnership model, PMO structure, and managed services handover criteria.

---

### 4. Dynamic Sector & Localization Adaptation

#### 4.1. The Injection Pipeline
To guarantee 100% multi-tenant adaptability, all business logic relies on dynamic JSON injections rather than hardcoded text blocks:
*   `case_input.json`: Defines the client scale (Revenue), target geography, and currency.
*   `industry_profiles/<sector>.json`: Automatically injects the correct compliance overlays. (e.g., If sector = Banking, `Platform 4` is automatically augmented with DORA resilience criteria and Basel III reporting specs).
*   `engine_config/rate_card.json`: Contains the dynamic hourly rates and blended daily rates for NTT DATA profiles (Architect, Engineer, PM) adapted to local market purchasing power (EUR vs. CHF vs. INR).

#### 4.2. Internationalization (i18n) Architecture
The AST compiler separates the semantic model from the rendering layer. 
*   **Core Execution:** Occurs purely in Technical English.
*   **Localization Mapping:** Uses `locales/<lang>.json` (English, Spanish, Portuguese, French, German, Japanese). 
*   **Compilation:** The final AST traversal dynamically swaps the semantic tags (e.g., `TXT_H1_STABILIZATION`) with the targeted business language prior to XML serialization, ensuring high-fidelity outputs in the client's native language without duplicating compiler logic.

---

### 5. Implementation Roadmap & Multi-Phase Execution Plan

*   **Phase 1: Domain Modeling & Pipeline Instantiation (Weeks 1-2)**
    *   Implement Pydantic schemas (`TargetStatePayload`, `TransformationPipelinePayload`) in Python.
    *   Build the Transformation Engine logic that reads the output of Tomo 1 (AS-IS deficits) and generates the JSON payloads for Tomo 2 and Tomo 3.
    *   *Quality Gate:* Unit tests validating schema outputs and dynamic rate-card calculations.
*   **Phase 2: Compiler Sub-Classing & Typography Enforcement (Weeks 3-4)**
    *   Develop `Tomo2TargetArchitectureCompiler` and `Tomo3TransformationRoadmapCompiler`.
    *   Implement strict OpenXML AST generation logic, including short-hyphen sanitization and table autofit algorithms.
    *   *Quality Gate:* Blank document generation with structurally perfect XML validation.
*   **Phase 3: Content Generation & Layout Logic (Weeks 5-6)**
    *   Map the 5 Transversal Platforms and the H1/H2/H3 horizons into the document block generators.
    *   Implement the Business Case financial tables and WBS dictionary blocks.
    *   *Quality Gate:* End-to-end integration test generating complete English documents based on dummy mid-market and top-tier $100B client profiles.
*   **Phase 4: Localization Engine & Final Polish (Weeks 7-8)**
    *   Implement the i18n tag-replacement layer during the AST rendering phase.
    *   Populate `locales.json` for all 6 target languages.
    *   *Quality Gate:* C-Suite Peer Review & Production Release (v1.0.0).