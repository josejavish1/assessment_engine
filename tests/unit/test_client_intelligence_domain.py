"""Top-Tier-1 cryptographic, property, and ontology unit tests for client intelligence."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from assessment_engine.infrastructure.client_intelligence import (
    build_client_context_packet,
    build_client_context_text,
    coerce_client_dossier_v2,
    coerce_client_dossier_v3,
    compute_dossier_hash,
    extract_target_maturity_map,
    get_target_maturity,
    infer_related_towers,
    is_client_dossier_v2,
    is_client_dossier_v3,
    sign_dossier,
    summarize_transformation_horizon,
    verify_dossier_integrity,
)


def test_cryptographic_seal_signing_and_tamper_detection():
    """Verify that sign_dossier generates a canonical SHA-256 seal and detects any body tampering."""
    raw_dossier = {
        "version": "3.0",
        "client_name": "Redeia",
        "profile": {"industry": "Energy & Utilities"},
        "business_context": {"transformation_horizon": {"stage": "H2"}},
    }

    signed = sign_dossier(raw_dossier)
    assert "metadata" in signed
    assert "integrity" in signed["metadata"]
    assert len(signed["metadata"]["integrity"]["hash"]) == 64  # SHA-256 hex string

    # 1. Verification of untampered dossier
    assert verify_dossier_integrity(signed) is True

    # 2. Adversarial Tamper Attack: mutate one nested value
    tampered = json.loads(json.dumps(signed))
    tampered["business_context"]["transformation_horizon"]["stage"] = "H3"
    assert verify_dossier_integrity(tampered) is False, "El sello criptográfico debe invalidarse ante cualquier mutación."

    # 3. Adversarial Tamper Attack: inject unexpected field
    tampered_inject = json.loads(json.dumps(signed))
    tampered_inject["unauthorized_backdoor"] = "malicious_payload"
    assert verify_dossier_integrity(tampered_inject) is False, "El sello criptográfico debe invalidarse ante inyección de campos."


def test_dossier_version_detection():
    """Verify strict version detection for V2 and V3 dossier schemas."""
    v2_valid = {
        "version": "2.0",
        "client_name": "Test",
        "profile": {"industry": "Tech"},
        "business_context": {},
    }
    assert is_client_dossier_v2(v2_valid) is True
    assert is_client_dossier_v2({"version": "2.0"}) is False

    v3_valid = {
        "version": "3.0",
        "client_name": "Test",
        "metadata": {},
        "profile": {},
        "business_context": {},
        "technology_context": {},
    }
    assert is_client_dossier_v3(v3_valid) is True
    assert is_client_dossier_v3({"version": "3.0"}) is False
    assert is_client_dossier_v3({}) is False


def test_extract_target_maturity_and_lookup():
    """Verify extraction of target maturity overrides across towers with default fallbacks."""
    dossier_v3 = {
        "version": "3.0",
        "metadata": {},
        "profile": {},
        "business_context": {},
        "technology_context": {},
        "tower_overrides": {
            "T1": {"target_maturity": 4.5},
            "T2": {"target_maturity": 4.0},
        },
    }
    mat_map = extract_target_maturity_map(dossier_v3)
    assert mat_map["T1"] == 4.5
    assert mat_map["T2"] == 4.0

    assert get_target_maturity(dossier_v3, "T1", default=3.0) == 4.5
    assert get_target_maturity(dossier_v3, "T2", default=3.0) == 4.0
    assert get_target_maturity(dossier_v3, "T99", default=3.2) == 3.2


def test_infer_related_towers_from_keywords():
    """Verify that keyword ontology infers corresponding technology tower IDs deterministically."""
    towers_t9 = infer_related_towers("Digital workplace, puesto de trabajo, Office 365, Teams")
    assert "T9" in towers_t9

    towers_t2 = infer_related_towers("Datacenter, VMware vSphere, Kubernetes, servidores x86, cloud")
    assert "T2" in towers_t2

    towers_t7 = infer_related_towers("Observabilidad, Dynatrace, APM, monitoring, sre")
    assert "T7" in towers_t7

    empty_towers = infer_related_towers("Palabras sin relación tecnológica alguna")
    assert empty_towers == []


def test_coerce_client_dossier_v3_idempotency_and_integrity():
    """Verify that coerce_client_dossier_v3 normalizes incomplete payloads into signed V3 contracts."""
    raw_input = {
        "client_name": "Endesa",
        "industry": "Utilities",
        "horizon": "H1",
    }

    coerced = coerce_client_dossier_v3("Endesa", raw_input)
    assert coerced["version"] == "3.0"
    assert coerced["client_name"] == "Endesa"
    assert "metadata" in coerced
    assert coerced["metadata"]["schema_version"] == "3.0"

    # Firma criptográfica y verificación del contrato coerced
    signed = sign_dossier(coerced)
    assert "integrity" in signed["metadata"]
    assert verify_dossier_integrity(signed) is True

    # Check idempotency: coercing an already valid V3 returns valid V3
    re_coerced = coerce_client_dossier_v3("Endesa", coerced)
    assert re_coerced["version"] == "3.0"


def test_build_client_context_packet_and_text():
    """Verify context packet construction and prompt text rendering for LLM analysts."""
    dossier = {
        "version": "3.0",
        "metadata": {},
        "profile": {"industry": "Banking & Financial Markets"},
        "business_context": {
            "transformation_horizon": {
                "stage": "H2",
                "label": "Consolidación y Soberanía",
                "rationale": "Migración hacia nube híbrida.",
            }
        },
        "technology_context": {},
        "tower_overrides": {
            "T1": {"target_maturity": 4.5, "business_criticality": 80.0}
        },
        "client_name": "Banco Santander",
    }

    packet = build_client_context_packet(dossier, tower_id="T1")
    assert packet["client_name"] == "Banco Santander"
    assert "Banking" in packet["profile"]["industry"]

    text = build_client_context_text(dossier, tower_id="T1")
    assert "Banco Santander" in text
    assert "Banking & Financial Markets" in text
    assert "H2" in text
