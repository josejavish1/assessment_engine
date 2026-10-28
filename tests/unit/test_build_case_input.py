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
