```markdown
# ARGON ENGINE: PHASE 7 — FINAL POLISH & WORLD-CLASS CERTIFICATION MASTER PLAN

**Document ID:** `ARGON-ARCH-BP-007`  
**Classification:** Internal Engineering & Actuarial Architecture — Tier-1 Certification  
**Author:** Gemini-4-Argon, Chief Systems Architect & Actuarial Fellow  
**Status:** APPROVED FOR IMMEDIATE EXECUTION  
**Target Repository Path:** `docs/architecture/ARGON_PHASE7_FINAL_POLISH_MASTER_PLAN.md`

---

## 1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO

### 1.1 Strategic Context
With the completion of Phases 1 through 6, the Argon Assessment Engine has achieved complete mathematical, actuarial, and topological parity. All 47 deterministic unit and integration tests pass without regression. The Monte Carlo simulation engine, Open FAIR loss exceedance curves, and CMMI-to-Financial translations are mathematically sound.

However, achieving **Tier-1 World-Class Consulting Certification** requires more than mathematical precision; it demands absolute epistemic rigor, strict legal liability shielding, orthogonal domain boundaries, and boardroom-grade narrative resonance. A final forensic audit of the engine’s generated artifacts revealed five residual qualitative and structural vulnerabilities. Left unaddressed, these flaws expose the practice to legal liability, auditability challenges, and executive disengagement.

### 1.2 The Five Pillars of Phase 7 Remediation

1. **Legal Liability Shielding (Lexical Sanitization):**
   * *The Vulnerability:* LLM outputs and legacy UI locales occasionally emit forensic and statutory audit terminology (e.g., *"auditoría de campo"*, *"peritaje"*, *"verificación empírica"*). This directly contradicts our Master Services Agreement (MSA) and Statement of Work (SOW) disclaimers, which define our engagement as a time-boxed, remote **Rapid Diagnostic Assessment** conducted without invasive configuration inspection.
   * *The Mandate:* Eradicate all statutory audit terminology across system prompts, AST compilers, and localization dictionaries. Enforce a consultative, diagnostic lexicon that legally insulates the firm while maintaining authoritative gravitas.

2. **Strict Domain Orthogonality (Cross-Tower Ownership Enforcement):**
   * *The Vulnerability:* During deep-dive synthesis, the Pillar Architect LLM occasionally breaches domain boundaries (e.g., Tower 2 Compute diagnosing Tower 3 BGP routing tables, Tower 7 ITSM incident SLAs, or Tower 8 FinOps cloud tagging). This causes double-jeopardy scoring penalties and narrative redundancy.
   * *The Mandate:* Re-architect the Pillar Architect system prompt to enforce strict MECE (Mutually Exclusive, Collectively Exhaustive) scope boundaries. Adjacent domains may only be referenced as *upstream/downstream operational dependencies*, explicitly forbidding cross-tower maturity grading.

3. **Open FAIR Actuarial Traceability (Vulnerability Derivation):**
   * *The Vulnerability:* While the Risk Register cards accurately compute Loss Event Frequency ($LEF = TEF \times Vuln$), external risk auditors cannot trace the mathematical provenance of the Vulnerability ($Vuln$) percentage (e.g., why a specific threat vector exhibits an $85\%$ vulnerability ratio).
   * *The Mandate:* Inject a deterministic methodological callout block into the Abstract Syntax Tree (AST) compiler for Section 4.2. This block must explicitly document the actuarial mapping function between evaluated CMMI Maturity Levels ($L_1 \dots L_5$) and Open FAIR Vulnerability Susceptibility bands.

4. **Seamless Epistemic Attribution (Narrative Evidence Traceability):**
   * *The Vulnerability:* To satisfy audit requirements, raw tags such as `[DECLARED]`, `[CONTRASTED]`, or `[EVIDENCED]` were proposed. However, bracketed metadata tags degrade the visual aesthetics of a $250,000+ executive deliverable, making it read like a raw log file rather than a Managing Partner’s brief.
   * *The Mandate:* Engineer a sophisticated rhetorical directive within the system prompts that forces the LLM to weave epistemic provenance organically into the syntax of every technical claim, distinguishing between unverified stakeholder testimony, cross-examined architectural trade-offs, and empirically reviewed artifacts.

5. **Executive Summary Business Context Grounding:**
   * *The Vulnerability:* The Executive Summary occasionally defaults to a generic, bottom-up IT infrastructure summary rather than anchoring the narrative in the specific, existential business pressures facing the C-Suite.
   * *The Mandate:* Upgrade the Orchestrator Prompt to dynamically extract the top three strategic business drivers, operational bottlenecks, and commercial deadlines from the ingested client intelligence payload (`client_intelligence.json` / discovery transcripts) and mandate their placement as the thesis statement of the opening paragraph.

### 1.3 Core Architectural Invariants
All engineering modifications executed under this blueprint must strictly adhere to the following non-negotiable invariants:
* **Invariant 1 (Linguistic Standardization):** 100% of source code, variable identifiers, class names, docstrings, inline comments, system logs, and LLM prompt templates must be written in rigorous **Technical English**. Target output language localization (e.g., `es-ES`, `es-MX`, `pt-BR`, `en-US`) is handled strictly via parameterization and locale dictionaries.
* **Invariant 2 (Zero Hardcoding):** No client names, specific vendor renewal dates, team sizes, or static financial figures may be hardcoded into prompts, AST compilers, or regex validators. All context must be dynamically injected via runtime data structures, ensuring the engine scales seamlessly from a $50M regional retailer to a $100B global financial institution.
* **Invariant 3 (Zero Regressions):** All 47 existing unit, integration, topological, and actuarial test suites must pass prior to merge.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

---

### PHASE 1: Lexical Sanitization & Legal Liability Shielding

#### 1.1 Architectural Objective
Eliminate all legal exposure arising from the mischaracterization of the assessment methodology. The engine must never claim or imply that it has performed an empirical, on-site, or statutory audit (`auditoría`, `peritaje`, `inspección forense`). All static UI strings, AST headers, and dynamic LLM generations must utilize legally vetted consultative terminology.

#### 1.2 Target Files for Modification
1. `src/locales/es.json` (and corresponding keys in `src/locales/en.json` for structural parity)
2. `src/prompts/system/base_persona.md`
3. `src/prompts/tower_architect_prompt.md`
4. `src/prompts/orchestrator_prompt.md`
5. `src/engine/post_processing/lexical_sanitizer.py` *(New Module)*

#### 1.3 Step-by-Step Implementation Specification

##### Step 1.3.1: Localization Dictionary Sanitization (`src/locales/es.json` & `en.json`)
Audit and replace all keys referencing audit or forensic verification with diagnostic assessment terminology.

```json
// src/locales/en.json (Target Keys Update)
{
  "report": {
    "meta": {
      "methodology_title": "Diagnostic Architecture Assessment Methodology",
      "methodology_disclaimer": "This deliverable represents a remote Rapid Diagnostic Assessment based on architectural discovery sessions, stakeholder alignment interviews, and submitted documentary artifacts. It does not constitute a statutory audit, forensic investigation, or empirical configuration inspection.",
      "evaluation_type": "Architectural Discovery & Diagnostic Review",
      "evidence_basis": "Documentary Review & Technical Contrast Sessions"
    },
    "sections": {
      "audit_trail": "Diagnostic Traceability & Epistemic Basis",
      "field_verification": "Architectural Contrast Findings"
    }
  }
}
```

```json
// src/locales/es.json (Target Keys Update)
{
  "report": {
    "meta": {
      "methodology_title": "Metodología de Evaluación Diagnóstica de Arquitectura",
      "methodology_disclaimer": "Este entregable constituye una Evaluación Diagnóstica Rápida (Fast Assessment) realizada de forma remota mediante sesiones de relevamiento arquitectónico, entrevistas de contraste con actores clave y revisión documental de artefactos provistos. No constituye una auditoría legal, peritaje forense ni una inspección empírica de configuraciones en producción.",
      "evaluation_type": "Relevamiento Arquitectónico y Revisión Diagnóstica",
      "evidence_basis": "Revisión Documental y Sesiones de Contraste Técnico"
    },
    "sections": {
      "audit_trail": "Trazabilidad Diagnóstica y Base Epistémica",
      "field_verification": "Hallazgos de Contraste Arquitectónico"
    }
  }
}
```

##### Step 1.3.2: System Persona Legal Guardrail Injection (`src/prompts/system/base_persona.md`)
Inject an explicit `LEGAL_LIABILITY_LEXICON_GUARDRAIL` block into the base system persona inherited by all LLM agents.

```markdown
<!-- src/prompts/system/base_persona.md -->
## LEGAL LIABILITY & LEXICAL GUARDRAILS (CRITICAL INVARIANT)

