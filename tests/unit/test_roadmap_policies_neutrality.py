import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.archimate import ArchiMateDeliverablesPolicy
from assessment_engine.infrastructure.policies.deduplication import DeduplicationPolicy
from assessment_engine.infrastructure.policies.reverse_traceability import ReverseTraceabilityPolicy
from assessment_engine.infrastructure.policies.sequencing import SequencingPolicy


def test_archimate_policy_cloud_neutrality():
    """Verify that ArchiMate deliverables do not force proprietary AWS services (EKS, Control Tower)."""
    graph = EpistemicGraph(client_id="test_azure_client")
    policy = ArchiMateDeliverablesPolicy()

    payload = {
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "projects_todo": [
                    {
                        "name": "Landing Zone Multi-Region",
                        "tech_objective": "landing zone governance",
                        "deliverables": [],
                    },
                    {
                        "name": "Orquestación de Kubernetes Empresarial",
                        "tech_objective": "kubernetes platform",
                        "deliverables": [],
                    },
                ],
            }
        ]
    }

    patched = policy.evaluate_and_patch(graph, payload)
    projs = patched["pillars_analysis"][0]["projects_todo"]
    all_delivs = " ".join(" ".join(p["deliverables"]) for p in projs)

    assert "AWS Control Tower" not in all_delivs
    assert "Módulo Terraform EKS" not in all_delivs
    assert "Framework de Landing Zone" in all_delivs


def test_reverse_traceability_formal_matching():
    """Verify that reverse traceability synthesizes remediation when finding is not mitigated,
    and does not get falsely suppressed by accidental 5-letter common words."""
    graph = EpistemicGraph(client_id="test_trace_client")
    policy = ReverseTraceabilityPolicy()

    payload = {
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "health_check_asis": [
                    {
                        "node_id": "gap_critical_1",
                        "finding": "Inexistencia de copias de seguridad inmutables contra ransomware",
                        "impact": "Pérdida irreversible de datos",
                        "capability": "DATA_PROTECTION",
                    }
                ],
                "projects_todo": [
                    {
                        "node_id": "proj_1",
                        "name": "Evolución de Redes y Conectividad",
                        "tech_objective": "Actualización de switches de acceso",
                        "capability": "NETWORKING",
                    }
                ],
            }
        ]
    }

    patched = policy.evaluate_and_patch(graph, payload)
    projs = patched["pillars_analysis"][0]["projects_todo"]

    # Must synthesize a tactical remediation project for DATA_PROTECTION
    assert len(projs) == 2
    remediation_proj = projs[1]
    assert remediation_proj["mitigates_risk_id"] == "gap_critical_1"
    assert "DATA_PROTECTION" in remediation_proj["name"]
