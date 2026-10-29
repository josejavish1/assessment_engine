"""Top-Tier-1 unit tests for Jurisdictional Architectural Sovereignty Policy."""

from __future__ import annotations

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.jurisdictional_sovereignty import (
    JurisdictionalSovereigntyPolicy,
    infer_jurisdiction_code,
    load_jurisdictional_registry,
)


def test_load_jurisdictional_registry_has_all_tier1_regions():
    """Verify registry loads cleanly and contains specifications for DE, ES, US, BR, MX, JP."""
    reg = load_jurisdictional_registry()
    assert len(reg.jurisdictions) >= 6

    for code in ("DE", "ES", "US", "BR", "MX", "JP"):
        assert code in reg.jurisdictions, f"Region {code} missing in jurisdictional registry."
        profile = reg.jurisdictions[code]
        assert len(profile.sovereign_cloud_providers) >= 2
        assert len(profile.architectural_invariants) >= 2
        assert len(profile.connectivity_standards) >= 1
        assert len(profile.data_residency_rules) >= 1


def test_infer_jurisdiction_code_by_country_and_regulations():
    """Verify deterministic inference of jurisdiction from country, regulatory tokens or language."""
    # Country string resolution
    assert infer_jurisdiction_code("Germany", [], "es") == "DE"
    assert infer_jurisdiction_code("Deutschland", [], "es") == "DE"
    assert infer_jurisdiction_code("España", [], "es") == "ES"
    assert infer_jurisdiction_code("United States", [], "es") == "US"
    assert infer_jurisdiction_code("Brasil", [], "es") == "BR"
    assert infer_jurisdiction_code("México", [], "es") == "MX"
    assert infer_jurisdiction_code("Japan", [], "es") == "JP"

    # Regulatory tokens resolution
    assert infer_jurisdiction_code(None, ["NIS2", "BSI IT-Grundschutz"], "es") == "DE"
    assert infer_jurisdiction_code(None, ["Esquema Nacional de Seguridad", "ENS Alta"], "es") == "ES"
    assert infer_jurisdiction_code(None, ["HIPAA", "NIST CSF", "FDA 21 CFR"], "es") == "US"
    assert infer_jurisdiction_code(None, ["Resolução BCB 85", "LGPD"], "es") == "BR"
    assert infer_jurisdiction_code(None, ["Disposiciones CNBV", "SPEI"], "es") == "MX"
    assert infer_jurisdiction_code(None, ["FISC Guidelines", "ISMAP"], "es") == "JP"

    # Language fallback resolution
    assert infer_jurisdiction_code(None, [], "de") == "DE"
    assert infer_jurisdiction_code(None, [], "ja") == "JP"
    assert infer_jurisdiction_code(None, [], "pt") == "BR"


