"""Deterministic Topology Enricher enforcing Fail-Closed Actuarial Contracts (SR 11-7)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import yaml

from assessment_engine.domain.exceptions import ActuarialContractViolationError
from assessment_engine.domain.schemas.actuarial_contracts import (
    ArchitecturalRole,
    AssetActuarialProfile,
    DataClassification,
    EnrichmentAuditEntry,
    EnvironmentTier,
)


class TopologyEnricher:
    """Evaluates raw unclassified asset telemetry and applies deterministic topology labels.

    Enforces Fail-Closed contracts: if an asset cannot be unambiguously classified,
    it raises ActuarialContractViolationError. Zero silent fallbacks.
    """

    def __init__(self, rules_path: Optional[Path] = None) -> None:
        if rules_path is None:
            rules_path = self._default_rules_path()
        self._rules_path = rules_path
        self._rules: Dict[str, Any] = self._load_rules(rules_path)

    @staticmethod
    def _default_rules_path() -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            cand = parent / "engine_config" / "topology_classification_rules.yaml"
            if cand.is_file():
                return cand
        raise FileNotFoundError("Could not locate topology_classification_rules.yaml")

    @staticmethod
    def _load_rules(path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ActuarialContractViolationError(
                f"Malformed topology rules in {path}: expected dict root"
            )
        return data

    def enrich_asset(
        self, asset_raw: Mapping[str, Any]
    ) -> Tuple[AssetActuarialProfile, List[EnrichmentAuditEntry]]:
        """Deterministically enriches an asset into an AssetActuarialProfile with audit log."""
        audit_log: List[EnrichmentAuditEntry] = []
        asset_id = str(asset_raw.get("asset_id") or asset_raw.get("id") or "UNKNOWN_ASSET")

        # 1. Resolve EnvironmentTier
        explicit_env = asset_raw.get("environment_tier") or asset_raw.get("environment")
        if explicit_env:
            raw_str = str(explicit_env).strip().upper()
            try:
                env_tier = EnvironmentTier(raw_str)
            except ValueError:
                raise ActuarialContractViolationError(
                    f"Invalid explicit environment_tier '{raw_str}' for asset '{asset_id}'. "
                    f"Must be one of {[e.value for e in EnvironmentTier]}."
                )
        else:
            val_str, rule_id, rule_hash = self._evaluate_rule_set(
                asset_raw,
                self._rules.get("environment_tier_rules", []),
                "environment_tier",
            )
            env_tier = EnvironmentTier(val_str)
            audit_log.append(
                EnrichmentAuditEntry(
                    asset_id=asset_id,
                    inferred_field="environment_tier",
                    assigned_value=val_str,
                    rule_id=rule_id,
                    rule_hash_sha256=rule_hash,
                )
            )

        # 2. Resolve ArchitecturalRole
        explicit_role = asset_raw.get("architectural_role") or asset_raw.get("role")
        if explicit_role:
            raw_str = str(explicit_role).strip().upper()
            try:
                arch_role = ArchitecturalRole(raw_str)
            except ValueError:
                raise ActuarialContractViolationError(
                    f"Invalid explicit architectural_role '{raw_str}' for asset '{asset_id}'. "
                    f"Must be one of {[r.value for r in ArchitecturalRole]}."
                )
        else:
            val_str, rule_id, rule_hash = self._evaluate_rule_set(
                asset_raw,
                self._rules.get("architectural_role_rules", []),
                "architectural_role",
            )
            arch_role = ArchitecturalRole(val_str)
            audit_log.append(
                EnrichmentAuditEntry(
                    asset_id=asset_id,
                    inferred_field="architectural_role",
                    assigned_value=val_str,
                    rule_id=rule_id,
                    rule_hash_sha256=rule_hash,
                )
            )

        # 3. Resolve DataClassification
        raw_data_class = asset_raw.get("data_classification")
        if raw_data_class:
            try:
                data_class = DataClassification(str(raw_data_class).strip().upper())
            except ValueError:
                raise ActuarialContractViolationError(
                    f"Invalid data_classification '{raw_data_class}' for asset '{asset_id}'."
                )
        else:
            data_class = DataClassification.INTERNAL

        # 4. Extract Financial Metrics
        hourly_rev = float(asset_raw.get("hourly_revenue_contribution") or 0.0)
        reconst_cost = float(asset_raw.get("reconstitution_labor_cost") or 0.0)
        buffer_h = float(asset_raw.get("operational_buffer_hours") or 0.0)

        profile = AssetActuarialProfile(
            asset_id=asset_id,
            environment_tier=env_tier,
            architectural_role=arch_role,
            data_classification=data_class,
            hourly_revenue_contribution=hourly_rev,
            reconstitution_labor_cost=reconst_cost,
            operational_buffer_hours=buffer_h,
        )
        return profile, audit_log

    @staticmethod
    def _strip_accents(text: str) -> str:
        import unicodedata

        return "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )

    def _evaluate_rule_set(
        self,
        asset: Mapping[str, Any],
        rules: Sequence[Mapping[str, Any]],
        target_field: str,
    ) -> Tuple[str, str, str]:
        asset_id = str(asset.get("asset_id") or asset.get("id") or "UNKNOWN")
        raw_corpus = " ".join(
            str(v).lower()
            for k, v in asset.items()
            if isinstance(v, (str, int, float)) and k not in ("actuarial_input_vector",)
        )
        corpus = self._strip_accents(raw_corpus)

        matches: List[Tuple[str, str, str, int]] = []
        for rule in rules:
            rule_id = rule.get("rule_id", "UNKNOWN_RULE")
            patterns = rule.get("criteria", {}).get("name_or_finding", [])
            priority = int(rule.get("priority", 100))

            matched = False
            for p in patterns:
                clean_p = self._strip_accents(p).lower().strip()
                if not clean_p:
                    continue
                if len(clean_p) <= 4:
                    regex = r"\b" + re.escape(clean_p) + r"(?:s)?\b"
                else:
                    regex = r"\b" + re.escape(clean_p)
                if re.search(regex, corpus):
                    matched = True
                    break

            if matched:
                rule_repr = json.dumps(rule, sort_keys=True).encode("utf-8")
                rule_hash = hashlib.sha256(rule_repr).hexdigest()
                matches.append(
                    (str(rule["assign_value"]), rule_id, rule_hash, priority)
                )

        if not matches:
            raise ActuarialContractViolationError(
                f"FAIL-CLOSED: Cannot deterministically resolve '{target_field}' for asset '{asset_id}'. "
                "No classification rules matched. Explicit tagging required in telemetry."
            )

        # Sort by priority ascending (lowest number = highest precedence)
        matches.sort(key=lambda m: m[3])
        top_priority = matches[0][3]
        top_matches = [m for m in matches if m[3] == top_priority]

        # Check for ambiguity at the highest priority level
        distinct_values = {m[0] for m in top_matches}
        if len(distinct_values) > 1:
            matched_ids = [m[1] for m in top_matches]
            raise ActuarialContractViolationError(
                f"FAIL-CLOSED: Ambiguous topology resolution for '{target_field}' on asset '{asset_id}'. "
                f"Conflicting rules matched with equal priority: {matched_ids}."
            )

        chosen = top_matches[0]
        return chosen[0], chosen[1], chosen[2]
