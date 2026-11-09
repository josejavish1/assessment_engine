"""Functional tests verifying synthetic control clients across orthogonal topologies and markets.

Validates:
1. Ingestion of raw inputs (transcription .docx and responses .txt) via build_case_input.
2. In-scope towers parse positive scores while out-of-scope towers short-circuit with 0 answers.
3. Industry profile mapping resolves to supported engine profiles.
4. Absolute zero-hardcoding and negative assertion: zero Molins contamination and correct currency bindings.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import pytest

from assessment_engine.application.build_case_input import build_case_input
from assessment_engine.infrastructure.config_loader import map_industry_to_profile

ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_DIR = ROOT / "tests" / "test_data" / "synthetic_clients"

CONTROL_CLIENTS: list[dict[str, any]] = [
    {
        "id": "uk_fintech",
        "name": "Starling Bank",
        "currency": "GBP",
        "currency_symbol": "£",
        "locale": "en",
        "in_scope_towers": ["T1", "T3", "T5", "T6", "T8", "T10"],
        "out_of_scope_towers": ["T2", "T4", "T7", "T9"],
        "expected_industry_profile": "banking",
    },
    {
        "id": "br_healthcare",
        "name": "Rede D'Or São Luiz",
        "currency": "BRL",
        "currency_symbol": "R$",
        "locale": "pt",
        "in_scope_towers": ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"],
        "out_of_scope_towers": ["T10"],
        "expected_industry_profile": "healthcare",
    },
    {
        "id": "fr_logistics",
        "name": "Geodis",
        "currency": "EUR",
        "currency_symbol": "€",
        "locale": "fr",
        "in_scope_towers": [f"T{i}" for i in range(1, 11)],
        "out_of_scope_towers": [],
        "expected_industry_profile": "critical_infrastructure",
    },
    {
        "id": "mx_retail",
        "name": "Grupo Comercial Chedraui",
        "currency": "MXN",
        "currency_symbol": "$",
        "locale": "es",
        "in_scope_towers": ["T2", "T3", "T7", "T9", "T10"],
        "out_of_scope_towers": ["T1", "T4", "T5", "T6", "T8"],
        "expected_industry_profile": "retail",
    },
    {
        "id": "us_saas",
        "name": "Datadog",
        "currency": "USD",
        "currency_symbol": "$",
        "locale": "en",
        "in_scope_towers": ["T1", "T5", "T6", "T9"],
        "out_of_scope_towers": ["T2", "T3", "T4", "T7", "T8", "T10"],
        "expected_industry_profile": "default",
    },
]


@pytest.mark.parametrize("client_spec", CONTROL_CLIENTS, ids=[c["id"] for c in CONTROL_CLIENTS])
def test_synthetic_client_raw_fixtures_exist(client_spec: dict[str, any]):
    """Verify that all raw source fixtures exist and are non-empty."""
    client_dir = SYNTHETIC_DIR / client_spec["id"]
    responses_file = client_dir / "assessment_responses.txt"
    transcript_file = client_dir / "transcription_interview_session.docx"
    intel_file = client_dir / "client_intelligence.json"

    assert responses_file.exists() and responses_file.stat().st_size > 0
    assert transcript_file.exists() and transcript_file.stat().st_size > 0
    assert intel_file.exists() and intel_file.stat().st_size > 0

    intel_data = json.loads(intel_file.read_text(encoding="utf-8"))
    assert intel_data["client_name"] == client_spec["name"]
    assert intel_data["metadata"]["currency"] == client_spec["currency"]
    assert intel_data["metadata"]["currency_symbol"] == client_spec["currency_symbol"]
    assert intel_data["metadata"]["lang"] == client_spec["locale"]

    # Negative assertion: zero Molins contamination in synthetic dossiers
    intel_raw = json.dumps(intel_data)
    assert "molins" not in intel_raw.lower(), f"Contamination detected in {client_spec['id']} intelligence."


@pytest.mark.parametrize("client_spec", CONTROL_CLIENTS, ids=[c["id"] for c in CONTROL_CLIENTS])
def test_synthetic_client_in_scope_towers_ingestion(client_spec: dict[str, any]):
    """Verify that every in-scope tower successfully parses non-zero scores and transcript summary."""
    client_dir = SYNTHETIC_DIR / client_spec["id"]
    responses_file = client_dir / "assessment_responses.txt"
    transcript_file = client_dir / "transcription_interview_session.docx"

    for tower_id in client_spec["in_scope_towers"]:
        args = argparse.Namespace(
            client=client_spec["name"],
            tower=tower_id,
            context_file=str(transcript_file),
            responses_file=str(responses_file),
        )
        case_data = build_case_input(args)
        assert case_data["tower_id"] == tower_id
        assert len(case_data["answers"]) > 0, f"Expected answers for in-scope tower {tower_id} in {client_spec['id']}"
        assert len(case_data["context_summary"]) > 100, f"Expected non-empty context summary for {tower_id}"

        # Verify negative assertion in generated case data
        assert "molins" not in case_data["client"].lower()


@pytest.mark.parametrize("client_spec", CONTROL_CLIENTS, ids=[c["id"] for c in CONTROL_CLIENTS])
def test_synthetic_client_out_of_scope_towers_short_circuit(client_spec: dict[str, any]):
    """Verify that out-of-scope towers parse exactly zero answers, allowing clean pipeline short-circuit."""
    client_dir = SYNTHETIC_DIR / client_spec["id"]
    responses_file = client_dir / "assessment_responses.txt"
    transcript_file = client_dir / "transcription_interview_session.docx"

    for tower_id in client_spec["out_of_scope_towers"]:
        args = argparse.Namespace(
            client=client_spec["name"],
            tower=tower_id,
            context_file=str(transcript_file),
            responses_file=str(responses_file),
        )
        case_data = build_case_input(args)
        assert len(case_data["answers"]) == 0, f"Expected 0 answers for out-of-scope tower {tower_id} in {client_spec['id']}"


@pytest.mark.parametrize("client_spec", CONTROL_CLIENTS, ids=[c["id"] for c in CONTROL_CLIENTS])
def test_synthetic_client_industry_profile_resolution(client_spec: dict[str, any]):
    """Verify that each client's industry maps to an existing industry profile without unhandled fallback."""
    client_dir = SYNTHETIC_DIR / client_spec["id"]
    intel_file = client_dir / "client_intelligence.json"
    intel_data = json.loads(intel_file.read_text(encoding="utf-8"))

    industry_name = intel_data.get("profile", {}).get("industry", "default")
    resolved_key = map_industry_to_profile(industry_name)
    assert resolved_key == client_spec["expected_industry_profile"]

    # Verify that the mapped industry profile JSON exists and is valid
    profile_path = ROOT / "engine_config" / "industry_profiles" / f"{resolved_key}.json"
    assert profile_path.exists(), f"Profile {resolved_key}.json does not exist"
    profile_data = json.loads(profile_path.read_text(encoding="utf-8"))
    assert "industry" in profile_data or "industry_name" in profile_data or "risk_multipliers" in profile_data


