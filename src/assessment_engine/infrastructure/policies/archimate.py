from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

ARCHIMATE_CATALOG_ES: dict[str, list[str]] = {
    "kubernetes": [
        "Manifiestos Base YAML",
        "Módulo Terraform de Orquestación de Contenedores",
        "Helm Charts de Gobernanza",
        "Pipeline GitLab/GitHub Actions",
    ],
    "eks": [
        "Manifiestos Base YAML",
        "Módulo Terraform de Clúster Gestionado",
        "Helm Charts de Gobernanza",
        "Pipeline GitLab/GitHub Actions",
    ],
    "contenedores": [
        "Manifiestos Base YAML",
        "Módulo Terraform de Orquestación de Contenedores",
        "Helm Charts de Gobernanza",
        "Pipeline GitLab/GitHub Actions",
    ],
    "landing zone": [
        "Framework de Landing Zone y Jerarquía Multi-Cuenta",
        "Políticas de Gobernanza y Guardrails Automatizados",
        "Módulo Terraform Base Network",
    ],
    "platform engineering": [
        "Catálogo Backstage/IDP",
        "Plantillas de Autoservicio IaC",
        "Framework de SLIs/SLOs",
    ],
    "observabilidad": [
        "Dashboards Unificados de Métricas y Trazas",
        "Reglas de Alertas PromQL",
        "Integración PagerDuty/ServiceNow",
    ],
    "aiops": [
        "Dashboards Unificados de Métricas y Trazas",
        "Modelos de Detección de Anomalías",
        "Integración ITSM",
    ],
    "scada": [
        "Topología de Red Purdue",
        "Reglas de Firewall Perimetral",
        "Diodo de Datos Unidireccional",
    ],
    "automatización": [
        "Playbooks Ansible",
        "Módulos Terraform",
        "Pipelines CI/CD",
    ],
    "iac": [
        "Módulos Terraform",
        "Repositorio GitOps",
        "Políticas OPA/Sentinel",
    ],
    "dr": [
        "Runbooks de Recuperación",
        "Plan de Pruebas de Failover",
        "Plantillas de Replicación y Automatización de Failover",
    ],
    "disaster recovery": [
        "Runbooks de Recuperación",
        "Plan de Pruebas de Failover",
        "Plantillas de Replicación y Automatización de Failover",
    ],
    "backup": [
        "Políticas de Retención",
        "Bóveda Inmutable",
        "Pruebas de Restauración Automatizadas",
    ],
}

ARCHIMATE_CATALOG_EN: dict[str, list[str]] = {
    "kubernetes": [
        "Base YAML Manifests",
        "Container Orchestration IaC Module",
        "Governance Helm Charts",
        "GitLab/GitHub Actions CI/CD Pipeline",
    ],
    "eks": [
        "Base YAML Manifests",
        "Managed Cluster IaC Module",
        "Governance Helm Charts",
        "CI/CD Pipeline",
    ],
    "container": [
        "Base YAML Manifests",
        "Container Orchestration IaC Module",
        "Governance Helm Charts",
        "CI/CD Pipeline",
    ],
    "landing zone": [
        "Multi-Account Landing Zone Hierarchy Framework",
        "Automated Governance Policies and Guardrails",
        "Base Network Terraform Module",
    ],
    "platform engineering": [
        "Internal Developer Portal (IDP) Service Catalog",
        "Self-Service IaC Templates",
        "SLI/SLO Framework",
    ],
    "observability": [
        "Unified Metrics & Tracing Dashboards",
        "PromQL Alerting Rules",
        "PagerDuty/ServiceNow Incident Integration",
    ],
    "aiops": [
        "Unified Observability Dashboards",
        "Anomaly Detection Models",
        "ITSM Integration",
    ],
    "scada": [
        "Purdue Network Architecture Blueprint",
        "Perimeter Firewall Policies",
        "Unidirectional Data Diode Implementation",
    ],
    "automation": [
        "Ansible Automation Playbooks",
        "Terraform Infrastructure Modules",
        "CI/CD Pipelines",
    ],
    "iac": [
        "Terraform Modules",
        "GitOps Repository Setup",
        "OPA/Sentinel Governance Policies",
    ],
    "dr": [
        "Disaster Recovery Runbooks",
        "Automated Failover Test Plan",
        "Replication & Failover Templates",
    ],
    "disaster recovery": [
        "Disaster Recovery Runbooks",
        "Automated Failover Test Plan",
        "Replication & Failover Templates",
    ],
    "backup": [
        "Retention Policies",
        "Immutable Backup Vault",
        "Automated Restoration Testing Suite",
    ],
}

# Backward compatibility alias
ARCHIMATE_CATALOG = ARCHIMATE_CATALOG_ES


def _resolve_project_deliverables(
    name: str, tech_obj: str, doc_lang: str = "es"
) -> list[str]:
    combined_text = f"{name.lower()} {tech_obj.lower()}"
    matched = set()
    catalog = (
        ARCHIMATE_CATALOG_EN if doc_lang == "en" else ARCHIMATE_CATALOG_ES
    )

    for kw, deliverables in catalog.items():
        if kw in combined_text:
            matched.update(deliverables)

    # Cross-match with the alternate catalog if no primary matches were found
    if not matched:
        alt_catalog = (
            ARCHIMATE_CATALOG_ES if doc_lang == "en" else ARCHIMATE_CATALOG_EN
        )
        for kw, deliverables in alt_catalog.items():
            if kw in combined_text:
                matched.update(deliverables)

    if matched:
        return list(matched)

    if doc_lang == "en":
        return [
            "Technical Architecture Design (HLD/LLD)",
            "Testing and Validation Plan",
        ]
    return [
        "Documento de Diseño Técnico (HLD/LLD)",
        "Plan de Pruebas y Validación",
    ]


class ArchiMateDeliverablesPolicy(BaseSovereignPolicy):
    """Populates or replaces generic deliverables with concrete ArchiMate technical deliverables."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replaces generic or missing project deliverables with catalog-based items."""
        pillars = payload.get("pillars_analysis", [])
        doc_lang = str(
            payload.get("document_meta", {}).get("language", "es")
        ).lower()

        for p in pillars:
            for proj in p.get("projects_todo", []):
                curr = proj.get("deliverables", [])
                is_generic = (
                    not curr
                    or any("diseño de arquitectura" in d.lower() for d in curr)
                    or any("architecture design" in d.lower() for d in curr)
                )
                if is_generic:
                    proj["deliverables"] = _resolve_project_deliverables(
                        proj.get("name", ""),
                        proj.get("tech_objective", ""),
                        doc_lang=doc_lang,
                    )
        return payload