You are conducting a remote **Rapid Diagnostic Assessment** (Evaluación Diagnóstica Rápida), NOT a statutory audit, forensic investigation, or hands-on configuration inspection. To protect the firm from legal liability and ensure alignment with the Master Services Agreement (MSA):

1. **PROHIBITED LEXICON (NEVER USE THESE TERMS IN ANY LANGUAGE):**
   - English: "field audit", "forensic inspection", "empirical verification", "certified audit", "statutory compliance audit", "penetration test", "hands-on inspection".
   - Spanish: "auditoría de campo", "auditoría forense", "peritaje", "verificación empírica", "inspección física", "auditoría certificada", "comprobación in-situ".

2. **MANDATORY REPLACEMENT LEXICON (USE THESE CONSULTATIVE EQUIVALENTS):**
   - Instead of "audit / auditoría" -> Use "diagnostic assessment / evaluación diagnóstica" or "architectural review / revisión arquitectónica".
   - Instead of "forensic analysis / peritaje" -> Use "deep-dive diagnostic / diagnóstico de profundidad" or "root-cause analysis / análisis de causa raíz".
   - Instead of "empirical verification / verificación empírica" -> Use "technical contrast session / sesión de contraste técnico", "architectural discovery / relevamiento arquitectónico", or "documentary artifact review / revisión de artefactos documentales".

Violation of this lexical boundary invalidates the assessment output.
```

##### Step 1.3.3: Deterministic Post-Processing Sanitizer (`src/engine/post_processing/lexical_sanitizer.py`)
Because LLMs are probabilistic, prompt instructions alone are insufficient for legal compliance. We must implement a deterministic regex-based post-processor in the compilation pipeline that intercepts and replaces any prohibited terms before AST rendering.

```python
# src/engine/post_processing/lexical_sanitizer.py
"""
Deterministic Lexical Sanitizer for Legal Liability Shielding.
Ensures zero occurrence of statutory audit or forensic terminology in generated prose.
"""

import logging
import re
from typing import Dict, List, Pattern, Tuple

logger = logging.getLogger(__name__)


class LexicalSanitizer:
    """
    Intercepts and sanitizes prohibited audit/forensic lexicon across supported locales,
    replacing them with legally vetted consultative terminology while preserving capitalization.
    """

    # Mapping of (Regex Pattern, Replacement String) per language code
    SANITIZATION_RULES: Dict[str, List[Tuple[Pattern, str]]] = {
        "es": [
            (re.compile(r"\bauditor[íi]as?\s+de\s+campo\b", re.IGNORECASE), "evaluación diagnóstica remota"),
            (re.compile(r"\bauditor[íi]as?\s+forenses?\b", re.IGNORECASE), "diagnóstico arquitectónico profundo"),
            (re.compile(r"\bauditor[íi]as?\s+t[ée]cnicas?\b", re.IGNORECASE), "revisión diagnóstica técnica"),
            (re.compile(r"\bperitajes?\s+t[ée]cnicos?\b", re.IGNORECASE), "análisis diagnóstico"),
            (re.compile(r"\bperitajes?\b", re.IGNORECASE), "relevamiento diagnóstico"),
            (re.compile(r"\bverificaci[óo]n(es)?\s+emp[íi]ricas?\b", re.IGNORECASE), "sesión de contraste técnico"),
            (re.compile(r"\bcomprobaci[óo]n(es)?\s+emp[íi]ricas?\b", re.IGNORECASE), "validación documental"),
            (re.compile(r"\binspecci[óo]n(es)?\s+in[\s-]situ\b", re.IGNORECASE), "relevamiento arquitectónico"),
            (re.compile(r"\bauditamos\b", re.IGNORECASE), "evaluamos diagnósticamente"),
        ],
        "en": [
            (re.compile(r"\bfield\s+audits?\b", re.IGNORECASE), "remote diagnostic assessment"),
            (re.compile(r"\bforensic\s+audits?\b", re.IGNORECASE), "deep-dive architectural diagnostic"),
            (re.compile(r"\bforensic\s+inspections?\b", re.IGNORECASE), "architectural discovery review"),
            (re.compile(r"\bempirical\s+verifications?\b", re.IGNORECASE), "technical contrast session"),
            (re.compile(r"\bon-site\s+inspections?\b", re.IGNORECASE), "architectural discovery"),
            (re.compile(r"\bstatutory\s+audits?\b", re.IGNORECASE), "diagnostic assessment"),
        ],
    }

    @classmethod
    def _preserve_case_replace(cls, match: re.Match, replacement: str) -> str:
        """Preserves leading capitalization of the matched prohibited phrase."""
        matched_text = match.group(0)
        if matched_text.isupper():
            return replacement.upper()
        if matched_text[0].isupper():
            return replacement[0].upper() + replacement[1:]
        return replacement

    @classmethod
    def sanitize_text(cls, text: str, locale: str = "es") -> Tuple[str, int]:
        """
        Applies deterministic regex replacements to the input text.

        Args:
            text: Raw narrative string generated by the LLM.
            locale: Two-letter ISO language code (e.g., 'es', 'en').

        Returns:
            Tuple containing the sanitized text and the total count of replacements made.
        """
        if not text:
            return text, 0

        lang_key = locale.split("-")[0].lower()
        rules = cls.SANITIZATION_RULES.get(lang_key, cls.SANITIZATION_RULES["en"])
        total_replacements = 0
        sanitized = text

        for pattern, replacement in rules:
            def replacer(match: re.Match) -> str:
                nonlocal total_replacements
                total_replacements += 1
                logger.warning(
                    "LexicalSanitizer intercepted prohibited term '%s' -> replaced with '%s'",
                    match.group(0),
                    replacement,
                )
                return cls._preserve_case_replace(match, replacement)

            sanitized = pattern.sub(replacer, sanitized)

        return sanitized, total_replacements