@pytest.mark.parametrize("client_spec", CONTROL_CLIENTS, ids=[c["id"] for c in CONTROL_CLIENTS])
def test_compile_client_deliverable_purity(client_spec: dict[str, any]):
    """Verify that compiling each benchmark client produces a pure, valid DOCX with zero cross-tenant contamination."""
    import re
    import docx
    from scripts.build_client_delivery_suite import compile_starling_delivery_suite

    res = compile_starling_delivery_suite(client_id=client_spec["id"], doc_lang=client_spec["locale"])
    docx_path = res[0] if isinstance(res, tuple) else res
    assert docx_path.exists() and docx_path.stat().st_size > 50_000

    doc = docx.Document(docx_path)
    full_text = "\n".join(p.text for p in doc.paragraphs) + "\n".join(
        "\n".join(c.text for c in r.cells) for t in doc.tables for r in t.rows
    )

    # 1. Zero Molins cross-contamination
    assert "molins" not in full_text.lower(), f"Found 'Molins' string in {client_spec['id']} deliverable"

    # 2. Zero industrial weighbridge / cement leaks
    assert "weighbridge" not in full_text.lower(), f"Found 'weighbridge' string in {client_spec['id']} deliverable"
    assert not re.findall(r"\b(cement|cemento|cementera)\b", full_text, flags=re.IGNORECASE), (
        f"Found isolated cement word in {client_spec['id']} deliverable"
    )

    # 3. Currency integrity: Native currency symbol present
    expected_sym = client_spec["currency_symbol"]
    assert expected_sym in full_text, f"Currency symbol '{expected_sym}' missing from {client_spec['id']} deliverable"

    # 4. Topology integrity: Exactly active towers rendered
    for t_id in client_spec["in_scope_towers"]:
        assert t_id in full_text, f"Active tower {t_id} missing from {client_spec['id']} deliverable"
    for t_out in client_spec["out_of_scope_towers"]:
        assert (
            f"Domain {t_out}" not in full_text
            and f"Dominio {t_out}" not in full_text
            and f"Domaine {t_out}" not in full_text
        ), f"Excluded tower {t_out} was erroneously rendered in {client_spec['id']} deliverable"

