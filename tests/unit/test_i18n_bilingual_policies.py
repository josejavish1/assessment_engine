import pytest

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.archimate import ArchiMateDeliverablesPolicy
from assessment_engine.infrastructure.policies.fair_risk import FairRiskPolicy
from assessment_engine.infrastructure.policies.reverse_traceability import ReverseTraceabilityPolicy


def test_fair_risk_bilingual_audit_justification():
    """Verify that FairRiskPolicy formats audit_justification in English when language is 'en' and uses client currency."""
    graph = EpistemicGraph(client_id="test_us_client")
    policy = FairRiskPolicy()

    payload = {
        "document_meta": {
            "client_name": "US Tech Corp",
            "language": "en",
            "currency_symbol": "$",
            "tower_code": "T2",
            "tower_name": "Compute & Platforms",
        },
        "pillars_analysis": [
            {
                "pilar_id": "T2.P1",
                "score": 3.0,
                "health_check_asis": [
                    {
                        "node_id": "f_1",
                        "finding": "High latency in automated container deployment",
                        "impact": "Productivity friction",
                        "severity": "Medium",
                    }
                ],
            }
        ],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    finding = patched["pillars_analysis"][0]["health_check_asis"][0]

    justification = finding.get("audit_justification", "")
    assert "Estimated primary accounting loss" in justification
    assert "$" in justification
    assert "Pérdida primaria" not in justification


def test_reverse_traceability_bilingual_remediation():
    """Verify that ReverseTraceabilityPolicy synthesizes English remediation projects when language is 'en'."""
    graph = EpistemicGraph(client_id="test_uk_client")
    policy = ReverseTraceabilityPolicy()

    payload = {
        "document_meta": {
            "language": "en",
        },
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "health_check_asis": [
                    {
                        "node_id": "gap_en_1",
                        "finding": "Absence of immutable backup copies against ransomware attacks",
                        "impact": "Data loss risk",
                        "capability": "DATA_RESILIENCE",
                    }
                ],
                "projects_todo": [],
            }
        ],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    proj = patched["pillars_analysis"][0]["projects_todo"][0]

    assert "Tactical Remediation Program: DATA_RESILIENCE" in proj["name"]
    assert "H1 (Months 1-3)" in proj["duration"]
    assert "Remediation Plan" in proj["deliverables"]


def test_archimate_bilingual_deliverables():
    """Verify that ArchiMate deliverables populate in English when language is 'en'."""
    graph = EpistemicGraph(client_id="test_global_client")
    policy = ArchiMateDeliverablesPolicy()

    payload = {
        "document_meta": {
            "language": "en",
        },
        "pillars_analysis": [
            {
                "pilar_id": "T1.P1",
                "projects_todo": [
                    {
                        "name": "Enterprise Kubernetes Platform Deployment",
                        "tech_objective": "kubernetes orchestration",
                        "deliverables": [],
                    }
                ],
            }
        ],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    delivs = patched["pillars_analysis"][0]["projects_todo"][0]["deliverables"]

    assert "Base YAML Manifests" in delivs
    assert "Container Orchestration IaC Module" in delivs
