"""Unit tests for the Declarative Domain-to-Archetype Mapping Registry."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from assessment_engine.domain.taxonomy.archetype_registry import (
    ActuarialTaxonomyRegistry,
    LossArchetypeType,
    TowerActuarialMapping,
    get_actuarial_archetype_registry,
)


def test_registry_loads_all_10_towers() -> None:
    registry = get_actuarial_archetype_registry()
    assert isinstance(registry, ActuarialTaxonomyRegistry)
    assert len(registry.mappings) == 10

    for i in range(1, 11):
        t_id = f"T{i}"
        mapping = registry.get_mapping_for_tower(t_id)
        assert mapping.tower_id == t_id
        assert isinstance(mapping.primary_archetype, LossArchetypeType)
        assert len(mapping.llm_framing_directive) > 10


def test_tower_code_normalization() -> None:
    registry = get_actuarial_archetype_registry()

    # T01 -> T1
    m1 = registry.get_mapping_for_tower("T01")
    assert m1.tower_id == "T1"
    assert m1.canonical_tower_name == "Physical Data Center & Facilities"

    # t8 -> T8
    m8 = registry.get_mapping_for_tower("t8")
    assert m8.tower_id == "T8"
    assert m8.canonical_tower_name == "Strategy, Governance & FinOps"

    # T08 -> T8
    m8_padded = registry.get_mapping_for_tower("T08")
    assert m8_padded.tower_id == "T8"


def test_finops_archetype_contract() -> None:
    registry = get_actuarial_archetype_registry()
    finops = registry.get_mapping_for_tower("T8")

    assert finops.primary_archetype == LossArchetypeType.CAPITAL_INEFFICIENCY
    assert "clearing halt" in finops.prohibited_narrative_terms
    assert "downtime per hour" in finops.prohibited_narrative_terms
    assert finops.primary_metric_unit == "/year"
    assert "FORBIDDEN: Do not mention payment clearing halts" in finops.llm_framing_directive


def test_workplace_archetype_contract() -> None:
    registry = get_actuarial_archetype_registry()
    workplace = registry.get_mapping_for_tower("T9")

    assert workplace.primary_archetype == LossArchetypeType.PRODUCTIVITY_TOIL
    assert "clearing halt" in workplace.prohibited_narrative_terms
    assert workplace.primary_metric_unit == "hours/year"


def test_security_archetype_contract() -> None:
    registry = get_actuarial_archetype_registry()
    sec = registry.get_mapping_for_tower("T6")

    assert sec.primary_archetype == LossArchetypeType.REGULATORY_AND_BREACH
    assert "downtime per hour" in sec.prohibited_narrative_terms
    assert sec.primary_metric_unit == "/event"


def test_immutability_enforced() -> None:
    registry = get_actuarial_archetype_registry()
    mapping = registry.get_mapping_for_tower("T1")

    with pytest.raises(ValidationError):
        # Attempting to mutate a frozen Pydantic model must fail
        mapping.primary_archetype = LossArchetypeType.CAPITAL_INEFFICIENCY  # type: ignore[misc]


def test_unknown_tower_raises_key_error() -> None:
    registry = get_actuarial_archetype_registry()

    with pytest.raises(KeyError, match="Unmapped Tower ID|not mapped in ActuarialTaxonomyRegistry"):
        registry.get_mapping_for_tower("T99")

    with pytest.raises(ValueError, match="Tower ID cannot be empty"):
        registry.get_mapping_for_tower("")
