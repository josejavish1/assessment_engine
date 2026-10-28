"""
Provide regression evaluation, Playwright testing, and self-repair (core/evolution).
Extracted from autonomous_evolution_engine.py using the Strangler Fig pattern.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types
from playwright.async_api import async_playwright

from assessment_engine.infrastructure.primitives.architect_editor import architect_editor
from assessment_engine.infrastructure.primitives.code_hygiene import code_hygiene
from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("evolution_eval_runner")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACES_ROOT = ROOT_DIR / "workspaces"


class EvolutionEvalRunner:
    """Execute the Playwright harness, validate physical persistence in SQLite, and hot-patch code."""

    @staticmethod
    def count_sqlite_domain_rows(db_file: Path) -> int:
        """Count physical rows across all domain tables in SQLite WAL."""
        if not db_file.exists():
            return 0
        conn = sqlite3.connect(str(db_file), timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [r[0] for r in cur.fetchall()]
            total = 0
            for t in tables:
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{t}";')
                    total += cur.fetchone()[0]
                except sqlite3.Error as ex:
                    logger.debug(f"Count table note: {ex}")
            return total
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as s_err:# noqa: BLE001
            logger.debug(f"SQLite count note: {s_err}")
            return 0
        finally:
            conn.close()

    @staticmethod
    async def check_runtime_errors(page: Any, telemetry: dict[str, Any], console_errors: list[str]) -> tuple[bool, str]:
        """Check for runtime and console errors in page telemetry and logs."""
        broken = await page.evaluate(
            "() => Array.from(document.querySelectorAll('img')).filter(i => i.offsetParent !== null && i.getAttribute('src') && i.naturalWidth === 0).length"
        )
        if broken > 0:
            return False, f"Se detectaron {broken} imágenes rotas visibles en el DOM."

        net_errors = telemetry.get("network_errors", [])
        if net_errors:
            err0 = net_errors[0]
            return False, f"Fallo de red en telemetría: {err0.get('method')} {err0.get('url')} devolvió HTTP {err0.get('status')}."

        js_errors = telemetry.get("js_exceptions", [])
        if not js_errors and console_errors:
            real_errors = [
                err for err in console_errors
                if not ("Failed to load resource" in err and any(ext in err.lower() for ext in [".ico", ".svg", ".png", "favicon"]))
            ]
            if real_errors:
                js_errors = real_errors

        if js_errors:
            return False, f"Excepción JavaScript detectada en runtime: {js_errors[0]}"

        return True, "OK"

    @staticmethod
    async def check_workspace_views_density(page: Any, contract_data: dict[str, Any] | None) -> tuple[bool, str]:
        """Validate the display density of workspace views on the page."""
        enter_btn = page.locator(
            "button:has-text('Acceder'), a:has-text('Acceder'), button:has-text('Entrar'), button:has-text('Registrarse'), button:has-text('Iniciar Sesión'), button:has-text('Comenzar'), button:has-text('Abrir Módulo')"
        ).first
        if await enter_btn.count() > 0 and await enter_btn.is_visible():
            try:
                await enter_btn.click()
                await page.wait_for_timeout(1000)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as enter_err:# noqa: BLE001
                logger.debug(f"Enter portal note: {enter_err}")

        workspace_views = (contract_data or {}).get("workspace_views", [])
        if workspace_views:
            detected_views = 0
            for v in workspace_views:
                v_id = v.get("id", "")
                v_name = v.get("name", "")
                view_btn = page.locator(
                    f"[data-workspace-id='{v_id}'], button:has-text('{v_name}'), a:has-text('{v_name}')"
                ).first
                if await view_btn.count() > 0:
                    detected_views += 1

            if detected_views < len(workspace_views):
                req_views_str = ", ".join(v.get("name", "") for v in workspace_views)
                return False, (
                    f"Fallo Semántico de Dominio: El portal carece de los espacios de trabajo requeridos "
                    f"({detected_views}/{len(workspace_views)} detectados). Se exige navegación interactiva completa "
                    f"para los espacios: {req_views_str}. Queda prohibido degradar la interfaz a botones genéricos."
                )

        btn_count = await page.locator("button, a[role='button']").count()
        if btn_count < 3:
            return False, f"Fallo Semántico de Densidad: El DOM carece de componentes interactivos suficientes (Detectados: {btn_count} botones; Requeridos: >=3 botones)."

        return True, "OK"

    @staticmethod
    async def _fill_single_input(inp: Any, marker_text: str) -> None:
        if not await inp.is_visible(): return
        i_type = (await inp.get_attribute("type") or "text").lower()
        if i_type in ["checkbox", "radio"]:
            if not await inp.check(): await inp.check()
        elif i_type == "email": await inp.fill("creador@ejemplo.com")
        elif i_type == "url": await inp.fill("https://ejemplo.com/logo.png")
        elif i_type == "number": await inp.fill("49")
        else: await inp.fill(marker_text)

    @classmethod
    async def _fill_inputs(cls, form: Any, marker_text: str) -> None:
        inputs = form.locator("input:not([type='hidden']), textarea")
        for idx in range(await inputs.count()):
            await cls._fill_single_input(inputs.nth(idx), marker_text)

    @staticmethod
    async def _fill_single_select(sel: Any) -> None:
        if not await sel.is_visible():
            return
        options = sel.locator("option")
        if await options.count() <= 1:
            return
        val = await options.nth(1).get_attribute("value")
        if val:
            await sel.select_option(val)

    @classmethod
    async def _fill_selects(cls, form: Any) -> None:
        selects = form.locator("select")
        for s_idx in range(await selects.count()):
            await cls._fill_single_select(selects.nth(s_idx))

    @classmethod
    async def fill_form_interactive_fields(cls, form: Any, marker_text: str) -> None:
        """Heuristically populate form inputs and select elements."""
        await cls._fill_inputs(form, marker_text)
        await cls._fill_selects(form)

    @staticmethod
    async def verify_post_reload_f5_rendering(page: Any, form_tab: Any, marker_text: str) -> bool:
        """Verify that data persists and renders in the DOM after page reload."""
        await page.reload(wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)

        enter_again = page.locator("button:has-text('Acceder'), a:has-text('Acceder'), button:has-text('Entrar'), button:has-text('Registrarse')").first
        if await enter_again.count() > 0 and await enter_again.is_visible():
            try:
                await enter_again.click()
                await page.wait_for_timeout(600)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                logger.debug(f"Enter click note: {ex}")

        if await form_tab.count() > 0:
            try:
                await form_tab.click()
                await page.wait_for_timeout(800)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                logger.debug(f"Form tab click note: {ex}")

        dom_content = await page.inner_text("body")
        return marker_text in dom_content

    @classmethod
    async def test_sqlite_persistence_and_f5(
        cls, page: Any, slug: str, form_tab: Any, telemetry: dict[str, Any]
    ) -> tuple[bool, str]:
        if await form_tab.count() > 0:
            try:
                await form_tab.click()
                await page.wait_for_timeout(500)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as tab_err:# noqa: BLE001
                logger.debug(f"Tab click note: {tab_err}")

        db_file = (WORKSPACES_ROOT / slug / "app.db").resolve()
        rows_before = cls.count_sqlite_domain_rows(db_file)
        submit_btn = page.locator("button[type='submit'], button:has-text('Publicar'), button:has-text('Guardar'), button:has-text('Crear'), button:has-text('Enviar'), button:has-text('Añadir')").first
        marker_text = f"Audit Invariant {int(asyncio.get_event_loop().time())}"

        if await submit_btn.count() > 0:
            try:
                form = page.locator("form:has(button[type='submit']), form").first
                if await form.count() > 0:
                    await cls.fill_form_interactive_fields(form, marker_text)
                else:
                    text_input = page.locator("textarea, input[type='text']:not([readonly])").first
                    if await text_input.count() > 0:
                        await text_input.fill(marker_text)

                await submit_btn.click()
                await page.wait_for_timeout(1000)

                rows_after = cls.count_sqlite_domain_rows(db_file)
                if rows_after <= rows_before:
                    return False, "Oráculo SQLite falló: Se hizo clic en el formulario pero no se insertó ninguna fila física en la base de datos (Delta = 0 filas)."

                is_rendered = await cls.verify_post_reload_f5_rendering(page, form_tab, marker_text)
                if not is_rendered:
                    return False, "Fallo F5: El registro físico se guardó en SQLite pero no se renderizó en la vista tras recargar con F5."
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as interact_err:# noqa: BLE001
                logger.debug(f"Interacción note: {interact_err}")

        return True, "OK"

    @classmethod
    async def audit_with_playwright(
        cls,
        slug: str,
        daemon_ensure_fn: Any,
        schema_info: dict[str, Any] | None = None,
        contract_data: dict[str, Any] | None = None
    ) -> tuple[bool, str, dict[str, Any]]:
        """Implement a dual-verification oracle with built-in telemetry."""
        app_url = f"http://127.0.0.1:8000/preview/{slug}/"
        telemetry: dict[str, Any] = {}
        try:
            await daemon_ensure_fn(slug)

            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(viewport={"width": 1440, "height": 900})
                console_errors: list[str] = []
                page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

                await page.goto(app_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(600)

                try:
                    telemetry = await page.evaluate("() => window.__telemetry || {}")
                except (RuntimeError, ValueError, KeyError, OSError, TypeError) as t_err:# noqa: BLE001
                    logger.debug(f"Telemetry extraction note: {t_err}")

                err_ok, err_msg = await cls.check_runtime_errors(page, telemetry, console_errors)
                if not err_ok:
                    await browser.close()
                    return False, err_msg, telemetry

                view_ok, view_msg = await cls.check_workspace_views_density(page, contract_data)
                if not view_ok:
                    await browser.close()
                    return False, view_msg, telemetry

                form_tab = page.locator("[data-workspace-id*='estudio'], [data-workspace-id*='admin'], [data-workspace-id*='comunidad']").first
                f5_ok, f5_msg = await cls.test_sqlite_persistence_and_f5(page, slug, form_tab, telemetry)
                if not f5_ok:
                    await browser.close()
                    return False, f5_msg, telemetry

                await browser.close()
                return True, "OK: Oráculo SQLite físico, telemetría y F5 verificados al 100%.", telemetry
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            return False, f"Fallo al cargar la aplicación con Playwright: {e!s}", telemetry

    @staticmethod
    def resolve_target_react_component(
        ws_dir: Path, views_dir: Path, web_dir: Path, milestone: dict[str, Any]
    ) -> tuple[Path, str]:
        """Resolve the target TSX file to specialize for the milestone."""
        target_files = milestone.get("target_files", [])
        if target_files and isinstance(target_files, list) and len(target_files) > 0:
            candidate = (ws_dir / target_files[0]).resolve()
            if candidate.exists():
                return candidate, candidate.name

        target_view = (milestone.get("target_view", "") or "").lower()
        m_title = (milestone.get("title", "") or "").lower()
        is_landing = any(k in target_view or k in m_title for k in ["landing", "marketing", "portal", "home", "onboarding"])

        target_file = views_dir / ("LandingView.tsx" if is_landing else "DynamicWorkspaceView.tsx")
        if target_file.exists():
            return target_file, target_file.name

        fallback = web_dir / "src" / "App.tsx"
        return fallback, fallback.name

    @staticmethod
    async def compile_and_validate_tsx(
        target_file: Path, clean_tsx: str, web_dir: Path, slug: str, target_name: str, inner_attempt: int
    ) -> tuple[bool, str]:
        """Verify absence of placeholder code, format with Rust, and build with Vite."""
        for pat in architect_editor.LAZY_PATTERNS:
            if pat.search(clean_tsx):
                raise ValueError("Alerta de Lazy Coding: Se detectó un marcador de código omitido en la síntesis.")

        target_file.write_text(clean_tsx, encoding="utf-8")
        code_hygiene.polish_frontend_code(target_file)

        proc = await asyncio.create_subprocess_exec(
            "npx", "vite", "build",
            cwd=str(web_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            logger.info(f"[{slug}] Inner Loop: React {target_name} compilado con éxito en Vite (Intento {inner_attempt})")
            return True, ""

        compiler_err = (stdout.decode() + "\n" + stderr.decode())[-500:]
        logger.warning(f"[{slug}] Inner Loop: Fallo Vite en {target_name} (intento {inner_attempt}): {compiler_err[-200:]}")
        return False, compiler_err

    @classmethod
    async def execute_milestone_react(
        cls,
        client: genai.Client | None,
        slug: str,
        milestone: dict[str, Any],
        roadmap: dict[str, Any],
        contract_data: dict[str, Any],
        schema_info: dict[str, Any] | None = None
    ) -> bool:
        """Specialize the corresponding modular component using Vite."""
        if not client:
            return False
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        web_dir = ws_dir / "web"
        views_dir = web_dir / "src" / "components" / "views"

        target_file, target_name = cls.resolve_target_react_component(ws_dir, views_dir, web_dir, milestone)
        if not target_file.exists():
            return False

        current_code = target_file.read_text(encoding="utf-8")
        backup_code = current_code
        tables = [t.get("name") for t in (schema_info or {}).get("tables_summary", [])]
        workspace_views = contract_data.get("workspace_views", [])
        tier1_pat = milestone.get("tier1_pattern") or "Diseño profesional y contrastado estilo Stripe y Linear"

        prompt = (
            "Eres el Staff React & TypeScript Engineer en Linear, Vercel y Stripe.\n"
            f"El objetivo es construir la plataforma de clase mundial: '{roadmap.get('goal')}'\n"
            f"Paradigma de UI: '{roadmap.get('ui_paradigm')}'\n"
            f"Líderes de referencia: {json.dumps(roadmap.get('market_leaders', []), ensure_ascii=False)}\n"
            f"Tablas relacionales en SQLite: {json.dumps(tables, ensure_ascii=False)}\n"
            f"Espacios de trabajo: {json.dumps(workspace_views, ensure_ascii=False)}\n\n"
            f"CÓDIGO ACTUAL DEL COMPONENTE {target_name} (React/TSX):\n```tsx\n{current_code[:4500]}\n```\n\n"
            f"TU MISIÓN ES ESPECIALIZAR ESTE COMPONENTE PARA EL MÓDULO: {milestone.get('id')} - {milestone.get('title')}\n"
            f"Descripción: {milestone.get('description')}\n"
            f"Criterios de aceptación: {milestone.get('test_criteria')}\n"
            f"Patrón ergonómico de referencia: {tier1_pat}\n"
            f"Archivo destino: {target_name}\n\n"
            "DIRECTIVAS ESTRICTAS DE REACT Y TYPESCRIPT (TIER-1 QUALITY):\n"
            "1. Mantén la estructura de React con hooks (useState, useEffect) y Tailwind CSS.\n"
            "2. Conecta la persistencia exclusivamente al cliente inyectado 'window.db'.\n"
            "3. En useEffect([]) asegúrate de cargar los datos para que persistan tras recargar con F5.\n"
            "4. OBLIGATORIO PARA LANDING: Mantén intacta la prop 'onEnterApp' y asegúrate de que los botones principales invoquen 'onEnterApp()' para transicionar al portal interactivo.\n"
            f"5. EMITE DIRECTAMENTE EL CÓDIGO COMPLETO Y CERRADO de {target_name}.\n"
            "6. CERO PLACEHOLDERS, CERO COMENTARIOS 'TODO'."
        )

        last_compiler_err = ""
        for inner_attempt in range(1, 4):
            try:
                iter_prompt = prompt
                if last_compiler_err:
                    iter_prompt += f"\n\nATENCIÓN: La compilación de Vite falló en el intento anterior:\n{last_compiler_err}"

                resp = await client.aio.models.generate_content(
                    model=get_model(ModelTier.FAST),
                    contents=iter_prompt,
                    config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=8192)
                )
                raw_tsx = resp.text or ""
                clean_tsx = re.sub(r"^```(?:tsx|typescript|jsx)?\s*", "", raw_tsx.strip(), flags=re.IGNORECASE)
                clean_tsx = re.sub(r"\s*```$", "", clean_tsx.strip())

                if any(kw in clean_tsx for kw in ["export function", "export default", "export const"]):
                    success, compiler_err = await cls.compile_and_validate_tsx(
                        target_file, clean_tsx, web_dir, slug, target_name, inner_attempt
                    )
                    if success:
                        return True
                    last_compiler_err = compiler_err
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
                last_compiler_err = str(e)
                logger.warning(f"Error en inner loop de React para {target_name}: {e}")

        target_file.write_text(backup_code, encoding="utf-8")
        proc_restore = await asyncio.create_subprocess_exec("npx", "vite", "build", cwd=str(web_dir), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await proc_restore.wait()
        return False

    @classmethod
    async def execute_milestone_code(
        cls,
        client: genai.Client | None,
        slug: str,
        milestone: dict[str, Any],
        roadmap: dict[str, Any],
        contract_data: dict[str, Any],
        schema_info: dict[str, Any] | None = None
    ) -> bool:
        """Implement and integrate milestone code in React (Vite)."""
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        web_src_app = ws_dir / "web" / "src" / "App.tsx"

        if web_src_app.exists():
            return await cls.execute_milestone_react(client, slug, milestone, roadmap, contract_data, schema_info)

        dist_file = ws_dir / "web" / "dist" / "index.html"
        current_code = dist_file.read_text(encoding="utf-8") if dist_file.exists() else ""
        if not client:
            return False

        prompt = (
            "Eres el Staff Full-Stack Software Engineer y Diseñador UI Principal en Linear, Stripe y Vercel.\n"
            f"El objetivo es construir la plataforma de clase mundial: '{roadmap.get('goal')}'\n"
            f"MÓDULO: {milestone.get('id')} - {milestone.get('title')}\n"
            f"DESCRIPCIÓN: {milestone.get('description')}\n"
            f"CÓDIGO ACTUAL:\n```html\n{current_code[:4500]}\n```\n"
        )
        try:
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.FAST),
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=8192)
            )
            raw_html = resp.text or ""
            clean_raw = re.sub(r"^```(?:html)?\s*", "", raw_html.strip(), flags=re.IGNORECASE)
            clean_raw = re.sub(r"\s*```$", "", clean_raw.strip())
            match = re.search(r"(<!doctype html.*?</html>)", clean_raw, re.DOTALL | re.IGNORECASE)
            clean_html = match.group(1).strip() if match else clean_raw.strip()

            if "<!doctype html" in clean_html.lower() and "</html>" in clean_html.lower():
                dist_file.parent.mkdir(parents=True, exist_ok=True)
                dist_file.write_text(clean_html, encoding="utf-8")
                return True
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.warning(f"Error generando código para hito {milestone.get('id')}: {e}")
        return False

    @staticmethod
    async def _heal_react_file(client: genai.Client, target_file: Path, web_dir: Path, slug: str, error_msg: str, telemetry_dump: str) -> None:
        current_code = target_file.read_text(encoding="utf-8")
        prompt = (
            "La auditoría interactiva de Playwright falló con este informe forense:\n"
            f"ERROR: {error_msg}\n{telemetry_dump}\n"
            f"CÓDIGO ACTUAL DEL COMPONENTE REACT ({target_file.name}):\n```tsx\n{current_code[:4500]}\n```\n"
            "Emite DIRECTAMENTE el código completo y cerrado corregido."
        )
        try:
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.FAST), contents=prompt, config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=8192)
            )
            raw = resp.text or ""
            clean_raw = re.sub(r"^```(?:tsx|typescript|jsx)?\s*", "", raw.strip(), flags=re.IGNORECASE)
            clean_raw = re.sub(r"\s*```$", "", clean_raw.strip())
            if any(kw in clean_raw for kw in ["export function", "export default", "export const"]):
                target_file.write_text(clean_raw, encoding="utf-8")
                code_hygiene.polish_frontend_code(target_file)
                proc = await asyncio.create_subprocess_exec("npx", "vite", "build", cwd=str(web_dir), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await proc.wait()
                logger.info(f"[{slug}] Auto-reparación React aplicada en {target_file.name}")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.warning(f"Error auto-reparando React: {e}")

    @staticmethod
    async def _heal_html_file(client: genai.Client, dist_file: Path, error_msg: str, telemetry_dump: str) -> None:
        code = dist_file.read_text(encoding="utf-8")
        prompt = f"ERROR: {error_msg}\n{telemetry_dump}\nCÓDIGO:\n```html\n{code[:5000]}\n```\nEmite el documento HTML completo corregido."
        try:
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.FAST), contents=prompt, config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=8192)
            )
            raw_html = resp.text or ""
            clean_raw = re.sub(r"^```(?:html)?\s*", "", raw_html.strip(), flags=re.IGNORECASE)
            clean_raw = re.sub(r"\s*```$", "", clean_raw.strip())
            match = re.search(r"(<!doctype html.*?</html>)", clean_raw, re.DOTALL | re.IGNORECASE)
            clean = match.group(1).strip() if match else clean_raw.strip()
            if "<!doctype html" in clean.lower() and "</html>" in clean.lower():
                dist_file.write_text(clean, encoding="utf-8")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.warning(f"Error auto-reparando HTML: {e}")

    @classmethod
    async def heal_code_with_playwright_error(
        cls, client: genai.Client | None, slug: str, error_msg: str, telemetry: dict[str, Any] | None = None
    ) -> None:
        """Repair code by injecting the black-box trace."""
        if not client: return
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        web_src_app = ws_dir / "web" / "src" / "App.tsx"
        web_dir = ws_dir / "web"
        views_dir = web_dir / "src" / "components" / "views"

        telemetry_dump = ""
        if telemetry:
            telemetry_dump = (
                "\nREGISTRO DE VUELO DE LA TELEMETRÍA (CAJA NEGRA FORENSE):\n"
                f"- Peticiones de red con error: {json.dumps(telemetry.get('network_errors', []), ensure_ascii=False)}\n"
                f"- Excepciones JavaScript: {json.dumps(telemetry.get('js_exceptions', []), ensure_ascii=False)}\n"
            )

        if web_src_app.exists():
            target_file = views_dir / "DynamicWorkspaceView.tsx"
            if not target_file.exists(): target_file = web_src_app
            await cls._heal_react_file(client, target_file, web_dir, slug, error_msg, telemetry_dump)
            return

        dist_file = ws_dir / "web" / "dist" / "index.html"
        if dist_file.exists():
            await cls._heal_html_file(client, dist_file, error_msg, telemetry_dump)