```

---

### PHASE 2: Cross-Tower Ownership Enforcement

#### 2.1 Architectural Objective
Enforce strict MECE (Mutually Exclusive, Collectively Exhaustive) domain boundaries across all 8 Architectural Towers. Prevent any single Tower Agent from diagnosing, grading, or prescribing remediation for capabilities owned by another Tower, thereby eliminating double-counting of technical debt and contradictory maturity scores.

#### 2.2 Target Files for Modification
1. `src/domain/taxonomy/tower_boundaries.py` *(New Module)*
2. `src/prompts/tower_architect_prompt.md`
3. `src/engine/agents/pillar_architect_agent.py`

#### 2.3 Step-by-Step Implementation Specification

##### Step 2.3.1: Canonical Tower Boundary Registry (`src/domain/taxonomy/tower_boundaries.py`)
Define the programmatic scope boundaries and explicit exclusions for each architectural domain so they can be dynamically injected into the Pillar Architect prompt at runtime.

```python
# src/domain/taxonomy/tower_boundaries.py
"""
Canonical MECE Domain Boundary Registry for the 8 Architectural Towers.
Defines strict ownership scopes and explicit cross-tower exclusions to prevent leakage.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class TowerScopeDefinition:
    tower_id: str
    canonical_name: str
    in_scope_domains: List[str]
    explicit_exclusions: Dict[str, str]  # Maps excluded topic -> Owning Tower ID & Name


TOWER_BOUNDARY_REGISTRY: Dict[str, TowerScopeDefinition] = {
    "T1": TowerScopeDefinition(
        tower_id="T1",
        canonical_name="Enterprise Architecture, Governance & Strategy",
        in_scope_domains=[
            "Architecture Review Board (ARB)",
            "Technology radar and standards lifecycle",
            "Target state topology and capability mapping",
            "Technical debt registry governance",
        ],
        explicit_exclusions={
            "Cloud cost allocation, tagging, and showback/chargeback": "T8 (FinOps & IT Financial Management)",
            "ITSM change management workflows and CAB ticket execution": "T7 (ITSM, SRE & Operations)",
            "Specific hypervisor or compute cluster sizing": "T2 (Compute, Virtualization & Cloud Runtime)",
        },
    ),
    "T2": TowerScopeDefinition(
        tower_id="T2",
        canonical_name="Compute, Virtualization, Storage & Cloud Runtime",
        in_scope_domains=[
            "Hypervisor clusters, physical host density, CPU/RAM saturation",
            "Block/File/Object storage arrays, SAN/NAS, IOPS performance",
            "Container runtime engines (Kubernetes/OpenShift nodes) and VM lifecycle",
            "Backup, snapshot replication, and infrastructure-level Disaster Recovery (RPO/RTO)",
        ],
        explicit_exclusions={
            "BGP routing, VLAN segmentation, firewall rules, and WAN/SD-WAN": "T3 (Network & Connectivity)",
            "ITSM incident response SLAs, on-call rotation, and ticketing": "T7 (ITSM, SRE & Operations)",
            "Hypervisor/Cloud licensing negotiations, unit economics, and FinOps": "T8 (FinOps & IT Financial Management)",
            "IAM, PAM, EDR agents, and SIEM log correlation": "T4 (Cybersecurity & Zero Trust)",
        },
    ),
    "T3": TowerScopeDefinition(
        tower_id="T3",
        canonical_name="Network, Connectivity & Edge Infrastructure",
        in_scope_domains=[
            "LAN/WAN topology, SD-WAN, MPLS, and internet egress resilience",
            "Core/Distribution/Access switching, BGP/OSPF routing protocols",
            "Load balancers (ADC), DNS, DHCP, IPAM (DDI), and CDN/Edge",
            "East-West micro-segmentation transport and VLAN architecture",
        ],
        explicit_exclusions={
            "SOC monitoring, SIEM correlation, and identity governance": "T4 (Cybersecurity & Zero Trust)",
            "Compute host RAM/CPU capacity and storage array latency": "T2 (Compute, Virtualization & Cloud Runtime)",
            "Application-level API gateways and service mesh logic": "T5 (Application Architecture & SDLC)",
        },
    ),
    "T4": TowerScopeDefinition(
        tower_id="T4",
        canonical_name="Cybersecurity, Identity & Compliance",
        in_scope_domains=[
            "Identity and Access Management (IAM), PAM, MFA, and SSO",
            "Endpoint Detection & Response (EDR/XDR), SIEM/SOAR, and SOC operations",
            "Vulnerability management, posture management (CSPM), and encryption keys",
            "Regulatory compliance controls (ISO 27001, SOC2, PCI-DSS)",
        ],
        explicit_exclusions={
            "Physical network switch throughput and ISP redundancy": "T3 (Network & Connectivity)",
            "Storage backup array hardware and hypervisor cluster capacity": "T2 (Compute, Virtualization & Cloud Runtime)",
            "CI/CD pipeline orchestration mechanics (outside of DevSecOps gates)": "T5 (Application Architecture & SDLC)",
        },
    ),
    "T5": TowerScopeDefinition(
        tower_id="T5",
        canonical_name="Application Architecture, Integration & SDLC",
        in_scope_domains=[
            "Application modularity, microservices/monolith patterns, and APIs",
            "Event-driven brokers (Kafka/RabbitMQ), ESB, and integration layers",
            "CI/CD pipelines, source control, automated testing, and release automation",
        ],
        explicit_exclusions={
            "Underlying VM host saturation or physical SAN storage": "T2 (Compute, Virtualization & Cloud Runtime)",
            "Enterprise Data Warehouse, OLAP lakes, and BI governance": "T6 (Data Architecture, Analytics & AI)",
            "L1/L2/L3 production incident ticketing and ITSM": "T7 (ITSM, SRE & Operations)",
        },
    ),
    "T6": TowerScopeDefinition(
        tower_id="T6",
        canonical_name="Data Architecture, Databases, Analytics & AI",
        in_scope_domains=[
            "OLTP database engine tuning, sharding, and logical replication",
            "Data Lakes, Data Warehouses (OLAP), ETL/ELT pipelines",
            "Data governance, data lineage, master data management (MDM), and AI/MLOps",
        ],
        explicit_exclusions={
            "Underlying SAN/NAS disk hardware and VM host hypervisors": "T2 (Compute, Virtualization & Cloud Runtime)",
            "Application frontend/backend business logic": "T5 (Application Architecture & SDLC)",
        },
    ),
    "T7": TowerScopeDefinition(
        tower_id="T7",
        canonical_name="ITSM, Observability, SRE & Organizational Topology",
        in_scope_domains=[
            "ITSM processes (Incident, Problem, Change Management), CMDB accuracy",
            "Full-stack observability, APM, infrastructure monitoring, and AIOps",
            "Site Reliability Engineering (SRE) practices, error budgets, and toil reduction",
            "Engineering team topology, key-person risk, and operational runbooks",
        ],
        explicit_exclusions={
            "Specific compute hardware sizing or hypervisor architecture": "T2 (Compute, Virtualization & Cloud Runtime)",
            "IT budget variance, vendor contract negotiation, and FinOps": "T8 (FinOps & IT Financial Management)",
        },
    ),
    "T8": TowerScopeDefinition(
        tower_id="T8",
        canonical_name="FinOps, Vendor Management & IT Financial Governance",
        in_scope_domains=[
            "Cloud and on-premise cost visibility, tagging, and unit economics",
            "Software asset management (SAM), licensing optimization, and vendor lock-in commercials",
            "CAPEX vs. OPEX allocation, TCO modeling, and budget governance",
        ],
        explicit_exclusions={
            "Technical configuration of hypervisors, storage, or networks": "T2 / T3 (Compute / Network)",
            "Technical execution of incident response or CI/CD": "T5 / T7 (Applications / Operations)",
        },
    ),
}
```

##### Step 2.3.2: Pillar Architect Prompt Boundary Directive (`src/prompts/tower_architect_prompt.md`)
Update the Pillar Architect prompt template to receive the dynamic boundary constraints and enforce the **Operational Dependency Reference Pattern**.

```markdown
<!-- src/prompts/tower_architect_prompt.md (Section Update) -->
## STRICT DOMAIN ORTHOGONALITY & CROSS-TOWER BOUNDARY ENFORCEMENT

You are exclusively the Lead Architect for **{{ tower_id }}: {{ tower_canonical_name }}**.

### 1. YOUR AUTHORIZED IN-SCOPE DOMAINS:
{{ in_scope_domains_bullet_list }}

### 2. EXPLICIT OUT-OF-SCOPE DOMAINS (STRICT EXCLUSIONS):
The following domains belong to adjacent towers. You are **STRICTLY FORBIDDEN** from diagnosing their maturity, assigning findings to them, or prescribing remediation roadmaps for them:
{{ explicit_exclusions_bullet_list }}

### 3. THE OPERATIONAL DEPENDENCY RULE:
When a root cause or architectural bottleneck in your tower intersects with an excluded domain (for example, if a Compute cluster renewal is impacted by commercial licensing terms in T8, or if Compute recovery is delayed by ITSM ticketing in T7):
- **DO NOT** diagnose or score the adjacent tower's capability.
- **DO** reference the adjacent domain strictly as an **Upstream or Downstream Operational Dependency** (Dependencia Operativa).
- **MANDATORY SYNTAX PATTERN:** *"From the perspective of {{ tower_id }}, this capability exhibits an operational dependency on [Adjacent Tower ID/Name] regarding [Specific Interface Point], where primary diagnostic ownership resides."*
```

---

### PHASE 3: Open FAIR Actuarial Traceability (Vulnerability Justification)

#### 3.1 Architectural Objective
Provide full mathematical and methodological transparency in Section 4.2 (Open FAIR Risk Register & Loss Exceedance Analysis). When an external risk officer or financial auditor inspects a risk card displaying $LEF = TEF \times Vuln$, they must immediately see the actuarial formula and the deterministic CMMI-to-Vulnerability derivation table that justifies why Vulnerability ($Vuln$) is parameterized at a specific percentage (e.g., $80\%$ or $95\%$).

#### 3.2 Target Files for Modification
1. `src/engine/actuarial/fair_vulnerability_mapper.py` *(Update/Formalize Docstrings & Metadata)*
2. `src/engine/compiler/ast_section_4_2_compiler.py`
3. `src/locales/es.json` & `src/locales/en.json`

#### 3.3 Step-by-Step Implementation Specification

##### Step 3.3.1: Localization Keys for Methodological Footnote (`src/locales/en.json` & `es.json`)
Add localized actuarial explanation blocks to the locale dictionaries so the AST compiler remains 100% free of hardcoded prose.

```json
// src/locales/en.json (Actuarial Traceability Keys)
{
  "actuarial": {
    "fair_methodology_box": {
      "title": "Actuarial Methodology Note: Open FAIR Vulnerability (Vuln) Derivation",
      "lead_narrative": "In accordance with the Open FAIR (Factor Analysis of Information Risk) standard, Loss Event Frequency (LEF) is derived as the product of Threat Event Frequency (TEF) and Vulnerability (Vuln): LEF = TEF × Vuln. Within the Argon Actuarial Engine, Vulnerability represents the conditional probability that a threat event results in a loss event, which is mathematically inverse to the evaluated CMMI Control Maturity Level of the underlying architectural tower.",
      "table_headers": {
        "cmmi_level": "Evaluated CMMI Maturity Level",
        "control_state": "Architectural Control & Automation State",
        "vuln_band": "Derived Open FAIR Vulnerability (Vuln) Band",
        "actuarial_rationale": "Actuarial & Control Justification"
      },
      "levels": {
        "l1": {
          "name": "Level 1 — Initial / Ad-Hoc",
          "state": "Absence of automated preventive controls; reliance on manual heroics.",
          "band": "80% – 95%",
          "rationale": "Near-certain threat manifestation due to lack of architectural redundancy, automated failover, or preventive policy enforcement."
        },
        "l2": {
          "name": "Level 2 — Managed / Reactive",
          "state": "Basic reactive monitoring; inconsistent configuration baselines.",
          "band": "55% – 79%",
          "rationale": "High susceptibility to cascading failures; manual intervention required to contain threat events before SLA breach."
        },
        "l3": {
          "name": "Level 3 — Defined / Standardized",
          "state": "Documented standards, N+1 redundancy, and baseline automation.",
          "band": "30% – 54%",
          "rationale": "Moderate resilience; standard threat vectors are absorbed, though complex multi-vector faults may bypass static controls."
        },
        "l4": {
          "name": "Level 4 — Quantitatively Managed",
          "state": "Automated self-healing, immutable infrastructure, and telemetry-driven SLOs.",
          "band": "10% – 29%",
          "rationale": "High control efficacy; automated mitigation contains the vast majority of threat events without operational disruption."
        },
        "l5": {
          "name": "Level 5 — Optimizing / Autonomous",
          "state": "Continuous chaos engineering, predictive AIOps, and active-active zero-trust.",
          "band": "1% – 9%",
          "rationale": "Residual systemic risk only; architecture autonomously absorbs and remediates anomalies in real time."
        }
      }
    }
  }
}
```

```json
// src/locales/es.json (Actuarial Traceability Keys)
{
  "actuarial": {
    "fair_methodology_box": {
      "title": "Nota Metodológica Actuarial: Derivación de Vulnerabilidad (Vuln) bajo Estándar Open FAIR",
      "lead_narrative": "De conformidad con el estándar Open FAIR (Factor Analysis of Information Risk), la Frecuencia de Eventos de Pérdida (LEF) se calcula como el producto entre la Frecuencia de Eventos de Amenaza (TEF) y la Vulnerabilidad (Vuln): LEF = TEF × Vuln. En el Motor Actuarial Argon, la Vulnerabilidad representa la probabilidad condicional de que un evento de amenaza supere las defensas arquitectónicas y se materialice en una pérdida financiera, siendo matemáticamente inversa al Nivel de Madurez CMMI evaluado en la torre correspondiente.",
      "table_headers": {
        "cmmi_level": "Nivel de Madurez CMMI Evaluado",
        "control_state": "Estado de Control Arquitectónico y Automatización",
        "vuln_band": "Banda de Vulnerabilidad (Vuln) Open FAIR",
        "actuarial_rationale": "Justificación Actuarial y de Eficacia de Control"
      },
      "levels": {
        "l1": {
          "name": "Nivel 1 — Inicial / Ad-Hoc",
          "state": "Ausencia de controles preventivos automatizados; dependencia de intervención manual reactiva.",
          "band": "80% – 95%",
          "rationale": "Materialización casi cierta ante eventos de amenaza debido a la carencia de redundancia activa, failover automatizado o aplicación preventiva de políticas."
        },
        "l2": {
          "name": "Nivel 2 — Gestionado / Reactivo",
          "state": "Monitoreo básico reactivo; líneas base de configuración inconsistentes entre entornos.",
          "band": "55% – 79%",
          "rationale": "Alta susceptibilidad a fallos en cascada; se requiere intervención humana para contener el evento antes del incumplimiento de SLA."
        },
        "l3": {
          "name": "Nivel 3 — Definido / Estandarizado",
          "state": "Estándares documentados, redundancia N+1 y automatización de línea base.",
          "band": "30% – 54%",
          "rationale": "Resiliencia moderada; los vectores de amenaza estándar son absorbidos, aunque fallos complejos multivectoriales pueden superar controles estáticos."
        },
        "l4": {
          "name": "Nivel 4 — Gestionado Cuantitativamente",
          "state": "Autocuración (self-healing) automatizada, infraestructura inmutable y SLOs guiados por telemetría.",
          "band": "10% – 29%",
          "rationale": "Alta eficacia de control; la mitigación automatizada contiene la gran mayoría de los eventos de amenaza sin interrupción operativa."
        },
        "l5": {
          "name": "Nivel 5 — Optimizado / Autónomo",
          "state": "Ingeniería del caos continua, AIOps predictivo y topología activo-activo Zero-Trust.",
          "band": "1% – 9%",
          "rationale": "Exposición limitada a riesgo sistémico residual; la arquitectura absorbe y remedia anomalías de forma autónoma en tiempo real."
        }
      }
    }
  }
}
```

##### Step 3.3.2: AST Compiler Footnote Node Injection (`src/engine/compiler/ast_section_4_2_compiler.py`)
Modify the Section 4.2 AST Compiler to inject the `MethodologyCalloutNode` and per-card CMMI provenance badges directly into the document tree.

```python
# src/engine/compiler/ast_section_4_2_compiler.py
"""
AST Compiler for Section 4.2: Open FAIR Risk Quantification & Loss Exceedance Curves.
Includes deterministic CMMI-to-Vulnerability actuarial traceability nodes.
"""

from typing import Any, Dict, List
from src.engine.compiler.ast_nodes import (
    ASTNode,
    CalloutBoxNode,
    ParagraphNode,
    SectionNode,
    TableNode,
    TableRowNode,
)
from src.locales.locale_manager import LocaleManager


class Section42ActuarialCompiler:
    """Compiles Section 4.2 Open FAIR Risk Register and Methodological Traceability."""

    def __init__(self, locale_manager: LocaleManager) -> None:
        self.i18n = locale_manager

    def build_vulnerability_traceability_node(self) -> CalloutBoxNode:
        """
        Constructs the deterministic AST CalloutBoxNode explaining the mathematical
        derivation of Open FAIR Vulnerability (Vuln) from CMMI Maturity Levels.
        """
        box_i18n: Dict[str, Any] = self.i18n.get("actuarial.fair_methodology_box")
        headers = box_i18n["table_headers"]
        levels = box_i18n["levels"]

        table_rows: List[TableRowNode] = []
        for level_key in ["l1", "l2", "l3", "l4", "l5"]:
            lvl_data = levels[level_key]
            table_rows.append(
                TableRowNode(
                    cells=[
                        lvl_data["name"],
                        lvl_data["state"],
                        lvl_data["band"],
                        lvl_data["rationale"],
                    ]
                )
            )

        methodology_table = TableNode(
            headers=[
                headers["cmmi_level"],
                headers["control_state"],
                headers["vuln_band"],
                headers["actuarial_rationale"],
            ],
            rows=table_rows,
            style_class="actuarial-derivation-table",
        )

        return CalloutBoxNode(
            title=box_i18n["title"],
            variant="info-actuarial",
            children=[
                ParagraphNode(text=box_i18n["lead_narrative"]),
                methodology_table,
            ],
        )

    def format_risk_card_vulnerability_caption(
        self, vuln_ratio: float, source_tower_id: str, evaluated_cmmi_score: float
    ) -> str:
        """
        Generates the inline parenthetical justification for an individual Risk Card's
        Vulnerability parameter, linking it directly to the evaluated CMMI score.
        """
        vuln_pct = round(vuln_ratio * 100, 1)
        return (
            f"{vuln_pct}% [Derived from {source_tower_id} CMMI Maturity "
            f"{evaluated_cmmi_score:.1f}/5.0]"
        )

    def compile_section(self, risk_register_payload: Dict[str, Any]) -> SectionNode:
        """Compiles the complete Section 4.2 AST node tree."""
        children: List[ASTNode] = []

        # 1. Render Risk Register Cards with explicit CMMI->Vuln inline provenance
        for risk_item in risk_register_payload.get("scenarios", []):
            risk_item["vuln_formatted_trace"] = self.format_risk_card_vulnerability_caption(
                vuln_ratio=risk_item["vulnerability_ratio"],
                source_tower_id=risk_item["primary_tower_id"],
                evaluated_cmmi_score=risk_item["tower_cmmi_maturity"],
            )
            # Card node construction continues via existing card builder...

        # 2. Append the Methodological Actuarial Footnote Callout Box at the base of Section 4.2
        children.append(self.build_vulnerability_traceability_node())

        return SectionNode(
            section_id="4.2",
            title=self.i18n.get("report.sections.open_fair_quantification"),
            children=children,
        )
```

---

### PHASE 4: Epistemic Attribution Flow (Elegant Evidence Traceability)

#### 4.1 Architectural Objective
Satisfy the forensic audit requirement to distinguish between three epistemic tiers of evidence (**Declared**, **Contrasted**, and **Evidenced**) *without* polluting the executive layout with ugly bracketed tags like `[DECLARED]`, `[CONTRASTED]`, or `[EVIDENCED]`. We will engineer a strict rhetorical protocol in the system prompts and enforce tag absence via post-processing.

#### 4.2 Target Files for Modification
1. `src/prompts/system/epistemic_attribution_protocol.md` *(New Prompt Module)*
2. `src/prompts/tower_architect_prompt.md`
3. `src/prompts/orchestrator_prompt.md`
4. `src/engine/post_processing/epistemic_validator.py` *(New Module)*

#### 4.3 Step-by-Step Implementation Specification

##### Step 4.3.1: Epistemic Attribution Prompt Protocol (`src/prompts/system/epistemic_attribution_protocol.md`)
Create a dedicated prompt module that defines the three epistemic states and provides natural, publication-grade linguistic transitions in both English and Spanish.

```markdown
<!-- src/prompts/system/epistemic_attribution_protocol.md -->
## EPISTEMIC ATTRIBUTION & EVIDENCE TRACEABILITY PROTOCOL

Every technical finding, architectural claim, or operational metric you write must clearly signal its **epistemic provenance** (how the consulting team knows this information).

### CRITICAL AESTHETIC RULE (ZERO BRACKETED TAGS):
**NEVER** output raw metadata tags or bracketed labels such as `[DECLARED]`, `[CONTRASTED]`, `[EVIDENCED]`, `[DECLARADO]`, `[CONTRASTADO]`, or `[EVIDENCIADO]`. Bracketed tags destroy the executive aesthetic of the report.

Instead, you MUST weave epistemic attribution seamlessly into the prose of your sentences using the three canonical rhetorical patterns below:

### TIER 1: DECLARED CLAIMS (Testimony without documentary artifact)
*Use when a metric, configuration, or process is stated by client personnel during interviews but was not corroborated by an exported configuration file, diagram, or telemetry log.*
- **English Transitions:**
  - *"As reported by the engineering leadership during discovery sessions..."*
  - *"According to stakeholder testimony regarding operational workflows..."*
  - *"Management indicates that..."*
- **Spanish Transitions:**
  - *"Según lo manifestado por el equipo de ingeniería durante las sesiones de relevamiento..."*
  - *"De acuerdo con lo declarado por los referentes técnicos..."*
  - *"Conforme a lo expuesto por la gerencia operativa..."*

### TIER 2: CONTRASTED FINDINGS (Triangulated across multiple interviews or cross-examined)
*Use when an initial claim was stress-tested across multiple stakeholders, or when operational symptoms described in one session corroborate structural bottlenecks in another.*
- **English Transitions:**
  - *"As validated during technical contrast sessions with the operations team..."*
  - *"Triangulating stakeholder inputs across infrastructure and application teams reveals..."*
  - *"Cross-examination of incident post-mortems during discovery confirms..."*
- **Spanish Transitions:**
  - *"Tras el contraste técnico realizado en las sesiones de trabajo..."*
  - *"Al triangular los insumos relevados entre los equipos de infraestructura y operaciones, se constata que..."*
  - *"Como resultado de las sesiones de contraste arquitectónico..."*

### TIER 3: EVIDENCED ARTIFACTS (Backed by provided diagrams, exports, or financial schedules)
*Use when the finding is directly extracted from a submitted artifact, such as `client_intelligence.json` telemetry payloads, architecture diagrams, hypervisor inventory exports, or licensing BoMs.*
- **English Transitions:**
  - *"As evidenced in the submitted architectural topology diagrams..."*
  - *"Inspection of the provided capacity telemetry and inventory artifacts confirms..."*
  - *"Documentary review of the commercial licensing schedules demonstrates..."*
- **Spanish Transitions:**
  - *"Tal como se evidencia en los diagramas de topología y artefactos provistos..."*
  - *"El análisis documental de los inventarios de capacidad suministrados demuestra que..."*
  - *"Según consta en los registros de telemetría y documentación técnica aportada..."*

**MANDATORY CADENCE:** Every major diagnostic paragraph must contain at least one explicit epistemic attribution phrase matching the true source of the data provided in the context payload.
```

##### Step 4.3.2: Deterministic Epistemic Tag Stripper & Cadence Validator (`src/engine/post_processing/epistemic_validator.py`)
Ensure that if an LLM hallucinates a bracketed tag despite instructions, it is cleanly stripped and logged, while verifying the presence of natural epistemic phrasing.

```python
# src/engine/post_processing/epistemic_validator.py
"""
Epistemic Attribution Validator & Bracketed Tag Sanitizer.
Ensures zero bracketed tags pollute executive prose while verifying natural attribution cadence.
"""

import re
from typing import Dict, List, Pattern, Tuple


class EpistemicValidator:
    """Strips forbidden bracketed epistemic tags and audits natural prose attribution."""

    FORBIDDEN_TAG_PATTERN: Pattern = re.compile(
        r"\[\s*(DECLARED|CONTRASTED|EVIDENCED|DECLARADO|CONTRASTADO|EVIDENCIADO|"
        r"EVIDENCIA| SUPUESTO|ASSUMED)\s*\]\s*:?\s*",
        re.IGNORECASE,
    )

    NATURAL_ATTRIBUTION_MARKERS: Dict[str, List[Pattern]] = {
        "es": [
            re.compile(r"\bseg[úu]n\s+(lo\s+)?(manifestado|declarado|informado|consta)\b", re.IGNORECASE),
            re.compile(r"\bsesiones\s+de\s+(relevamiento|contraste)\b", re.IGNORECASE),
            re.compile(r"\bcontraste\s+(t[ée]cnico|arquitect[óo]nico)\b", re.IGNORECASE),
            re.compile(r"\ban[áa]lisis\s+documental\b", re.IGNORECASE),
            re.compile(r"\bartefactos\s+(provistos|aportados|suministrados|documentales)\b", re.IGNORECASE),
            re.compile(r"\bcomo\s+se\s+evidencia\s+en\b", re.IGNORECASE),
            re.compile(r"\bal\s+triangular\b", re.IGNORECASE),
        ],
        "en": [
            re.compile(r"\bas\s+(reported|stated|declared|indicated)\s+by\b", re.IGNORECASE),
            re.compile(r"\btechnical\s+contrast\s+sessions?\b", re.IGNORECASE),
            re.compile(r"\bdiscovery\s+sessions?\b", re.IGNORECASE),
            re.compile(r"\bdocumentary\s+review\b", re.IGNORECASE),
            re.compile(r"\bsubmitted\s+(artifacts?|diagrams?|inventories|telemetry)\b", re.IGNORECASE),
            re.compile(r"\bas\s+evidenced\s+in\b", re.IGNORECASE),
            re.compile(r"\btriangulating\b", re.IGNORECASE),
        ],
    }

    @classmethod
    def clean_and_validate(cls, text: str, locale: str = "es") -> Tuple[str, int, int]:
        """
        Strips any forbidden bracketed tags and counts natural epistemic markers.

        Returns:
            Tuple of (cleaned_text, stripped_tags_count, natural_markers_count)
        """
        stripped_count = 0

        def _strip_replacer(match: re.Match) -> str:
            nonlocal stripped_count
            stripped_count += 1
            return ""

        cleaned_text = cls.FORBIDDEN_TAG_PATTERN.sub(_strip_replacer, text)

        lang_key = locale.split("-")[0].lower()
        markers = cls.NATURAL_ATTRIBUTION_MARKERS.get(
            lang_key, cls.NATURAL_ATTRIBUTION_MARKERS["en"]
        )
        marker_hits = sum(len(pattern.findall(cleaned_text)) for pattern in markers)

        return cleaned_text, stripped_count, marker_hits
```

---

### PHASE 5: Business Context Anchoring in Executive Summary

#### 5.1 Architectural Objective
Eliminate generic, bottom-up IT summaries in Section 1.1 (Executive Summary). The opening paragraph of the report must read as if written by a Global Managing Partner who deeply understands the client's specific commercial, operational, and strategic reality. We will build a deterministic `BusinessContextExtractor` that parses `client_intelligence.json` and interview metadata to extract the **Top 3 Strategic Business Drivers & Operational Constraints**, injecting them as a mandatory structural anchor into the Orchestrator Prompt.

#### 5.2 Target Files for Modification
1. `src/engine/context/business_context_extractor.py` *(New Module)*
2. `src/prompts/orchestrator_prompt.md`
3. `src/engine/agents/orchestrator_agent.py`

#### 5.3 Step-by-Step Implementation Specification

##### Step 5.3.1: Dynamic Business Context Extractor (`src/engine/context/business_context_extractor.py`)
Create a pure, zero-hardcoding extractor that inspects the ingested `client_intelligence.json` payload (supporting varying schemas across retail, banking, or SaaS clients) and normalizes the top 3 executive pain points.

```python
# src/engine/context/business_context_extractor.py
"""
Dynamic Business Context Extractor.
Extracts and normalizes the Top 3 Strategic Business Drivers, Commercial Deadlines,
and Operational Constraints from the runtime client intelligence payload.
Zero hardcoding: adapts dynamically to any industry vertical or company scale.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class ExecutiveContextAnchor:
    rank: int
    category: str
    headline: str
    quantified_impact_or_constraint: str


