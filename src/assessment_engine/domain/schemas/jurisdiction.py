"""Domain schemas for Jurisdictional Architectural Sovereignty."""

from __future__ import annotations

from enum import Enum, IntEnum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CloudSovereigntyLevel(str, Enum):
    """Legacy coarse-grained sovereignty level enum retained for backwards compatibility."""

    PUBLIC_CLOUD = "Public Cloud"
    SOVEREIGN_CLOUD = "Sovereign Cloud"
    AIR_GAPPED_ON_PREMISES = "Air-Gapped On-Premises"


class NetworkTopologyLevel(IntEnum):
    """Dimension 1: Physical and logical network topology isolation levels."""

    PUBLIC_ROUTABLE = 10
    VPC_PEERING = 20
    DEDICATED_INTERCONNECT = 30
    AIR_GAP_DIODE = 50


class KeyCustodyLevel(IntEnum):
    """Dimension 2: Cryptographic key custody and HSM hardware boundary levels."""

    CSP_MANAGED = 10
    CUSTOMER_KMS = 20
    DEDICATED_CLOUD_HSM_L3 = 30
    EXTERNAL_HYOK_SOVEREIGN_HSM_L4 = 40


class ConfidentialComputeLevel(IntEnum):
    """Dimension 3: Memory encryption and hardware enclave attestation levels."""

    STANDARD_HYPERVISOR = 10
    MEMORY_ENCRYPTION_AMD_SEV_TDX = 20
    ATTESTED_HARDWARE_ENCLAVE = 30


class LegalImmunityLevel(IntEnum):
    """Dimension 4: Extraterritorial legal immunity and jurisdictional control levels."""

    FOREIGN_COMPULSION_CLOUD_ACT = 10
    EU_SOVEREIGN_PARTNER = 20
    DOMESTIC_LEGAL_ENTITY_ONLY = 30


class OperationalResidencyLevel(IntEnum):
    """Dimension 5: Operational support residency and security clearance levels."""

    FOLLOW_THE_SUN_SUPPORT = 10
    REGIONAL_RESIDENT_ENGINEERS = 20
    SECURITY_CLEARED_CITIZENS = 30


class SovereigntyFrameworkStandard(str, Enum):
    """International and regional sovereign cloud compliance frameworks."""

    GAIA_X_LEVEL_3 = "Gaia-X Label Level 3"
    BSI_C5 = "BSI C5"
    SAUDI_NCA_CCRF = "Saudi NCA CCRF"


