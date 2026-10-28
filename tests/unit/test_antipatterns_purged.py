import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.business_case import BusinessCaseGroundingPolicy
from assessment_engine.infrastructure.policies.ot_perimeter import OTPerimeterPolicy


def test_business_case_policy_preserves_nis2_and_no_forced_dora():
    """Verify that BusinessCaseGroundingPolicy preserves NIS2 and does not force DORA on non-financial clients."""
    graph = EpistemicGraph(client_id="test_pharma_client")
    policy = BusinessCaseGroundingPolicy()

    # Pharma client with NIS2 and GDPR
    payload = {
        "document_meta": {
            "language": "es",
            "regulatory_frameworks": ["NIS2", "GDPR"],
        },
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "health_check_asis": [],
                "projects_todo": [
                    {
                        "name": "Consolidación de Identidades",
                        "tech_objective": "Directorio único corporativo",
                    }
                ],
            }
        ],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    bc = patched["pillars_analysis"][0]["projects_todo"][0]["business_case"]

    # Must retain NIS2 and GDPR, and NOT inject DORA
    assert "NIS2" in bc
    assert "GDPR" in bc
    assert "DORA" not in bc


def test_ot_perimeter_policy_cloud_neutrality():
    """Verify that OTPerimeterPolicy does not hardcode AWS IoT Core when client uses Azure or private cloud."""
    graph = EpistemicGraph(client_id="test_energy_client")
    policy = OTPerimeterPolicy()

    payload = {
        "document_meta": {
            "cloud_provider": "Azure IoT Hub",
        },
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "projects_todo": [
                    {
                        "name": "Integración de Infraestructura SCADA y OT",
                        "deliverables": [],
                    },
                    {
                        "name": "Plataforma de Observabilidad AIOps",
                        "deliverables": [],
                    },
                ],
            }
        ],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    aiops_proj = patched["pillars_analysis"][0]["projects_todo"][1]
    deliverables_text = " ".join(aiops_proj.get("deliverables", []))

    # Must target Azure IoT Hub, NOT AWS IoT Core
    assert "Azure IoT Hub" in deliverables_text
    assert "AWS IoT Core" not in deliverables_text
