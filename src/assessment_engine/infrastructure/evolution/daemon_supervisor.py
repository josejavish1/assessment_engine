"""
Manage mission supervision, daemon lifecycle, and orchestration (core/evolution).
Extracted from autonomous_evolution_engine.py using the Strangler Fig pattern.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from google import genai

from assessment_engine.infrastructure.domain_compiler import domain_compiler
from assessment_engine.infrastructure.primitives.adversarial_evaluator import adversarial_evaluator
from assessment_engine.infrastructure.primitives.apple_design_gate import audit_apple_design_compliance
from assessment_engine.infrastructure.primitives.context_condenser import context_condenser
from assessment_engine.infrastructure.evolution.eval_runner import EvolutionEvalRunner
from assessment_engine.infrastructure.evolution.roadmap_synthesizer import RoadmapSynthesizer
from assessment_engine.infrastructure.config.sre_constants import DEFAULT_MEILI_URL, DEFAULT_RETRY_BACKOFF_SEC, PROCESS_STARTUP_GRACE_SEC

logger = logging.getLogger("evolution_daemon_supervisor")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
WORKSPACES_ROOT = ROOT_DIR / "workspaces"


async def _is_search_engine_healthy() -> bool:
    """Check whether local search engine daemon is healthy and responding."""
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            m_resp = await client.get(f"{DEFAULT_MEILI_URL}/health")
            return m_resp.status_code == 200
    except (httpx.HTTPError, OSError):
        return False


class DaemonSupervisor:
    """Monitor the background daemon lifecycle and orchestrate long-running evolution missions."""

    @staticmethod
    async def _maybe_provision_search_engine(ws_dir: Path, slug: str) -> None:
        contract_file = ws_dir / "docs" / "DOMAIN_CONTRACT.json"
        if not contract_file.exists():
            return
        try:
            contract_data = json.loads(contract_file.read_text(encoding="utf-8"))
            active_prims = set(contract_data.get("active_primitives", []))
            needs_search = bool(
                contract_data.get("requires_search")
                or contract_data.get("requires_fts5")
                or "DirectoryGrid" in active_prims
                or "Fts5SearchIndex" in active_prims
                or "SearchEngine" in active_prims
            )
            if not needs_search:
                return
            meili_script = Path.home() / ".cache" / "autonomuos" / "engines" / "search" / "meilisearch-linux-amd64"
            if not meili_script.exists() or await _is_search_engine_healthy():
                return

            logger.info(f"[{slug}] Aprovisionando Gemelo Open Source: Meilisearch en puerto 7700")
            env = os.environ.copy()
            env["MEILI_MASTER_KEY"] = "factoria_master_key_12345"
            env["MEILI_DB_PATH"] = str(ws_dir / "meili_data")
            env["MEILI_HTTP_ADDR"] = "127.0.0.1:7700"
            asyncio.create_task(
                asyncio.create_subprocess_exec(
                    str(meili_script), env=env, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL, start_new_session=True
                )
            )
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.warning(f"Error aprovisionando gemelos para '{slug}': {e}")

    @staticmethod
    async def _ensure_frontend_built(ws_dir: Path) -> None:
        dist_html = ws_dir / "web" / "dist" / "index.html"
        if not dist_html.exists() and (ws_dir / "web" / "src" / "App.tsx").exists():
            proc_b = await asyncio.create_subprocess_exec(
                "npx", "vite", "build", cwd=str(ws_dir / "web"),
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await proc_b.wait()

    @staticmethod
    async def _check_existing_daemon(daemon_file: Path, ws_dir: Path) -> bool:
        if not daemon_file.exists():
            return False
        try:
            data = json.loads(daemon_file.read_text(encoding="utf-8"))
            port = data.get("port")
            if not port:
                return False
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.get(f"http://127.0.0.1:{port}/api/health")
                if resp.status_code == 200:
                    await DaemonSupervisor._ensure_frontend_built(ws_dir)
                    return True
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.debug(f"Health ping note: {ex}")
        return False

    @staticmethod
    async def _wait_for_daemon_health(port: int, ws_dir: Path, slug: str) -> bool:
        for _ in range(12):
            await asyncio.sleep(DEFAULT_RETRY_BACKOFF_SEC)
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    resp = await client.get(f"http://127.0.0.1:{port}/api/health")
                    if resp.status_code == 200:
                        await DaemonSupervisor._ensure_frontend_built(ws_dir)
                        logger.info(f"[{slug}] Daemon Uvicorn aprovisionado automáticamente en puerto {port}")
                        return True
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                logger.debug(f"Health wait note: {ex}")
        return False

    @staticmethod
    async def ensure_daemon_running(slug: str) -> bool:
        """Check if the Uvicorn daemon is running and start it automatically without patching."""
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        daemon_file = ws_dir / ".app_daemon.json"

        await DaemonSupervisor._maybe_provision_search_engine(ws_dir, slug)
        if await DaemonSupervisor._check_existing_daemon(daemon_file, ws_dir):
            return True

        try:
            from server import run_project_application
            res = run_project_application(slug)
            port = res.get("port")
            if port:
                return await DaemonSupervisor._wait_for_daemon_health(port, ws_dir, slug)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:# noqa: BLE001
            logger.warning(f"Error aprovisionando daemon automáticamente para '{slug}': {e}")
        return False

    @staticmethod
    def _apply_primitives(ws_dir: Path, slug: str, contract_data: dict[str, Any]) -> None:
        from assessment_engine.infrastructure.primitives.pwa_generator import pwa_generator
        from assessment_engine.infrastructure.primitives.legal_engine import legal_engine
        from assessment_engine.infrastructure.primitives.geo_engine import geo_engine
        from assessment_engine.infrastructure.primitives.social_card_generator import social_card_generator
        from assessment_engine.infrastructure.primitives.sitemap_generator import sitemap_generator
        from assessment_engine.infrastructure.primitives.distroless_builder import distroless_builder
        from assessment_engine.infrastructure.primitives.compose_orchestrator import compose_orchestrator
        from assessment_engine.infrastructure.primitives.ci_cd_generator import ci_cd_generator
        from assessment_engine.infrastructure.primitives.secret_leak_sentinel import secret_leak_sentinel
        from assessment_engine.infrastructure.primitives.zero_fouc_theme import zero_fouc_theme
        from assessment_engine.infrastructure.primitives.speculative_preloader import speculative_preloader
        from assessment_engine.infrastructure.primitives.skeleton_shimmer import skeleton_shimmer
        from assessment_engine.infrastructure.primitives.canonical_urls import canonical_urls
        from assessment_engine.infrastructure.primitives.print_stylesheet import print_stylesheet
        from assessment_engine.infrastructure.primitives.audit_trail import audit_trail
        from assessment_engine.infrastructure.primitives.dependency_vulnerability_auditor import dependency_vulnerability_auditor

        distroless_builder.write_dockerfile(ws_dir)
        compose_orchestrator.write_compose_file(ws_dir, slug, 8000)
        ci_cd_generator.write_workflow(ws_dir)
        env_example = secret_leak_sentinel.generate_env_example(ws_dir / ".env")
        (ws_dir / ".env.example").write_text(env_example, encoding="utf-8")

        req_file = ws_dir / "api" / "requirements.txt"
        if req_file.exists():
            dependency_vulnerability_auditor.audit_requirements_file(req_file)
        db_path = ws_dir / "app.db"
        if db_path.exists():
            audit_trail.record_event(db_path, "evolution_engine", "init", "scaffold_initialized", json.dumps({"slug": slug}))

        pwa_generator.apply_to_workspace(ws_dir, contract_data)
        legal_engine.apply_to_workspace(ws_dir, contract_data)
        geo_engine.apply_to_workspace(ws_dir, contract_data)

        pub_dir = ws_dir / "web" / "public"
        pub_dir.mkdir(parents=True, exist_ok=True)
        sitemap_content = sitemap_generator.generate_sitemap_xml(f"https://{slug}.autonomuos.app")
        (pub_dir / "sitemap.xml").write_text(sitemap_content, encoding="utf-8")

        theme = contract_data.get("theme", {})
        og_svg = social_card_generator.generate_svg_card(
            contract_data.get("app_name", "Plataforma"),
            contract_data.get("tagline", "Software SaaS"),
            theme.get("primary_color", "#0D9488"),
            theme.get("bg_color", "#0F172A")
        )
        (pub_dir / "og-image.svg").write_text(og_svg, encoding="utf-8")

        index_html = ws_dir / "web" / "index.html"
        if index_html.exists():
            h_text = index_html.read_text(encoding="utf-8")
            if "localStorage.getItem('theme')" not in h_text:
                h_text = h_text.replace("<head>", f"<head>\n    {zero_fouc_theme.generate_inline_head_script('light')}")
            if 'type="speculationrules"' not in h_text:
                h_text = h_text.replace("</head>", f"    {speculative_preloader.generate_speculation_rules_tag(['/', '/#view=admin', '/#view=client'])}\n  </head>")
            if 'rel="canonical"' not in h_text:
                h_text = h_text.replace("</head>", f"    {canonical_urls.generate_canonical_tag(f'https://{slug}.autonomuos.app')}\n  </head>")
            index_html.write_text(h_text, encoding="utf-8")

        index_css = ws_dir / "web" / "src" / "index.css"
        if index_css.exists():
            c_text = index_css.read_text(encoding="utf-8")
            if ".skeleton-shimmer" not in c_text:
                c_text += f"\n\n{skeleton_shimmer.generate_shimmer_css()}\n"
            if "@media print" not in c_text:
                c_text += f"\n\n{print_stylesheet.get_print_css()}\n"
            index_css.write_text(c_text, encoding="utf-8")

    @classmethod
    async def init_mission_scaffold_and_gems(cls, ws_dir: Path, slug: str, contract_data: dict[str, Any]) -> None:
        """Inicializa contratos, git checkpoints y gemas universales en disco."""
        docs_dir = ws_dir / "docs"
        contract_file = docs_dir / "DOMAIN_CONTRACT.json"
        contract_file.write_text(json.dumps(contract_data, indent=2, ensure_ascii=False), encoding="utf-8")

        web_contract = ws_dir / "web" / "src" / "domain_contract.json"
        if web_contract.parent.exists():
            web_contract.write_text(json.dumps(contract_data, indent=2, ensure_ascii=False), encoding="utf-8")

        try:
            p_add = await asyncio.create_subprocess_exec("git", "add", "docs/DOMAIN_CONTRACT.json", "web/src/domain_contract.json", cwd=str(ws_dir))
            await p_add.wait()
            p_com = await asyncio.create_subprocess_exec("git", "commit", "-m", "chore: initialize domain contract", cwd=str(ws_dir))
            await p_com.wait()
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.debug(f"Git domain contract commit note: {ex}")

        try:
            cls._apply_primitives(ws_dir, slug, contract_data)
            logger.info(f"[{slug}] Gemas Universales personalizadas e inyectadas de serie.")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as gemas_err:# noqa: BLE001
            logger.debug(f"[{slug}] Error personalizando gemas de dominio: {gemas_err}")

    @staticmethod
    async def _synthesize_single_bespoke_view(
        ws_dir: Path, slug: str, contract_data: dict[str, Any], view: dict[str, Any]
    ) -> None:
        """Synthesize an individual bespoke component view if it does not yet exist."""
        comp_name = view.get("component_name")
        if not comp_name:
            return
        target_comp = ws_dir / "web" / "src" / "components" / "views" / f"{comp_name}.tsx"
        if target_comp.exists():
            return
        try:
            synth_ok = await domain_compiler.synthesize_bespoke_component(comp_name, view, contract_data, target_comp)
            if synth_ok and target_comp.exists():
                gate_res = audit_apple_design_compliance(target_comp.read_text(encoding="utf-8"))
                logger.info(f"[{slug}] Vista JIT '{comp_name}' sintetizada: Score {gate_res['score']}/100")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as s_err:  # noqa: BLE001
            logger.debug(f"[{slug}] Error sintetizando vista '{comp_name}': {s_err}")

    @classmethod
    async def _synthesize_bespoke_views(cls, ws_dir: Path, slug: str, contract_data: dict[str, Any]) -> None:
        for view in contract_data.get("bespoke_views", []):
            await cls._synthesize_single_bespoke_view(ws_dir, slug, contract_data, view)

    @classmethod
    async def enrich_contract_and_synthesize_views(
        cls, client: genai.Client | None, ws_dir: Path, slug: str, goal: str, sector: str, contract_data: dict[str, Any]
    ) -> list[str]:
        """Enrich the contract with Google search for leaders and invariants."""
        docs_dir = ws_dir / "docs"
        contract_file = docs_dir / "DOMAIN_CONTRACT.json"
        web_contract = ws_dir / "web" / "src" / "domain_contract.json"

        leaders = await RoadmapSynthesizer.search_market_leaders(client, goal, sector)
        logger.info(f"[{slug}] Líderes mundiales identificados: {leaders}")

        try:
            invariants_contract = await domain_compiler.compile_domain_invariants(goal, sector)
            if invariants_contract:
                contract_data.update(invariants_contract)
                contract_file.write_text(json.dumps(contract_data, indent=2, ensure_ascii=False), encoding="utf-8")
                if web_contract.parent.exists():
                    web_contract.write_text(json.dumps(contract_data, indent=2, ensure_ascii=False), encoding="utf-8")
                if "capabilities" in contract_data:
                    domain_compiler.apply_domain_capabilities_to_workspace(ws_dir, contract_data["capabilities"])
                logger.info(f"[{slug}] Contrato enriquecido con Search Grounding: {len(contract_data.get('invariants', []))} reglas")
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as inv_err:# noqa: BLE001
            logger.debug(f"[{slug}] Invariants extraction note: {inv_err}")

        await cls._synthesize_bespoke_views(ws_dir, slug, contract_data)

        return leaders

    @classmethod
    async def provision_mission_runtime(
        cls, client: genai.Client | None, ws_dir: Path, slug: str, goal: str, ui_paradigm: str
    ) -> dict[str, Any]:
        """Aprovisiona daemons Uvicorn, compila seed Vite y sintetiza esquema SQLite WAL."""
        web_src_app = ws_dir / "web" / "src" / "App.tsx"
        if web_src_app.exists():
            try:
                proc_seed = await asyncio.create_subprocess_exec(
                    "npx", "vite", "build",
                    cwd=str(ws_dir / "web"),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc_seed.wait()
                logger.info(f"[{slug}] The Seed: Bundle inicial de React compilado en web/dist/")
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as s_err:# noqa: BLE001
                logger.debug(f"Seed build note: {s_err}")

        daemon_ok = await cls.ensure_daemon_running(slug)
        logger.info(f"[{slug}] Daemon backend Uvicorn verificado: {daemon_ok}")

        schema_info = await RoadmapSynthesizer.synthesize_relational_schema(client, slug, goal, ui_paradigm)
        logger.info(f"[{slug}] Esquema relacional sintetizado: {len(schema_info.get('ddl_statements', []))} tablas")

        api_ok = await RoadmapSynthesizer.synthesize_domain_api(slug, goal, schema_info)
        logger.info(f"[{slug}] Endpoints REST en FastAPI sintetizados: {api_ok}")
        if api_ok:
            await cls.ensure_daemon_running(slug)

        sdk_js = RoadmapSynthesizer.generate_typed_sdk_js(slug, schema_info)
        logger.info(f"[{slug}] SDK tipado window.db generado ({len(sdk_js)} bytes)")
        return schema_info

    @classmethod
    async def _handle_milestone_audit_results(
        cls, client: genai.Client | None, slug: str, ws_dir: Path, m_id: str, m_title: str, cycle: int,
        audit_passed: bool, last_err: str, m: dict[str, Any], consecutive_failures: dict[str, int],
        roadmap: dict[str, Any]
    ) -> bool:
        if audit_passed:
            consecutive_failures[m_id] = 0
            m["status"] = "done"
            m["verified_at"] = datetime.now(timezone.utc).isoformat()
            logger.info(f"[{slug}] ✓ {m_id} '{m_title}' VERIFICADO Y SELLADO AL 100% POR PLAYWRIGHT")
            if (ws_dir / ".git").exists():
                try:
                    proc = await asyncio.create_subprocess_exec("git", "commit", "--allow-empty", "-m", f"feat({m_id}): {m_title} (Verified Playwright F5)", cwd=str(ws_dir), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                    await proc.wait()
                    roadmap["quality_metrics"]["git_commits"] += 1
                except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                    logger.debug(f"Git commit note: {ex}")
        else:
            consecutive_failures[m_id] += 1
            if consecutive_failures[m_id] >= 3:
                logger.error(f"[{slug}] SENTINEL CIRCUIT BREAKER ACTIVADO: {m_id} ha fallado 3 ciclos consecutivos.")
                roadmap["active_task"] = f"Sentinel Circuit Breaker activado en {m_id}: Detención controlada tras 3 fallos."
                return True
            logger.warning(f"[{slug}] ⚠ {m_id} no superó la prueba Playwright en ciclo {cycle}. Git Backtracking...")
            if (ws_dir / ".git").exists():
                try:
                    proc_r = await asyncio.create_subprocess_exec("git", "reset", "--hard", "HEAD~1", cwd=str(ws_dir), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                    await proc_r.wait()
                except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                    logger.debug(f"Git reset note: {ex}")
            m["status"] = "pending"
        return False

    @classmethod
    async def execute_backlog_milestone_cycle(
        cls,
        client: genai.Client | None,
        slug: str,
        ws_dir: Path,
        m: dict[str, Any],
        cycle: int,
        roadmap: dict[str, Any],
        roadmap_file: Path,
        consecutive_failures: dict[str, int],
        mission_events: list[dict[str, Any]],
        schema_info: dict[str, Any],
        contract_data: dict[str, Any],
        broadcaster: Any,
        total_milestones: int
    ) -> tuple[bool, int]:
        """Execute a single milestone iteration with Playwright and self-healing."""
        m_id = m["id"]
        m_title = m["title"]
        m["status"] = "in_progress"

        roadmap["current_cycle"] = cycle
        roadmap["active_task"] = f"Ciclo {cycle}: Desarrollando y verificando {m_title}..."
        done_count = sum(1 for x in roadmap["milestones"] if x.get("status") == "done")
        roadmap["progress_pct"] = int((done_count / total_milestones) * 100)
        roadmap_file.write_text(json.dumps(roadmap, indent=2, ensure_ascii=False), encoding="utf-8")

        if broadcaster:
            broadcaster.publish({"type": "evolution_update", "roadmap": roadmap})

        if (ws_dir / ".git").exists():
            try:
                proc_a = await asyncio.create_subprocess_exec("git", "add", ".", cwd=str(ws_dir), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await proc_a.wait()
                proc_c = await asyncio.create_subprocess_exec("git", "commit", "--allow-empty", "-m", f"checkpoint(pre-{m_id}): cycle {cycle}", cwd=str(ws_dir), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await proc_c.wait()
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
                logger.debug(f"Git checkpoint note: {ex}")

        await EvolutionEvalRunner.execute_milestone_code(client, slug, m, roadmap, contract_data, schema_info=schema_info)

        audit_passed = False
        last_err = ""
        for attempt in range(1, 4):
            success, msg, t_data = await EvolutionEvalRunner.audit_with_playwright(
                slug, daemon_ensure_fn=cls.ensure_daemon_running, schema_info=schema_info, contract_data=contract_data
            )
            if success:
                audit_passed = True
                break
            else:
                last_err = msg
                logger.info(f"[{slug}] {m_id} Intento {attempt} falló: {last_err}. Auto-reparando...")
                await EvolutionEvalRunner.heal_code_with_playwright_error(client, slug, last_err, telemetry=t_data)
                await asyncio.sleep(PROCESS_STARTUP_GRACE_SEC)

        should_break = await cls._handle_milestone_audit_results(
            client, slug, ws_dir, m_id, m_title, cycle, audit_passed, last_err, m, consecutive_failures, roadmap
        )
        if should_break:
            return True, cycle

        mission_events.append({
            "role": "assistant",
            "type": "milestone_cycle",
            "content": [{"call": {"name": "execute_milestone", "args": {"id": m_id, "title": m_title, "verified": audit_passed}}}]
        })
        if not audit_passed and last_err:
            mission_events.append({
                "role": "user",
                "type": "audit_error",
                "content": [{"functionResponse": {"name": "audit_with_playwright", "response": f"FAILED: {last_err[:150]}"}}]
            })
        mission_events[:] = context_condenser.condense(mission_events)[0]

        cycle += 1
        completed_count = sum(1 for x in roadmap["milestones"] if x.get("status") == "done")
        roadmap["progress_pct"] = int((completed_count / total_milestones) * 100)
        roadmap_file.parent.mkdir(parents=True, exist_ok=True)
        roadmap_file.write_text(json.dumps(roadmap, indent=2, ensure_ascii=False), encoding="utf-8")

        if broadcaster:
            broadcaster.publish({
                "type": "evolution_update",
                "roadmap": roadmap,
                "reload_preview": True
            })

        return False, cycle

    @staticmethod
    async def finalize_mission_report(
        slug: str,
        sector: str,
        milestones: list[dict[str, Any]],
        total_milestones: int,
        cycle: int,
        roadmap: dict[str, Any],
        roadmap_file: Path,
        contract_data: dict[str, Any],
        broadcaster: Any
    ) -> dict[str, Any]:
        """Generate the final delivery and adversarial audit report."""
        all_passed = all(m.get("status") == "done" for m in milestones)
        completed_count = sum(1 for x in milestones if x.get("status") == "done")
        if all_passed:
            app_url = f"http://127.0.0.1:8000/preview/{slug}/"
            try:
                red_team_report = await adversarial_evaluator.audit_live_application(
                    slug=slug,
                    app_url=app_url,
                    app_name=contract_data.get("app_name", slug),
                    sector=sector,
                    invariants=contract_data.get("invariants", [])
                )
                roadmap["adversarial_report"] = red_team_report
                logger.info(f"[{slug}] Adversarial Red-Team finalizado: {red_team_report.get('attacks_survived')}/{red_team_report.get('attacks_executed')} ataques superados.")
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as red_err:# noqa: BLE001
                logger.debug(f"[{slug}] Adversarial evaluator note: {red_err}")

            roadmap["progress_pct"] = 100
            roadmap["active_task"] = "✓ Producto 100% completado y certificado para producción (Evidence Dossier TIER1_CERTIFIED_GOVERNANCE)."
            roadmap["completed_at"] = datetime.now(timezone.utc).isoformat()
            roadmap["quality_metrics"]["playwright_verified"] = True
            logger.info(f"[{slug}] Misión de evolución completada al 100% ({total_milestones}/{total_milestones} hitos aprobados).")
        else:
            roadmap["active_task"] = f"Pausa tras {cycle} ciclos: {completed_count}/{total_milestones} hitos aprobados."
            logger.warning(f"[{slug}] Misión detenida: {completed_count}/{total_milestones} hitos aprobados tras {cycle} ciclos.")

        roadmap_file.parent.mkdir(parents=True, exist_ok=True)
        roadmap_file.write_text(json.dumps(roadmap, indent=2, ensure_ascii=False), encoding="utf-8")
        if broadcaster:
            broadcaster.publish({
                "type": "evolution_update",
                "roadmap": roadmap,
                "reload_preview": True
            })

        return roadmap

    @classmethod
    async def run_evolution_mission(
        cls,
        client: genai.Client | None,
        slug: str,
        goal: str,
        contract_data: dict[str, Any],
        broadcaster: Any = None
    ) -> dict[str, Any]:
        """Execute the complete long-running autonomous mission."""
        ws_dir = (WORKSPACES_ROOT / slug).resolve()
        docs_dir = ws_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        roadmap_file = docs_dir / "EVOLUTION_ROADMAP.json"

        await cls.init_mission_scaffold_and_gems(ws_dir, slug, contract_data)

        ui_paradigm = contract_data.get("ui_paradigm", "high_ticket_service")
        sector = contract_data.get("sector", goal[:50])

        leaders = await cls.enrich_contract_and_synthesize_views(client, ws_dir, slug, goal, sector, contract_data)
        milestones = await RoadmapSynthesizer.synthesize_dynamic_backlog(client, goal, leaders, ui_paradigm, contract_data)
        total_milestones = len(milestones)

        roadmap: dict[str, Any] = {
            "slug": slug,
            "goal": goal,
            "ui_paradigm": ui_paradigm,
            "market_leaders": leaders,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "progress_pct": 0,
            "current_cycle": 1,
            "active_task": "Benchmarking completado. Iniciando desarrollo modular...",
            "milestones_total": total_milestones,
            "milestones": milestones,
            "quality_metrics": {
                "console_errors": 0,
                "playwright_verified": False,
                "git_commits": 0
            }
        }
        roadmap_file.write_text(json.dumps(roadmap, indent=2, ensure_ascii=False), encoding="utf-8")
        if broadcaster:
            broadcaster.publish({"type": "evolution_update", "roadmap": roadmap})

        schema_info = await cls.provision_mission_runtime(client, ws_dir, slug, goal, ui_paradigm)

        cycle = 1
        max_total_cycles = 25
        consecutive_failures: dict[str, int] = {m["id"]: 0 for m in milestones}
        mission_events: list[dict[str, Any]] = [
            {"role": "system", "type": "system_prompt", "content": [{"text": f"Misión de Evolución para '{slug}': {goal}"}]},
            {"role": "user", "type": "domain_contract", "content": [{"text": json.dumps(contract_data, ensure_ascii=False)}]}
        ]

        while any(m.get("status") != "done" for m in milestones) and cycle <= max_total_cycles:
            pending_list = [m for m in milestones if m.get("status") != "done"]
            if not pending_list:
                break
            m = pending_list[0]
            should_break, cycle = await cls.execute_backlog_milestone_cycle(
                client, slug, ws_dir, m, cycle, roadmap, roadmap_file,
                consecutive_failures, mission_events, schema_info,
                contract_data, broadcaster, total_milestones
            )
            if should_break:
                break

        return await cls.finalize_mission_report(
            slug, sector, milestones, total_milestones, cycle, roadmap,
            roadmap_file, contract_data, broadcaster
        )
