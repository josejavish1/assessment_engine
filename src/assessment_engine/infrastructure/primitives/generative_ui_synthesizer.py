"""
Generative UI Synthesizer Primitive — SOTA 2026 Engine (RFC-016).
Synthesizes bespoke, modular React TSX views using Gemini 3.1 Pro Preview.
Enforces the Zero-Hex Mandate via a semantic linter that eliminates arbitrary
Tailwind classes (bg-[#...]) in favor of Material 3 / Stitch semantic tokens.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("assessment_engine.infrastructure.primitives.generative_ui_synthesizer")


from assessment_engine.infrastructure.primitives.taste_engine import taste_engine


@dataclass(frozen=True)
class SemanticLintViolation:
    """Represent a Tailwind semantic contract violation."""
    line_number: int
    raw_class: str
    suggested_token: str
    message: str


@dataclass
class SynthesisResult:
    """Represent the result of generative UI compilation."""
    success: bool
    tsx_code: str
    sloc: int
    violations_detected: list[SemanticLintViolation] = field(default_factory=list)
    repaired_automatically: bool = False
    error_message: str | None = None


class SemanticLinter:
    """Audit TSX/HTML code to ensure compliance with the zero-hex mandate and semantic token consistency."""

    HEX_CLASS_PATTERN = re.compile(r'(?:bg|text|border|ring|fill|stroke)-\[#([0-9a-fA-F]{3,8})\]')

    def lint_code(self, tsx_code: str) -> list[SemanticLintViolation]:
        """Detect Tailwind classes with arbitrary hex values."""
        violations: list[SemanticLintViolation] = []
        for line_idx, line in enumerate(tsx_code.splitlines(), start=1):
            matches = self.HEX_CLASS_PATTERN.findall(line)
            for hex_val in matches:
                full_match = f"- [#{hex_val}]"
                violations.append(
                    SemanticLintViolation(
                        line_number=line_idx,
                        raw_class=f"#{hex_val}",
                        suggested_token="var(--primary) o clase semántica equivalente",
                        message=f"Uso de clase fija arbitraria #{hex_val} en línea {line_idx}. Debe usar tokens semánticos (bg-primary, text-on-surface, border-outline)."
                    )
                )
        return violations

    def auto_repair_hex_classes(self, tsx_code: str, hex_to_token_map: dict[str, str]) -> tuple[str, int]:
        """Replace known arbitrary classes with corresponding semantic tokens and return the repaired code along with the substitution count."""
        repaired = tsx_code
        total_substitutions = 0

        # Map standard Tailwind prefixes to tokens.
        prefix_mappings = [
            ("bg", "bg-"),
            ("text", "text-"),
            ("border", "border-"),
            ("ring", "ring-"),
            ("from", "from-"),
            ("to", "to-"),
            ("via", "via-"),
            ("fill", "fill-"),
            ("stroke", "stroke-"),
        ]

        for hex_code, token_name in hex_to_token_map.items():
            clean_hex = hex_code.strip().lstrip("#").lower()
            clean_token = token_name.replace("_", "-").lstrip("-")

            for tw_prefix, replacement_prefix in prefix_mappings:
                # Match case-insensitive bg-[#HEX] or text-[#HEX] patterns.
                pattern = re.compile(rf"{tw_prefix}-\[#{clean_hex}\]", re.IGNORECASE)
                matches = pattern.findall(repaired)
                if matches:
                    total_substitutions += len(matches)
                    repaired = pattern.sub(f"{replacement_prefix}{clean_token}", repaired)

        return repaired, total_substitutions

    def audit_semantic_accessibility(self, tsx_code: str) -> list[str]:
        """Audit DOM semantics for WCAG accessibility and responsiveness compliance."""
        findings: list[str] = []
        if "<main" not in tsx_code:
            findings.append("Falta el elemento raíz semántico <main> para lectores de pantalla.")
        if "<h1" not in tsx_code:
            findings.append("Falta el titular semántico <h1>.")
        if "<img" not in tsx_code:
            findings.append("Falta de activos visuales: El componente carece de imágenes fotográficas (<img />) de producto o contexto.")
        input_pattern = re.compile(r"<input\b(?![^>]*\baria-label\b)[^>]*>", re.IGNORECASE)
        unlabeled_inputs = input_pattern.findall(tsx_code)
        if unlabeled_inputs:
            findings.append(f"Detectados {len(unlabeled_inputs)} inputs sin atributo aria-label.")
        return findings


def _build_hex_to_token_map(design_spec: dict[str, Any]) -> dict[str, str]:
    """Build mapping from hex color codes to semantic token names."""
    theme_dict = design_spec.get("theme") if isinstance(design_spec.get("theme"), dict) else {}
    colors_dict = design_spec.get("colors") if isinstance(design_spec.get("colors"), dict) else {}
    combined_colors = {**colors_dict, **theme_dict}
    hex_map: dict[str, str] = {}
    for k, v in combined_colors.items():
        if isinstance(v, str) and v.startswith("#"):
            token = k.replace("_color", "").replace("color", "")
            hex_map[v] = token
    return hex_map


class GenerativeUISynthesizer:
    """Compile React TSX interfaces, assembling complete, reactive views governed by DESIGN.md."""

    def __init__(self, linter: SemanticLinter | None = None) -> None:
        self.linter = linter or SemanticLinter()

    def build_system_instruction(self, design_spec: dict[str, Any]) -> str:
        """Build system directives inspired by v0 and Stitch."""
        app_name = design_spec.get("app_name", "Plataforma de Prestigio")
        paradigm = design_spec.get("aesthetic_paradigm", "MODERN_HIGH_CONTRAST")

        return (
            "Eres el Ingeniero Principal de Frontend y Sistemas de Diseño (Estándar Galileo AI, v0 de Vercel y Google Stitch SOTA 2026).\n"
            "Tu misión es escribir UN COMPONENTE REACT TSX COMPLETO Y LISTO PARA PRODUCCIÓN llamado 'GenerativeLandingView'.\n\n"
            "DIRECTRICES ARQUITECTÓNICAS MANDATORIAS:\n"
            "1. ZERO-HEX MANDATE (ESTRICTO): Queda TERMINANTEMENTE PROHIBIDO usar clases hexadecimales con corchetes (ej. 'bg-[#...]', 'text-[#...]').\n"
            "   Debes usar EXCLUSIVAMENTE los tokens semánticos de Tailwind inyectados:\n"
            "   - Superficies: bg-surface, bg-surface-container-lowest, bg-surface-container-low, bg-surface-container, bg-surface-container-high\n"
            "   - Textos: text-on-surface, text-on-surface-variant, text-primary, text-outline\n"
            "   - Acciones: bg-primary, text-on-primary, hover:bg-primary-container, bg-secondary\n"
            "   - Bordes: border-outline, border-outline-variant\n"
            "   - Tipografía: font-display (titulares), font-sans (cuerpo), font-mono (cifras/datos tabulares)\n"
            "2. INTERACTIVIDAD NATIVA EN REACT: Incluye estado real local con 'useState' y 'useMemo' para crear widgets interactivos (simuladores de coste, calculadoras de ROI, conmutadores mensuales/anuales, selectores de escala del sector).\n"
            "3. DATOS HIPER-REALISTAS: Prohibido usar 'Lorem Ipsum', 'Servicio 1' o marcadores vacíos. Todo debe tener terminología técnica, precios, métricas y nombres verosímiles del negocio.\n"
            "4. TIPADO ESTRICTO: Cero 'any'. Define interfaces TypeScript claras para cada modelo de datos.\n"
            "5. ICONOS: Importa exclusivamente desde 'lucide-react'.\n"
            "6. SEMÁNTICA DOM & ACCESIBILIDAD WCAG 2.2 AA (OBLIGATORIO):\n"
            "   - El contenedor raíz DEBE ser un elemento semántico <main id=\"main-content\" className=\"w-full max-w-full overflow-x-hidden ...\">\n"
            "   - Debe incluir un <header> estructurado y exactamente un titular principal <h1>.\n"
            "   - Si usas <input> o controles de formulario, DEBEN tener un atributo aria-label explicativo (ej. aria-label=\"Search\" o aria-label=\"Email\").\n"
            "   - Todas las listas de elementos <li> DEBEN estar contenidas dentro de una etiqueta <ul> o <ol>.\n"
            "7. RESPONSIVIDAD MÓVIL ESTRICTA (0 OVERFLOW EN 375px):\n"
            "   - Toda tabla, rejilla densa o selector de múltiples columnas debe incluir la clase 'overflow-x-auto w-full' para evitar desbordamiento horizontal en móviles.\n"
            "   - Evita anchos fijos en píxeles (w-[...px]); usa clases fluidas (w-full, max-w-7xl, grid-cols-1 md:grid-cols-2 lg:grid-cols-3).\n"
            "8. COTA MODULAR: Sintetiza un diseño editorial de alto impacto de entre 450 y 750 líneas sin código redundante.\n"
            "9. RIQUEZA DE ACTIVOS FOTOGRÁFICOS Y ATMÓSFERA SOTA (OBLIGATORIO):\n"
            "   - Queda TERMINANTEMENTE PROHIBIDO generar una página de solo texto plano sin imágenes reales.\n"
            "   - Incluye al menos 3 a 5 imágenes fotográficas en alta resolución de Unsplash relevantes al sector (ej. https://images.unsplash.com/photo-...) con encuadres elegantes (rounded-lg, aspect-video o aspect-square, object-cover, shadow-lg, border border-outline/10).\n"
            "   - En el Hero: Incorpora una vitrina visual de producto o mockup fotográfico con iluminación ambiental (bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(197,168,128,0.15),transparent)]).\n"
            "   - En las tarjetas del catálogo/lotes: Cada producto o servicio debe mostrar su fotografía de alta gama con precio y estado.\n"
            "10. ENLACES MULTI-PÁGINA Y NAVEGACIÓN CANÓNICA UNIVERSAL (RFC-020 / RFC-023):\n"
            "   - El Navbar, los menús y los botones CTA DEBEN incluir enlaces dinámicos a las rutas del portal configuradas en 'contract.routes' (ej. '/convocatorias', '/precios', '/portal', '/reservas') mediante 'href=\"#view=...\"' o 'onClick={() => window.location.hash = \"#view=...\"}'.\n"
            "   - Queda TERMINANTEMENTE PROHIBIDO usar enlaces vacíos o decorativos 'href=\"#\"' sin destino real.\n"
            "   - Enlaces Globales de Cumplimiento Legal (Footer): Todo pie de página DEBE incluir enlaces semánticos a las rutas legales globales: Aviso Legal ('#view=legal'), Privacidad ('#view=privacy') y Política de Cookies ('#view=cookies'). Los modales legales están gobernados por el Layout Raíz (App.tsx); la portada NO DEBE importar ni gestionar modales locales.\n"
            "   - Enlaces de Publicación y Fichas: El botón de publicar anuncios/ofertas debe despachar a '#view=publish'. Los clics en tarjetas de producto/inmueble deben navegar a '#view=item-{item.id}' para abrir la ficha de detalle global.\n"
            "   - Botón Iniciar Sesión en Navbar: Debe despachar a '#view=login' o llamar a 'onLogin?.()'.\n"
            "DEVUELVE EXCLUSIVAMENTE EL CÓDIGO TSX LIMPIO."
        )

    def extract_clean_code(self, raw_response: str) -> str:
        """Extract pure TypeScript code from markdown blocks returned by the LLM."""
        match = re.search(r"```(?:tsx|typescript)?\s*(.*?)\s*```", raw_response, re.DOTALL)
        if match:
            clean = match.group(1).strip()
        else:
            clean = re.sub(r"^```(?:tsx|typescript)?\n", "", raw_response, flags=re.MULTILINE)
            clean = re.sub(r"```$", "", clean, flags=re.MULTILINE).strip()
        return re.sub(r"```[a-zA-Z]*", "", clean).strip()

    def _build_user_prompt(self, prompt: str, design_spec: dict[str, Any]) -> str:
        """Build user prompt with deduplicated assets and fallback resolution."""
        assets_block = ""
        if "CATÁLOGO DE FOTOS" not in prompt and "verified_assets" not in prompt:
            assets_file = Path(__file__).resolve().parent.parent / "fixtures" / "verified_assets.json"
            if assets_file.exists():
                try:
                    assets_dict = json.loads(assets_file.read_text(encoding="utf-8"))
                    assets_block = f"\n\nCATÁLOGO DE ACTIVOS FOTOGRÁFICOS VERIFICADOS (USA EXCLUSIVAMENTE ESTAS URLS PARA GARANTIZAR QUE NUNCA DEN 404):\n{json.dumps(assets_dict, indent=2)}\n"
                except Exception as e:
                    logger.debug(f"Assets load note: {e}")

        brand_name = design_spec.get("app_name") or design_spec.get("brand_name") or "Plataforma SOTA"
        tagline = design_spec.get("tagline") or design_spec.get("hero_headline") or ""
        paradigm = design_spec.get("aesthetic_paradigm") or "Clean High-End Craft"

        return (
            f"PROMPT DEL NEGOCIO:\n{prompt}\n\n"
            f"ESPECIFICACIÓN DE DIRECCIÓN DE ARTE (DESIGN.md):\n"
            f"- Nombre Comercial: {brand_name}\n"
            f"- Paradigma: {paradigm}\n"
            f"- Tagline: {tagline}\n"
            f"- Vocabulario Ontológico: {', '.join(design_spec.get('ontological_terms', []))}\n"
            f"{assets_block}\n"
            "Genera el componente 'GenerativeLandingView' cumpliendo el Zero-Hex Mandate, usando fotos verificadas y exportando 'LandingView'."
        )

    def _execute_resilient_generation(
        self, client: Any, effective_model: str, system_instruction: str, user_prompt: str
    ) -> tuple[bool, str, str]:
        """Execute LLM generation with automatic ModelTier.FAST failover on timeout."""
        current_model = effective_model
        for attempt in range(1, 4):
            try:
                if attempt > 1:
                    current_model = get_model(ModelTier.FAST)
                    logger.warning(f"Reintentando síntesis UI con modelo de alta resiliencia ({current_model})...")

                resp = client.models.generate_content(
                    model=current_model,
                    contents=user_prompt,
                    config={"system_instruction": system_instruction, "temperature": 0.2},
                )
                if resp and resp.text:
                    return True, resp.text, ""
            except Exception as net_err:
                if attempt < 3:
                    time.sleep(2.0 * attempt)
                    continue
                logger.error(f"Error invocando Gemini UI tras 3 intentos: {net_err}")
                return False, "", str(net_err)

        return False, "", "Inferencia sin respuesta"

    def _post_process_and_repair(self, raw_text: str, design_spec: dict[str, Any]) -> SynthesisResult:
        """Clean markdown, auto-repair taste violations, and enforce export conventions."""
        try:
            clean_tsx = self.extract_clean_code(raw_text)
            violations = self.linter.lint_code(clean_tsx)
            repaired = False

            clean_tsx = taste_engine.auto_repair_taste_violations(clean_tsx)

            if "export const LandingView" not in clean_tsx and "export function LandingView" not in clean_tsx:
                clean_tsx += "\n\nexport const LandingView = GenerativeLandingView;\n"
            if "export default" not in clean_tsx:
                clean_tsx += "export default GenerativeLandingView;\n"

            if violations:
                logger.warning(f"Se detectaron {len(violations)} violaciones del Zero-Hex Mandate. Aplicando auto-reparación...")
                hex_map = _build_hex_to_token_map(design_spec)
                repaired_tsx, count = self.linter.auto_repair_hex_classes(clean_tsx, hex_map)
                if count > 0:
                    clean_tsx = repaired_tsx
                    repaired = True
                    violations = self.linter.lint_code(clean_tsx)

            sloc = len(clean_tsx.splitlines())
            return SynthesisResult(
                success=True,
                tsx_code=clean_tsx,
                sloc=sloc,
                violations_detected=violations,
                repaired_automatically=repaired,
            )
        except Exception as exc:
            logger.error(f"Error en post-procesado generativo: {exc}", exc_info=True)
            return SynthesisResult(success=False, tsx_code="", sloc=0, error_message=str(exc))

    def synthesize_view(
        self,
        client: Any,
        prompt: str,
        design_spec: dict[str, Any],
        model_id: str | None = None
    ) -> SynthesisResult:
        """Synthesize a complete TSX view guided by art direction and validate semantic token compliance with auto-repair."""
        effective_model = model_id or get_model(ModelTier.REASONING)
        system_instruction = self.build_system_instruction(design_spec)
        user_prompt = self._build_user_prompt(prompt, design_spec)

        success, raw_text, err = self._execute_resilient_generation(
            client, effective_model, system_instruction, user_prompt
        )
        if not success:
            return SynthesisResult(success=False, tsx_code="", sloc=0, error_message=err)

        return self._post_process_and_repair(raw_text, design_spec)


generative_ui_synthesizer = GenerativeUISynthesizer()
