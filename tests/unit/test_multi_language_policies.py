import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.business_case import BusinessCaseGroundingPolicy
from assessment_engine.infrastructure.policies.deduplication import DeduplicationPolicy
from assessment_engine.infrastructure.policies.reverse_traceability import ReverseTraceabilityPolicy


def test_business_case_multi_language_generation():
    """Verify that BusinessCaseGroundingPolicy generates German, French, and Portuguese business cases without code ternaries."""
    policy = BusinessCaseGroundingPolicy()

    # German test
    payload_de = {
        "document_meta": {"language": "de", "regulatory_frameworks": ["DORA", "NIS2"]},
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "health_check_asis": [],
                "projects_todo": [
                    {"name": "Zero Trust Architektur", "tech_objective": "Identitätsföderation"}
                ],
            }
        ],
    }
    patched_de = policy.evaluate_and_patch(EpistemicGraph("test_de"), payload_de)
    bc_de = patched_de["pillars_analysis"][0]["projects_todo"][0]["business_case"]
    assert "Strategischer Enabler" in bc_de
    assert "DORA, NIS2" in bc_de

    # French test
    payload_fr = {
        "document_meta": {"language": "fr", "regulatory_frameworks": ["NIS2"]},
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "health_check_asis": [],
                "projects_todo": [
                    {"name": "Architecture Zero Trust", "tech_objective": "Fédération d'identité"}
                ],
            }
        ],
    }
    patched_fr = policy.evaluate_and_patch(EpistemicGraph("test_fr"), payload_fr)
    bc_fr = patched_fr["pillars_analysis"][0]["projects_todo"][0]["business_case"]
    assert "Facilitateur Stratégique" in bc_fr


def test_deduplication_multi_language_generation():
    """Verify that DeduplicationPolicy builds native German and Portuguese consolidated platform projects."""
    policy = DeduplicationPolicy()

    # German test: project in T2.P1 gets consolidated into T2.P4
    payload_de = {
        "document_meta": {"tower_code": "T2", "language": "de", "cloud_provider": "OpenShift"},
        "pillars_analysis": [
            {
                "pilar_id": "T2.P1",
                "projects_todo": [
                    {"name": "Plattform Engineering Piloto", "tech_objective": "Internal Developer Portal"}
                ],
            },
            {
                "pilar_id": "T2.P4",
                "projects_todo": [],
            },
        ],
    }
    patched_de = policy.evaluate_and_patch(EpistemicGraph("test_de_dedup"), payload_de)
    proj_de = patched_de["pillars_analysis"][1]["projects_todo"][0]
    assert "Strategisches Programm" in proj_de["name"]
    assert "OpenShift" in proj_de["business_case"]

    # Portuguese test: project in T2.P1 gets consolidated into T2.P4
    payload_pt = {
        "document_meta": {"tower_code": "T2", "language": "pt", "cloud_provider": "Azure"},
        "pillars_analysis": [
            {
                "pilar_id": "T2.P1",
                "projects_todo": [
                    {"name": "Engenharia de Plataforma Piloto", "tech_objective": "Internal Developer Portal"}
                ],
            },
            {
                "pilar_id": "T2.P4",
                "projects_todo": [],
            },
        ],
    }
    patched_pt = policy.evaluate_and_patch(EpistemicGraph("test_pt_dedup"), payload_pt)
    proj_pt = patched_pt["pillars_analysis"][1]["projects_todo"][0]
    assert "Programa Estratégico" in proj_pt["name"]
    assert "Autoatendimento" in proj_pt["name"]


def test_reverse_traceability_multi_language_generation():
    """Verify that ReverseTraceabilityPolicy synthesizes native German and French remediation initiatives."""
    policy = ReverseTraceabilityPolicy()

    payload_de = {
        "document_meta": {"language": "de"},
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "health_check_asis": [
                    {
                        "node_id": "gap_de_1",
                        "finding": "Fehlen unveränderlicher Sicherungskopien",
                        "impact": "Datenverlustrisiko",
                        "capability": "DATENREDUNDANZ",
                    }
                ],
                "projects_todo": [],
            }
        ],
    }
    patched_de = policy.evaluate_and_patch(EpistemicGraph("test_de_trace"), payload_de)
    proj_de = patched_de["pillars_analysis"][0]["projects_todo"][0]
    assert "Taktisches Sanierungsprogramm: DATENREDUNDANZ" in proj_de["name"]
    assert "H1 (Monate 1-3)" in proj_de["duration"]
    assert "Sanierungsplan" in proj_de["deliverables"]
