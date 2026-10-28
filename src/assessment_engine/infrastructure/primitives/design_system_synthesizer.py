"""
Design System Synthesizer Primitive (Tier-1 Aesthetic & Ergonomics SOTA 2026).
Erradicates generic template cloning by dynamically generating tailored
Design Systems (tailwind.config.js & index.css) based on industry archetypes:
- Clinical Light: Pure medical whites, surgical teals, high-contrast slate typography.
- Editorial Luxury: Warm off-whites, espresso/charcoal typography, serif accents.
- Athletic Energy: Dynamic emeralds and high-contrast court aesthetics.
- Modern Enterprise: Neutral clean slate, deep indigo accents, high data density.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sqlite3
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.design_system_synthesizer")


def _resolve_macro_category_from_db(prompt: str, sector: str) -> str:
    """Query enterprise taxonomy database to resolve canonical macro category."""
    try:
        from assessment_engine.infrastructure.evolution.orthogonal_archetypes import match_sector_for_hybrid
        matched = match_sector_for_hybrid(f"{prompt} {sector}")
        if matched:
            conn = sqlite3.connect("data/enterprise_taxonomy.db")
            cur = conn.cursor()
            cur.execute("SELECT macro_code FROM enterprises WHERE sector_name = ? LIMIT 1;", (matched,))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return row[0].upper()
    except Exception as ex:
        logger.debug(f"[DesignSystemSynthesizer] Error consultando macro categoría: {ex}")
    return ""


class DesignSystemSynthesizer:
    """
    Sintetizador dinámico de sistemas de diseño para Tailwind CSS y estilos raíz.
    Adapta la estética visual, ergonomía y paleta cromática a la industria objetivo.
    """

    def detect_archetype(self, prompt: str, sector: str) -> dict[str, Any]:
        """Detect the optimal visual archetype using the formal enterprise taxonomy database."""
        macro = _resolve_macro_category_from_db(prompt, sector)

        # 1. Clinical / Healthcare Archetype (Clinical Light)
        if macro in ("HEALTH", "HEALTH_WELLNESS_DAILY", "PETS_SERVICES_CARE"):
            return {
                "id": "clinical_light",
                "name": "Clinical High-Density Light",
                "mode": "light",
                "primary": "#0D9488",        # Surgical teal
                "primary_hover": "#0F766E",
                "accent": "#0284C7",         # Clinical cyan
                "bg_base": "#F8FAFC",        # Slate 50 limpio
                "bg_surface": "#FFFFFF",     # Blanco puro
                "bg_card": "#FFFFFF",
                "border": "#E2E8F0",         # Slate 200
                "border_strong": "#CBD5E1",  # Slate 300
                "text_primary": "#0F172A",   # High-contrast Slate 900
                "text_secondary": "#475569", # Slate 600
                "text_muted": "#64748B",     # Slate 500
                "badge_success": "#ECFDF5",
                "badge_success_text": "#065F46",
                "badge_urgent": "#FEF2F2",
                "badge_urgent_text": "#991B1B",
                "font_family": "system-ui, -apple-system, 'Inter', 'Segoe UI', sans-serif"
            }

        if macro in ("LUXURY", "FOOD_HOSPITALITY", "SMB_CREATIVE_DIGITAL"):
            return {
                "id": "editorial_luxury",
                "name": "Editorial Warm Luxury",
                "mode": "light",
                "primary": "#78350F",        # Amber / deep coffee
                "primary_hover": "#92400E",
                "accent": "#D97706",
                "bg_base": "#FAF8F5",        # Warm off-white
                "bg_surface": "#FFFFFF",
                "bg_card": "#FFFFFF",
                "border": "#E7E2DA",
                "border_strong": "#D5CEBF",
                "text_primary": "#1C1917",   # Warm stone 900
                "text_secondary": "#57534E",
                "text_muted": "#78716C",
                "font_family": "system-ui, -apple-system, sans-serif"
            }

        if macro in ("SPORTS", "FITNESS_SPORTS_CLUBS"):
            return {
                "id": "athletic_energy",
                "name": "Athletic Energy",
                "mode": "dark",
                "primary": "#10B981",        # Verde esmeralda pista
                "primary_hover": "#059669",
                "accent": "#06B6D4",
                "bg_base": "#0B0F19",
                "bg_surface": "#111827",
                "bg_card": "#161F30",
                "border": "rgba(255, 255, 255, 0.08)",
                "border_strong": "rgba(255, 255, 255, 0.16)",
                "text_primary": "#F9FAFB",
                "text_secondary": "#9CA3AF",
                "text_muted": "#6B7280",
                "font_family": "system-ui, -apple-system, sans-serif"
            }

        # 4. Default: Modern Enterprise Light
        return {
            "id": "enterprise_modern",
            "name": "Enterprise Clean Light",
            "mode": "light",
            "primary": "#2563EB",        # Enterprise indigo blue
            "primary_hover": "#1D4ED8",
            "accent": "#0D9488",
            "bg_base": "#F8FAFC",
            "bg_surface": "#FFFFFF",
            "bg_card": "#FFFFFF",
            "border": "#E2E8F0",
            "border_strong": "#CBD5E1",
            "text_primary": "#0F172A",
            "text_secondary": "#475569",
            "text_muted": "#64748B",
            "font_family": "system-ui, -apple-system, 'Inter', sans-serif"
        }

    def generate_tailwind_config(self, archetype: dict[str, Any]) -> str:
        """Generate the tailwind.config.js file adapted to the archetype."""
        return f"""/** @type {{import('tailwindcss').Config}} */
