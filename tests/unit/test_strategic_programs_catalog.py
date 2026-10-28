from __future__ import annotations

import pytest

from assessment_engine.infrastructure.config_loader import (
    load_strategic_programs,
    resolve_canonical_program_id,
)


def test_load_strategic_programs_structure():
    """Verify that canonical strategic programs are loaded with schema integrity."""
    catalog = load_strategic_programs()
    assert "programs" in catalog
    programs = catalog["programs"]

    # Must contain at least the 7 foundational enterprise architecture programs
    assert len(programs) >= 7

    program_ids = {p["id"] for p in programs}
    expected_foundational = {
        "PROG_OBSERVABILITY",
        "PROG_ZERO_TRUST_IAM",
        "PROG_SOVEREIGN_CLOUD",
        "PROG_NETWORK_FABRIC",
        "PROG_CORE_MODERNIZATION",
        "PROG_DATA_AI_PLATFORM",
        "PROG_BUSINESS_RESILIENCE",
    }
    assert expected_foundational.issubset(program_ids)

    for prog in programs:
        assert "id" in prog
        assert "name" in prog
        assert "lead_towers" in prog
        assert "description" in prog
        assert isinstance(prog["lead_towers"], list)


def test_resolve_canonical_program_id_exact():
    """Verify exact program_id resolution."""
    assert (
        resolve_canonical_program_id("PROG_OBSERVABILITY")
        == "PROG_OBSERVABILITY"
    )
    assert (
        resolve_canonical_program_id("PROG_ZERO_TRUST_IAM")
        == "PROG_ZERO_TRUST_IAM"
    )


def test_resolve_canonical_program_id_fuzzy_alias():
    """Verify semantic and alias matching for natural language initiative titles."""
    assert (
        resolve_canonical_program_id(
            "Implantación de Observabilidad Centralizada y Telemetría"
        )
        == "PROG_OBSERVABILITY"
    )
    assert (
        resolve_canonical_program_id(
            "Despliegue de Arquitectura Zero Trust y Gestión de Identidades"
        )
        == "PROG_ZERO_TRUST_IAM"
    )
    assert (
        resolve_canonical_program_id(
            "Migración y Despliegue de Landing Zone en Cloud Híbrido"
        )
        == "PROG_SOVEREIGN_CLOUD"
    )
    assert (
        resolve_canonical_program_id(
            "Plan de Continuidad de Negocio y Disaster Recovery Geográfico"
        )
        == "PROG_BUSINESS_RESILIENCE"
    )


def test_resolve_canonical_program_id_local_fallback():
    """Verify that hyper-local, single-tower initiatives do not get falsely matched to global programs."""
    assert (
        resolve_canonical_program_id("Sustitución de baterías de SAI de la Sala A")
        is None
    )
    assert (
        resolve_canonical_program_id("Actualización de firmware de switch ToR 4")
        is None
    )
