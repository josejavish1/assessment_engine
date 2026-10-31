"""Authoritative Ontology Registry and Boot-Time Bijective Gatekeeper."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from pydantic import PrivateAttr, model_validator

from assessment_engine.infrastructure.ontology.exceptions import OntologyIntegrityError
from assessment_engine.infrastructure.ontology.models import (
    CanonicalControlId,
    ControlBenchmarkMapping,
    IndustryProfile,
    Polarity,
    StrictBaseModel,
    TowerDefinition,
)

logger = logging.getLogger(__name__)


class OntologyRegistry(StrictBaseModel):
    """Authoritative boot-time gatekeeper validating bijective integrity across towers and benchmarks."""

    towers: dict[str, TowerDefinition]
    profiles: dict[str, IndustryProfile]
    _benchmark_index: dict[tuple[str, CanonicalControlId], ControlBenchmarkMapping] = PrivateAttr(
        default_factory=dict
    )

    @model_validator(mode="after")
    def verify_bipartite_graph_integrity(self) -> OntologyRegistry:
        """Formal verification of the ontology graph, polarity coherence, and O(1) index construction."""
        if not self.towers or not self.profiles:
            raise OntologyIntegrityError(
                "OntologyRegistry requires at least one TowerDefinition and one IndustryProfile."
            )

        orphan_controls_by_profile: dict[str, set[str]] = {}
        dangling_refs_by_profile: dict[str, set[str]] = {}
        index: dict[tuple[str, CanonicalControlId], ControlBenchmarkMapping] = {}

        # Global uniqueness tracking across all towers
        global_pillars: dict[str, str] = {}
        global_kpis: dict[str, str] = {}
        control_polarities: dict[CanonicalControlId, Polarity] = {}

        # 1. Pre-compute control sets per tower, check global ID collisions, and verify weights
        tower_to_controls: dict[str, set[CanonicalControlId]] = {}
        for tower_key, tower in self.towers.items():
            if tower_key != tower.tower_id:
                raise OntologyIntegrityError(
                    f"Tower dictionary key '{tower_key}' mismatches internal tower_id '{tower.tower_id}'."
                )

            total_weight = math.fsum(p.weight for p in tower.pillars)
            if abs(total_weight - 1.0) > 1e-5:
                raise OntologyIntegrityError(
                    f"Tower '{tower_key}' pillar weights sum to {total_weight:.4f}, expected 1.0."
                )

            controls: set[CanonicalControlId] = set()
            for pillar in tower.pillars:
                if pillar.pillar_id in global_pillars:
                    raise OntologyIntegrityError(
                        f"Global pillar_id collision: '{pillar.pillar_id}' defined in both "
                        f"'{global_pillars[pillar.pillar_id]}' and '{tower_key}'."
                    )
                global_pillars[pillar.pillar_id] = tower_key

                for kpi in pillar.kpis:
                    if kpi.kpi_id in global_kpis:
                        raise OntologyIntegrityError(
                            f"Global kpi_id collision: '{kpi.kpi_id}' defined in both "
                            f"'{global_kpis[kpi.kpi_id]}' and '{tower_key}'."
                        )
                    global_kpis[kpi.kpi_id] = tower_key

                    for ctrl_id in kpi.canonical_control_ids:
                        if (
                            ctrl_id in control_polarities
                            and control_polarities[ctrl_id] != kpi.polarity
                        ):
                            raise OntologyIntegrityError(
                                f"Control '{ctrl_id}' is bound to KPIs with conflicting polarities "
                                f"({control_polarities[ctrl_id].value} vs {kpi.polarity.value})."
                            )
                        control_polarities[ctrl_id] = kpi.polarity
                        controls.add(ctrl_id)

            tower_to_controls[tower_key] = controls

        # 2. Verify bijection per IndustryProfile subgraph, polarity alignment, and build O(1) index
        for profile_key, profile in self.profiles.items():
            if profile_key != profile.profile_id:
                raise OntologyIntegrityError(
                    f"Profile dictionary key '{profile_key}' mismatches internal profile_id '{profile.profile_id}'."
                )

            required_controls: set[CanonicalControlId] = set()
            for app_tower_id in profile.applicable_towers:
                if app_tower_id not in self.towers:
                    raise OntologyIntegrityError(
                        f"Profile '{profile_key}' references non-existent tower '{app_tower_id}'."
                    )
                required_controls.update(tower_to_controls[app_tower_id])

            provided_controls: set[CanonicalControlId] = set()
            for mapping in profile.control_mappings:
                if mapping.control_id in provided_controls:
                    raise OntologyIntegrityError(
                        f"Profile '{profile_key}' contains duplicate control_id mapping '{mapping.control_id}'."
                    )
                provided_controls.add(mapping.control_id)

                # Verify benchmark threshold direction matches KPI polarity if control exists
                if mapping.control_id in control_polarities:
                    polarity = control_polarities[mapping.control_id]
                    thresh = mapping.quantitative_thresholds
                    if (
                        polarity == Polarity.HIGHER_IS_BETTER
                        and thresh.tier_1_global_leader < thresh.minimum_acceptable
                    ):
                        raise OntologyIntegrityError(
                            f"Polarity mismatch in profile '{profile_key}' for control '{mapping.control_id}': "
                            "KPI polarity is HIGHER_IS_BETTER, but tier_1_global_leader "
                            f"({thresh.tier_1_global_leader}) < minimum_acceptable ({thresh.minimum_acceptable})."
                        )
                    if (
                        polarity == Polarity.LOWER_IS_BETTER
                        and thresh.tier_1_global_leader > thresh.minimum_acceptable
                    ):
                        raise OntologyIntegrityError(
                            f"Polarity mismatch in profile '{profile_key}' for control '{mapping.control_id}': "
                            "KPI polarity is LOWER_IS_BETTER, but tier_1_global_leader "
                            f"({thresh.tier_1_global_leader}) > minimum_acceptable ({thresh.minimum_acceptable})."
                        )

                index[(profile_key, mapping.control_id)] = mapping

            orphans = required_controls - provided_controls
            if orphans:
                orphan_controls_by_profile[profile_key] = set(orphans)

            dangling = provided_controls - required_controls
            if dangling:
                dangling_refs_by_profile[profile_key] = set(dangling)

        if orphan_controls_by_profile or dangling_refs_by_profile:
            raise OntologyIntegrityError(
                message="Bijective verification failed between Technical Towers and Industry Profiles.",
                orphan_controls_by_profile=orphan_controls_by_profile,
                dangling_references_by_profile=dangling_refs_by_profile,
            )

        self._benchmark_index = index
        return self

    def resolve_benchmark_for_control(
        self, profile_id: str, control_id: CanonicalControlId
    ) -> ControlBenchmarkMapping:
        """Deterministic O(1) lookup of control benchmark mapping, guaranteed by boot-time validation."""
        if profile_id not in self.profiles:
            raise KeyError(f"Profile '{profile_id}' not found in registered ontology.")

        try:
            return self._benchmark_index[(profile_id, control_id)]
        except KeyError as exc:
            raise KeyError(
                f"Control '{control_id}' not mapped in profile '{profile_id}'."
            ) from exc

    @classmethod
    def from_config_directories(
        cls, towers_dir: Path, profiles_dir: Path
    ) -> OntologyRegistry:
        """Load and validate all tower and industry profile catalogs from directories."""
        t_path = Path(towers_dir)
        p_path = Path(profiles_dir)

        if not t_path.exists() or not p_path.exists():
            raise FileNotFoundError(f"Configuration paths missing: {t_path} or {p_path}")

        towers_dict: dict[str, TowerDefinition] = {}
        profiles_dict: dict[str, IndustryProfile] = {}

        for file_path in sorted(t_path.glob("*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    tower = TowerDefinition.model_validate(data)
                    if tower.tower_id in towers_dict:
                        raise OntologyIntegrityError(
                            f"Duplicate tower_id '{tower.tower_id}' found."
                        )
                    towers_dict[tower.tower_id] = tower
            except Exception as ex:
                logger.error("Failed loading tower definition from %s: %s", file_path, ex)
                raise

        for file_path in sorted(p_path.glob("*.json")):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    profile = IndustryProfile.model_validate(data)
                    if profile.profile_id in profiles_dict:
                        raise OntologyIntegrityError(
                            f"Duplicate profile_id '{profile.profile_id}' found."
                        )
                    profiles_dict[profile.profile_id] = profile
            except Exception as ex:
                logger.error("Failed loading industry profile from %s: %s", file_path, ex)
                raise

        if not towers_dict or not profiles_dict:
            raise OntologyIntegrityError(
                "Cannot initialize OntologyRegistry with empty directories."
            )

        return cls(towers=towers_dict, profiles=profiles_dict)
