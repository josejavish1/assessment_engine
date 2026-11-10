"""Unit test for Section 4 receptor locale parity across 6 languages."""

import json
from pathlib import Path

def test_ch4_receptor_locale_parity() -> None:
    path = Path("engine_config/locales.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    
    languages = ["en", "es", "pt", "fr", "de", "ja"]
    receptors = ["AVAILABILITY_OUTAGE", "CAPITAL_INEFFICIENCY", "PRODUCTIVITY_TOIL", "REGULATORY_AND_BREACH"]
    keys = [
        "methodology_intro",
        "formula_expression",
        "vector_alpha_label",
        "vector_alpha_desc",
        "vector_beta_label",
        "vector_beta_desc",
        "vector_gamma_label",
        "vector_gamma_desc",
        "prioritization_rationale",
    ]
    
    for lang in languages:
        assert lang in data
        assert "annex_ch4_receptors" in data[lang]
        ch4 = data[lang]["annex_ch4_receptors"]
        
        for receptor in receptors:
            assert receptor in ch4, f"Missing receptor {receptor} in {lang}"
            r_dict = ch4[receptor]
            
            for key in keys:
                assert key in r_dict, f"Missing key {key} in {receptor} for {lang}"
                assert isinstance(r_dict[key], str)
                assert len(r_dict[key]) > 0
                
            # Verify {domain_name} placeholder exists in methodology_intro
            assert "{domain_name}" in r_dict["methodology_intro"]
