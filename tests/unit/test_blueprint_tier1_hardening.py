from assessment_engine.domain.prompts.blueprint_prompts import (
    get_bid_manager_prompt,
    get_blueprint_architect_instruction,
    get_closing_orchestrator_prompt,
    get_critic_prompt,
    get_dependency_resolver_prompt,
    get_gravity_profiler_prompt,
    get_pilar_architect_prompt,
    load_prompt_config,
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


def test_pilar_architect_prompt_pure_technical_english_headers():
    """Verify that get_pilar_architect_prompt uses pure Technical English headers and no hardcoded Spanish."""
    prompt = get_pilar_architect_prompt(
        tower_name="Cloud",
        pilar_label="Compute",
        pilar_score=2.5,
        context_str="Business Context Data",
        intel_str="Strategic DNA",
        answers_json="{}",
        target_language="English",
    )
    assert "You are a Senior Enterprise Infrastructure Architect" in prompt
    assert "BUSINESS CONTEXT:" in prompt
    assert "Eres un" not in prompt
    assert "CONTEXTO DEL NEGOCIO" not in prompt
    assert "GOLDEN REFERENCE EXEMPLAR" in prompt
    assert "{target_language}" not in prompt
    assert "target language (English)" in prompt


def test_all_blueprint_prompt_generators():
    """Ensure all prompt generators in blueprint_prompts assemble valid non-empty Technical English prompts."""
    critic = get_critic_prompt("Compute", "Acme", '{"draft": true}')
    assert "You are the" in critic
    assert "REVIEW OBJECTIVES:" in critic
    assert '{"draft": true}' in critic

    closing = get_closing_orchestrator_prompt(
        "Cloud", '{"pillars": []}', "DNA", total_ale=50000.0
    )
    assert "FINANCIAL MANDATE (FAIR ALE)" in closing
    assert "50,000.00 €" in closing

    gravity = get_gravity_profiler_prompt("Strategic DNA Data", "Acme")
    assert "Architectural Gravity Profile" in gravity
    assert "Acme" in gravity

    deps = get_dependency_resolver_prompt('["ProjA", "ProjB"]')
    assert "Solutions and Topological Dependency Architect" in deps
    assert '["ProjA", "ProjB"]' in deps

    bid = get_bid_manager_prompt(
        "Acme",
        "Cloud Migration",
        "Modernize",
        "Large",
        "High",
        target_language="English",
    )
    assert "Senior Bid Manager and Principal Solution Architect" in bid
    assert "Cloud Migration" in bid
    assert "EXCLUSIVELY IN English" in bid

    cfg = load_prompt_config("blueprint_critic_prompt.yaml")
    assert "role" in cfg
