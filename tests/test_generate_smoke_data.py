from __future__ import annotations

import json

from assessment_engine.scripts.tools.generate_smoke_data import generate_smoke_inputs


def test_generate_smoke_inputs_writes_vodafone_public_dossier(tmp_path) -> None:
    for tower_id in ("T2", "T3", "T5"):
        tower_dir = tmp_path / "engine_config" / "towers" / tower_id
        tower_dir.mkdir(parents=True)
        (tower_dir / f"tower_definition_{tower_id}.json").write_text(
            json.dumps(
                {
                    "pillars": [
                        {
                            "kpis": [
                                {"kpi_id": f"{tower_id}.P1.K1"},
                                {"kpi_id": f"{tower_id}.P1.K2"},
                            ]
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    context_path, responses_path = generate_smoke_inputs(
        client="vodafone_demo",
        towers=["T2", "T3", "T5"],
        seed=42,
        scenario="vodafone-public",
        root=tmp_path,
        write_files=True,
    )

    dossier_path = tmp_path / "working" / "vodafone_demo" / "client_intelligence.json"

    assert context_path == tmp_path / "working" / "vodafone_demo" / "context.txt"
    assert responses_path == tmp_path / "working" / "vodafone_demo" / "responses.txt"
    assert "Vodafone" in context_path.read_text(encoding="utf-8")
    assert dossier_path.exists()

    dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    assert dossier["version"] == "3.0"
    assert dossier["client_name"] == "vodafone_demo"
    assert dossier["profile"]["industry"] == "Telecomunicaciones"
    assert dossier["profile"]["priority_markets"] == [
        "Alemania",
        "Reino Unido",
        "España",
        "Italia",
    ]
    assert "B2B digital" in dossier["profile"]["business_lines"]
    assert dossier["technology_context"]["vendor_dependencies"]
    assert dossier["technology_context"]["recent_incident_signals"]
    assert dossier["tower_overrides"]["T2"]["target_maturity"] == 3.9
    assert dossier["tower_overrides"]["T3"]["target_maturity"] == 3.8
    assert dossier["tower_overrides"]["T5"]["target_maturity"] == 3.7
    assert len(dossier["claims"]) >= 6
    assert any(claim["claim_type"] == "scenario" for claim in dossier["claims"])
    assert any(
        source["source_type"] == "synthetic"
        for claim in dossier["claims"]
        for source in claim["sources"]
    )
    assert dossier["tower_overrides"]["T5"]["related_claim_ids"]

    responses = responses_path.read_text(encoding="utf-8")
    assert "T2." in responses
    assert "T3." in responses
    assert "T5." in responses


def test_generate_smoke_inputs_removes_stale_dossier_for_baseline(tmp_path) -> None:
    for tower_id in ("T2", "T3", "T5"):
        tower_dir = tmp_path / "engine_config" / "towers" / tower_id
        tower_dir.mkdir(parents=True)
        (tower_dir / f"tower_definition_{tower_id}.json").write_text(
            json.dumps(
                {
                    "pillars": [
                        {
                            "kpis": [
                                {"kpi_id": f"{tower_id}.P1.K1"},
                                {"kpi_id": f"{tower_id}.P1.K2"},
                            ]
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

    client_dir = tmp_path / "working" / "smoke_ivirma"
    client_dir.mkdir(parents=True)
    dossier_path = client_dir / "client_intelligence.json"
    dossier_path.write_text('{"stale": true}\n', encoding="utf-8")

    generate_smoke_inputs(
        client="smoke_ivirma",
        towers=["T2", "T3", "T5"],
        seed=42,
        scenario="baseline",
        root=tmp_path,
        write_files=True,
    )

    assert not dossier_path.exists()
