"""Declarative Domain-to-Archetype Mapping Registry for Polymorphic Open FAIR."""

from __future__ import annotations

import json
import re
import threading
from enum import StrEnum
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    tower_id: str = Field(
        ...,
        pattern=r"^(?:T\d{1,2}|D_[A-Z0-9_]+|[A-Z][A-Z0-9_]{1,31})$",
        description="Normalized canonical or supported dynamic/custom tower code (e.g. T1, D_FAC, EDGE_01)",
    )
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
        if not raw_tower_id or not isinstance(raw_tower_id, str) or not raw_tower_id.strip():
            raise ValueError("Tower ID cannot be empty.")

        cleaned = raw_tower_id.strip().upper()

        # 1. Canonical tower normalization: T01 -> T1, T08 -> T8
        match = re.search(r"^T0?(\d+)$", cleaned)
        if match:
            normalized_key = f"T{match.group(1)}"
            if normalized_key in self.mappings:
                return self.mappings[normalized_key]
            # Canonical IDs not in registry (e.g. T99, T00, T11) MUST raise KeyError
            raise KeyError(
                f"Forensic Taxonomy Error: Canonical tower ID '{raw_tower_id}' (normalized: '{normalized_key}') "
                f"is not mapped in ActuarialTaxonomyRegistry. Available towers: {list(self.mappings.keys())}"
            )

        # 2. Known dynamic domain aliases (RFC 088 / SR 11-7 Section II)
        dynamic_defaults: Dict[str, str] = {
            "D_FAC": "T1",
            "D_OT": "T1",
            "D_AI": "T4",
            "D_SEC": "T6",
            "D_FIN": "T8",
            "D_EUC": "T9",
        }
        if cleaned in dynamic_defaults and dynamic_defaults[cleaned] in self.mappings:
            target_map = self.mappings[dynamic_defaults[cleaned]]
            return TowerActuarialMapping(
                tower_id=cleaned,
                canonical_tower_name=f"Dynamic Domain ({cleaned} -> {target_map.canonical_tower_name})",
                primary_archetype=target_map.primary_archetype,
                secondary_archetype=target_map.secondary_archetype,
                default_vulnerability_baseline=target_map.default_vulnerability_baseline,
                narrative_semantic_key=target_map.narrative_semantic_key,
                primary_metric_label=target_map.primary_metric_label,
                primary_metric_unit=target_map.primary_metric_unit,
                prohibited_narrative_terms=list(target_map.prohibited_narrative_terms),
                llm_framing_directive=target_map.llm_framing_directive,
            )

        # 3. Arbitrary dynamic D_* towers inherit T1 infrastructure baseline
        t1_map = self.mappings.get("T1")
        if cleaned.startswith("D_") and t1_map:
            return TowerActuarialMapping(
                tower_id=cleaned,
                canonical_tower_name=f"Dynamic Operational Domain ({cleaned})",
                primary_archetype=t1_map.primary_archetype,
                secondary_archetype=t1_map.secondary_archetype,
                default_vulnerability_baseline=t1_map.default_vulnerability_baseline,
                narrative_semantic_key=t1_map.narrative_semantic_key,
                primary_metric_label=t1_map.primary_metric_label,
                primary_metric_unit=t1_map.primary_metric_unit,
                prohibited_narrative_terms=list(t1_map.prohibited_narrative_terms),
                llm_framing_directive=t1_map.llm_framing_directive,
            )

        # 4. Arbitrary custom domain identifiers (e.g. EDGE_01) inherit T1 infrastructure baseline
        prohibited_custom_ids = {"UNKNOWN", "NONE", "NULL", "UNDEFINED", "N_A", "NA", "DEFAULT"}
        if (
            cleaned not in prohibited_custom_ids
            and re.match(r"^[A-Z][A-Z0-9_]{1,31}$", cleaned)
            and t1_map is not None
        ):
            return TowerActuarialMapping(
                tower_id=cleaned,
                canonical_tower_name=f"Custom Assessment Domain ({cleaned})",
                primary_archetype=t1_map.primary_archetype,
                secondary_archetype=t1_map.secondary_archetype,
                default_vulnerability_baseline=t1_map.default_vulnerability_baseline,
                narrative_semantic_key=t1_map.narrative_semantic_key,
                primary_metric_label=t1_map.primary_metric_label,
                primary_metric_unit=t1_map.primary_metric_unit,
                prohibited_narrative_terms=list(t1_map.prohibited_narrative_terms),
                llm_framing_directive=t1_map.llm_framing_directive,
            )

        raise KeyError(
            f"Forensic Taxonomy Error: Tower ID '{raw_tower_id}' (normalized: '{cleaned}') "
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
