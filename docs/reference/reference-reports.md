---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
last_verified_against: 2026-11-12
applies_to:
- humans
- ai-agents
doc_type: reference_generated
diataxis: reference
verification_mode: editorial
notes: Historical executive deliverable benchmark reference (FNMT-CERES structure).
---
# Executive Deliverable Reference Architecture

This reference catalog documents the benchmark deliverable structure established in historical enterprise assessments (FNMT-CERES baseline). It serves as the editorial, structural, and typographic benchmark for OpenXML (`.docx`) document compilers.

---

## 1. Document Suite Hierarchy

The canonical enterprise assessment delivery suite is structured into two executive volumes supported by domain-specific specialist annexes:

### Executive Strategic Volumes
1. **Consolidated AS-IS Diagnostic Report (Volume 1):**
   - Transversal executive summary, global maturity radar scorecard, multi-tower findings synthesis, and actuarial risk quantification.
   - Reference cover typography: sober corporate layout, formal metadata block, and strict monochrome framing.
2. **Consolidated TO-BE Strategic Roadmap (Volume 2):**
   - Target architecture state, strategic migration work packages, investment horizons (TCO), and implementation sequencing.

### Technical Specialist Annexes (Domain Deep-Dives)
- **Annex A (Facilities & Data Center):** Physical infrastructure, energy distribution, redundancy (Tier-III/IV), and environmental controls.
- **Annex B (Energy & HVAC):** Thermal dissipation, PUE telemetry, cooling loops, and electrical failover infrastructure.
- **Annex C (Compute & Hybrid Cloud):** Hypervisors, virtualization clusters, private cloud platforms, and operating system fleets.
- **Annex D (Data Platforms & Storage):** SAN/NAS arrays, backup retention policies, immutable snapshots, and replication topology.
- **Annex E (Networks & Perimeter Security):** Core routing, WAN/SD-WAN, segmentation, firewalls, and perimeter defense.
- **Annex F (Database Systems):** RDBMS/NoSQL clusters, replication consistency, licensing, and database maintenance lifecycle.
- **Annex G (ITSM & Observability):** IT service management, incident workflows, SRE monitoring, and telemetry collection.

---

## 2. Local Asset Preservation

In accordance with Tier-1 repository hygiene policies, heavy historical binary PDFs (7.6 MB) are excluded from Git to prevent repository bloat. Complete reference PDFs are preserved locally for inspection:

```
working/reference_reports/
├── fnmt_ceres_as_is_consolidated_report_v1.1.pdf
├── fnmt_ceres_to_be_consolidated_report_v1.1.pdf
├── fnmt_ceres_to_do_consolidated_report_v1.1.pdf
└── anexos_as_is/
    ├── anexo_a_cpd_v1.2.pdf
    ├── anexo_b_energia_refrigeracion_v1.1.pdf
    ├── anexo_c_virtualizacion_v1.1.pdf
    ├── anexo_d_almacenamiento_backup_v1.1.pdf
    ├── anexo_e_comunicaciones_seguridad_v1.1.pdf
    ├── anexo_f_bases_datos_v1.1.pdf
    └── anexo_g_monitorizacion_operaciones_v1.1.pdf
```
