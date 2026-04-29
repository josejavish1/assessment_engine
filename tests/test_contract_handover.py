import json
from pathlib import Path
import pytest
from assessment_engine.schemas.blueprint import BlueprintPayload
from assessment_engine.schemas.annex_synthesis import AnnexPayload
from assessment_engine.schemas.global_report import GlobalReportPayload
from assessment_engine.schemas.commercial import CommercialPayload

ROOT = Path(__file__).resolve().parents[1]
T5_DIR = ROOT / "working" / "smoke_ivirma" / "T5"

def _load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

@pytest.mark.contract
def test_contract_blueprint_to_annex():
    """
    Valida que el Blueprint generado por el motor es un contrato válido 
    para el sintetizador del Anexo.
    """
    bp_path = T5_DIR / "blueprint_t5_payload.json"
    assert bp_path.exists(), "Debe existir el payload del blueprint de T5"
    
    bp_data = _load_json(bp_path)
    # Validar que el blueprint cumple su propio esquema (con alias)
    bp_payload = BlueprintPayload.model_validate(bp_data)
    
    # Simular la carga en el sintetizador
    # (El sintetizador usa bp_payload para inyectar datos en el prompt y en el resultado final)
    assert bp_payload.document_meta.tower_code == "T5"
    assert len(bp_payload.pillars_analysis) > 0

@pytest.mark.contract
def test_contract_annex_is_valid_payload():
    """
    Valida que el Anexo sintetizado cumple con el esquema AnnexPayload 
    requerido por el renderizador Word.
    """
    annex_path = T5_DIR / "approved_annex_t5.template_payload.json"
    assert annex_path.exists(), "Debe existir el payload del anexo de T5"
    
    annex_data = _load_json(annex_path)
    # Validar integridad estructural y tipos
    annex_payload = AnnexPayload.model_validate(annex_data)
    
    assert annex_payload.document_meta["tower_code"] == "T5"
    assert annex_payload.sections.gap is not None
    assert len(annex_payload.sections.risks.risks) > 0

@pytest.mark.contract
def test_contract_global_report_schema():
    """
    Valida que si existiera un Global Report, este cumpliría con su esquema.
    Nota: Actualmente no tenemos un smoke test global validado en working/, 
    pero validamos que el esquema sea robusto.
    """
    # Test estructural mínimo completo
    data = {
        "_generation_metadata": {"artifact_type": "global_report_payload", "artifact_version": "1.0.0"},
        "meta": {"client": "test", "date": "today", "version": "1.0"},
        "executive_summary": {
            "headline": "Hi", 
            "narrative": "...", 
            "key_business_impacts": ["Impact 1"]
        },
        "burning_platform": [
            {"theme": "Theme", "business_risk": "Risk", "root_causes": ["Cause"]}
        ],
        "heatmap": [],
        "tower_summaries": [],
        "tower_bottom_lines": [
            {
                "id": "T1", "name": "Tower", "score": "3.0", "band": "B", 
                "status_color": "C", "bottom_line": "Msg"
            }
        ],
        "target_vision": {
            "value_proposition": "Value",
            "evolution_principles": [{"principle": "P", "description": "D"}],
            "strategic_pillars": [{"pillar": "Pil", "description": "Des"}]
        },
        "execution_roadmap": {
            "programs": [{"name": "Prog", "description": "Desc"}],
            "horizons": {
                "quick_wins_0_3_months": [],
                "year_1_3_12_months": [],
                "year_2_12_24_months": [],
                "year_3_24_36_months": []
            }
        },
        "executive_decisions": {
            "immediate_decisions": [
                {"decision_type": "D", "action_required": "A", "impact_if_delayed": "I"}
            ]
        },
        "strategic_risks": [],
        "architecture_principles": [],
        "operating_model_implications": [],
        "key_initiatives": [],
        "visuals": {}
    }
    payload = GlobalReportPayload.model_validate(data)
    assert payload.meta.client == "test"

@pytest.mark.contract
def test_contract_commercial_hybrid_lineage():
    """
    Valida el nuevo contrato híbrido para el Account Plan.
    Debe poder recibir metadatos del Global y detalle del Blueprint.
    """
    # Simulación de un payload comercial que ha bebido de ambas fuentes
    commercial_data = {
        "_generation_metadata": {
            "artifact_type": "commercial_payload",
            "artifact_version": "1.0.0",
            "source_version": "global-1.0.0 + bp-1.0.0"
        },
        "meta": {"client": "ivirma", "date": "2026-04-29", "version": "v1"},
        "commercial_summary": {
            "deal_flash": {"purchase_driver": "Expansion", "ntt_win_theme": "Resilience"},
            "why_now_bullets": ["Risk is high"],
            "how_we_win_bullets": ["Expertise"],
            "estimated_tam": "1M"
        },
        "gtm_strategy": {
            "trojan_horse": "Strategy",
            "self_funded_transformation": "Yes",
            "lock_in": "High"
        },
        "opportunities_pipeline": [],
        "proactive_proposals": [],
        "intelligence_dossier": {
            "source_blueprints": ["T5"],
            "upselling_opportunities": ["Disaster Recovery implementation"]
        }
    }
    payload = CommercialPayload.model_validate(commercial_data)
    assert "source_blueprints" in payload.intelligence_dossier