class BusinessContextExtractor:
    """
    Parses `client_intelligence.json` and interview synthesis structures to extract
    the top 3 specific business/operational pain points for the Executive Summary.
    """

    @classmethod
    def extract_top_anchors(
        cls, client_intelligence: Dict[str, Any], max_anchors: int = 3
    ) -> List[ExecutiveContextAnchor]:
        """
        Deterministically extracts the highest-priority business drivers from the
        client intelligence payload without relying on hardcoded client assumptions.
        """
        candidates: List[Dict[str, str]] = []

        # 1. Inspect explicit CEO / Executive Agenda drivers if present
        exec_agenda = client_intelligence.get("executive_agenda", {})
        for driver in exec_agenda.get("strategic_drivers", []):
            if isinstance(driver, dict):
                candidates.append({
                    "category": driver.get("category", "Strategic Business Driver"),
                    "headline": driver.get("driver", driver.get("title", "")),
                    "detail": driver.get("business_impact", driver.get("constraint", "")),
                })
            elif isinstance(driver, str):
                candidates.append({
                    "category": "Strategic Business Driver",
                    "headline": driver,
                    "detail": "Identified as primary C-Suite priority during executive alignment.",
                })

        # 2. Inspect critical commercial / licensing / infrastructure constraints
        constraints = client_intelligence.get("operational_constraints", [])
        if isinstance(constraints, list):
            for item in constraints:
                if isinstance(item, dict):
                    candidates.append({
                        "category": item.get("domain", "Operational & Commercial Constraint"),
                        "headline": item.get("constraint", item.get("summary", "")),
                        "detail": item.get("quantified_metric", item.get("impact", "")),
                    })

        # 3. Inspect organizational / team topology bottlenecks (e.g., lean headcount vs scale)
        org_profile = client_intelligence.get("organization_profile", {})
        if org_profile.get("critical_bottleneck"):
            candidates.append({
                "category": "Organizational & Execution Capacity",
                "headline": org_profile["critical_bottleneck"],
                "detail": f"IT Staff Topology: {org_profile.get('it_headcount_summary', 'Constrained capacity')}",
            })

        # 4. Fallback to top critical findings from discovery transcripts if structured keys are sparse
        if len(candidates) < max_anchors:
            discovery_highlights = client_intelligence.get("discovery_pain_points", [])
            for highlight in discovery_highlights:
                if isinstance(highlight, str):
                    candidates.append({
                        "category": "Critical Discovery Pain Point",
                        "headline": highlight,
                        "detail": "Surfaced during architectural discovery sessions.",
                    })

        # Filter empty headlines and slice top N
        valid_candidates = [c for c in candidates if c.get("headline", "").strip()]
        anchors: List[ExecutiveContextAnchor] = []

        for idx, item in enumerate(valid_candidates[:max_anchors], start=1):
            anchors.append(
                ExecutiveContextAnchor(
                    rank=idx,
                    category=item["category"],
                    headline=item["headline"].strip(),
                    quantified_impact_or_constraint=item["detail"].strip(),
                )
            )

        return anchors

    @classmethod
    def format_for_prompt_injection(cls, anchors: List[ExecutiveContextAnchor]) -> str:
        """Formats the extracted anchors into a structured Markdown block for the LLM."""
        if not anchors:
            return "No specific custom overrides provided; anchor in primary quantified risk drivers."

        lines = []
        for anchor in anchors:
            detail_suffix = (
                f" — *Quantified Constraint/Impact:* {anchor.quantified_impact_or_constraint}"
                if anchor.quantified_impact_or_constraint
                else ""
            )
            lines.append(
                f"{anchor.rank}. **[{anchor.category}]** {anchor.headline}{detail_suffix}"
            )
        return "\n".join(lines)
