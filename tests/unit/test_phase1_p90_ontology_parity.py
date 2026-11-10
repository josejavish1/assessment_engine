"""Unit test verifying canonical P90 crisis ontology parity and zero cross-domain contamination."""

import json
from pathlib import Path
import pytest


def test_p90_ontology_parity_and_cleanliness() -> None:
    path = Path("engine_config/locales.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    languages = ["en", "es", "pt", "fr", "de", "ja"]
    tower_ids = [f"T{i}" for i in range(1, 11)]

    for lang in languages:
        assert lang in data, f"Missing language {lang} in locales.json"
        assert "tower_p90_triggers" in data[lang], f"Missing tower_p90_triggers in {lang}"
        triggers = data[lang]["tower_p90_triggers"]

        for t_id in tower_ids:
            assert t_id in triggers, f"Missing trigger for {t_id} in {lang}"
            text = triggers[t_id]
            assert isinstance(text, str) and len(text) > 15

        # Anti-contamination assertions in English
        en_t3 = triggers["T3"].lower()
        assert "backup" not in en_t3, "T3 (Networks) contains storage/backup contamination!"
        assert "storage" not in en_t3, "T3 (Networks) contains storage contamination!"
        assert "routing" in en_t3 or "network" in en_t3 or "wan" in en_t3

        en_t10 = triggers["T10"].lower()
        assert "database" not in en_t10, "T10 (Plant OT) contains database contamination!"
        assert "storage" not in en_t10, "T10 (Plant OT) contains storage contamination!"
        assert "scada" in en_t10 or "plc" in en_t10 or "dispatch" in en_t10 or "weighbridge" in en_t10

        # Anti-contamination assertions in Spanish
        es_t3 = triggers["T3"].lower()
        assert "backup" not in es_t3 and "respaldo" not in es_t3, "T3 contains backup contamination in Spanish!"
        assert "almacenamiento" not in es_t3, "T3 contains storage contamination in Spanish!"
        assert "conmutación" in es_t3 or "wan" in es_t3 or "enrutamiento" in es_t3

        es_t10 = triggers["T10"].lower()
        assert "base de datos" not in es_t10 and "bases de datos" not in es_t10, "T10 contains DB contamination in Spanish!"
        assert "almacenamiento" not in es_t10, "T10 contains storage contamination in Spanish!"
        assert "scada" in es_t10 or "plc" in es_t10 or "pesaje" in es_t10 or "expedición" in es_t10
