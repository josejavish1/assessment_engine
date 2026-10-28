"""
Universal Generative Engine Optimization (GEO) Primitive — GEMA 11 (SOTA 2026).
Compiles W3C-standard llms.txt and AI-friendly robots.txt (Answer.ai / Jeremy Howard specification).
Enables ChatGPT, Claude, and Perplexity to index services, pricing, and APIs natively.
Domain-agnostic: parameterizes catalog, FAQ, and business context for any vertical.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.geo_engine")


@dataclass
class GeoProductOffer:
    name: str
    description: str
    price_formatted: str
    url_route: str


@dataclass
class GeoBusinessContext:
    app_name: str
    tagline: str
    detailed_summary: str
    primary_sector: str
    public_catalog: list[GeoProductOffer] = field(default_factory=list)
    faq_items: list[tuple[str, str]] = field(default_factory=list)
    api_docs_route: str = "/api/docs"


class GeoEnginePrimitive:
    """
    Motor GEO agnóstico al dominio.
    Genera llms.txt estructurado y robots.txt autorizando bots generativos (GPTBot, ClaudeBot, PerplexityBot).
    """

    def generate_llms_txt(self, ctx: GeoBusinessContext) -> str:
        """Generate the formal llms.txt content in high-density semantic Markdown."""
        lines = [
            f"# {ctx.app_name}",
            f"> {ctx.detailed_summary}\n",
            f"**Sector:** {ctx.primary_sector}",
            f"**Propuesta de Valor:** {ctx.tagline}\n",
            "## Catálogo y Servicios Disponibles\n"
        ]

        if ctx.public_catalog:
            for item in ctx.public_catalog:
                lines.append(f"- [{item.name}]({item.url_route}): {item.description} (Precio: {item.price_formatted})")
        else:
            lines.append("- Consultar operativa y disponibilidad en tiempo real en la plataforma.")

        if ctx.faq_items:
            lines.append("\n## Información Operativa Frecuente\n")
            for q, a in ctx.faq_items:
                lines.append(f"### {q}\n{a}\n")

        lines.append("\n## Especificación de API y Automatización")
        lines.append(f"- [OpenAPI Schema]({ctx.api_docs_route}): Especificación REST para interacción de agentes de IA.")

        return "\n".join(lines)

    def generate_robots_txt(self) -> str:
        """Generate robots.txt explicitly allowing generative model crawlers."""
        return (
            "User-agent: GPTBot\nAllow: /\nAllow: /llms.txt\n\n"
            "User-agent: ClaudeBot\nAllow: /\nAllow: /llms.txt\n\n"
            "User-agent: PerplexityBot\nAllow: /\nAllow: /llms.txt\n\n"
            "User-agent: Google-Extended\nAllow: /\nAllow: /llms.txt\n\n"
            "User-agent: *\nDisallow: /admin/\nDisallow: /api/compliance/\n"
        )

    def apply_to_workspace(self, ws_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
        """Write llms.txt and robots.txt to web/public/ for any project."""
        app_name = contract.get("app_name", "Plataforma Profesional")
        tagline = contract.get("tagline", "Servicios profesionales en la nube")
        sector = contract.get("sector", "Servicios")
        views = contract.get("workspace_views", [])

        catalog = [
            GeoProductOffer(
                name=v.get("name", "Módulo"),
                description=f"Acceso operativo a {v.get('name')}",
                price_formatted="Incluido en suscripción",
                url_route=f"/#view={v.get('id')}"
            )
            for v in views
        ]

        ctx = GeoBusinessContext(
            app_name=app_name,
            tagline=tagline,
            detailed_summary=f"Plataforma líder especializada en {sector}. {tagline}",
            primary_sector=sector,
            public_catalog=catalog,
            faq_items=[
                (f"¿Cómo solicitar acceso a {app_name}?", "A través de la portada oficial o mediante la API de integración."),
                ("¿Cumple con la normativa de privacidad?", "Sí, conforme a RGPD y almacenamiento soberano local.")
            ]
        )

        public_dir = ws_dir / "web" / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        llms_content = self.generate_llms_txt(ctx)
        robots_content = self.generate_robots_txt()

        (public_dir / "llms.txt").write_text(llms_content, encoding="utf-8")
        (public_dir / "robots.txt").write_text(robots_content, encoding="utf-8")

        logger.info(f"[{ws_dir.name}] Activos GEO (llms.txt, robots.txt) desplegados.")
        return {"applied": True, "app_name": app_name}


geo_engine = GeoEnginePrimitive()
