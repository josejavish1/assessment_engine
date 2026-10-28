"""Unit tests for build_case_input parsing and text extraction utilities."""

from __future__ import annotations

from pathlib import Path

from assessment_engine.application.build_case_input import (
    build_question_text,
    parse_responses,
    read_rtf_text,
    read_text,
)


def test_read_rtf_text(tmp_path: Path):
    """Verify that read_rtf_text extracts clean plain text from RTF content."""
    rtf_content = r"{\rtf1\ansi\deff0 {\fonttbl {\f0 Arial;}} \par Hola \line Mundo \par}"
    rtf_file = tmp_path / "sample.rtf"
    rtf_file.write_text(rtf_content, encoding="utf-8")

    text = read_rtf_text(rtf_file)
    assert "Hola" in text
    assert "Mundo" in text


def test_read_text_fallback(tmp_path: Path):
    """Verify that read_text falls back to direct UTF-8 read for unknown suffixes."""
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("Contexto plano de prueba", encoding="utf-8")

    text = read_text(txt_file)
    assert text == "Contexto plano de prueba"


def test_parse_responses_regex():
    """Verify that parse_responses parses question IDs and values accurately."""
    raw = """
    T1.P1.K1.PR1: 4,5
    T1.P1.K1.PR2: 3.0
    T2.P1.K1.PR1: 5.0
    """
    scores = parse_responses(raw, tower_id="T1")
    assert "T1.P1.K1.PR1" in scores
    assert scores["T1.P1.K1.PR1"] == 4.5
    assert scores["T1.P1.K1.PR2"] == 3.0
    assert "T2.P1.K1.PR1" not in scores


def test_build_question_text():
    """Verify that build_question_text builds standard Spanish assessment prompt."""
    res = build_question_text("Capacidad de Cómputo")
    assert "Capacidad de Cómputo" in res
    assert "escala 1-5" in res


def test_build_question_lookup_hierarchy():
    """Verify that build_question_lookup traverses top-level, pillars, and KPIs hierarchy."""
    from assessment_engine.application.build_case_input import build_question_lookup

    tower_def = {
        "questions": [
            {"question_id": "T1.Q1", "question_text": "Pregunta de nivel superior"}
        ],
        "pillars": [
            {
                "kpis": [
                    {
                        "questions": [
                            {"question_id": "T1.Q1", "question_text": "Ignorada por ser duplicada"},
                            {"question_id": "T1.P1.K1.PR1", "question_text": "¿Está automatizado el puesto?"},
                        ]
                    }
                ]
            }
        ],
    }

    lookup = build_question_lookup(tower_def)
    assert lookup["T1.Q1"] == "Pregunta de nivel superior"
    assert lookup["T1.P1.K1.PR1"] == "¿Está automatizado el puesto?"


def test_build_case_input_full_cli(tmp_path: Path):
    """Verify end-to-end CLI generation of case_input.json from input artifacts."""
    import json
    import shutil
    from assessment_engine.application.build_case_input import main
    from assessment_engine.infrastructure.runtime_paths import resolve_case_dir

    ctx_file = tmp_path / "context.txt"
    ctx_file.write_text("Contexto de infraestructura para la torre Workplace.", encoding="utf-8")

    resp_file = tmp_path / "responses.txt"
    resp_file.write_text("T1.P1.K1.PR1: 4.0\nT1.P1.K2.PR1: 3.5\n", encoding="utf-8")

    main([
        "--client", "Cliente Auditoria",
        "--tower", "T1",
        "--context-file", str(ctx_file),
        "--responses-file", str(resp_file),
    ])

    case_dir = resolve_case_dir("cliente_auditoria", "T1")
    try:
        case_input_file = case_dir / "case_input.json"
        assert case_input_file.is_file(), "El archivo case_input.json debe haberse generado."

        data = json.loads(case_input_file.read_text(encoding="utf-8"))
        assert data["client"] == "Cliente Auditoria"
        assert data["tower_id"] == "T1"
        assert len(data["answers"]) >= 1
        assert data["_build_metadata"]["answers_detected"] >= 1
    finally:
        client_dir = case_dir.parent
        if client_dir.exists():
            shutil.rmtree(client_dir, ignore_errors=True)
