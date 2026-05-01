import json
from pathlib import Path

import pytest

from assessment_engine.scripts.render_web_presentation import generate_web_dashboard

# El directorio 'working' ahora se encuentra desde la raíz del proyecto
WORKING_DIR = Path("working")

@pytest.fixture
def setup_real_test_data():
    client_id = "web_test_client_real"
    test_dir = WORKING_DIR / client_id
    test_dir.mkdir(parents=True, exist_ok=True)

    global_report_data = {
        "meta": {"global_score_display": "3.1"},
        "executive_summary": {"headline": "Test Headline", "narrative": "Summary...", "key_business_impacts": ["Impact 1"]},
        "burning_platform": [{"theme": "Risk", "business_risk": "Risk summary"}],
        "target_vision": {"operating_model_implications": [{"area": "People", "description": "Desc..."}]},
        "execution_roadmap": {"programs": [], "horizons": {}},
        "heatmap": [{"id": "T1", "name": "Test Tower 1", "score": "3.5"}]
    }
    (test_dir / "global_report_payload.json").write_text(json.dumps(global_report_data))

    blueprint_dir = test_dir / "T1"
    blueprint_dir.mkdir(exist_ok=True)
    blueprint_data = {
        "document_meta": {"tower_name": "Test Tower 1", "tower_code": "T1"},
        "executive_snapshot": {"score": 3.5, "band": "Managed", "executive_summary": "BP Summary"},
        "pillars_analysis": [], "executive_decisions": [], "roadmap": {}, "cross_capabilities_analysis": {}
    }
    (blueprint_dir / "blueprint_T1_payload.json").write_text(json.dumps(blueprint_data))
    
    yield client_id
    
    import shutil
    shutil.rmtree(test_dir)

def test_generate_web_dashboard_with_real_files(setup_real_test_data):
    client_id = setup_real_test_data
    output_html_path = WORKING_DIR / client_id / "presentation" / "index.html"
    
    # La lógica del script original usa una ruta relativa a __file__, 
    # por lo que no necesita mocks si la estructura de directorios es correcta.
    generate_web_dashboard(client_id)

    assert output_html_path.exists(), "El fichero index.html no fue creado."
    content = output_html_path.read_text(encoding="utf-8")
    assert len(content) > 5000, f"El contenido del HTML es demasiado pequeño ({len(content)} bytes)."
    assert '"headline": "Test Headline"' in content, "El 'headline' no fue inyectado."
