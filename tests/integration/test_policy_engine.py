import os
import shutil
from pathlib import Path

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policy_engine import SovereignPolicyEngine


def test_sovereign_policy_engine_compilation():
    os.environ["ASSESSMENT_CLIENT_ID"] = "redeia_v3"

    # 1. Initialize a temporary graph in memory
    # --- ARRANGE ---
    try:
        graph = EpistemicGraph(client_id="test_client")

        # 2. Setup a dummy blueprint payload representing Tower 2 with incoherencies
        payload = {
            "document_meta": {
                "client_name": "REDEIA",
                "tower_code": "T2",
                "tower_name": "Hybrid Compute & Platforms",
            },
            "pillars_analysis": [
                {
                    "pilar_id": "T2.P1",
                    "pilar_name": "Compute Foundation & Virtualization",
                    "projects_todo": [
                        {
                            "name": "Unificación de Cómputo con Platform Engineering",
                            "tech_objective": "Habilitar platform engineering para el cómputo principal.",
                            "deliverables": ["Design base"],
                            "duration": "Horizonte 2 (Mes 6-12)",
                        },
                        {
                            "name": "Aislamiento y Contención de SCADA/OT",
                            "tech_objective": "Aislar la red crítica de transporte eléctrico SCADA.",
                            "deliverables": ["Firewall de red"],
                            "duration": "Horizonte 1 (Mes 1-6)",
                        },
                    ],
                },
                {
                    "pilar_id": "T2.P2",
                    "pilar_name": "Container Platform",
                    "projects_todo": [
                        {
                            "name": "Piloto de Kubernetes en AWS",
                            "tech_objective": "Desplegar el piloto.",
                            "deliverables": ["Piloto"],
                            "duration": "Horizonte 1 (Mes 1-6)",
                        },
                        {
                            "name": "Plan de Adopción de Plataforma de Contenedores",
                            "tech_objective": "Diseñar la política.",
                            "deliverables": ["Política"],
                            "duration": "Horizonte 1 (Mes 1-6)",
                        },
                    ],
                },
                {
                    "pilar_id": "T2.P4",
                    "pilar_name": "Automation & Self-Service",
                    "projects_todo": [],
                },
                {
                    "pilar_id": "T2.P5",
                    "pilar_name": "Platform Operations & Observability",
                    "projects_todo": [
                        {
                            "name": "Implantación de Observabilidad Predictiva con AIOps",
                            "tech_objective": "Extraer logs y telemetría de todos los entornos híbridos e industriales OT.",
                            "deliverables": ["AIOps dashboard"],
                            "duration": "Horizonte 2 (Mes 6-12)",
                        }
                    ],
                },
            ],
        }

        # 3. Instantiate the Policy Engine
        engine = SovereignPolicyEngine(graph)

        # 4. Compile the payload (executes all registered policies)
        # --- ACT ---
        compiled_payload = engine.compile(payload)

        # --- TESTING POLICY 1: DEDUPLICATION ---
        # The duplicate "Platform Engineering" project under T2.P1 should be removed,
        # and a consolidated master project should be injected into T2.P4.
        p4 = next(
            p for p in compiled_payload["pillars_analysis"] if p["pilar_id"] == "T2.P4"
        )
        assert len(p4["projects_todo"]) == 1
        assert "Platform Engineering" in p4["projects_todo"][0]["name"]

        p1 = next(
            p for p in compiled_payload["pillars_analysis"] if p["pilar_id"] == "T2.P1"
        )
        # Verify that the redundant compute platform project was removed, leaving only SCADA
        assert len(p1["projects_todo"]) == 1
        assert "SCADA" in p1["projects_todo"][0]["name"]

        # --- TESTING POLICY 2: SEQUENCING ---
        # The Container Adoption Plan should be scheduled in H1 (Mes 1-2),
        # while Kubernetes pilots should be pushed to H2.
        p2 = next(
            p for p in compiled_payload["pillars_analysis"] if p["pilar_id"] == "T2.P2"
        )
        adoption_plan = next(
            proj
            for proj in p2["projects_todo"]
            if "Adopción de Plataforma" in proj["name"]
        )
        k8s_pilot = next(
            proj for proj in p2["projects_todo"] if "Piloto" in proj["name"]
        )

        assert "Fase de Arranque (Mes 1-2)" in adoption_plan["duration"]
        assert "Horizonte 2" in k8s_pilot["duration"]

        # --- TESTING POLICY 3: OT PERIMETER SAFEGARD ---
        # Since there's a SCADA project in P1 and an Observability/AIOps project in P5,
        # the Hardware Data Diode deliverable must be injected in both.
        scada_project = p1["projects_todo"][0]
        p5 = next(
            p for p in compiled_payload["pillars_analysis"] if p["pilar_id"] == "T2.P5"
        )
        aiops_project = p5["projects_todo"][0]

        assert any("Diodo de Datos" in d for d in scada_project["deliverables"])
        assert any("Diodo de Datos" in d for d in aiops_project["deliverables"])
        assert "diodo" in scada_project["tech_objective"].lower()
        assert "diodo" in aiops_project["tech_objective"].lower()

        print("✅ All Sovereign Policies compiled and validated perfectly!")
    finally:
        test_client_path = Path("working/test_client")
        if test_client_path.exists():
            shutil.rmtree(test_client_path)


