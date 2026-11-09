---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
last_verified_against: 2026-11-08
applies_to:
- architecture
- domain
- compilers
doc_type: architecture
diataxis: reference
verification_mode: formal
---

# RFC-083: Pillar-Level Epistemic Calibration, Scope Exclusion, and Executive Diagnostic Cards

## 1. Executive Summary

This RFC establishes the definitive architectural doctrine and data model for evaluating technological capabilities across all ten assessment towers. It resolves the fundamental distinction between:
1. **Modernization Debt (CMMI 1.00 / Initial):** Standard industry capabilities that the enterprise currently lacks or performs manually, causing operational friction or systemic fragility.
2. **Out-of-Scope Exclusions (N/A / Non-Applicable):** Technologies or domains genuinely irrelevant to the client's business model, requiring dynamic mathematical weight redistribution across remaining active pillars to strictly maintain $\sum W_i = 100.0\%$.
3. **Epistemic Divergence Tracking:** Systematic recording and reconciliation of **Declared Maturity ($S_{\text{declared}}$)** from client questionnaires against **Calibrated Forensic Maturity ($S_{\text{calibrated}}$)** from technical interviews and evidence vaults.

---

## 2. Theoretical Doctrine: Modernization Gap vs. Scope Exclusion

### 2.1 The Modernization Debt Axiom (CMMI 1.00)
When an enterprise lacks an established industry capability (e.g., container platforms, immutable backup vaults, or automated infrastructure pipelines) that modern peers utilize to maintain agility and operational resilience:
* **The capability MUST NOT be excluded or marked N/A.**
* Excluding an absent capability creates an artificial inflation of domain maturity, concealing technical debt from executive leadership.
* The absence of the capability is scored as **CMMI 1.00 (Initial / Ad-Hoc)**.
* **Economic Justification:** The CMMI 1.00 score directly justifies the target architecture, financial budget, and modernization initiatives defined in Volume 2 (TO-BE Transformation Roadmap).

### 2.2 The Scope Exclusion Axiom (N/A / `is_applicable: false`)
When a technological capability is genuinely alien or inapplicable to an enterprise's organizational typology (e.g., Mainframe legacy operations for a cloud-native SaaS enterprise, or deep industrial OT automation for an asset-light trading firm):
* The pillar is flagged with `"is_applicable": false`.
* **Dynamic Weight Redistribution:** The weight assigned to the excluded pillar ($W_{\text{excluded}}$) is redistributed proportionally across all active pillars in that tower:
  $$W'_k = W_k \times \frac{100.0}{100.0 - W_{\text{excluded}}}$$
  Guaranteeing:
  $$\sum_{k \in \text{active}} W'_k = 100.0\% \quad (\text{with } 0.00\% \text{ rounding drift})$$
* The pillar diagnostic card is replaced with an institutional scope boundary notice detailing the rationale for exclusion.

---

## 3. Data Schema & Architecture

### 3.1 Pillar Diagnostic Entity Schema
Each pillar in `pillars_analysis` is extended with structured epistemic attributes:

```json
{
  "pillar_id": "T2.P2",
  "pillar_name": "Container Platforms & Kubernetes Operations",
  "is_applicable": true,
  "weight_pct": 20.0,
  "recalibrated_weight_pct": 20.0,
  "declared_score": 4.25,
  "calibrated_score": 1.00,
  "divergence": -3.25,
  "divergence_class": "OPERATIONAL_GAP",
  "epistemic_rationale": {
    "questionnaire_assertion": "The client self-assessment indicated governed and versioned cluster operations.",
    "forensic_evidence": "Technical discovery confirmed zero container clusters deployed in production; all development and core workloads reside on legacy monolithic virtual machines.",
    "calibration_justification": "Maturity is calibrated at CMMI 1.00 to reflect the absence of container runtime environments and establish the baseline for Volume 2 modernization."
  },
  "executive_narrative": {
    "operational_reality": "Application deployment at the organization relies entirely on traditional monolithic virtualization across hyperconverged infrastructure.",
    "resilience_gap": "Absence of container orchestration engines prevents elastic scaling and modern microservices decoupling, compounding memory saturation across physical clusters."
  }
}
```

### 3.2 Epistemic Divergence Taxonomy

| Divergence Range ($\Delta = S_{\text{cal}} - S_{\text{dec}}$) | Epistemic Classification | Executive Framing Strategy |
| :--- | :--- | :--- |
| $\mathbf{\Delta = 0.00}$ | **Validated Alignment** | The technical assessment corroborates self-assessment findings with zero operational friction. |
| $\mathbf{-1.00 \le \Delta < 0.00}$ | **Procedural Drift** | Governance frameworks exist in policy documentation but lack continuous verification or automated tooling in daily operations. |
| $\mathbf{\Delta < -1.00}$ | **Operational Divergence** | Strategic decoupling between high-level architectural intent and physical on-premise realities in production environments. |
| $\mathbf{\Delta > 0.00}$ | **Conservative Understatement** | Operational practices in production exceed documented policies, demonstrating unrecorded institutional resilience. |

---

## 4. Visual Delivery: Executive Pillar Diagnostic Cards

Instead of compressing divergent assessments into a narrow 3-column table cell, Chapter 3 of each Specialist Technical Annex will render a high-impact **Pillar Diagnostic Card** for each of the five pillars:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PILAR 2: CONTENEDORES Y PLATAFORMAS KUBERNETES                                         │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────┤
│  Autoevaluación Declarada  │  Madurez Técnica Calibrada  │  Divergencia de Diagnóstico │
│  4,25 / 5,00 (Gestionado)  │  1,00 / 5,00 (Inicial)      │  -3,25 (Brecha Operativa)   │
├────────────────────────────┴─────────────────────────────┴─────────────────────────────┤
│  Realidad Operativa y Base Instalada                                                   │
│  El despliegue de aplicaciones en la organización descansa íntegramente sobre una      │
│  arquitectura de virtualización tradicional monolítica alojada en nodos locales.       │
│                                                                                        │
│  Fundamento de la Calibración y Brecha de Continuidad                                  │
│  Aunque el marco normativo inicial proyectaba procesos gestionados en microservicios, │
│  la auditoría técnica constata la inexistencia de clústeres de contenedores en         │
│  producción. Esta divergencia refleja la brecha habitual entre diseño documental y     │
│  adopción en planta. Por ello, la capacidad se calibra objetivamente en Nivel 1.00     │
│  para justificar la iniciativa de modernización hacia nube híbrida en el Tomo 2.       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Implementation Roadmap

1. **Phase A (Schema & Hydrator Integration):**
   * Update `TowerPayloadHydrator` to parse questionnaire responses, compute `declared_score`, compare against forensic findings, calculate `divergence`, and handle `is_applicable` weight redistributions.
2. **Phase B (AST Word Compiler Enhancement):**
   * Implement `_render_pillar_diagnostic_cards` in `in_memory_asis_compiler.py` and `payload_to_ast.py` using structured `TableNode` components with brand accent styling.
3. **Phase C (Full Verification & Scale Invariance):**
   * Add automated assertions verifying that all 10 towers maintain $\sum W_i = 100.0\%$, all divergences are mathematically signed, and text narratives remain strictly non-accusatory.
