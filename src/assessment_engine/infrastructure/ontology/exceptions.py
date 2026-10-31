"""Domain exceptions for ontology validation and bipartite graph integrity."""

from __future__ import annotations

from typing import Any


class OntologyError(Exception):
    """Base exception for all ontology-related failures."""


class OntologyIntegrityError(OntologyError):
    """Raised at boot-time when the bipartite graph fails bijective or surjective validation."""

    def __init__(
        self,
        message: str,
        orphan_controls_by_profile: dict[str, set[str]] | None = None,
        dangling_references_by_profile: dict[str, set[str]] | None = None,
        unmapped_kpis_by_tower: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(message)
        self.orphan_controls_by_profile = orphan_controls_by_profile or {}
        self.dangling_references_by_profile = dangling_references_by_profile or {}
        self.unmapped_kpis_by_tower = unmapped_kpis_by_tower or {}

    def to_diagnostic_report(self) -> dict[str, Any]:
        """Format structured diagnostic report for forensic observability."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "diagnostics": {
                "orphan_controls_in_profiles": {
                    k: sorted(list(v)) for k, v in self.orphan_controls_by_profile.items()
                },
                "dangling_control_references": {
                    k: sorted(list(v)) for k, v in self.dangling_references_by_profile.items()
                },
                "unmapped_kpis": self.unmapped_kpis_by_tower,
            },
        }