class SovereigntyPostureVector(BaseModel):
    """Immutable 5-dimensional lattice modeling architectural and legal sovereignty posture."""

    model_config = ConfigDict(frozen=True)

    network_topology: NetworkTopologyLevel = Field(
        default=NetworkTopologyLevel.PUBLIC_ROUTABLE,
        description="Physical and logical network boundary isolation level (10 -> 20 -> 30 -> 50).",
    )
    key_custody: KeyCustodyLevel = Field(
        default=KeyCustodyLevel.CSP_MANAGED,
        description="Cryptographic key custody and hardware security module boundary (10 -> 20 -> 30 -> 40).",
    )
    confidential_compute: ConfidentialComputeLevel = Field(
        default=ConfidentialComputeLevel.STANDARD_HYPERVISOR,
        description="Runtime memory encryption and hardware enclave attestation posture (10 -> 20 -> 30).",
    )
    legal_immunity: LegalImmunityLevel = Field(
        default=LegalImmunityLevel.FOREIGN_COMPULSION_CLOUD_ACT,
        description="Immunity from extraterritorial legal compulsion such as US CLOUD Act (10 -> 20 -> 30).",
    )
    operational_residency: OperationalResidencyLevel = Field(
        default=OperationalResidencyLevel.FOLLOW_THE_SUN_SUPPORT,
        description="Citizenship, residency, and security clearance of operational personnel (10 -> 20 -> 30).",
    )

    @property
    def composite_score(self) -> int:
        """Calculates the aggregate posture score across all 5 sovereignty dimensions."""
        return (
            int(self.network_topology)
            + int(self.key_custody)
            + int(self.confidential_compute)
            + int(self.legal_immunity)
            + int(self.operational_residency)
        )

    def dominates(self, required: SovereigntyPostureVector) -> bool:
        """Partial order comparator on the 5-dimensional sovereignty lattice.

        Returns True if and only if every dimension of this posture vector
        is greater than or equal to the corresponding dimension of `required`.
        """
        return (
            self.network_topology >= required.network_topology
            and self.key_custody >= required.key_custody
            and self.confidential_compute >= required.confidential_compute
            and self.legal_immunity >= required.legal_immunity
            and self.operational_residency >= required.operational_residency
        )

    def dimension_deficits(self, required: SovereigntyPostureVector) -> Dict[str, int]:
        """Returns a dictionary of dimensions where this vector falls short of `required`."""
        deficits: Dict[str, int] = {}
        if self.network_topology < required.network_topology:
            deficits["network_topology"] = int(required.network_topology) - int(self.network_topology)
        if self.key_custody < required.key_custody:
            deficits["key_custody"] = int(required.key_custody) - int(self.key_custody)
        if self.confidential_compute < required.confidential_compute:
            deficits["confidential_compute"] = int(required.confidential_compute) - int(self.confidential_compute)
        if self.legal_immunity < required.legal_immunity:
            deficits["legal_immunity"] = int(required.legal_immunity) - int(self.legal_immunity)
        if self.operational_residency < required.operational_residency:
            deficits["operational_residency"] = int(required.operational_residency) - int(self.operational_residency)
        return deficits

    def satisfies_gaia_x_level_3(self) -> bool:
        """Evaluates full compliance against Gaia-X Label Level 3 invariants.

        Requires strict immunity from foreign legal compulsion (Domestic Legal Entity),
        external HYOK sovereign HSM or dedicated cloud HSM L3+, memory encryption or
        attested enclave, dedicated interconnect+, and security-cleared domestic operators.
        """
        return self.dominates(GAIA_X_LEVEL_3_BASELINE_VECTOR)

    def satisfies_bsi_c5(self) -> bool:
        """Evaluates full compliance against German BSI C5 sovereign cloud invariants."""
        return self.dominates(BSI_C5_BASELINE_VECTOR)

    def satisfies_saudi_nca_ccrf(self) -> bool:
        """Evaluates full compliance against Saudi NCA Cloud Cybersecurity Regulatory Framework (CCRF)."""
        return self.dominates(SAUDI_NCA_CCRF_BASELINE_VECTOR)

    def evaluate_framework_compliance(self) -> Dict[str, bool]:
        """Evaluates compliance across all canonical sovereign regulatory frameworks."""
        return {
            SovereigntyFrameworkStandard.GAIA_X_LEVEL_3.value: self.satisfies_gaia_x_level_3(),
            SovereigntyFrameworkStandard.BSI_C5.value: self.satisfies_bsi_c5(),
            SovereigntyFrameworkStandard.SAUDI_NCA_CCRF.value: self.satisfies_saudi_nca_ccrf(),
        }

    @classmethod
    def from_legacy_level(cls, level: CloudSovereigntyLevel | str) -> SovereigntyPostureVector:
        """Projects a coarse-grained legacy CloudSovereigntyLevel onto the 5D posture lattice."""
        normalized = level.value if isinstance(level, CloudSovereigntyLevel) else str(level).strip()
        if normalized == CloudSovereigntyLevel.AIR_GAPPED_ON_PREMISES.value:
            return cls(
                network_topology=NetworkTopologyLevel.AIR_GAP_DIODE,
                key_custody=KeyCustodyLevel.EXTERNAL_HYOK_SOVEREIGN_HSM_L4,
                confidential_compute=ConfidentialComputeLevel.ATTESTED_HARDWARE_ENCLAVE,
                legal_immunity=LegalImmunityLevel.DOMESTIC_LEGAL_ENTITY_ONLY,
                operational_residency=OperationalResidencyLevel.SECURITY_CLEARED_CITIZENS,
            )
        if normalized == CloudSovereigntyLevel.SOVEREIGN_CLOUD.value:
            return cls(
                network_topology=NetworkTopologyLevel.DEDICATED_INTERCONNECT,
                key_custody=KeyCustodyLevel.DEDICATED_CLOUD_HSM_L3,
                confidential_compute=ConfidentialComputeLevel.MEMORY_ENCRYPTION_AMD_SEV_TDX,
                legal_immunity=LegalImmunityLevel.EU_SOVEREIGN_PARTNER,
                operational_residency=OperationalResidencyLevel.REGIONAL_RESIDENT_ENGINEERS,
            )
        return cls(
            network_topology=NetworkTopologyLevel.PUBLIC_ROUTABLE,
            key_custody=KeyCustodyLevel.CSP_MANAGED,
            confidential_compute=ConfidentialComputeLevel.STANDARD_HYPERVISOR,
            legal_immunity=LegalImmunityLevel.FOREIGN_COMPULSION_CLOUD_ACT,
            operational_residency=OperationalResidencyLevel.FOLLOW_THE_SUN_SUPPORT,
        )


