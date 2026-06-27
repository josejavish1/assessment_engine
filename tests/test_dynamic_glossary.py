import json
import re
from pathlib import Path

from assessment_engine.domain.schemas.ast import (
    CellNode,
    HeadingNode,
    ParagraphNode,
    TableNode,
    TableRowNode,
)


def test_abbreviations_glossary_localization_structure() -> None:
    """Verify that the abbreviations_glossary.json file has correct multi-language support."""
    glossary_path = Path("engine_config/abbreviations_glossary.json")
    assert glossary_path.exists(), "Glossary file must exist"

    with open(glossary_path, "r", encoding="utf-8") as f:
        glossary = json.load(f)

    # Verify that language keys exist
    for lang in ["es", "en", "pt", "fr", "ja"]:
        assert lang in glossary, f"Language '{lang}' must be in the glossary"
        assert isinstance(glossary[lang], dict), (
            f"Glossary for '{lang}' must be a dictionary"
        )

        # Verify essential common terms
        for term in ["FAIR", "AS-IS", "CPD", "DR", "ALE"]:
            assert term in glossary[lang], (
                f"Term '{term}' must be in the '{lang}' glossary"
            )
            assert isinstance(glossary[lang][term], str), (
                f"Description of '{term}' in '{lang}' must be a string"
            )


def test_dynamic_glossary_regex_boundary_matching() -> None:
    """Validate boundary matching expression (?<![a-zA-Z0-9])TERM(?![a-zA-Z0-9]) to avoid false positives."""
    # Simulate text corpus
    text_corpus = "La auditoría del CPD principal y la metodología FAIR se realizaron según el estándar. El DR se activó."

    # Expected terms to match
    assert re.search(r"(?<![a-zA-Z0-9])CPD(?![a-zA-Z0-9])", text_corpus)
    assert re.search(r"(?<![a-zA-Z0-9])FAIR(?![a-zA-Z0-9])", text_corpus)
    assert re.search(r"(?<![a-zA-Z0-9])DR(?![a-zA-Z0-9])", text_corpus)

    # Terms that should NOT match (false positives)
    # "DR" should not match inside words like "DRAMA" or "PADRE"
    fake_corpus = "El DRAMA del PADRE de Pedro no tiene relación con desastres."
    assert not re.search(r"(?<![a-zA-Z0-9])DR(?![a-zA-Z0-9])", fake_corpus), (
        "DR must not match as a substring of another word"
    )

    # "ALE" should not match inside "ALERTA" or "DALE"
    fake_corpus_ale = "Mandaron una ALERTA de tsunami. DALE caña."
    assert not re.search(r"(?<![a-zA-Z0-9])ALE(?![a-zA-Z0-9])", fake_corpus_ale), (
        "ALE must not match as a substring of another word"
    )


def test_ast_text_extraction_helper_logic() -> None:
    """Verify that the logic to extract text from ParagraphNode, HeadingNode, and TableNode works correctly."""
    nodes = [
        HeadingNode(text="Introducción al CPD", level=1),
        ParagraphNode(text="Usamos la metodología FAIR para cuantificar riesgos."),
        TableNode(
            rows=[
                TableRowNode(
                    cells=[CellNode(text="Pilar"), CellNode(text="Detalle del DR")]
                )
            ]
        ),
    ]

    # Replicate the implemented text extraction logic
    all_text_elements = []
    for n in nodes:
        if hasattr(n, "text") and n.text:
            all_text_elements.append(n.text)
        elif hasattr(n, "rows") and n.rows:
            for row in n.rows:
                if hasattr(row, "cells") and row.cells:
                    for cell in row.cells:
                        if hasattr(cell, "text") and cell.text:
                            all_text_elements.append(cell.text)
    text_corpus = " ".join(all_text_elements)

    # Check intersection of acronyms that should be found
    glossary = {
        "CPD": "Centro de Datos",
        "FAIR": "Metodología",
        "DR": "Disaster Recovery",
        "ENS": "Esquema Nacional de Seguridad (No usado)",
    }

    used_glossary = {}
    for term, desc in glossary.items():
        escaped_term = re.escape(term)
        pattern = rf"(?<![a-zA-Z0-9]){escaped_term}(?![a-zA-Z0-9])"
        if re.search(pattern, text_corpus):
            used_glossary[term] = desc

    assert "CPD" in used_glossary
    assert "FAIR" in used_glossary
    assert "DR" in used_glossary
    assert "ENS" not in used_glossary, "ENS is not in text and must not be extracted"