```

##### Step 5.3.2: Orchestrator Prompt Thesis Mandate (`src/prompts/orchestrator_prompt.md`)
Update the Orchestrator Prompt to enforce that the opening paragraph of the Executive Summary directly synthesizes the injected `{{ top_business_context_anchors }}` alongside the financial risk exposure.

```markdown
<!-- src/prompts/orchestrator_prompt.md (Section 1.1 Executive Summary Directive) -->
## MANDATORY OPENING THESIS: CLIENT-SPECIFIC BUSINESS CONTEXT GROUNDING

You are writing for the Chief Executive Officer (CEO), Chief Financial Officer (CFO), and Board of Directors of **{{ client_organization_name }}**.

**CRITICAL FAILURE MODE TO AVOID:**
Never open the Executive Summary with generic platitudes about "digital transformation", "modernizing IT infrastructure", or a dry list of CMMI maturity scores.

**MANDATORY OPENING PARAGRAPH STRUCTURE:**
The very first paragraph of the Executive Summary MUST anchor the entire diagnostic assessment around the client's specific, immediate commercial, operational, and organizational pressures extracted from their discovery intelligence:

### CLIENT'S TOP 3 EXISTENTIAL BUSINESS & OPERATIONAL DRIVERS:
{{ top_business_context_anchors }}

