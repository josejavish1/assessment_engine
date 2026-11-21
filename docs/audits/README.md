---
status: Verified
owner: docs-governance
source_of_truth:
- docs/audits/audit-framework.md
- src/assessment_engine/application/cli.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: reference
verification_mode: editorial
notes: Canonical index and operational routing for the audit framework, automated probes, and certification deliverables.
---
# Audits & Forensic Telemetry Index

Canonical operational index documenting the multidimensional audit framework, automated diagnostic probes, and generated compliance deliverables across `assessment-engine`.

---

## 1. Audit Framework Routing Matrix

| Specification Entrypoint | Operational Role | Primary Probes & Scope | Command / Tool |
|---|---|---|---|
| [`audit-framework.md`](audit-framework.md) | Multidimensional Quality Engine | 21 Automated Probes: SAST, DAST, mutation testing, SBOM, AST complexity, FinOps, and prompt safety | `python -m assessment_engine.application.cli audit` |

---

## 2. Generated Due Diligence Artifacts

When `cli audit` executes, the following machine-readable and executive artifacts serialize into this directory:
- `AUDIT_REPORT.json`: Machine-readable diagnostic telemetry across all 21 evaluated probes.
- `AUDIT_CERTIFICATE.html`: Formal executive compliance certificate for CTOs and due diligence auditors.
- `SBOM_CYCLONEDX.json`: Software Bill of Materials tracking 100% of production dependencies and zero CVEs.