export default {{
  content: [
    "./index.html",
    "./src/**/*.{'{js,ts,jsx,tsx}'}",
  ],
  theme: {{
    extend: {{
      colors: {{
        primary: {{
          DEFAULT: "{archetype['primary']}",
          hover: "{archetype['primary_hover']}",
        }},
        accent: {{
          DEFAULT: "{archetype['accent']}",
        }},
        app: {{
          base: "{archetype['bg_base']}",
          surface: "{archetype['bg_surface']}",
          card: "{archetype['bg_card']}",
          border: "{archetype['border']}",
          borderStrong: "{archetype['border_strong']}",
        }},
      }},
      fontFamily: {{
        sans: ["{archetype['font_family']}"],
      }},
    }},
  }},
  plugins: [],
}}
"""

    def generate_index_css(self, archetype: dict[str, Any]) -> str:
        """Generate the index.css file with CSS variables and aesthetics adapted to the industry."""
        is_light = archetype.get("mode") == "light"

        return f"""@tailwind base;
@tailwind components;
@tailwind utilities;

:root {{
  --bg-base: {archetype['bg_base']};
  --bg-surface: {archetype['bg_surface']};
  --bg-card: {archetype['bg_card']};
  --border-subtle: {archetype['border']};
  --border-strong: {archetype['border_strong']};
  --text-main: {archetype['text_primary']};
  --text-muted: {archetype['text_secondary']};
  --primary: {archetype['primary']};
  --primary-hover: {archetype['primary_hover']};
  --accent: {archetype['accent']};
}}

body {{
  background-color: var(--bg-base);
  color: var(--text-main);
  font-family: {archetype['font_family']};
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

/* Estilos de Botones y Componentes del Arquetipo {archetype['name']} */
.btn-primary {{
  background-color: var(--primary);
  color: #FFFFFF;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}}
.btn-primary:hover {{
  background-color: var(--primary-hover);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
}}

.btn-secondary {{
  background-color: var(--bg-surface);
  color: var(--text-main);
  border: 1px solid var(--border-subtle);
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  transition: all 150ms ease;
}}
.btn-secondary:hover {{
  border-color: var(--border-strong);
  background-color: var(--bg-base);
}}

.card-archetype {{
  background-color: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 0.75rem;
  box-shadow: {("0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)" if is_light else "0 4px 6px -1px rgba(0, 0, 0, 0.3)")};
}}

.badge-clinical {{
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.6875rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}}
"""

    def apply_to_workspace(self, ws_dir: Path, prompt: str, sector: str) -> dict[str, Any]:
        """Apply the adaptive design system directly to workspace files."""
        archetype = self.detect_archetype(prompt, sector)
        web_dir = ws_dir / "web"
        if not web_dir.exists():
            return {"applied": False, "reason": "web_dir_missing"}

        tailwind_cfg = self.generate_tailwind_config(archetype)
        (web_dir / "tailwind.config.js").write_text(tailwind_cfg, encoding="utf-8")

        src_dir = web_dir / "src"
        src_dir.mkdir(exist_ok=True)
        index_css = self.generate_index_css(archetype)
        (src_dir / "index.css").write_text(index_css, encoding="utf-8")

        logger.info(f"[{ws_dir.name}] Design System aplicado: {archetype['name']} ({archetype['mode']})")
        return {"applied": True, "archetype": archetype}


design_system_synthesizer = DesignSystemSynthesizer()