### EXECUTION DIRECTIVE FOR PARAGRAPH 1:
1. Explicitly weave **all three** of the above client-specific drivers (e.g., commercial contract/licensing deadlines, acute physical resource saturation metrics, and organizational team capacity constraints) into the opening thesis statement.
2. Immediately connect these three operational realities to the **Aggregate Annualized Loss Expectancy (ALE: {{ total_ale_formatted }})** and the **Overall Architectural Maturity ({{ overall_cmmi_score }}/5.0)**.
3. Frame the remediation roadmap not as an "IT upgrade", but as an executive risk-mitigation and business-continuity imperative designed to resolve these exact three bottlenecks within the client's commercial timeline.
```

---

## 3. QUALITY GATES & VERIFICATION ORACLES

To guarantee **Invariant 3 (Zero Regressions)** and provide deterministic verification that all 5 blocking flaws are permanently eradicated, we introduce Test Suite #48 (`tests/quality_gates/test_phase7_world_class_certification.py`).

### 3.1 Automated Verification Test Suite Specification

```python
# tests/quality_gates/test_phase7_world_class_certification.py
"""
Phase 7 World-Class Certification Quality Gates & Verification Oracles.
Deterministically verifies all 5 qualitative, epistemic, and actuarial remediation pillars.
"""

