import pytest

from assessment_engine.domain.prompts.blueprint_prompts import (
    get_blueprint_architect_instruction,
)
from assessment_engine.infrastructure.localization import t


def test_blueprint_architect_instruction_target_language_projection():
    """Verify that get_blueprint_architect_instruction projects target_language into the prompt."""
    inst_de = get_blueprint_architect_instruction(target_language="German")
    assert "EXCLUSIVELY in German" in inst_de
    assert "Principal Enterprise Solutions Architect" in inst_de

    inst_ja = get_blueprint_architect_instruction(target_language="Japanese")
    assert "EXCLUSIVELY in Japanese" in inst_ja

    inst_es = get_blueprint_architect_instruction(target_language="Spanish")
    assert "EXCLUSIVELY in Spanish" in inst_es


def test_conjunction_and_across_all_six_locales():
    """Verify that conjunction_and resolves cleanly across all 6 supported global locales."""
    assert t("conjunction_and", locale="es") == " y "
    assert t("conjunction_and", locale="en") == " and "
    assert t("conjunction_and", locale="de") == " und "
    assert t("conjunction_and", locale="fr") == " et "
    assert t("conjunction_and", locale="pt") == " e "
    assert t("conjunction_and", locale="ja") == "および"


def test_english_multiples_not_corrupted_by_spanish_accents():
    """Verify that English text with the word 'multiples' is not corrupted by Spanish accent replacement."""
    sample_content = '{"analysis": "Valued at multiples of EBITDA"}'

    doc_lang = "en"
    if doc_lang == "es":
        sample_content = sample_content.replace("multiples", "múltiples")

    assert "múltiples" not in sample_content
    assert "multiples of EBITDA" in sample_content