def test_sovereign_policy_engine_fallback_recovery():
    """Verify that SovereignPolicyEngine degrades gracefully if configuration loading fails."""
    from unittest.mock import patch
    
    # Arrange - Patch load_policy_file to raise an Exception
    with patch("assessment_engine.infrastructure.config_loader.load_policy_file") as mock_load:
        mock_load.side_effect = Exception("Malformed risk profiles JSON")
        
        graph = EpistemicGraph(client_id="test_client_fallback")
        engine = SovereignPolicyEngine(graph)
        
        payload = {
            "document_meta": {
                "client_name": "REDEIA",
                "tower_code": "T2",
                "tower_name": "Hybrid Compute & Platforms",
            },
            "pillars_analysis": []
        }
        
        # Act - This call should NOT crash and should degrade gracefully to empty profiles
        try:
            compiled = engine.compile(payload)
            # Assert - The compilation completes successfully
            assert "document_meta" in compiled
        finally:
            fallback_client_path = Path("working/test_client_fallback")
            if fallback_client_path.exists():
                shutil.rmtree(fallback_client_path)


def test_sovereign_policy_engine_ofair_heuristics():
    """Verify that SovereignPolicyEngine correctly applies O-FAIR risk heuristics and Monte Carlo simulation."""
    # 1. --- ARRANGE ---
    # Setup graph and payload with specific qualitative threat & vulnerability text
    graph = EpistemicGraph(client_id="test_client_ofair")
    engine = SovereignPolicyEngine(graph)
    
    payload = {
        "document_meta": {
            "client_name": "REDEIA",
            "tower_code": "T2",
            "tower_name": "Hybrid Compute & Platforms",
        },
        "pillars_analysis": [
            {
                "pilar_id": "T2.P1",
                "pilar_name": "Compute Foundation",
                "projects_todo": [],
                "health_check_asis": [
                    {
                        "finding": "Infiltración por Ransomware en la red pública de internet",
                        "impact": "Vulnerabilidad crítica sin parchear expone los perfiles de control ante sanción de directiva NIS2"
                    }
                ]
            }
        ]
    }
    
    # 2. --- ACT ---
    try:
        compiled = engine.compile(payload)
        
        # 3. --- ASSERT ---
        pillar = compiled["pillars_analysis"][0]
        finding = pillar["health_check_asis"][0]
        
        # Assert that the O-FAIR heuristics correctly elevated TEF and Vuln scores
        assert finding["threat_event_frequency"] == 5, "Expected elevated TEF due to 'ransomware/internet' keyword."
        assert finding["loss_magnitude"] == 4, "Expected high loss magnitude mapping for critical findings."
        
        # Verify that the Monte Carlo simulation generated statistical convergence values
        assert finding["fair_ale_score"] > 0.0, "Expected computed annualized loss exposure value."
        assert finding["fair_p90_score"] >= finding["fair_ale_score"], "P90 maximum exposure must be greater than or equal to the mean ALE."
        assert finding["fair_max_score"] > finding["fair_min_score"], "Max exposure range must exceed min exposure."
    finally:
        test_client_path = Path("working/test_client_ofair")
        if test_client_path.exists():
            shutil.rmtree(test_client_path)