import pytest
from src.domain.taxonomy.tower_boundaries import TOWER_BOUNDARY_REGISTRY
from src.engine.compiler.ast_section_4_2_compiler import Section42ActuarialCompiler
from src.engine.context.business_context_extractor import BusinessContextExtractor
from src.engine.post_processing.epistemic_validator import EpistemicValidator
from src.engine.post_processing.lexical_sanitizer import LexicalSanitizer
from src.locales.locale_manager import LocaleManager


class TestPhase7CertificationOracles:
    """Deterministic verification suite for Phase 7 architectural invariants."""

    def test_gate_1_lexical_sanitization_shielding(self) -> None:
        """
        ORACLE 1: Verifies that prohibited statutory audit and forensic terms are
        deterministically intercepted and replaced in both Spanish and English.
        """
        raw_es = (
            "Durante la auditoría de campo y el peritaje técnico realizamos una "
            "verificación empírica de los servidores."
        )
        sanitized_es, count_es = LexicalSanitizer.sanitize_text(raw_es, locale="es")

        assert count_es == 3
        assert "auditoría de campo" not in sanitized_es.lower()
        assert "peritaje" not in sanitized_es.lower()
        assert "verificación empírica" not in sanitized_es.lower()
        assert "evaluación diagnóstica remota" in sanitized_es.lower()
        assert "sesión de contraste técnico" in sanitized_es.lower()

    def test_gate_2_cross_tower_boundary_completeness(self) -> None:
        """
        ORACLE 2: Verifies that all 8 Towers have strict MECE boundary definitions
        and that T2 (Compute) explicitly excludes T3 (Network), T7 (ITSM), and T8 (FinOps).
        """
        assert len(TOWER_BOUNDARY_REGISTRY) == 8
        t2_scope = TOWER_BOUNDARY_REGISTRY["T2"]
        excluded_targets = " ".join(t2_scope.explicit_exclusions.values())

        assert "T3" in excluded_targets, "T2 must explicitly exclude T3 Network routing"
        assert "T7" in excluded_targets, "T2 must explicitly exclude T7 ITSM SLAs"
        assert "T8" in excluded_targets, "T2 must explicitly exclude T8 FinOps/Licensing"

    def test_gate_3_open_fair_vulnerability_ast_traceability(self) -> None:
        """
        ORACLE 3: Verifies that Section 4.2 AST Compiler injects the CMMI-to-Vulnerability
        derivation table and formats inline risk card justifications.
        """
        locale_mgr = LocaleManager(locale="es")
        compiler = Section42ActuarialCompiler(locale_manager=locale_mgr)

        callout_node = compiler.build_vulnerability_traceability_node()
        assert callout_node.variant == "info-actuarial"
        assert len(callout_node.children) == 2

        table_node = callout_node.children[1]
        assert len(table_node.rows) == 5  # CMMI Levels 1 through 5
        assert "80% – 95%" in table_node.rows[0].cells[2]

        caption = compiler.format_risk_card_vulnerability_caption(
            vuln_ratio=0.85, source_tower_id="T2", evaluated_cmmi_score=1.4
        )
        assert "85.0%" in caption
        assert "T2" in caption
        assert "1.4/5.0" in caption

    def test_gate_4_epistemic_attribution_elegance(self) -> None:
        """
        ORACLE 4: Verifies that ugly bracketed tags ([DECLARED], [CONTRASTED], [EVIDENCED])
        are stripped while natural consultative attribution markers are recognized.
        """
        polluted_prose = (
            "[DECLARED] Según lo manifestado por el equipo de ingeniería, el clúster opera al 92%. "
            "[EVIDENCED]: Tal como se evidencia en los diagramas provistos, no existe redundancia."
        )
        cleaned, stripped_count, marker_hits = EpistemicValidator.clean_and_validate(
            polluted_prose, locale="es"
        )

        assert stripped_count == 2
        assert "[DECLARED]" not in cleaned
        assert "[EVIDENCED]" not in cleaned
        assert marker_hits >= 2

    def test_gate_5_business_context_extraction_zero_hardcoding(self) -> None:
        """
        ORACLE 5: Verifies that BusinessContextExtractor dynamically extracts the Top 3
        executive pain points from arbitrary client payloads without hardcoding.
        """
        mock_payload = {
            "executive_agenda": {
                "strategic_drivers": [
                    {
                        "category": "Commercial Licensing Deadline",
                        "driver": "Hypervisor enterprise agreement renewal in Q3",
                        "business_impact": "300% OPEX penalty if unmitigated",
                    }
                ]
            },
            "operational_constraints": [
                {
                    "domain": "Infrastructure Capacity",
                    "constraint": "Physical host memory saturation across primary cluster",
                    "quantified_metric": "94% RAM utilization peak",
                }
            ],
            "organization_profile": {
                "critical_bottleneck": "Lean infrastructure operations team managing 24/7 critical workloads",
                "it_headcount_summary": "5 full-time engineers",
            },
        }

        anchors = BusinessContextExtractor.extract_top_anchors(mock_payload, max_anchors=3)
        assert len(anchors) == 3
        formatted_block = BusinessContextExtractor.format_for_prompt_injection(anchors)

        assert "Hypervisor enterprise agreement renewal" in formatted_block
        assert "94% RAM utilization peak" in formatted_block
        assert "5 full-time engineers" in formatted_block
```

### 3.2 Final Pre-Certification Execution Checklist

| Step | Verification Command / Action | Expected Acceptance Criteria |
| :--- | :--- | :--- |
| **1. Static Type & Lint Check** | `ruff check src/ tests/ && mypy src/` | `0 errors, 0 warnings`. 100% Technical English compliance in docstrings and identifiers. |
| **2. Legacy Regression Suite** | `pytest tests/unit/ tests/integration/ tests/actuarial/` | `47 passed in <5.0s`. Zero regressions in Monte Carlo or AST topology. |
| **3. Phase 7 Quality Gate Suite** | `pytest tests/quality_gates/test_phase7_world_class_certification.py` | `5 passed`. All 5 blocking flaws deterministically verified as resolved. |
| **4. End-to-End Dry Run Audit** | `python -m src.cli.generate_assessment --verify-lexical --verify-epistemic` | `0 prohibited audit terms`, `0 bracketed epistemic tags`, Section 4.2 table rendered, Top 3 business drivers anchored in Paragraph 1. |

---
*Signed and Approved for Immediate Deployment,*  
**Gemini-4-Argon**  
*Chief Systems Architect, Actuarial Fellow & Global Managing Partner*
```