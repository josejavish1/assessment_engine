from pathlib import Path

from assessment_engine.infrastructure.vendor_intelligence import (
    DynamicVendorSynthesizer,
    VendorRegistry,
)


def test_vendor_registry_loads_static_blueprints():
    VendorRegistry.initialize()
    supported = VendorRegistry.get_supported_vendor_ids()
    assert len(supported) >= 80, f"Expected >= 80 blueprints, found {len(supported)}"
    assert "netapp" in supported
    assert "cisco" in supported
    assert "cohesity" in supported
    assert "fortinet" in supported
    assert "azure" in supported


def test_vendor_detection_in_text():
    sample_text = (
        "El cliente dispone de almacenamiento NetApp AFF para producción y cabinas secundarias con Cohesity "
        "para copias de seguridad. La red perimetral está protegida con firewalls Fortinet y switches Cisco."
    )
    detected = VendorRegistry.detect_vendors_in_text(sample_text)
    detected_ids = [d["vendor_id"] for d in detected]

    assert "netapp" in detected_ids
    assert "cohesity" in detected_ids
    assert "fortinet" in detected_ids
    assert "cisco" in detected_ids

    prompt_context = VendorRegistry.format_vendor_context_for_architect(detected)
    assert "NetApp" in prompt_context
    assert "Cohesity" in prompt_context
    assert "Fortinet" in prompt_context


def test_dynamic_vendor_synthesizer_jit(tmp_path: Path):
    synthesizer = DynamicVendorSynthesizer(dynamic_dir=tmp_path)
    # Synthesizes an unknown/niche vendor
    bp = synthesizer.synthesize_blueprint(
        "rockwell_automation", context_clue="Sistemas PLC y SCADA industrial"
    )

    assert bp["vendor_id"] == "rockwell_automation"
    assert "official_domains" in bp
    assert len(bp["coverage_domains"]) > 0
    assert (tmp_path / "rockwell_automation.yaml").exists()
