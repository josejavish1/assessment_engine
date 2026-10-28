"""Unit tests for DynamicLocaleSynthesizer and JIT Multi-Language Architecture."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from assessment_engine.infrastructure.localization import (
    DynamicLocaleSynthesizer,
    get_localized_string,
    t,
)
from assessment_engine.infrastructure.config_loader import resolve_localized_vocabulary


def test_dynamic_locale_synthesizer_from_cache(tmp_path: Path) -> None:
    """Verify that DynamicLocaleSynthesizer reads from cache if a translated dictionary exists."""
    cache_dir = tmp_path / "locales_dynamic"
    cache_dir.mkdir(parents=True, exist_ok=True)

    dummy_nl = {f"k_{i}": f"v_{i}" for i in range(60)}
    dummy_nl["title"] = "Statusbeoordelingsrapport (AS-IS)"
    dummy_nl["annex_technical_prefix"] = "Technische bijlage:"
    dummy_nl["toc_title"] = "Inhoudsopgave"

    (cache_dir / "nl.json").write_text(json.dumps(dummy_nl), encoding="utf-8")

    synthesizer = DynamicLocaleSynthesizer(cache_dir=cache_dir)
    res = synthesizer.synthesize_locale("nl")

    assert res["title"] == "Statusbeoordelingsrapport (AS-IS)"
    assert res["annex_technical_prefix"] == "Technische bijlage:"
    assert res["toc_title"] == "Inhoudsopgave"


def test_dynamic_locale_synthesizer_ai_call_fallback(tmp_path: Path) -> None:
    """Verify that DynamicLocaleSynthesizer handles synthesis and gracefully falls back to English if AI fails."""
    cache_dir = tmp_path / "locales_dynamic"
    cache_dir.mkdir(parents=True, exist_ok=True)

    synthesizer = DynamicLocaleSynthesizer(cache_dir=cache_dir)
    # Mocking failure to verify resilient fallback
    with patch("assessment_engine.infrastructure.genai_client.create_genai_client", side_effect=RuntimeError("AI Offline")):
        res = synthesizer.synthesize_locale("xyz_nonexistent")
        assert "title" in res
        assert "Current State" in res["title"]  # English fallback
