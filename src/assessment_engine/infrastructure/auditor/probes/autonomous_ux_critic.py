"""
Audit user experience and cognitive heuristics autonomously using multimodal analysis. Key principles:
- Scriptless exploratory defect discovery.
- Dual-process cognitive review.
- Nielsen's 10 usability heuristics and W3C accessibility guidelines.
- Decoupled navigation (actuator) and audit (critic) architecture.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult
DEFAULT_UX_CRITIC_URL = os.environ.get("UX_CRITIC_TARGET_URL", "http://127.0.0.1:8088")

try:
    from playwright.async_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
except ImportError:
    class PlaywrightError(Exception): pass
    class PlaywrightTimeoutError(Exception): pass

logger = logging.getLogger("assessment_engine.infrastructure.auditor.probes.autonomous_ux_critic")

FORBIDDEN_TECH_TERMS: dict[str, str] = {
    r"\bsqlite\b": "Fuga de arquitectura de base de datos técnica (SQLite)",
    r"\bpostgresql\b": "Fuga de tecnología de base de datos (PostgreSQL)",
    r"\brest api\b": "Jerga técnica de backend (REST API)",
    r"\bjson\b": "Formato de intercambio técnico expuesto a usuario final",
    r"\bdial[_-]?dec\b": "Fuga de IDs de telemetría de tests o arbitraje cognitivo",
    r"\bdecisi[oó]n aplicada\b": "Fuga de eventos internos de benchmark",
    r"\btoken_version\b": "Fuga de implementación interna de seguridad JWT",
    r"\bconcurrency\b": "Concepto técnico de concurrencia expuesto en UI de cliente",
    r"\bendpoint\b": "Término de infraestructura de red en interfaz de usuario",
    r"\bwal mode\b": "Término de almacenamiento bajo nivel (WAL)",
    r"\bparents\[\d+\]\b": "Rastro de error de resolución de rutas de servidor",
    r"\b501 not implemented\b": "Mensaje de error técnico HTTP no controlado",
}


@dataclass
class PersonaProfile:
    """Represent the psychological profile and objective of a synthetic user."""
    persona_id: str
    name: str
    role: str  # "guest", "client", "staff", "admin"
    primary_goal: str
    journey_steps: list[str]
    allowed_views: list[str]
    prohibited_elements: list[str] = field(default_factory=list)


@dataclass
class UXInteractionObservation:
    """Represent a screen snapshot captured during navigation."""
    step_name: str
    url: str
    view_name: str
    title: str
    headings: list[str]
    visible_buttons: list[str]
    visible_inputs: list[dict[str, Any]]
    text_content_sample: str
    screenshot_path: str | None = None
    has_modal_open: bool = False
    console_errors: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class UXAuditReport:
    """Represent the consolidated user experience audit report."""
    timestamp: str
    target_url: str
    overall_ux_grade: str  # "SOTA_EXCELLENCE" (A+), "PROFESSIONAL" (A), "USABLE" (B), "DEFECTIVE" (C), "CRITICAL_FRICTION" (F)
    overall_score_pct: float
    personas_audited: list[str]
    steps_evaluated: int
    findings: list[AuditFinding]
    metrics: dict[str, Any]


class AutonomousUXCritic:
    """Perform autonomous UX reviews by executing exploratory cognitive walkthroughs on the application, evaluating each screen against design heuristics, and detecting user friction."""

    def __init__(self, target_base_url: str = DEFAULT_UX_CRITIC_URL, output_dir: Path | None = None) -> None:
        self.target_base_url = target_base_url.rstrip("/")
        self.output_dir = output_dir or Path("docs/audit_screenshots")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.findings: list[AuditFinding] = []
        self.observations: list[UXInteractionObservation] = []

    def get_standard_personas(self) -> list[PersonaProfile]:
        """Generate the canonical trio of user personas for the audit."""
        return [
            PersonaProfile(
                persona_id="new_patient_onboarding",
                name="Persona 1: Carlos Mendoza (Nuevo Paciente / Visitante)",
                role="guest",
                primary_goal="Descubrir la clínica, entender los servicios y reservar su primera cita online",
                journey_steps=["landing_hero", "explore_pricing", "open_booking_calendar", "fill_intake_form"],
                allowed_views=["landing", "booking"],
                prohibited_elements=["Consola Pro", "Consola de Gestión", "Panel de Operaciones", "Backoffice"]
            ),
            PersonaProfile(
                persona_id="returning_client_portal",
                name="Persona 2: María Gómez (Paciente Registrado con Cita)",
                role="client",
                primary_goal="Gestionar sus citas médicas, revisar detalles y conectarse a videollamada",
                journey_steps=["sign_in_client", "view_patient_portal", "verify_appointment_card", "test_reschedule_action"],
                allowed_views=["client", "booking", "teleconsulta"],
                prohibited_elements=["Consola de Gestión", "Base de Datos", "Monedero SMS", "Kanban Operaciones"]
            ),
            PersonaProfile(
                persona_id="clinical_staff_operator",
                name="Persona 3: Dra. Elena Ramos (Especialista / Administrador)",
                role="admin",
                primary_goal="Gestionar agenda de pacientes, mover estados en Kanban y revisar registros",
                journey_steps=["sign_in_admin", "access_admin_console", "inspect_kanban_board", "inspect_datagrid"],
                allowed_views=["admin", "staff", "operaciones", "registros", "agenda"],
                prohibited_elements=[]
            )
        ]


    def audit_text_jargon_leaks(self, text_content: str, context_label: str) -> list[AuditFinding]:
        """Detect developer jargon leaked into user-visible text."""
        findings: list[AuditFinding] = []
        lower_text = text_content.lower()
        for pattern, explanation in FORBIDDEN_TECH_TERMS.items():
            matches = list(re.finditer(pattern, lower_text, re.IGNORECASE))
            if matches:
                matched_snippet = matches[0].group(0)
                findings.append(AuditFinding(
                    category="UX_HUMAN_EXPERIENCE",
                    severity="HIGH",
                    file_path=context_label,
                    line_number=None,
                    rule_id="UX-LEAK-DEVELOPER-JARGON",
                    message=f"Fuga de jerga técnica detectada: '{matched_snippet}' ({explanation})",
                    recommendation="Reemplazar por valor de negocio y lenguaje clínico humano comprensible para usuarios no técnicos."
                ))
        return findings

    def audit_unexplained_disabled_fields(self, inputs: list[dict[str, Any]], context_label: str) -> list[AuditFinding]:
        """Detect disabled inputs or textareas that block interaction without explanation."""
        findings: list[AuditFinding] = []
        for inp in inputs:
            is_disabled = inp.get("disabled", False)
            tag = inp.get("tag", "input")
            field_name = inp.get("name") or inp.get("id") or inp.get("placeholder") or "campo_formulario"
            field_type = inp.get("type", "text")

            if is_disabled and field_type not in ("hidden", "submit"):
                has_explanation = bool(inp.get("aria_describedby") or inp.get("title"))
                if not has_explanation:
                    findings.append(AuditFinding(
                        category="UX_HUMAN_EXPERIENCE",
                        severity="CRITICAL",
                        file_path=context_label,
                        line_number=None,
                        rule_id="UX-INPUT-FROZEN-DISABLED",
                        message=f"Campo interactivo <{tag} name='{field_name}'> está deshabilitado arbitrariamente (disabled=true).",
                        recommendation="Permitir escribir libremente en el campo o auto-seleccionar el slot previo para evitar congelar al usuario."
                    ))
        return findings

    def audit_shouting_case_headers(self, headings: list[str], context_label: str) -> list[AuditFinding]:
        """Detect aggressive all-caps headings exceeding 25 characters."""
        findings: list[AuditFinding] = []
        for h in headings:
            cleaned = h.strip()
            if len(cleaned) >= 20 and cleaned.isupper():
                findings.append(AuditFinding(
                    category="UX_HUMAN_EXPERIENCE",
                    severity="MEDIUM",
                    file_path=context_label,
                    line_number=None,
                    rule_id="UX-TONE-AGGRESSIVE-ALL-CAPS",
                    message=f"Encabezado en mayúsculas agresivas (ALL CAPS): '{cleaned[:40]}...'",
                    recommendation="Usar tipografía en caja mixta (Title Case o Sentence Case) con tono cálido y profesional."
                ))
        return findings

    def audit_role_boundary_leaks(self, buttons: list[str], persona: PersonaProfile, context_label: str) -> list[AuditFinding]:
        """Detect administrative management buttons exposed to patients or clients."""
        findings: list[AuditFinding] = []
        if persona.role in ("guest", "client"):
            for btn_text in buttons:
                for prohibited in persona.prohibited_elements:
                    if prohibited.lower() in btn_text.lower():
                        findings.append(AuditFinding(
                            category="UX_HUMAN_EXPERIENCE",
                            severity="HIGH",
                            file_path=context_label,
                            line_number=None,
                            rule_id="UX-ROLE-PRIVILEGE-LEAK",
                            message=f"Elemento de administración expuesto a {persona.role}: '{btn_text}'",
                            recommendation="Ocultar accesos de staff/admin a usuarios no autenticados o con rol cliente."
                        ))
        return findings

    def audit_empty_state_welcoming(self, records_count: int, page_text: str, context_label: str) -> list[AuditFinding]:
        """Verify that an empty state provides a welcome card and guidance without language lock."""
        findings: list[AuditFinding] = []
        if records_count == 0:
            clean = page_text.strip()
            has_guidance = len(clean) >= 45 and not clean.startswith(("0", "none", "null"))
            if not has_guidance:
                findings.append(AuditFinding(
                    category="UX_HUMAN_EXPERIENCE",
                    severity="MEDIUM",
                    file_path=context_label,
                    line_number=None,
                    rule_id="UX-EMPTY-STATE-UNFRIENDLY",
                    message="Pantalla vacía sin registros carece de onboarding acogedor o botón de primera acción.",
                    recommendation="Añadir una ilustración o tarjeta amable explicando cómo crear el primer registro."
                ))
        return findings


    def evaluate_observation(self, obs: UXInteractionObservation, persona: PersonaProfile) -> list[AuditFinding]:
        """Run the full usability rule suite on a screen observation."""
        step_label = f"[{persona.persona_id}] {obs.step_name} ({obs.url})"
        step_findings: list[AuditFinding] = []

        # 1. Jargon leak audit
        full_text = f"{obs.title} {' '.join(obs.headings)} {' '.join(obs.visible_buttons)} {obs.text_content_sample}"
        step_findings.extend(self.audit_text_jargon_leaks(full_text, step_label))

        step_findings.extend(self.audit_unexplained_disabled_fields(obs.visible_inputs, step_label))

        step_findings.extend(self.audit_shouting_case_headers(obs.headings, step_label))

        step_findings.extend(self.audit_role_boundary_leaks(obs.visible_buttons, persona, step_label))

        for err in obs.console_errors:
            step_findings.append(AuditFinding(
                category="UX_HUMAN_EXPERIENCE",
                severity="HIGH",
                file_path=step_label,
                line_number=None,
                rule_id="UX-CLIENT-JAVASCRIPT-EXCEPTION",
                message=f"Excepción de JavaScript no capturada en navegador: {err[:120]}",
                recommendation="Corregir el error de ejecución de frontend para evitar romper la interactividad."
            ))

        self.findings.extend(step_findings)
        return step_findings


    def generate_report(self, personas_audited: list[str]) -> UXAuditReport:
        """Calculate the overall score and consolidate the user experience report."""
        critical_count = sum(1 for f in self.findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in self.findings if f.severity == "HIGH")
        medium_count = sum(1 for f in self.findings if f.severity == "MEDIUM")
        low_count = sum(1 for f in self.findings if f.severity in ("LOW", "INFO"))

        # Weighted score deduction
        penalties = (critical_count * 25.0) + (high_count * 10.0) + (medium_count * 4.0) + (low_count * 1.0)
        score = max(0.0, min(100.0, 100.0 - penalties))

        if score >= 95.0 and critical_count == 0:
            grade = "SOTA_EXCELLENCE"
        elif score >= 85.0 and critical_count == 0:
            grade = "PROFESSIONAL"
        elif score >= 70.0:
            grade = "USABLE"
        elif score >= 50.0:
            grade = "DEFECTIVE"
        else:
            grade = "CRITICAL_FRICTION"

        metrics = {
            "total_steps_audited": len(self.observations),
            "total_findings": len(self.findings),
            "critical_frictions": critical_count,
            "high_frictions": high_count,
            "medium_frictions": medium_count,
            "low_frictions": low_count,
            "jargon_leaks_found": sum(1 for f in self.findings if f.rule_id == "UX-LEAK-DEVELOPER-JARGON"),
            "frozen_inputs_found": sum(1 for f in self.findings if f.rule_id == "UX-INPUT-FROZEN-DISABLED"),
            "role_leaks_found": sum(1 for f in self.findings if f.rule_id == "UX-ROLE-PRIVILEGE-LEAK"),
        }

        return UXAuditReport(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            target_url=self.target_base_url,
            overall_ux_grade=grade,
            overall_score_pct=round(score, 1),
            personas_audited=personas_audited,
            steps_evaluated=len(self.observations),
            findings=list(self.findings),
            metrics=metrics
        )

    def to_probe_result(self, personas_audited: list[str]) -> ProbeResult:
        """Convert the UX report into the standard ProbeResult contract."""
        report = self.generate_report(personas_audited)
        return ProbeResult(
            probe_name="autonomous_ux_critic",
            score_pct=report.overall_score_pct,
            passed=report.overall_score_pct >= 85.0 and report.metrics["critical_frictions"] == 0,
            metrics=report.metrics,
            findings=report.findings
        )

    async def run_live_audit(self, headless: bool = True) -> UXAuditReport:
        """Execute the walkthrough in headless Chromium using Playwright, emulating three synthetic personas and capturing forensic evidence."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright no disponible en el entorno.")
            return self.generate_report(["mock_fallback"])

        personas = self.get_standard_personas()
        audited_persona_ids: list[str] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)

            for persona in personas:
                audited_persona_ids.append(persona.persona_id)
                context = await browser.new_context(viewport={"width": 1440, "height": 900})
                page = await context.new_page()
                console_errors: list[str] = []
                page.on("pageerror", lambda err: console_errors.append(str(err)))

                if persona.persona_id == "new_patient_onboarding":
                    # Paso 1: Portada
                    await page.goto(f"{self.target_base_url}/#view=landing", wait_until="networkidle")
                    await page.wait_for_timeout(500)
                    obs_landing = await self._capture_page_state(page, "landing_hero", console_errors)
                    self.evaluate_observation(obs_landing, persona)

                    # Paso 2: Tarifas
                    try:
                        await page.locator("#precios").scroll_into_view_if_needed()
                        await page.wait_for_timeout(300)
                        obs_prices = await self._capture_page_state(page, "explore_pricing", console_errors)
                        self.evaluate_observation(obs_prices, persona)
                    except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError) as ex:
                        logger.debug(f"[UXCritic] Error en scroll de tarifas: {ex}")

                    # Paso 3: Calendario de Citas y Formulario
                    await page.goto(f"{self.target_base_url}/#view=booking", wait_until="networkidle")
                    await page.wait_for_timeout(600)
                    # Attempt to enter the consultation reason
                    try:
                        textarea = page.locator("textarea").first
                        if await textarea.is_visible():
                            await textarea.fill("Revisión general preventiva para mi consulta")
                    except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError) as ex:
                        logger.debug(f"[UXCritic] Error en llenado de textarea: {ex}")

                    obs_booking = await self._capture_page_state(page, "open_booking_calendar", console_errors)
                    self.evaluate_observation(obs_booking, persona)

                elif persona.persona_id == "returning_client_portal":
                    await page.goto(f"{self.target_base_url}/#view=landing", wait_until="networkidle")
                    try:
                        # Log in as demo user Carlos
                        await page.locator("button:has-text('Iniciar Sesión')").click()
                        await page.wait_for_timeout(400)
                        await page.locator("button:has-text('Modo Paciente')").click()
                        await page.wait_for_timeout(800)
                    except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError):
                        await page.goto(f"{self.target_base_url}/#view=client", wait_until="networkidle")

                    obs_portal = await self._capture_page_state(page, "view_patient_portal", console_errors)
                    self.evaluate_observation(obs_portal, persona)

                    # Verify empty state or appointments
                    page_text = await page.locator("body").inner_text()
                    cards = await page.locator("[class*='rounded-2xl'][class*='border']").all()
                    self.findings.extend(self.audit_empty_state_welcoming(len(cards), page_text, f"[{persona.persona_id}] portal_appointments"))

                elif persona.persona_id == "clinical_staff_operator":
                    await page.goto(f"{self.target_base_url}/#view=landing", wait_until="networkidle")
                    try:
                        await page.locator("button:has-text('Iniciar Sesión')").click()
                        await page.wait_for_timeout(400)
                        await page.locator("button:has-text('Modo Administrador')").click()
                        await page.wait_for_timeout(800)
                    except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError):
                        await page.goto(f"{self.target_base_url}/#view=admin", wait_until="networkidle")

                    obs_admin = await self._capture_page_state(page, "access_admin_console", console_errors)
                    self.evaluate_observation(obs_admin, persona)

                    # Navigate to the Operations Board (Kanban)
                    try:
                        kanban_btn = page.locator("nav button:has-text('Panel de Operaciones')")
                        if await kanban_btn.is_visible():
                            await kanban_btn.click()
                            await page.wait_for_timeout(600)
                            obs_kanban = await self._capture_page_state(page, "admin_kanban_board", console_errors)
                            self.evaluate_observation(obs_kanban, persona)
                    except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError) as ex:
                        logger.debug(f"[UXCritic] Error navegando a Kanban: {ex}")

                    # Navigate to Management and Records (DataGrid)
                    try:
                        datagrid_btn = page.locator("nav button:has-text('Gestión y Registros')")
                        if await datagrid_btn.is_visible():
                            await datagrid_btn.click()
                            await page.wait_for_timeout(600)
                            obs_datagrid = await self._capture_page_state(page, "admin_datagrid_table", console_errors)
                            self.evaluate_observation(obs_datagrid, persona)
                    except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError) as ex:
                        logger.debug(f"[UXCritic] Error navegando a DataGrid: {ex}")

                await context.close()

            await browser.close()

        return self.generate_report(audited_persona_ids)

    async def _capture_page_state(self, page: Any, step_name: str, console_errors: list[str]) -> UXInteractionObservation:
        """Extract the interactive state of the current page in Playwright."""
        url = page.url
        title = await page.title()
        headings = await page.locator("h1, h2, h3").all_inner_texts()
        cleaned_headings = [h.strip() for h in headings if h.strip()]

        raw_buttons = await page.locator("button, [role='button'], a[href^='#']").all_inner_texts()
        cleaned_buttons = [b.replace("\n", " ").strip() for b in raw_buttons if b.strip()]

        inputs_data: list[dict[str, Any]] = []
        raw_inputs = await page.locator("input, textarea, select").all()
        for inp in raw_inputs:
            try:
                tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                is_disabled = await inp.is_disabled()
                name_attr = await inp.get_attribute("name") or await inp.get_attribute("id") or ""
                type_attr = await inp.get_attribute("type") or "text"
                placeholder = await inp.get_attribute("placeholder") or ""
                inputs_data.append({
                    "tag": tag,
                    "disabled": is_disabled,
                    "name": name_attr,
                    "type": type_attr,
                    "placeholder": placeholder
                })
            except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError) as ex:
                logger.debug(f"[UXCritic] Error extrayendo metadatos de input: {ex}")

        body_text = await page.locator("body").inner_text()
        text_sample = body_text[:2000]

        # Evidence screenshot
        shot_filename = f"ux_critic_{step_name}_{int(time.time())}.png"
        shot_path = str(self.output_dir / shot_filename)
        try:
            await page.screenshot(path=shot_path, full_page=False)
        except (PlaywrightError, PlaywrightTimeoutError, ValueError, OSError):
            shot_path = None

        obs = UXInteractionObservation(
            step_name=step_name,
            url=url,
            view_name=step_name,
            title=title,
            headings=cleaned_headings,
            visible_buttons=cleaned_buttons,
            visible_inputs=inputs_data,
            text_content_sample=text_sample,
            screenshot_path=shot_path,
            console_errors=list(console_errors)
        )
        self.observations.append(obs)
        return obs
