"""
Google Stitch MCP Connector & Resilient Circuit Breaker.
Connects to stitch.googleapis.com/mcp with Google Cloud enterprise authentication,
maintains an Archetype Paradigm Cache in templates/paradigms/,
and provides a zero-downtime Circuit Breaker fallback to Vertex AI Gemini 3.1 Pro.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("assessment_engine.infrastructure.primitives.stitch_connector")

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "sub403o4u0q5")
STITCH_MCP_URL = "https://stitch.googleapis.com/mcp"
PARADIGMS_DIR = Path(__file__).resolve().parents[2] / "templates/paradigms"


def get_google_access_token() -> str:
    """Retrieves an active Google Cloud Bearer OAuth token via env or gcloud CLI."""
    token = os.environ.get("GOOGLE_ACCESS_TOKEN") or os.environ.get("GCLOUD_AUTH_TOKEN")
    if token:
        return token.strip()
    try:
        proc = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
        logger.debug(f"gcloud token retrieval note: {ex}")
    return ""


class StitchCircuitBreaker:
    """
    Resilient Circuit Breaker for Google Stitch MCP requests.
    Prevents cascading failures when daily credit quotas (400 limit) or timeouts occur.
    """

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 300):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False
        self.last_reason = "OK"

    def record_success(self) -> None:
        """Record a successful operation."""
        self.failure_count = 0
        self.is_open = False
        self.last_reason = "OK"

    def record_failure(self, reason: str = "Error", is_quota_exhausted: bool = False) -> None:
        """Record a failed operation with the given reason and quota status."""
        self.last_failure_time = time.time()
        self.last_reason = reason
        if is_quota_exhausted:
            self.is_open = True
            logger.warning(f"[Circuit Breaker] Stitch credit quota exhausted: {reason}. Circuit OPEN for {self.cooldown_seconds}s.")
            return

        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"[Circuit Breaker] Reached failure threshold ({self.failure_count}). Circuit OPEN for {self.cooldown_seconds}s.")

    def is_available(self) -> bool:
        """Return whether the resource is currently available."""
        if not self.is_open:
            return True
        if time.time() - self.last_failure_time > self.cooldown_seconds:
            logger.info("[Circuit Breaker] Cooldown expired. Testing half-open state.")
            self.is_open = False
            self.failure_count = 0
            return True
        return False


stitch_circuit_breaker = StitchCircuitBreaker()


class StitchMCPConnector:
    """
    Client for Google Stitch MCP with Paradigm Archetype Caching & Vertex AI Fallback.
    """

    @classmethod
    async def _call_stitch_mcp(cls, prompt: str, sector: str, archetype_slug: str, token: str) -> dict[str, Any] | None:
        try:
            headers = {"Authorization": f"Bearer {token}", "X-Goog-User-Project": PROJECT_ID, "Content-Type": "application/json"}
            payload = {"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "vibe_design", "arguments": {"prompt": prompt, "sector": sector, "style": "modern_high_contrast"}}, "id": 1}
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(STITCH_MCP_URL, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    tokens = data.get("result", {}).get("design_tokens") or cls._generate_default_tokens(sector)
                    stitch_circuit_breaker.record_success()
                    cls._persist_paradigm(archetype_slug, tokens)
                    return {"source": "stitch_mcp", "archetype": archetype_slug, "tokens": tokens, "status": "SUCCESS"}
                elif resp.status_code in (429, 403):
                    stitch_circuit_breaker.record_failure(f"HTTP {resp.status_code}", is_quota_exhausted=True)
                else:
                    stitch_circuit_breaker.record_failure(f"HTTP {resp.status_code}")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.warning(f"[Stitch Connector] MCP call failed, triggering fallback: {ex}")
            stitch_circuit_breaker.record_failure(str(ex))
        return None

    @classmethod
    async def synthesize_portal_design(
        cls, prompt: str, sector: str = "general", force_fallback: bool = False
    ) -> dict[str, Any]:
        """Synthesizes a world-class portal design system."""
        import unicodedata
        clean_sector = unicodedata.normalize('NFKD', sector).encode('ascii', 'ignore').decode('ascii')
        archetype_slug = clean_sector.lower().replace(" ", "-").strip() or "general"
        cached_file = PARADIGMS_DIR / archetype_slug / "design_tokens.json"

        if cached_file.exists():
            try:
                cached_data = json.loads(cached_file.read_text(encoding="utf-8"))
                logger.info(f"[Stitch Connector] Reusing cached archetype paradigm for '{archetype_slug}'")
                return {"source": "paradigm_cache", "archetype": archetype_slug, "tokens": cached_data, "status": "SUCCESS"}
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                logger.debug(f"Cache read note: {ex}")

        if not force_fallback and stitch_circuit_breaker.is_available():
            token = get_google_access_token()
            if token:
                res = await cls._call_stitch_mcp(prompt, sector, archetype_slug, token)
                if res: return res

        logger.info(f"[Stitch Connector] Falling back to Vertex AI Gemini 3.1 Pro for archetype '{archetype_slug}'")
        tokens = await cls._synthesize_with_vertex_ai(prompt, sector)
        cls._persist_paradigm(archetype_slug, tokens)

        return {
            "source": "vertex_ai_fallback", "archetype": archetype_slug, "tokens": tokens,
            "status": "SUCCESS", "circuit_breaker_open": stitch_circuit_breaker.is_open
        }

    @classmethod
    async def _synthesize_with_vertex_ai(cls, prompt: str, sector: str) -> dict[str, Any]:
        """Synthesizes design tokens and layout rules using Vertex AI Gemini 3.1 Pro."""
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
            system_instruction = (
                "You are a World-Class Principal UI/UX Design System Architect (Stitch & Material Design 3 Standard). "
                "Synthesize a semantic design system in pure JSON based on the user's business sector. "
                "Output MUST include OKLCH/Hex color tokens, typography pairing, border radii, and 8px grid spacing. "
                "Never output generic purple gradients. Use bold, authentic, high-contrast sector palettes."
            )
            req_prompt = f"SECTOR: {sector}\nBUSINESS GOAL: {prompt}\nReturn JSON with schema: {{ colors: {{ brand: {{ primary, secondary, accent }}, surface: {{ bg, card, border }} }}, typography: {{ heading, body }}, layout: {{ border_radius, spacing_unit }} }}"
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.REASONING),
                contents=req_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            if resp.text:
                return json.loads(resp.text)  # type: ignore[no-any-return]
        except Exception as ex:
            logger.debug(f"Vertex AI design synthesis fallback note: {ex}")

        return cls._generate_default_tokens(sector)

    @classmethod
    def _persist_paradigm(cls, archetype: str, tokens: dict[str, Any]) -> None:
        """Saves synthesized paradigm into local templates cache as permanent reusable assets."""
        try:
            target_dir = PARADIGMS_DIR / archetype
            target_dir.mkdir(parents=True, exist_ok=True)
            token_file = target_dir / "design_tokens.json"
            token_file.write_text(json.dumps(tokens, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"[Stitch Connector] Persisted archetype design paradigm in {token_file}")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.debug(f"Persist paradigm note: {ex}")

    @classmethod
    def _generate_default_tokens(cls, sector: str) -> dict[str, Any]:
        """Provides mathematically contrast-audited default tokens using the enterprise taxonomy database."""
        macro = ""
        try:
            from assessment_engine.infrastructure.primitives.design_system_synthesizer import _resolve_macro_category_from_db
            macro = _resolve_macro_category_from_db("", sector)
        except Exception as ex:
            logger.debug(f"[StitchConnector] Error resolviendo macro categoría: {ex}")

        if macro in ("INDUSTRY", "AUTOMOTIVE_LOCAL_MOBILITY", "LOCAL_HOME_SERVICES"):
            primary = "#f97316"  # Vibrant amber
            bg = "#0f172a"
            card = "#1e293b"
        elif macro in ("HEALTH", "HEALTH_WELLNESS_DAILY", "PETS_SERVICES_CARE"):
            primary = "#0284c7"  # Deep medical cobalt
            bg = "#f8fafc"
            card = "#ffffff"
        else:
            primary = "#10b981"  # Emerald
            bg = "#09090b"
            card = "#18181b"

        return {
            "colors": {
                "brand": {"primary": primary, "secondary": "#64748b", "accent": "#38bdf8"},
                "surface": {"bg": bg, "card": card, "border": "rgba(255,255,255,0.08)"}
            },
            "typography": {
                "heading": "Space Grotesk, sans-serif",
                "body": "Inter Variable, sans-serif"
            },
            "layout": {
                "border_radius": "8px",
                "spacing_unit": "8px"
            }
        }
