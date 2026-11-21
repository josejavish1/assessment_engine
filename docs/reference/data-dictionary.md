---
status: Verified
owner: docs-governance
source_of_truth:
- engine_config/governance_scales.json
- src/assessment_engine/domain/actuarial/schemas.py
- src/assessment_engine/domain/schemas/blueprint.py
- src/assessment_engine/domain/maturity_band.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical data dictionary and ontological glossary defining actuarial metrics, CMMI scales, and governance concepts.
---
# Canonical Data Dictionary & Ontological Glossary

Canonical reference specification establishing unified, mathematical definitions for all actuarial metrics, CMMI maturity scales, risk scoring variables, and regulatory terminology used across `assessment-engine`.

---

## 1. Actuarial Risk Modeling Metrics (FAIR & TCO)

Defined in `src/assessment_engine/domain/actuarial/schemas.py` and computed via `bayesian_fair_copula_engine.py`:

| Term | Full Name | Mathematical / Operational Definition | Invariant Range |
|---|---|---|:---:|
| **TEF** | Threat Event Frequency | The estimated frequency with which a threat agent attempts to exploit an asset vulnerability within a given period. Modeled as a Poisson process updated via conjugate Gamma distribution ($\Gamma(\alpha, \beta)$). | Events / Year ($\ge 0.0$) |
| **VULN** | Vulnerability | The probability that a threat event succeeds against existing operational defenses. Modeled via conjugate Beta distribution ($\text{Beta}(\alpha, \beta)$) conditioned on evidence. | Probability $[0.0, 1.0]$ |
| **LEF** | Loss Event Frequency | The frequency at which loss events actually occur: $\text{LEF} = \text{TEF} \times \text{VULN}$. | Events / Year ($\ge 0.0$) |
| **SLE** | Single Loss Expectancy | The estimated monetary loss incurred from a single incident: $\text{SLE} = \text{Asset Value} \times \text{Exposure Factor}$. | Currency ($\ge 0.0$) |
| **ALE** | Annualized Loss Expectancy | The mean statistical loss expected per year: $\text{ALE} = \text{LEF} \times \text{SLE}$. Calculated across 10,000 Monte Carlo runs. | Currency / Year ($\ge 0.0$) |
| **VaR (P90)** | Value at Risk (90th Percentile) | The loss threshold that will not be exceeded with 90% statistical confidence over a 1-year horizon. Represents extreme operational risk. | Currency ($\ge 0.0$) |
| **CVaR (90)** | Conditional Value at Risk | The expected monetary loss given that the loss event exceeds the 90th percentile threshold (expected tail loss). | Currency ($\ge 0.0$) |
| **COI** | Cost of Inaction | Cumulative operational and financial losses projected across a 3-year horizon if identified technical gaps remain unmitigated. | Currency ($\ge 0.0$) |
| **TCO** | Total Cost of Ownership | Complete financial projection combining infrastructure licensing, depreciation, hardware maintenance, and workforce labor. | Currency ($\ge 0.0$) |

---

## 2. Governance & Capability Maturity Scales (CMMI)

Governed by `engine_config/governance_scales.json` and resolved dynamically via `maturity_band.py`:

| Level | Rating Range | Canonical Maturity Band | Operational Definition |
|:---:|:---:|---|---|
| **1** | $[1.00, 1.80)$ | **Initial** | Ad-hoc, chaotic processes; unpredictable velocity; zero formal automation. |
| **2** | $[1.80, 2.60)$ | **Managed** | Documented project-level discipline; localized scripting; reactive maintenance. |
| **3** | $[2.60, 3.40)$ | **Defined** | Standardized enterprise-wide engineering processes; continuous integration active. |
| **4** | $[3.40, 4.20)$ | **Quantitatively Managed** | Data-driven process control; automated telemetry, SRE SLOs, and quality gates. |
| **5** | $[4.20, 5.00]$ | **Optimizing** | Continuous self-healing automation, automated canary rollouts, and active learning. |

---

## 3. Technology Tower Identifiers

Canonical codes mapping technical capabilities to specialized assessment workflows:

| Tower ID | Technology Domain Name | Core Evaluated Architecture |
|:---:|---|---|
| **T1** | Data Center & Physical Infrastructure | Tier III/IV facilities, power redundancy, HVAC cooling loops, physical security. |
| **T2** | Hybrid Cloud & Compute | Virtualization clusters, public cloud tenants (AWS/Azure/GCP), container fleets. |
| **T3** | Core Networks & Connectivity | Routing, SD-WAN topologies, perimeter firewalls, campus switching, zero trust. |
| **T4** | Data Platforms & Storage | Storage Area Networks (SAN/NAS), data lakes, backup retention, disaster recovery. |
| **T5** | Cyber Security Operations (SOC) | SIEM/SOAR integration, EDR fleets, incident response playbooks, threat intelligence. |
| **T6** | Database Systems & Engines | RDBMS/NoSQL databases, replication topology, query performance, DB lifecycle. |
| **T7** | ITSM & Digital Workplace | ServiceNow workflows, service desk SLAs, endpoint management fleets. |
| **T8** | Application Architecture | Microservices, API gateways, message queues, software delivery lifecycle (SDLC). |
| **T9** | Observability & SRE | Telemetry aggregation (metrics, logs, traces), synthetic monitoring, alerting thresholds. |
| **T10** | Enterprise Governance & Strategy | IT steering committees, architecture review boards (ARB), vendor procurement. |

---

## 4. Regulatory Framework Taxonomy

Standards ingested by the RAGE empirical benchmarking engine (`agentic_benchmarker.py`):

| Regulatory Code | Full Standard Title | Jurisdiction / Mandate |
|---|---|---|
| **ENS (Alta)** | Esquema Nacional de Seguridad (Categoría Alta) | Spanish national cybersecurity certification for essential public and private services. |
| **DORA** | Digital Operational Resilience Act | European Union regulation mandating ICT risk management for financial institutions. |
| **NIS2** | Network and Information Security Directive 2 | European Union cybersecurity directive enforcing supply chain security and OT data diodes. |
| **ISO 27001** | Information Security Management Systems | International benchmark for enterprise information security controls. |
| **CMMI** | Capability Maturity Model Integration | Process improvement and capability evaluation model. |

---

## 5. Architectural Invariants for AI Agents

1. **Monistic Terminology:** Agents must use the exact canonical acronyms and bands defined in this dictionary. Inventing non-standard maturity levels (e.g., "Intermediate", "Advanced") is prohibited.
2. **Numeric Score Bounds:** All calculated maturity ratings must strictly evaluate within $[1.0, 5.0]$.
3. **Currency Localization:** Currency figures must reflect the client's declared ISO-4217 currency code in `enterprise_registry.json`.
