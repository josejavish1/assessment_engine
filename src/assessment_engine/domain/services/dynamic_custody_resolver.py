"""Dynamic Actuarial Custody Resolver Domain Service.

Orchestrates context-aware cross-tower risk deduplication and prevents
actuarial blind spots in partial-scope assessments by dynamically promoting
orphaned tangential risks to primary custodians.
"""

from __future__ import annotations

import copy
import logging
import re
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CustodyRole(str, Enum):
    """Enumeration of actuarial risk custody roles."""

    PRIMARY_CUSTODIAN = "PRIMARY_CUSTODIAN"
    TANGENTIAL_CONTRIBUTOR = "TANGENTIAL_CONTRIBUTOR"


class DynamicCustodyResolver:
    """Domain service responsible for preventing actuarial blind spots in partial-scope

    assessments by dynamically promoting orphaned tangential risks.
    """

    DEFAULT_TOWER_EXTRACTION_PATTERN = r"^([A-Za-z0-9_]+?)(?:[-_.:]|$)"

    def __init__(
        self,
        active_towers_scope: Optional[Set[str]] = None,
        localizer: Optional[Callable[..., str]] = None,
        tower_extraction_pattern: str = DEFAULT_TOWER_EXTRACTION_PATTERN,
    ) -> None:
        """Initializes the resolver with the contracted assessment scope.

        Args:
            active_towers_scope: Set of tower IDs currently under evaluation.
                If None or empty, assumes single-tower evaluation isolation.
            localizer: Optional callback function `(key, **kwargs) -> str` tied to locales.json.
            tower_extraction_pattern: Regex pattern to extract the tower ID from a risk reference.
        """
        self.active_scope: Set[str] = {
            str(tower).strip().upper() for tower in (active_towers_scope or set()) if tower
        }
        self.localizer = localizer
        self._regex = re.compile(tower_extraction_pattern)

    def extract_target_tower(self, risk_payload: Dict[str, Any]) -> Optional[str]:
        """Extracts the target custodian tower identifier from a risk payload.

        Prioritizes explicit metadata before falling back to reference parsing.
        """
        explicit_tower = risk_payload.get("primary_custodian_tower")
        if explicit_tower and isinstance(explicit_tower, str):
            return explicit_tower.strip().upper()

        primary_ref = risk_payload.get("primary_risk_ref")
        if not primary_ref or not isinstance(primary_ref, str):
            return None

        match = self._regex.match(primary_ref.strip())
        if match:
            return match.group(1).upper()

        return None

    def resolve_portfolio(
        self, risks: List[Dict[str, Any]], current_tower_id: str
    ) -> List[Dict[str, Any]]:
        """Evaluates a collection of risk payloads for a given tower and promotes

        orphaned tangential risks if their primary custodian is out of scope.

        Args:
            risks: List of raw risk dictionaries.
            current_tower_id: Identifier of the tower currently being processed.

        Returns:
            A new list of resolved risk dictionaries (non-mutating).
        """
        if not risks:
            return []

        resolved_risks: List[Dict[str, Any]] = []
        normalized_current_tower = str(current_tower_id).strip().upper()

        # The currently evaluated tower is always implicitly active
        effective_scope = self.active_scope.union({normalized_current_tower})

        for raw_risk in risks:
            if not isinstance(raw_risk, dict):
                logger.warning("Skipping malformed risk payload: expected dict, got %s", type(raw_risk))
                continue

            risk = copy.deepcopy(raw_risk)
            raw_role = str(risk.get("ownership_type") or risk.get("custody_role") or CustodyRole.PRIMARY_CUSTODIAN.value).strip().upper()

            if raw_role == CustodyRole.TANGENTIAL_CONTRIBUTOR.value:
                target_tower = self.extract_target_tower(risk)

                is_dangling_ref = target_tower is None
                is_out_of_scope = target_tower is not None and target_tower not in effective_scope

                if is_dangling_ref or is_out_of_scope:
                    self._promote_risk(
                        risk=risk,
                        source_tower=normalized_current_tower,
                        missing_target_tower=target_tower,
                    )

            resolved_risks.append(risk)

        return resolved_risks

    def _promote_risk(
        self,
        risk: Dict[str, Any],
        source_tower: str,
        missing_target_tower: Optional[str],
    ) -> None:
        """Mutates a copied risk instance in-place to elevate its custody role

        and append a transparent, localized scope footnote.
        """
        risk_id = risk.get("id") or risk.get("risk_id", "UNKNOWN_RISK")
        original_ref = str(risk.get("primary_risk_ref") or "UNSPECIFIED").strip()

        # 1. Elevate Custody Role
        risk["ownership_type"] = CustodyRole.PRIMARY_CUSTODIAN.value
        risk["custody_role"] = CustodyRole.PRIMARY_CUSTODIAN.value

        # 2. Preserve Audit Lineage Metadata
        risk["custody_resolution_metadata"] = {
            "dynamically_promoted": True,
            "original_custody_role": CustodyRole.TANGENTIAL_CONTRIBUTOR.value,
            "original_primary_risk_ref": original_ref,
            "designated_custodian_tower": missing_target_tower,
            "promoted_in_tower": source_tower,
        }

        # 3. Inject Plain-Language Localized Footnote
        footnote = self._build_footnote(
            missing_target_tower=missing_target_tower,
            original_ref=original_ref,
        )
        if footnote:
            existing_notes = str(risk.get("actuarial_notes") or "").strip()
            separator = " " if existing_notes else ""
            risk["actuarial_notes"] = f"{existing_notes}{separator}{footnote}"
            risk["scope_note"] = footnote

        logger.info(
            "Actuarial Promotion: Risk '%s' in tower '%s' promoted to PRIMARY_CUSTODIAN. "
            "Target domain '%s' (ref: '%s') is outside active scope %s.",
            risk_id,
            source_tower,
            missing_target_tower,
            original_ref,
            sorted(list(self.active_scope)),
        )

    def _build_footnote(
        self, missing_target_tower: Optional[str], original_ref: str
    ) -> str:
        """Generates the plain-language localized explanation using the injected localizer."""
        if not self.localizer:
            return ""

        if missing_target_tower:
            return self.localizer(
                "actuarial_custody_promoted_scope_note",
                target_tower=missing_target_tower,
                primary_risk_ref=original_ref,
            )
        return self.localizer(
            "actuarial_custody_promoted_unmapped_note",
            primary_risk_ref=original_ref,
        )
