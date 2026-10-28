from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

ARCHIMATE_CATALOG: dict[str, list[str]] = {
    "kubernetes": [
        "Manifiestos Base YAML",
        "Módulo Terraform EKS",
        "Helm Charts de Gobernanza",
        "Pipeline GitLab/GitHub Actions",
    ],
    "eks": [
        "Manifiestos Base YAML",
        "Módulo Terraform EKS",
        "Helm Charts de Gobernanza",
        "Pipeline GitLab/GitHub Actions",
    ],
    "contenedores": [
        "Manifiestos Base YAML",
        "Módulo Terraform EKS",
        "Helm Charts de Gobernanza",
        "Pipeline GitLab/GitHub Actions",
    ],
    "landing zone": [
        "AWS Control Tower Account Factory",
        "Políticas SCP (Service Control Policies)",
        "Módulo Terraform Base Network",
    ],
    "platform engineering": [
        "Catálogo Backstage/IDP",
        "Plantillas de Autoservicio IaC",
        "Framework de SLIs/SLOs",
    ],
    "observabilidad": [
        "Dashboards Grafana/CloudWatch",
        "Reglas de Alertas PromQL",
        "Integración PagerDuty/ServiceNow",
    ],
    "aiops": [
        "Dashboards Grafana/CloudWatch",
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
        "Plantillas AWS Elastic Disaster Recovery",
    ],
    "disaster recovery": [
        "Runbooks de Recuperación",
        "Plan de Pruebas de Failover",
        "Plantillas AWS Elastic Disaster Recovery",
    ],
    "backup": [
        "Políticas de Retención",
        "Bóveda Inmutable",
        "Pruebas de Restauración Automatizadas",
    ],
}


def _resolve_project_deliverables(name: str, tech_obj: str) -> list[str]:
    combined_text = f"{name.lower()} {tech_obj.lower()}"
    matched = set()
    for kw, deliverables in ARCHIMATE_CATALOG.items():
        if kw in combined_text:
            matched.update(deliverables)
    if matched:
        return list(matched)
    return [
        "Documento de Diseño Técnico (HLD/LLD)",
        "Plan de Pruebas y Validation",
    ]


class ArchiMateDeliverablesPolicy(BaseSovereignPolicy):
    """Populates or replaces generic deliverables with concrete ArchiMate technical deliverables."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replaces generic or missing project deliverables with catalog-based items."""
        pillars = payload.get("pillars_analysis", [])
        for p in pillars:
            for proj in p.get("projects_todo", []):
                curr = proj.get("deliverables", [])
                is_generic = not curr or any("diseño de arquitectura" in d.lower() for d in curr)
                if is_generic:
                    proj["deliverables"] = _resolve_project_deliverables(
                        proj.get("name", ""), proj.get("tech_objective", "")
                    )
        return payload
