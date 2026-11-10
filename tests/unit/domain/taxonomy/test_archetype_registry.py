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

    with pytest.raises(KeyError, match="Canonical tower ID 'T99'|Unmapped Tower ID|not mapped in ActuarialTaxonomyRegistry"):
        registry.get_mapping_for_tower("T99")

    with pytest.raises(ValueError, match="Tower ID cannot be empty"):
        registry.get_mapping_for_tower("")


def test_dynamic_tower_dfac_inheritance() -> None:
    registry = get_actuarial_archetype_registry()
    mapping = registry.get_mapping_for_tower("D_FAC")
    t1_map = registry.get_mapping_for_tower("T1")

    assert mapping.tower_id == "D_FAC"
    assert mapping.primary_archetype == t1_map.primary_archetype
    assert mapping.default_vulnerability_baseline == t1_map.default_vulnerability_baseline
    assert "D_FAC" in mapping.canonical_tower_name
    # Must survive roundtrip serialization and model validation
    validated = TowerActuarialMapping.model_validate(mapping.model_dump())
    assert validated.tower_id == "D_FAC"


def test_custom_domain_generic_fallback() -> None:
    registry = get_actuarial_archetype_registry()
    mapping = registry.get_mapping_for_tower("EDGE_01")
    t1_map = registry.get_mapping_for_tower("T1")

    assert mapping.tower_id == "EDGE_01"
    assert mapping.primary_archetype == t1_map.primary_archetype
    assert mapping.classification_confidence == "UNCONFIRMED"
    assert mapping.review_required is True
    # Must survive roundtrip serialization and model validation
    validated = TowerActuarialMapping.model_validate(mapping.model_dump())
    assert validated.tower_id == "EDGE_01"


def test_canonical_unregistered_t99_raises_key_error() -> None:
    registry = get_actuarial_archetype_registry()

    with pytest.raises(KeyError, match="Canonical tower ID 'T99'.*is not mapped"):
        registry.get_mapping_for_tower("T99")


def test_prohibited_sentinels_raise_key_error() -> None:
    registry = get_actuarial_archetype_registry()
    for sentinel in ["UNKNOWN", "NONE", "NULL", "UNDEFINED", "DEFAULT"]:
        with pytest.raises(KeyError):
            registry.get_mapping_for_tower(sentinel)
