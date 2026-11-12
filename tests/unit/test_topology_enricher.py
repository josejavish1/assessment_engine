"""Unit test suite for TopologyEnricher and Fail-Closed Actuarial Contracts (SR 11-7)."""

from __future__ import annotations

import pytest

from assessment_engine.domain.actuarial.topology_enricher import TopologyEnricher
from assessment_engine.domain.exceptions import ActuarialContractViolationError
from assessment_engine.domain.schemas.actuarial_contracts import (
    ArchitecturalRole,
    DataClassification,
    EnvironmentTier,
)


def test_orc_01_fail_closed_unresolvable_asset_raises_violation() -> None:
    """ORC-01: Asset JSON with unknown names bypassing rules must raise ActuarialContractViolationError."""
    enricher = TopologyEnricher()
    unresolvable_asset = {
        "asset_id": "ASSET-MYSTERY-99",
        "description": "Custom appliance with opaque vendor terminology and no indicators.",
    }

    with pytest.raises(ActuarialContractViolationError) as exc_info:
        enricher.enrich_asset(unresolvable_asset)

    assert "FAIL-CLOSED" in str(exc_info.value)
    assert "environment_tier" in str(exc_info.value)


def test_orc_02_fail_closed_ambiguous_resolution_raises_violation(tmp_path) -> None:
    """ORC-02: Asset matching multiple conflicting rules with identical priority must fail closed."""
    import yaml

    conflicting_rules = {
        "schema_version": "2.0.0-SR117",
        "environment_tier_rules": [
            {
                "rule_id": "RULE-A",
                "assign_value": "PROD_CRITICAL",
                "priority": 10,
                "criteria": {"name_or_finding": ["hybrid"]},
            },
            {
                "rule_id": "RULE-B",
                "assign_value": "LAB_DEV_TEST",
                "priority": 10,
                "criteria": {"name_or_finding": ["hybrid"]},
            },
        ],
        "architectural_role_rules": [
            {
                "rule_id": "ROLE-DEFAULT",
                "assign_value": "DATA_PLANE",
                "priority": 10,
                "criteria": {"name_or_finding": ["hybrid"]},
            }
        ],
    }
    rules_file = tmp_path / "conflicting_rules.yaml"
    rules_file.write_text(yaml.dump(conflicting_rules), encoding="utf-8")

    enricher = TopologyEnricher(rules_path=rules_file)
    asset = {"asset_id": "AMBIGUOUS-01", "name": "hybrid cluster"}

    with pytest.raises(ActuarialContractViolationError) as exc_info:
        enricher.enrich_asset(asset)

    assert "FAIL-CLOSED: Ambiguous topology resolution" in str(exc_info.value)
    assert "RULE-A" in str(exc_info.value) and "RULE-B" in str(exc_info.value)


def test_orc_03_enrichment_provenance_and_sha256_audit_entry() -> None:
    """ORC-03: Valid untagged K8s lab node resolves LAB_DEV_TEST with valid SHA-256 audit entry."""
    enricher = TopologyEnricher()
    k8s_lab_asset = {
        "asset_id": "T2-RVS03",
        "name": "dev-cluster experimental k8s laboratory",
        "finding": "Oportunidad de formalizar estandares en futuros clusters kubernetes de pruebas.",
        "capability": "Container Platform",
    }

    profile, audit_log = enricher.enrich_asset(k8s_lab_asset)

    assert profile.asset_id == "T2-RVS03"
    assert profile.environment_tier == EnvironmentTier.LAB_DEV_TEST
    assert profile.architectural_role == ArchitecturalRole.DATA_PLANE

    assert len(audit_log) == 2  # environment_tier and architectural_role
    env_audit = next(a for a in audit_log if a.inferred_field == "environment_tier")
    assert env_audit.assigned_value == "LAB_DEV_TEST"
    assert env_audit.rule_id == "ENV-LAB-DEV-TEST"
    assert len(env_audit.rule_hash_sha256) == 64  # Valid 64-char hex SHA-256
    assert env_audit.confidence == 1.0


def test_pam_root_resolves_control_plane_and_prod_critical() -> None:
    """Verifies that shared root accounts and PAM vault resolve to CONTROL_PLANE and PROD_CRITICAL."""
    enricher = TopologyEnricher()
    pam_asset = {
        "asset_id": "T6-RVS02",
        "name": "Gestion y Boveda de Accesos Privilegiados PAM Root compartido",
        "finding": "Operacion mediante cuentas root compartidas y credenciales administrativas sin boveda PAM en produccion core.",
        "capability": "Privileged Access Management",
    }

    profile, audit_log = enricher.enrich_asset(pam_asset)

    assert profile.asset_id == "T6-RVS02"
    assert profile.environment_tier == EnvironmentTier.PROD_CRITICAL
    assert profile.architectural_role == ArchitecturalRole.CONTROL_PLANE

    role_audit = next(a for a in audit_log if a.inferred_field == "architectural_role")
    assert role_audit.assigned_value == "CONTROL_PLANE"
    assert role_audit.rule_id == "ROLE-CONTROL-PLANE"


def test_disk_log_saturation_resolves_telemetry_logging() -> None:
    """Verifies that disk and /var/log saturation resolves to TELEMETRY_LOGGING role."""
    enricher = TopologyEnricher()
    disk_asset = {
        "asset_id": "T4-RVS02",
        "name": "Dimensionamiento y Gestion de Logs",
        "finding": "Saturacion de particion /var/log y politicas restrictivas de rotacion de logs en produccion.",
    }

    profile, audit_log = enricher.enrich_asset(disk_asset)

    assert profile.asset_id == "T4-RVS02"
    assert profile.environment_tier == EnvironmentTier.PROD_CRITICAL
    assert profile.architectural_role == ArchitecturalRole.TELEMETRY_LOGGING
