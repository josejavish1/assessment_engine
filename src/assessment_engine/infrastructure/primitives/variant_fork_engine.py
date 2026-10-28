"""
Multi-Variant Visual Branching Engine — GEMA 78 (Tier-1 SOTA 2026).
Manages simultaneous A/B/C visual design forks (v0-style multi-variant synthesis).
Allows instant toggling between design archetypes (Minimalist, Editorial, Compact)
with zero reload latency and atomic variant selection.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.primitives.base import CapabilityPrimitive

logger = logging.getLogger("assessment_engine.infrastructure.primitives.variant_fork_engine")
WORKSPACES_DIR = Path(os.environ.get("AUTONOMUOS_WORKSPACES_DIR", str(Path(__file__).resolve().parents[2] / "workspaces")))

DEFAULT_VARIANTS = [
    {
        "id": "variant-a",
        "label": "Variante A (Editorial Luxe)",
        "archetype": "editorial_luxe",
        "theme_hue": 260.0,
        "is_active": True,
        "description": "Tipografía serif, fondos profundos, iluminación difusa y espaciado generoso.",
    },
    {
        "id": "variant-b",
        "label": "Variante B (Corporate Clean)",
        "archetype": "corporate_clean",
        "theme_hue": 210.0,
        "is_active": False,
        "description": "Modo claro impoluto OKLCH, micro-pastillas de estado y sombras con dispersión negativa.",
    },
    {
        "id": "variant-c",
        "label": "Variante C (High-Density Tech)",
        "archetype": "high_density_tech",
        "theme_hue": 160.0,
        "is_active": False,
        "description": "Acentos esmeralda, métricas compactas, rejilla modular y alta densidad de datos.",
    },
]


class VariantForkEngine(CapabilityPrimitive):
    """Orchestrates 3-way visual branching and active design selection."""

    def __init__(self, workspaces_dir: Path | None = None) -> None:
        self.workspaces_dir = workspaces_dir or WORKSPACES_DIR

    @property
    def namespace(self) -> str:
        """Return the unique namespace identifier for the capability."""
        return "variant_fork"

    def get_capabilities(self) -> dict[str, Any]:
        """Expose capability metadata and operations schema."""
        return {
            "version": "1.0.0",
            "supported_archetypes": ["editorial_luxe", "corporate_clean", "high_density_tech"],
            "features": ["3_way_forking", "atomic_variant_switch", "live_theme_reconfiguration"],
        }

    def _get_variants_file(self, slug: str, view_name: str) -> Path:
        clean_slug = re.sub(r"[^\w.-]", "", slug)
        clean_view = re.sub(r"[^\w.-]", "", view_name)
        data_dir = self.workspaces_dir / clean_slug / "data" / "variants"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / f"{clean_view}.json"

    def list_variants(self, slug: str, view_name: str = "landing") -> list[dict[str, Any]]:
        """Retrieve the 3 active visual forks for the specified project view."""
        v_file = self._get_variants_file(slug, view_name)
        if not v_file.exists():
            v_file.write_text(json.dumps(DEFAULT_VARIANTS, indent=2), encoding="utf-8")
            return DEFAULT_VARIANTS

        try:
            return json.loads(v_file.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_VARIANTS

    def select_active_variant(self, slug: str, view_name: str, variant_id: str) -> dict[str, Any]:
        """Atomically set the active design variant for the project view."""
        v_file = self._get_variants_file(slug, view_name)
        variants = self.list_variants(slug, view_name)
        selected: dict[str, Any] | None = None

        for v in variants:
            if v["id"] == variant_id:
                v["is_active"] = True
                selected = v
            else:
                v["is_active"] = False

        if not selected:
            raise ValueError(f"Variante no encontrada: '{variant_id}'")

        v_file.write_text(json.dumps(variants, indent=2), encoding="utf-8")
        logger.info(f"[VariantFork] Variante activa conmutada a '{variant_id}' en '{slug}:{view_name}'")
        return selected

    def commit_variant(
        self,
        slug: str,
        view_name: str,
        variant_id: str,
        commit_hash: str,
        amount_cents: int,
        canonical_payload_bytes: bytes,
    ) -> dict[str, Any]:
        """Commit a variant selection with cryptographic and financial validation."""
        if not (isinstance(amount_cents, int) and amount_cents >= 0 and not isinstance(amount_cents, bool)):
            raise ValueError("Invalid amount_cents")

        if not (isinstance(commit_hash, str) and len(commit_hash) == 64 and all(c in '0123456789abcdef' for c in commit_hash) and commit_hash == hashlib.sha256(canonical_payload_bytes).hexdigest()):
            raise ValueError("Invalid commit_hash")

        return self.select_active_variant(slug, view_name, variant_id)


variant_fork_engine = VariantForkEngine()