def test_germany_gaia_x_and_bsi_sovereignty_injection():
    """Verify German public/industrial entity gets GAIA-X and BSI C5 architectural invariants."""
    policy = JurisdictionalSovereigntyPolicy()
    graph = EpistemicGraph(client_id="test_de")

    payload = {
        "document_meta": {
            "client_name": "Nordic Grid Power GmbH",
            "tower_code": "T2",
            "country": "Germany",
            "regulatory_context": ["NIS2", "ISO 27001"],
            "language": "de",
        },
        "pillars_analysis": [
            {
                "pilar_id": "P1",
                "projects_todo": [
                    {
                        "name": "Plattform-Modernisierung",
                        "deliverables": ["Architektur-Blueprint"],
                    }
                ],
            }
        ],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    meta = patched["document_meta"]

    assert meta["jurisdiction_code"] == "DE"
    assert "Germany" in meta["jurisdiction_name"]
    sov = meta["jurisdictional_sovereignty"]
    assert any("GAIA-X" in inv for inv in sov["architectural_invariants"])
    assert any("BSI C5" in inv for inv in sov["architectural_invariants"])
    assert "STACKIT (Schwarz Gruppe)" in sov["sovereign_cloud_providers"]

    # Verify deliverable augmented
    delivs = patched["pillars_analysis"][0]["projects_todo"][0]["deliverables"]
    assert any("GAIA-X" in d for d in delivs)

    # Verify epistemic graph resolution
    truth = graph.resolve_truth()
    subject_key = "Nordic Grid Power GmbH".upper()
    assert truth[subject_key]["BOUND_TO_JURISDICTION"]["value"] == "Germany / DACH & Central Europe"
    assert "T2" in truth
    assert truth["T2"]["QUALIFIED_SOVEREIGN_PROVIDER"]["value"] in (
        "STACKIT (Schwarz Gruppe)",
        "Open Telekom Cloud (T-Systems)",
    )

    ctx_str = graph.get_resolved_context_string()
    assert "GAIA-X" in ctx_str


def test_spain_red_sara_and_ens_alta_injection():
    """Verify Spanish public/critical entity gets Red SARA and ENS Alta architectural invariants."""
    policy = JurisdictionalSovereigntyPolicy()
    graph = EpistemicGraph()

    payload = {
        "document_meta": {
            "client_name": "Agencia Tributaria Regional",
            "tower_code": "T1",
            "country": "España",
            "regulatory_context": ["ENS Alta", "GDPR"],
        },
        "pillars_analysis": [],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    meta = patched["document_meta"]

    assert meta["jurisdiction_code"] == "ES"
    sov = meta["jurisdictional_sovereignty"]
    assert any("Esquema Nacional de Seguridad" in inv for inv in sov["architectural_invariants"])
    assert any("Red SARA" in conn for conn in sov["connectivity_standards"])


def test_brazil_pix_and_bcb85_sovereignty_injection():
    """Verify Brazilian financial institution gets BCB 85 and Pix failover invariants."""
    policy = JurisdictionalSovereigntyPolicy()
    graph = EpistemicGraph()

    payload = {
        "document_meta": {
            "client_name": "Banco Paulista S.A.",
            "tower_code": "T3",
            "country": "Brasil",
            "regulatory_context": ["Resolução BCB 85", "Pix"],
        },
        "pillars_analysis": [],
    }

    patched = policy.evaluate_and_patch(graph, payload)
    meta = patched["document_meta"]

    assert meta["jurisdiction_code"] == "BR"
    sov = meta["jurisdictional_sovereignty"]
    assert any("Pix" in inv for inv in sov["architectural_invariants"])
    assert any("RSFN" in conn for conn in sov["connectivity_standards"])


def test_jit_synthesis_and_caching_for_unlisted_jurisdiction(tmp_path, monkeypatch):
    """Verify runtime JIT synthesis creates and caches a valid profile for unlisted countries."""
    import json
    from unittest.mock import MagicMock, patch

    import assessment_engine.infrastructure.policies.jurisdictional_sovereignty as j_mod

    monkeypatch.setattr(j_mod, "DYNAMIC_DIR", tmp_path / "jurisdictions_dynamic")

    mock_resp = MagicMock()
    mock_resp.text = json.dumps({
        "name": "Singapore / Financial & Gov Cloud",
        "region_code": "SG",
        "sovereign_cloud_providers": ["AWS Singapore (ap-southeast-1)", "Singtel Sovereign Enclave"],
        "architectural_invariants": [
            "MAS Technology Risk Management (TRM) Guidelines",
            "Monetary Authority of Singapore Outsource Guidelines",
        ],
        "connectivity_standards": ["Singapore Internet Exchange (SGIX) Direct Peering"],
        "primary_hsm_standard": "FIPS 140-2 Level 3",
        "data_residency_rules": ["Zero offshore transfer for regulated financial records without MAS approval"],
    })

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp

    with patch("assessment_engine.infrastructure.genai_client.create_genai_client", return_value=mock_client):
        # 1. Synthesize JIT
        profile = j_mod.synthesize_jurisdiction_profile_jit("Singapore", ["MAS TRM"], region_code="SG")
        assert profile is not None
        assert profile.region_code == "SG"
        assert "MAS Technology Risk Management" in profile.architectural_invariants[0]
        assert mock_client.models.generate_content.call_count == 1

        # 2. Second call must hit cache with 0 LLM calls
        cached_profile = j_mod.synthesize_jurisdiction_profile_jit("Singapore", ["MAS TRM"], region_code="SG")
        assert cached_profile is not None
        assert cached_profile.region_code == "SG"
        assert mock_client.models.generate_content.call_count == 1  # Unchanged!

        # 3. Policy integration test
        policy = j_mod.JurisdictionalSovereigntyPolicy()
        graph = EpistemicGraph(client_id="test_sg")
        payload = {
            "document_meta": {
                "client_name": "DBS Bank Singapore",
                "tower_code": "T1",
                "country": "Singapore",
                "regulatory_context": ["MAS TRM"],
            },
            "pillars_analysis": [
                {
                    "pilar_id": "P1",
                    "projects_todo": [{"name": "Core Banking Modernization", "deliverables": []}],
                }
            ],
        }
        patched = policy.evaluate_and_patch(graph, payload)
        assert patched["document_meta"]["jurisdiction_code"] == "SG"
        delivs = patched["pillars_analysis"][0]["projects_todo"][0]["deliverables"]
        assert any("MAS Technology Risk Management" in d for d in delivs)

