"""
Competitive Intelligence & Counter-Positioning Engine — SOTA 2026.
Executes real-time market leader discovery, bypass-free forensic inspection,
and asymmetric counter-positioning to ensure any synthesized SaaS outclasses
established industry leaders.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from google import genai
from google.genai import types

from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model
from assessment_engine.infrastructure.primitives.content_pruner import content_pruner

logger = logging.getLogger("core.competitive_intelligence")


class CompetitiveIntelligenceEngine:
    """
    Tier-1 Competitive Benchmarking & Counter-Positioning Engine.
    Discovers market leaders, performs deep domain extraction via Google Index,
    and synthesizes asymmetric value propositions.
    """

    def __init__(self) -> None:
        self.client: genai.Client | None = None
        try:
            self.client = create_genai_client()
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.debug(f"GenAI client init note: {e}")
            self.client = None

    async def discover_and_analyze_leaders(
        self, prompt: str, sector: str
    ) -> dict[str, Any]:
        """
        Executes Steps 1, 2, and 3 in an ultra-optimized pipeline:
        1. Discover top 2-3 real competitors in Google's live index.
        2. Extract their pricing, features, and user friction points.
        3. Synthesize the asymmetric counter-positioning hook.
        """
        logger.info(f"[Competitive Intel] Investigando líderes del mercado para: {sector} - {prompt[:60]}...")

        if not self.client:
            return self._fallback_intelligence(prompt, sector)

        grounding_prompt = (
            f"Investiga en Google los 2 o 3 software y empresas líderes mundiales en este nicho: {sector} - {prompt}.\n"
            "Dame de forma ultra-concreta:\n"
            "1. Nombres de las 2-3 empresas/software líderes reales.\n"
            "2. Qué precios cobran y qué modelo de suscripción tienen.\n"
            "3. Cuáles son sus 4 funcionalidades clave.\n"
            "4. Qué quejas o fricciones habituales tienen sus usuarios (ej. comisiones altas, interfaz vieja, lentitud)."
        )

        grounded_data = ""
        try:
            ground_config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=600,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
            g_resp = await asyncio.to_thread(
                self.client.models.generate_content,
                model=get_model(ModelTier.FAST),
                contents=grounding_prompt,
                config=ground_config,
            )
            if g_resp and g_resp.text:
                raw_grounded = g_resp.text.strip()
                if "<" in raw_grounded and ">" in raw_grounded:
                    pruned = content_pruner.prune_html(raw_grounded)
                    grounded_data = pruned["markdown"] or raw_grounded
                    logger.info(f"[Competitive Intel] Datos podados algorítmicamente: {pruned['compression_ratio']*100:.1f}% ruido eliminado.")
                else:
                    grounded_data = raw_grounded
                logger.info(f"[Competitive Intel] Datos de líderes extraídos ({len(grounded_data)} chars).")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as err:# noqa: BLE001
            logger.debug(f"[Competitive Intel] Grounding fallback note: {err}")
            return self._fallback_intelligence(prompt, sector)

        # Synthesize asymmetric counter-positioning in JSON.
        analysis_prompt = (
            "Eres el Director de Estrategia de Producto y Contra-Posicionamiento (SOTA 2026).\n"
            f"A partir de estos datos reales de los competidores líderes del mercado:\n\n{grounded_data}\n\n"
            f"Para el nuevo producto: '{prompt}' ({sector}):\n\n"
            "Sintetiza la ESTRATEGIA DE CONTRA-POSICIONAMIENTO ASIMÉTRICO para superar a estos líderes.\n"
            "RESPONDE EXCLUSIVAMENTE CON UN OBJETO JSON VÁLIDO CON ESTA ESTRUCTURA:\n"
            "{\n"
            '  "leaders": ["Nombre Líder 1", "Nombre Líder 2"],\n'
            '  "leader_pricing_benchmark": "Resumen de precios del mercado (ej. 29€ - 89€/mes)",\n'
            '  "leader_weaknesses": ["Fricción 1 del líder", "Fricción 2 del líder"],\n'
            '  "unfair_advantage": "Nuestra ventaja competitiva demoledora (ej. 0% comisiones directas + domótica en 1 clic)",\n'
            '  "hero_killer_hook": "Titular de alto impacto que deja en evidencia la debilidad del líder",\n'
            '  "must_have_features": ["Feature 1", "Feature 2", "Feature 3", "Feature 4"]\n'
            "}"
        )

        try:
            resp = await asyncio.to_thread(
                self.client.models.generate_content,
                model=get_model(ModelTier.FAST),
                contents=analysis_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(resp.text or "{}")
            logger.info(f"[Competitive Intel] Contra-posicionamiento sintetizado para '{data.get('hero_killer_hook', '')[:50]}'.")
            return data
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as s_err:# noqa: BLE001
            logger.warning(f"[Competitive Intel] Error estructurando contra-posicionamiento: {s_err}")
            return self._fallback_intelligence(prompt, sector)

    def _fallback_intelligence(self, prompt: str, sector: str) -> dict[str, Any]:
        """Fallback determinista si Vertex AI no estuviera disponible."""
        is_padel = "padel" in prompt.lower() or "pista" in prompt.lower()
        if is_padel:
            return {
                "leaders": ["Playtomic", "Matchpoint", "Tieplayer"],
                "leader_pricing_benchmark": "Cuotas de club desde 79€/mes + comisiones por jugador",
                "leader_weaknesses": [
                    "Comisiones abusivas por jugador en cada reserva",
                    "Interfaces heredadas de 2015 poco intuitivas"
                ],
                "unfair_advantage": "0% comisiones en reservas directas, Split Pay 4x automático y control domótico de pistas",
                "hero_killer_hook": "El software para clubes de pádel con 0% comisiones y cobro fraccionado al instante",
                "must_have_features": [
                    "Cuadrante de reservas en tiempo real",
                    "Split Pay fraccionado 4x (Bizum / Tarjeta)",
                    "Torneos oficiales con cuadros y punto de oro",
                    "Ranking dinámico Elo de socios"
                ]
            }

        return {
            "leaders": ["Líder Sectorial A", "Líder Sectorial B"],
            "leader_pricing_benchmark": "Planes de 49€ a 149€/mes",
            "leader_weaknesses": ["Curva de aprendizaje empinada", "Falta de automatización en tiempo real"],
            "unfair_advantage": "Automatización operativa completa con arquitectura de alta disponibilidad",
            "hero_killer_hook": f"La plataforma moderna para {sector} diseñada para operar sin fricciones",
            "must_have_features": ["Gestión operativa", "Facturación integrada", "Métricas en tiempo real"]
        }


competitive_intelligence = CompetitiveIntelligenceEngine()
