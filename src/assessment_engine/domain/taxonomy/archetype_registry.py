"""Declarative Domain-to-Archetype Mapping Registry for Polymorphic Open FAIR."""

from __future__ import annotations

import json
import re
import threading
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LossArchetypeType(StrEnum):
    """Canonical Open FAIR Economic Loss Archetypes."""

    AVAILABILITY_OUTAGE = "AVAILABILITY_OUTAGE"
    CAPITAL_INEFFICIENCY = "CAPITAL_INEFFICIENCY"
    PRODUCTIVITY_TOIL = "PRODUCTIVITY_TOIL"
    REGULATORY_AND_BREACH = "REGULATORY_AND_BREACH"


class TowerActuarialMapping(BaseModel):
    """Immutable domain contract binding a technological tower to its economic loss model."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str = Field(..., pattern=r"^T\d{1,2}$", description="Normalized tower code (e.g. T1, T10)")
    canonical_tower_name: str = Field(..., min_length=3)
    primary_archetype: LossArchetypeType
    secondary_archetype: Optional[LossArchetypeType] = None
    default_vulnerability_baseline: float = Field(default=0.20, ge=0.0, le=1.0)
    narrative_semantic_key: str = Field(..., min_length=2)
    primary_metric_label: str = Field(..., min_length=2)
    primary_metric_unit: str = Field(..., min_length=1)
    prohibited_narrative_terms: List[str] = Field(default_factory=list)
    llm_framing_directive: str = Field(..., min_length=10)


class ReceptorWeights(BaseModel):
    """Canonical weights for allocating total ALE into vectors alpha, beta, and gamma."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    vector_alpha_weight: float = Field(..., ge=0.0, le=1.0)
    vector_beta_weight: float = Field(..., ge=0.0, le=1.0)
    vector_gamma_weight: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights_sum(self) -> Any:
        total = self.vector_alpha_weight + self.vector_beta_weight + self.vector_gamma_weight
        if abs(total - 1.0) > 1e-5:
            raise ValueError(f"Receptor weights must sum to 1.0, got {total}")
        return self


class ActuarialTaxonomyRegistry(BaseModel):
    """Immutable registry of all 10 domain tower actuarial mappings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: str = Field(default="2.0.0")
    doctrine: str = Field(...)
    mappings: Dict[str, TowerActuarialMapping]
    operational_archetypes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    receptor_weights: Optional[Dict[LossArchetypeType, ReceptorWeights]] = Field(default_factory=dict)

    def get_mapping_for_tower(self, raw_tower_id: str) -> TowerActuarialMapping:
        """Retrieves the actuarial mapping for any tower code, normalizing representations."""
        if not raw_tower_id:
            raise ValueError("Tower ID cannot be empty.")

        cleaned = raw_tower_id.strip().upper()
        # Normalize T01 -> T1, T08 -> T8
        match = re.search(r"T0?(\d+)", cleaned)
        normalized_key = f"T{match.group(1)}" if match else cleaned

        if normalized_key in self.mappings:
            return self.mappings[normalized_key]

        # Dynamic / custom enterprise domain fallback (e.g. D_FAC, D_OT, D_AI, D_SEC, EDGE_01)
        # Sourced from standard enterprise infrastructure baseline (RFC 088 / SR 11-7 Section II)
        dynamic_defaults: Dict[str, str] = {
            "D_FAC": "T1",
            "D_OT": "T1",
            "D_AI": "T4",
            "D_SEC": "T6",
            "D_FIN": "T8",
            "D_EUC": "T9",
        }
        if normalized_key in dynamic_defaults and dynamic_defaults[normalized_key] in self.mappings:
            target_map = self.mappings[dynamic_defaults[normalized_key]]
            return TowerActuarialMapping(
                tower_id=cleaned,
                domain_name=f"Dynamic Domain ({cleaned})",
                primary_archetype=target_map.primary_archetype,
                secondary_archetype=target_map.secondary_archetype,
                default_cmmi_benchmark=target_map.default_cmmi_benchmark,
                vector_alpha_weight=target_map.vector_alpha_weight,
                vector_beta_weight=target_map.vector_beta_weight,
                vector_gamma_weight=target_map.vector_gamma_weight,
            )

        # Generic enterprise fallback for arbitrary dynamic towers
        t1_map = self.mappings.get("T1")
        if t1_map:
            return TowerActuarialMapping(
                tower_id=cleaned,
                domain_name=f"Enterprise Operational Tower ({cleaned})",
                primary_archetype=LossArchetypeType.AVAILABILITY_OUTAGE,
                secondary_archetype=LossArchetypeType.PRODUCTIVITY_TOIL,
                default_cmmi_benchmark=2.5,
                vector_alpha_weight=t1_map.vector_alpha_weight,
                vector_beta_weight=t1_map.vector_beta_weight,
                vector_gamma_weight=t1_map.vector_gamma_weight,
            )

        raise KeyError(
            f"Forensic Taxonomy Error: Tower ID '{raw_tower_id}' (normalized: '{normalized_key}') "
            f"is not mapped in ActuarialTaxonomyRegistry. Available towers: {list(self.mappings.keys())}"
        )

    @classmethod
    def from_json_file(cls, path: Path) -> ActuarialTaxonomyRegistry:
        """Loads and parses the registry from an external JSON specification."""
        if not path.is_file():
            raise FileNotFoundError(f"Actuarial archetypes configuration file not found at: {path}")

        raw_data = json.loads(path.read_text(encoding="utf-8"))
        return cls.model_validate(raw_data)


ActuarialTaxonomyRegistry.model_rebuild()

_REGISTRY_LOCK = threading.Lock()
_CACHED_REGISTRY: Optional[ActuarialTaxonomyRegistry] = None


def get_actuarial_archetype_registry() -> ActuarialTaxonomyRegistry:
    """Thread-safe singleton provider for the Actuarial Taxonomy Registry."""
    global _CACHED_REGISTRY
    if _CACHED_REGISTRY is not None:
        return _CACHED_REGISTRY

    with _REGISTRY_LOCK:
        if _CACHED_REGISTRY is not None:
            return _CACHED_REGISTRY

        config_path = (
            Path(__file__).resolve().parents[4]
            / "engine_config"
            / "taxonomy_actuarial_archetypes.json"
        )
        _CACHED_REGISTRY = ActuarialTaxonomyRegistry.from_json_file(config_path)
        return _CACHED_REGISTRY