GAIA_X_LEVEL_3_BASELINE_VECTOR = SovereigntyPostureVector(
    network_topology=NetworkTopologyLevel.DEDICATED_INTERCONNECT,
    key_custody=KeyCustodyLevel.EXTERNAL_HYOK_SOVEREIGN_HSM_L4,
    confidential_compute=ConfidentialComputeLevel.MEMORY_ENCRYPTION_AMD_SEV_TDX,
    legal_immunity=LegalImmunityLevel.DOMESTIC_LEGAL_ENTITY_ONLY,
    operational_residency=OperationalResidencyLevel.SECURITY_CLEARED_CITIZENS,
)

BSI_C5_BASELINE_VECTOR = SovereigntyPostureVector(
    network_topology=NetworkTopologyLevel.VPC_PEERING,
    key_custody=KeyCustodyLevel.DEDICATED_CLOUD_HSM_L3,
    confidential_compute=ConfidentialComputeLevel.MEMORY_ENCRYPTION_AMD_SEV_TDX,
    legal_immunity=LegalImmunityLevel.EU_SOVEREIGN_PARTNER,
    operational_residency=OperationalResidencyLevel.REGIONAL_RESIDENT_ENGINEERS,
)

SAUDI_NCA_CCRF_BASELINE_VECTOR = SovereigntyPostureVector(
    network_topology=NetworkTopologyLevel.DEDICATED_INTERCONNECT,
    key_custody=KeyCustodyLevel.DEDICATED_CLOUD_HSM_L3,
    confidential_compute=ConfidentialComputeLevel.MEMORY_ENCRYPTION_AMD_SEV_TDX,
    legal_immunity=LegalImmunityLevel.DOMESTIC_LEGAL_ENTITY_ONLY,
    operational_residency=OperationalResidencyLevel.SECURITY_CLEARED_CITIZENS,
)


class JurisdictionSovereigntyProfile(BaseModel):
    """Encapsulates territorial architectural invariants and sovereign cloud requirements for a jurisdiction."""

    name: str = Field(description="Full jurisdiction designation, e.g. Germany / DACH & Central Europe.")
    region_code: str = Field(description="ISO 3166-1 alpha-2 country code or region tag, e.g. DE, ES, US.")
    sovereign_cloud_providers: List[str] = Field(
        default_factory=list,
        description="Qualified sovereign cloud and datacenter providers with regional enclaves.",
    )
    architectural_invariants: List[str] = Field(
        default_factory=list,
        description="Mandatory technical and operational architecture invariants required in this jurisdiction.",
    )
    connectivity_standards: List[str] = Field(
        default_factory=list,
        description="Direct peering, interconnection and physical encryption network standards.",
    )
    primary_hsm_standard: str = Field(
        default="FIPS 140-2 Level 3",
        description="Jurisdiction-mandated hardware security module (HSM) qualification standard.",
    )
    data_residency_rules: List[str] = Field(
        default_factory=list,
        description="Legal and technical data boundary, custody, and residency requirements.",
    )
    minimum_posture_vector: Optional[SovereigntyPostureVector] = Field(
        default=None,
        description="Optional minimum 5-dimensional sovereignty posture lattice required by the jurisdiction.",
    )
    regulatory_frameworks: List[str] = Field(
        default_factory=list,
        description="Applicable regulatory sovereignty frameworks (e.g., Gaia-X Label Level 3, BSI C5, Saudi NCA CCRF).",
    )


class JurisdictionalRegistry(BaseModel):
    """Top-level registry mapping region codes to their corresponding sovereign profiles."""

    version: str = "1.0.0"
    jurisdictions: Dict[str, JurisdictionSovereigntyProfile] = Field(default_factory=dict)
