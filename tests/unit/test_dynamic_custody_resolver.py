"""Unit tests for DynamicCustodyResolver (RFC 057).

Verifies context-aware cross-tower risk deduplication and prevention
of actuarial blind spots in partial-scope assessments.
"""

from __future__ import annotations

import pytest

from assessment_engine.domain.services.dynamic_custody_resolver import (
    CustodyRole,
    DynamicCustodyResolver,
)
from assessment_engine.infrastructure.localization import t


def test_full_scope_tangential_remains_deduplicated() -> None:
    """When the target custodian tower is inside active scope, the risk remains tangential."""
    active_scope = {"T1", "T2", "T6"}
    resolver = DynamicCustodyResolver(
        active_towers_scope=active_scope,
        localizer=lambda k, **kw: t(k, locale="es", **kw),
    )

    portfolio = [
        {
            "id": "RVS01",
            "ownership_type": CustodyRole.TANGENTIAL_CONTRIBUTOR.value,
            "primary_risk_ref": "T6.R01",
            "capability": "Identity & Access Governance",
        }
    ]

    resolved = resolver.resolve_portfolio(portfolio, current_tower_id="T2")

    assert len(resolved) == 1
    assert resolved[0]["ownership_type"] == CustodyRole.TANGENTIAL_CONTRIBUTOR.value
    assert "custody_resolution_metadata" not in resolved[0]
    assert resolved[0].get("scope_note") is None


def test_partial_scope_orphaned_risk_is_promoted() -> None:
    """When the target custodian tower is outside active scope, the risk is promoted to primary."""
    active_scope = {"T1", "T2"}  # T6 is omitted!
    resolver = DynamicCustodyResolver(
        active_towers_scope=active_scope,
        localizer=lambda k, **kw: t(k, locale="es", **kw),
    )

    portfolio = [
        {
            "id": "RVS01",
            "ownership_type": CustodyRole.TANGENTIAL_CONTRIBUTOR.value,
            "primary_risk_ref": "T6.R01",
            "capability": "Identity & Access Governance",
        }
    ]

    resolved = resolver.resolve_portfolio(portfolio, current_tower_id="T2")

    assert len(resolved) == 1
    item = resolved[0]
    assert item["ownership_type"] == CustodyRole.PRIMARY_CUSTODIAN.value
    assert item["custody_role"] == CustodyRole.PRIMARY_CUSTODIAN.value

    # Check audit metadata
    meta = item.get("custody_resolution_metadata", {})
    assert meta.get("dynamically_promoted") is True
    assert meta.get("original_custody_role") == CustodyRole.TANGENTIAL_CONTRIBUTOR.value
    assert meta.get("designated_custodian_tower") == "T6"
    assert meta.get("promoted_in_tower") == "T2"

    # Check plain-language scope note
    scope_note = item.get("scope_note", "")
    assert "Nota de Alcance:" in scope_note
    assert "T6" in scope_note
    assert "T6.R01" in scope_note
    assert "no forma parte de los servicios evaluados" in scope_note
    # Ensure zero jargon
    assert "Custodio Principal" not in scope_note
    assert "Gobernanza Actuarial" not in scope_note
    # Ensure zero long dashes
    assert "—" not in scope_note
    assert "–" not in scope_note


def test_dangling_reference_safety() -> None:
    """A tangential risk with a null or unmapped reference is safely promoted without crashing."""
    resolver = DynamicCustodyResolver(
        active_towers_scope={"T1", "T2"},
        localizer=lambda k, **kw: t(k, locale="en", **kw),
    )

    portfolio = [
        {
            "id": "RVS99",
            "ownership_type": CustodyRole.TANGENTIAL_CONTRIBUTOR.value,
            "primary_risk_ref": None,
        }
    ]

    resolved = resolver.resolve_portfolio(portfolio, current_tower_id="T1")

    assert len(resolved) == 1
    item = resolved[0]
    assert item["ownership_type"] == CustodyRole.PRIMARY_CUSTODIAN.value
    assert "Scope Note:" in item.get("scope_note", "")


def test_input_immutability() -> None:
    """Ensures input dictionaries are never mutated by the resolver."""
    resolver = DynamicCustodyResolver(active_towers_scope={"T1"})
    original_risk = {
        "id": "RVS01",
        "ownership_type": CustodyRole.TANGENTIAL_CONTRIBUTOR.value,
        "primary_risk_ref": "T6.R01",
    }

    _ = resolver.resolve_portfolio([original_risk], current_tower_id="T1")

    # Original must remain completely unchanged
    assert original_risk["ownership_type"] == CustodyRole.TANGENTIAL_CONTRIBUTOR.value
    assert "custody_resolution_metadata" not in original_risk