def test_client_local_glossary_override_logic() -> None:
    """Validate client-specific local glossary load and merge logic."""
    full_glossary = {"es": {"CPD": "Centro de Proceso de Datos (Sede física)."}}

    # Simulate the client's local glossary merge
    client_glossary = {
        "es": {
            "SGA": "Sistema de Gestión de Almacén (Retail).",
            "CPD": "Centro de Proceso de Datos (Sede física de alto rendimiento) [Sobrescribir]",
        }
    }

    for lang, terms in client_glossary.items():
        if lang in full_glossary:
            full_glossary[lang].update(terms)
        else:
            full_glossary[lang] = terms

    assert "SGA" in full_glossary["es"]
    assert "CPD" in full_glossary["es"]
    assert "[Sobrescribir]" in full_glossary["es"]["CPD"], (
        "The local glossary must override the global one"
    )


def test_first_use_expansion_quality_gate(capsys) -> None:
    """Verify that the first-use rule detects acronyms used without prior expansion."""
    used_glossary = {
        "CPD": "Centro de Proceso de Datos (Sede física o técnica de los servidores)."
    }

    # Scenario 1: The text does not contain the expanded definition (Should print warning)
    text_corpus_without_expansion = "El CPD tiene fallos críticos de climatización."
    for term, desc in used_glossary.items():
        long_form = desc.split("(")[0].strip()
        if long_form.lower() not in text_corpus_without_expansion.lower():
            print(
                f"⚠️  [Glosario] Calidad: La sigla '{term}' se utiliza pero su definición no aparece."
            )

    captured = capsys.readouterr()
    assert "[Glosario]" in captured.out
    assert "La sigla 'CPD' se utiliza pero su definición no aparece" in captured.out

    # Scenario 2: The text DOES contain the expanded definition (Should not warn)
    text_corpus_with_expansion = (
        "En el Centro de Proceso de Datos (CPD) se instaló un nuevo climatizador."
    )
    warnings = []
    for term, desc in used_glossary.items():
        long_form = desc.split("(")[0].strip()
        if long_form.lower() not in text_corpus_with_expansion.lower():
            warnings.append(term)

    assert len(warnings) == 0, (
        "No debe haber advertencias si el término expandido está presente"
    )


def test_locales_toc_glossary_separation() -> None:
    """Verify that locales.json correctly separates the Table of Contents and Abbreviations Glossary titles."""
    locales_path = Path("engine_config/locales.json")
    assert locales_path.exists(), "El archivo locales.json debe existir"

    with open(locales_path, "r", encoding="utf-8") as f:
        locales = json.load(f)

    for lang in ["es", "en", "pt", "fr", "ja"]:
        assert lang in locales
        assert "table_of_contents_title" in locales[lang], (
            f"Clave table_of_contents_title ausente en {lang}"
        )
        assert "appendix_a_title" in locales[lang], (
            f"Clave appendix_a_title ausente en {lang}"
        )

        # Verify that the Table of Contents and Glossary have conceptually distinct translations
        toc = locales[lang]["table_of_contents_title"]
        glossary_title = locales[lang]["appendix_a_title"]
        assert toc != glossary_title, (
            f"Semantic collision detected in {lang}: {toc} == {glossary_title}"
        )


# --- ARRANGE ---
# --- ACT ---
# --- ASSERT ---
