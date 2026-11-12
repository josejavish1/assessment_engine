"""Domain schemas and contracts for Fail-Closed Topology and Actuarial Ingestion (SR 11-7)."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnvironmentTier(str, Enum):
    """Operational environment classification with deterministic revenue loss scaling."""

    PROD_CRITICAL = "PROD_CRITICAL"      # Core production; 100% operational revenue dependency (omega = 1.00)
    PROD_SUPPORT = "PROD_SUPPORT"        # Peripheral production/auxiliary; partial revenue dependency (omega = 0.35)
    STAGING_UAT = "STAGING_UAT"          # Pre-production validation; zero revenue loss (omega = 0.00)
    LAB_DEV_TEST = "LAB_DEV_TEST"        # Sandbox, experimental, or test lab; strictly zero revenue loss (omega = 0.00)


class ArchitecturalRole(str, Enum):
    """Architectural role and privilege tier governing blast radius and cascading potential."""

    CONTROL_PLANE = "CONTROL_PLANE"            # Identity root, hypervisor cluster managers, PAM, IAM, core switching
    DATA_PLANE = "DATA_PLANE"                  # Production transaction processing, database engines, ERP application servers
    MANAGEMENT_PLANE = "MANAGEMENT_PLANE"      # Configuration management, CI/CD runners, deployment controllers
    TELEMETRY_LOGGING = "TELEMETRY_LOGGING"    # Monitoring, centralized logging, SIEM ingest agents
    STANDALONE_ENDPOINT = "STANDALONE_ENDPOINT"# User endpoints, localized utility nodes, peripheral scanners


class CausalNature(str, Enum):
    """Physical or operational causal mechanism triggering the threat event."""

    MALICIOUS_EXFILTRATION = "MALICIOUS_EXFILTRATION"            # Targeted data theft, credential compromise, active exfiltration
    DESTRUCTIVE_SABOTAGE = "DESTRUCTIVE_SABOTAGE"                # Ransomware encryption, wiper malware, hypervisor purge
    ACCIDENTAL_PHYSICAL_SEVERANCE = "ACCIDENTAL_PHYSICAL_SEVERANCE" # Backhoe cable cuts, telecom backhaul disruption, power grid drop
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"                  # Disk full, /var/log saturation, memory leaks, runaway queries
    CONFIGURATION_DRIFT = "CONFIGURATION_DRIFT"                  # Human configuration errors, routing misconfigurations, expired certificates


class DataClassification(str, Enum):
    """Statutory data classification dictating regulatory exposure eligibility."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    RESTRICTED_CONFIDENTIAL = "RESTRICTED_CONFIDENTIAL"
    REGULATED_PII_FINANCIAL = "REGULATED_PII_FINANCIAL"          # Triggers GDPR Art. 83 / NIS2 / DORA statutory fine mechanisms


class EnrichmentAuditEntry(BaseModel):
    """Immutable provenance record documenting deterministic topology resolution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_id: str = Field(..., description="Target asset identifier.")
    inferred_field: str = Field(..., description="Field resolved by the enricher.")
    assigned_value: str = Field(..., description="Assigned enumeration string.")
    rule_id: str = Field(..., description="ID of the matching classification rule.")
    rule_hash_sha256: str = Field(..., description="SHA-256 hash of the exact rule definition.")
    confidence: float = Field(default=1.0, ge=1.0, le=1.0, description="Deterministic confidence score.")


class ThreatVectorPhysics(BaseModel):
    """Causal physics specification dictating empirical MTTR and regulatory liability."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    causal_nature: CausalNature = Field(..., description="Root cause failure mechanism.")
    min_hours: float = Field(..., ge=0.0, description="Minimum recovery duration in hours.")
    mode_hours: float = Field(..., ge=0.0, description="Most likely recovery duration in hours.")
    max_hours: float = Field(..., ge=0.0, description="Maximum plausible recovery duration in hours.")
    buffer_hours: float = Field(default=0.0, ge=0.0, description="Operational buffer / process inertia tolerance in hours.")

    @field_validator("max_hours")
    @classmethod
    def validate_pert_ordering(cls, v: float, info: Any) -> float:
        data = info.data
        mode = data.get("mode_hours")
        min_val = data.get("min_hours")
        if min_val is not None and mode is not None:
            if not (min_val <= mode <= v):
                raise ValueError(
                    f"Invalid PERT bounds: min ({min_val}) <= mode ({mode}) <= max ({v}) violated."
                )
        return v


class AssetActuarialProfile(BaseModel):
    """Strict fail-closed actuarial contract for an asset or assessed component."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    asset_id: str = Field(..., min_length=1, description="Unique asset or capability node identifier.")
    environment_tier: EnvironmentTier = Field(..., description="Mandatory operational environment tier.")
    architectural_role: ArchitecturalRole = Field(..., description="Mandatory architectural role.")
    data_classification: DataClassification = Field(default=DataClassification.INTERNAL, description="Data privacy tier.")
    hourly_revenue_contribution: float = Field(default=0.0, ge=0.0, description="Direct hourly business revenue generation.")
    reconstitution_labor_cost: float = Field(default=0.0, ge=0.0, description="Fixed internal IT/SRE labor cost for rebuild.")
    operational_buffer_hours: float = Field(default=0.0, ge=0.0, description="Process decoupling tolerance buffer.")
