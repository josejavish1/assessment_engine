"""
Implement the 9-step neuro-symbolic deliberation pipeline.
Execute engineering deliberative reasoning (System 2 / Test-Time Compute) by chaining 9 strict gates where the output of each step constrains the next: 0. Symbolic Anchor & Blast Radius (Deterministic tool: RepoMap + AST) 1. Teleological Boundary (Cognitive: Strict boundary UI vs API vs DB) 2. Epistemic Grounding (Domain mining: Invariants and market leaders) 3. Skeptic Red Team Probe (Hostile auditor: Hidden pitfall probe) 4. Pragmatic Reuse Audit (Deterministic tool: package.json and @/components/ui) 5. Situational Context Gauge (Governance policy: Zero new deps, McCabe V(G) <= 10) 6. Asymmetric Synthesis (Pareto) (Cognitive: Zero-cost CSS/algorithmic engineering tricks) 7. Topological DAG Partitioning (Topological sorting: Types -> API -> UI -> Shell) 8. TDD Oracle Specification (Formal verification contracts in sandbox)
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

from pydantic import BaseModel, Field

from assessment_engine.infrastructure.genai_client import create_genai_client
from .socratic_catalog import get_domain_fallback_data
from .socratic_models import (
    AsymmetricSynthesis,
    ModuleExecutionStep,
    PragmaticReuseAudit,
    SituationalContextGauge,
    SkepticProbeReport,
    SocraticDeliberationReport,
    SotaEpistemicGrounding,
    SymbolicAnchorReport,
    TddOracleSpecification,
    TeleologicalBoundary,
    TopologicalDagPlan,
)

logger = logging.getLogger("assessment_engine.infrastructure.evolution.socratic_deliberator")



class SocraticDeliberator:
    """
    Orquestador de Deliberación Neuro-Simbólica en 9 Pasos.
    Ejecuta el protocolo socrático formal donde cada paso es la premisa del siguiente.
    """

    def __init__(self, repo_root: Path | None = None, client: Any | None = "DEFAULT") -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        if client == "DEFAULT":
            try:
                self.client = create_genai_client()
            except (RuntimeError, ValueError, KeyError, OSError, TypeError):
                self.client = None
        else:
            self.client = client

    def _call_llm_json(self, prompt: str, schema_cls: type[BaseModel]) -> Optional[BaseModel]:
        """Call the LLM requesting Pydantic-validated JSON format with guardrails."""
        if not self.client:
            return None

        from google.genai import types
        model_name = get_model(ModelTier.REASONING)
        
        system_instruction = (
            "Eres un Principal Software Architect de Google/Anthropic. "
            "Responde con absoluta precisión técnica en formato JSON estricto cumpliendo el schema solicitado. "
            "Cero texto conversacional, sin relleno ni preámbulos."
        )

        try:
            config = types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=system_instruction,
                response_mime_type="application/json",
            )
            resp = self.client.models.generate_content(
                model=model_name,
                contents=f"{prompt}\n\nEsquema JSON requerido:\n{json.dumps(schema_cls.model_json_schema())}",
                config=config,
            )
            raw_text = resp.text if hasattr(resp, "text") else str(resp)
            # Limpiar bloques markdown si vinieran
            clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
            data = json.loads(clean_json)
            return schema_cls.model_validate(data)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.warning(f"[SocraticDeliberator] Fallo en llamada LLM JSON: {ex}")
            return None

    def _extract_task_slugs(self, task: str) -> tuple[str, str]:
        """Extract the API slug (snake_case) and component name (PascalCase) dynamically from any task."""
        pascal_matches = re.findall(r"\b[A-Z][a-zA-Z0-9]+(?:Dashboard|Stage|Matrix|Drawer|Viewer|Configurator|Tree|Canvas|Grid|View|Modal|Hub|Feed)\b", task)
        if pascal_matches:
            comp_name = pascal_matches[0]
            s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", comp_name)
            slug = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
            slug = slug.replace("_view", "").replace("_component", "").replace("_stage", "").replace("_dashboard", "").replace("_matrix", "").replace("_drawer", "").replace("_viewer", "").replace("_tree", "").replace("_canvas", "").replace("_configurator", "").replace("_grid", "").replace("_feed", "")
            parts = [p for p in slug.split("_") if p not in {"dynamic", "visual", "hierarchical", "interactive", "collaborative"}]
            slug = "_".join(parts) if parts else slug
        else:
            words = [w.lower() for w in re.findall(r"[a-zA-Z0-9]+", task) if len(w) > 3 and w.lower() not in {"implementar", "primitiva", "crear", "modulo", "para", "desde", "con"}]
            slug = words[0] if words else "feature"
            comp_name = "".join(w.capitalize() for w in words[:3]) or "FeatureComponent"

        return slug, comp_name

    def _get_domain_fallback(self, slug: str) -> dict[str, Any]:
        """Generate domain-specific invariants, pitfalls, and Pareto solutions by delegating to the catalog."""
        return get_domain_fallback_data(slug)

    def step_0_symbolic_anchor(self, task: str, target_hint: str | None = None) -> SymbolicAnchorReport:
        """Map existing symbols, SQLite tables, and routes to prevent hallucinations."""
        tables: list[str] = []
        db_path = self.repo_root / "templates" / "golden_polyglot_starter" / "api" / "src" / "database.py"
        if db_path.exists():
            content = db_path.read_text(encoding="utf-8", errors="ignore")
            tables = re.findall(r"class\s+([A-Za-z0-9_]+)\s*\(\s*Base\s*\)", content)

        routers: list[str] = []
        routers_dir = self.repo_root / "templates" / "golden_polyglot_starter" / "api" / "src" / "routers"
        if routers_dir.exists():
            routers = [f.stem for f in routers_dir.glob("*.py") if f.is_file()]

        slug, comp_name = self._extract_task_slugs(task)
        candidate_targets = [
            f"templates/golden_polyglot_starter/api/src/routers/{slug}_routes.py",
            "templates/golden_polyglot_starter/api/src/main.py",
            "templates/golden_polyglot_starter/web/src/domain_contract.json",
            f"templates/golden_polyglot_starter/web/src/components/primitives/{comp_name}.tsx",
            "templates/golden_polyglot_starter/web/src/App.tsx",
        ]
        if target_hint and target_hint not in candidate_targets:
            candidate_targets.append(target_hint)

        primitives_dir = self.repo_root / "core" / "primitives"
        primitive_symbols: list[str] = []
        if primitives_dir.exists():
            primitive_symbols = [f.stem for f in primitives_dir.glob("*.py") if not f.name.startswith("__")]

        return SymbolicAnchorReport(
            existing_symbols=primitive_symbols or ["pricing_rules", "geo_engine", "zero_cookie_analytics", "openmetrics_exporter"],
            existing_tables=tables or ["domain_records", "users", "appointments", "privacy_analytics_views"],
            existing_routers=routers or ["auth_routes", "billing_routes", "directory_routes"],
            candidate_targets=candidate_targets,
        )

    def step_1_teleological_boundary(
        self,
        task: str,
        anchor: SymbolicAnchorReport,
        force_fallback: bool = False,
    ) -> TeleologicalBoundary:
        """Strictly define layer responsibilities and forbidden operations."""
        if not force_fallback and self.client:
            prompt = (
                f"TAREA: '{task}'\n"
                f"SÍMBOLOS EXISTENTES: {anchor.existing_symbols}\n"
                f"ROUTERS EXISTENTES: {anchor.existing_routers}\n"
                f"Define las fronteras de arquitectura separando estrictamente UI, API y Base de Datos. "
                f"Prohíbe terminantemente mezclar capas (ej. renderizar SVG en Python o consultar SQL en React)."
            )
            res = self._call_llm_json(prompt, TeleologicalBoundary)
            if isinstance(res, TeleologicalBoundary):
                return res

        # Fallback Determinista Robusto
        return TeleologicalBoundary(
            domain_scope="Fullstack Decoupled (FastAPI Router + React Component)",
            ui_responsibilities=[
                "Renderizado visual interactivo a 60 FPS en React",
                "Formateo y presentación de datos agregados",
                "Manejo de eventos táctiles y de puntero en cliente",
            ],
            api_responsibilities=[
                "Exposición de endpoints REST seguros en /api/",
                "Agregación y cálculo determinista de métricas sobre SQLite WAL",
                "Emisión de respuestas JSON serializadas y tipadas",
            ],
            database_responsibilities=[
                "Consultas SELECT de solo lectura sobre tablas existentes sin alterar esquemas",
            ],
            strictly_forbidden_actions=[
                "Prohibido generar o embeber strings de SVG/HTML dentro del backend Python",
                "Prohibido consultar SQLite directamente desde componentes del frontend",
                "Prohibido mutar o renombrar tablas maestras existentes sin migración formal",
            ],
        )

    def step_2_sota_epistemic_grounding(
        self,
        task: str,
        boundary: TeleologicalBoundary,
        sector: str,
        force_fallback: bool = False,
    ) -> SotaEpistemicGrounding:
        """Identify reference implementations and mandatory invariants for the problem."""
        if not force_fallback and self.client:
            prompt = (
                f"TAREA: '{task}' en Sector '{sector}'\n"
                f"FRONTERA: {boundary.domain_scope}\n"
                f"Extrae los 3 líderes mundiales Tier-1 en esta funcionalidad (ej. Plausible, Stripe, Vercel). "
                f"Identifica los invariantes obligatorios de producto y las anti-features a descartar por YAGNI."
            )
            res = self._call_llm_json(prompt, SotaEpistemicGrounding)
            if isinstance(res, SotaEpistemicGrounding):
                return res

        # Universal Dynamic Deterministic Fallback
        slug, _ = self._extract_task_slugs(task)
        df = self._get_domain_fallback(slug)
        return SotaEpistemicGrounding(
            industry_benchmarks=df["benchmarks"],
            must_have_invariants=df["invariants"],
            unfair_advantages=[
                f"Coste de infraestructura $0.00 usando SQLite WAL local para {slug}",
                "Cero dependencias pesadas para preservar TTI < 800ms",
            ],
            deliberate_anti_features=[
                f"Librerías monolíticas o servicios de pago en la nube para {slug}",
                "Complejidad innecesaria de microservicios o WebSockets para flujos simples",
                "Evasión de tipado con 'any' en TypeScript o Python",
            ],
        )

    def step_3_skeptic_probe(
        self,
        boundary: TeleologicalBoundary,
        sota: SotaEpistemicGrounding,
        force_fallback: bool = False,
    ) -> SkepticProbeReport:
        """Perform hostile audit to identify pitfalls of the naive approach."""
        if not force_fallback and self.client:
            prompt = (
                f"LÍDERES: {sota.industry_benchmarks}\n"
                f"INVARIANTES: {sota.must_have_invariants}\n"
                f"Actúa como un Principal Engineer Hostil. ¿Por qué una solución ingenua desde cero fracasará en producción? "
                f"Detecta trampas de hit-testing táctil, desbordamiento de tooltips, aspecto de ratio y solapamiento de fechas."
            )
            res = self._call_llm_json(prompt, SkepticProbeReport)
            if isinstance(res, SkepticProbeReport):
                return res

        # Universal Dynamic Deterministic Fallback
        domain_text = " ".join(sota.industry_benchmarks + sota.must_have_invariants)
        df = self._get_domain_fallback(domain_text)
        return SkepticProbeReport(
            hidden_traps=df["traps"],
            failure_modes=[
                "Parpadeo (jank) al interactuar en pantallas táctiles móviles",
                "Invisibilidad para lectores de pantalla (incumplimiento WCAG 2.2 AA)",
            ],
            edge_cases=[
                "Respuestas lentas o desconexión en redes 3G simuladas",
                "Datos iniciales vacíos en base de datos recién inicializada",
            ],
            must_address_flaws=[
                "Debe implementar mitigaciones robustas para el dominio sin librerías externas",
            ],
        )

    def step_4_reuse_audit(self) -> PragmaticReuseAudit:
        """Inspect existing project libraries and components on disk."""
        packages: list[str] = []
        pkg_file = self.repo_root / "templates" / "golden_polyglot_starter" / "web" / "package.json"
        if pkg_file.exists():
            try:
                pkg_data = json.loads(pkg_file.read_text(encoding="utf-8"))
                packages = list(pkg_data.get("dependencies", {}).keys())
            except (json.JSONDecodeError, OSError) as ex:
                logger.debug(f"[Reuse] Error leyendo package.json: {ex}")

        ui_components: list[str] = []
        ui_dir = self.repo_root / "templates" / "golden_polyglot_starter" / "web" / "src" / "components" / "ui"
        if ui_dir.exists():
            ui_components = [f.name for f in ui_dir.glob("*.tsx")]

        primitives_dir = self.repo_root / "core" / "primitives"
        backend_primitives: list[str] = []
        if primitives_dir.exists():
            backend_primitives = [f.name for f in primitives_dir.glob("*.py") if not f.name.startswith("__")]

        return PragmaticReuseAudit(
            installed_frontend_packages=packages or ["react", "lucide-react", "clsx", "tailwind-merge"],
            existing_ui_components=ui_components or ["card.tsx", "badge.tsx", "button.tsx", "input.tsx"],
            reusable_backend_primitives=backend_primitives or ["pricing_rules.py", "geo_engine.py", "zero_cookie_analytics.py"],
        )

    def step_5_situational_gauge(self, reuse: PragmaticReuseAudit) -> SituationalContextGauge:
        """Apply immutable repository governance policy."""
        return SituationalContextGauge(
            zero_new_dependency_mandate=True,
            max_cyclomatic_complexity=10,
            max_nesting_depth=3,
            hard_constraints=[
                "Prohibido añadir paquetes npm a package.json (infraestructura congelada)",
                "Prohibido el uso de ': any' o casts 'as any' en TypeScript",
                "Toda función debe mantener V(G) <= 10 y CoC <= 15",
                "El tiempo de compilación 'npm run build' debe ser inferior a 1.5 segundos",
            ],
        )

    def step_6_asymmetric_synthesis(
        self,
        skeptic: SkepticProbeReport,
        gauge: SituationalContextGauge,
        reuse: PragmaticReuseAudit,
        force_fallback: bool = False,
    ) -> AsymmetricSynthesis:
        """Design technical engineering patterns that yield zero-cost benefits."""
        if not force_fallback and self.client:
            prompt = (
                f"TRAMPAS A RESOLVER: {skeptic.hidden_traps}\n"
                f"RESTRICCIONES: {gauge.hard_constraints}\n"
                f"RECURSOS DISPONIBLES: {reuse.installed_frontend_packages}, {reuse.existing_ui_components}\n"
                f"Diseña las soluciones asimétricas de ingeniería para neutralizar cada trampa sin instalar librerías. "
                f"Especifica la regla del cuadrante CSS, ejes HTML fijos y proyección paramétrica."
            )
            res = self._call_llm_json(prompt, AsymmetricSynthesis)
            if isinstance(res, AsymmetricSynthesis):
                return res

        # Universal Dynamic Deterministic Fallback
        domain_text = " ".join(skeptic.hidden_traps)
        df = self._get_domain_fallback(domain_text)
        return AsymmetricSynthesis(
            pareto_solutions=df["pareto"],
            technical_tradeoffs_resolved=[
                "Cero dependencias externas manteniendo interactividad nativa idéntica a líderes Tier-1",
                "Accesibilidad completa incorporando atributos WAI-ARIA para lectores de pantalla",
            ],
            mitigations_for_hidden_traps=[
                "Diseño defensivo con fallbacks visuales elegantes ante ausencia de datos",
                "Contención estricta en layout sin causar desbordamientos en viewport",
            ],
        )

    def step_7_topological_dag(
        self,
        task: str,
        boundary: TeleologicalBoundary,
        pareto: AsymmetricSynthesis,
        anchor: SymbolicAnchorReport,
        force_fallback: bool = False,
    ) -> TopologicalDagPlan:
        """Determine the strict topological build sequence: API -> Mount -> Contract -> UI -> Shell."""
        if not force_fallback and self.client:
            prompt = (
                f"TAREA: '{task}'\n"
                f"ALCANCE: {boundary.domain_scope}\n"
                f"SOLUCIONES PARETO: {pareto.pareto_solutions}\n"
                f"CANDIDATOS LOCALES: {anchor.candidate_targets}\n\n"
                "Diseña el TopologicalDagPlan ordenando exactamente 5 capas sin ciclos:\n"
                "1. layer='backend_api': El nuevo router FastAPI (templates/golden_polyglot_starter/api/src/routers/<slug>_routes.py). "
                "REGLA DE SIMETRÍA HEADLESS: Si la capacidad involucra documentos, exportaciones, facturas o reportes, "
                "el router debe exponer endpoints desatendidos para descarga/stream binario ('GET /{id}/download' o 'GET /{id}/pdf' con StreamingResponse/FileResponse).\n"
                "2. layer='backend_mount': El montaje en templates/golden_polyglot_starter/api/src/main.py (app.include_router)\n"
                "3. layer='contract_declaration': La vista en templates/golden_polyglot_starter/web/src/domain_contract.json (workspace_views)\n"
                "4. layer='frontend_ui': El componente React (templates/golden_polyglot_starter/web/src/components/primitives/<Comp>.tsx)\n"
                "5. layer='shell_integration': El despacho en templates/golden_polyglot_starter/web/src/App.tsx (renderWorkspaceContent y hash)\n"
                "Asegura que las dependencias reflejen este orden secuencial estricto."
            )
            res = self._call_llm_json(prompt, TopologicalDagPlan)
            if isinstance(res, TopologicalDagPlan) and len(res.ordered_steps) >= 4:
                return res

        # Universal Dynamic Deterministic Fallback
        slug, comp_name = self._extract_task_slugs(task)
        steps = [
            ModuleExecutionStep(
                id=f"MOD_API_{slug.upper()}",
                name=f"Endpoint y Router de {slug.capitalize()} en FastAPI",
                target_file=f"templates/golden_polyglot_starter/api/src/routers/{slug}_routes.py",
                test_file=f"templates/golden_polyglot_starter/api/tests/test_{slug}_api.py",
                layer="backend_api",
                purpose=f"Expone endpoints REST y lógica de negocio en /api/{slug}/ sobre SQLite WAL",
                invariants=[
                    "Retornar respuestas serializadas y tipadas con Pydantic",
                    "Complejidad ciclomática V(G) <= 10",
                    "Cero dependencias externas no autorizadas",
                ],
                dependencies=[],
            ),
            ModuleExecutionStep(
                id=f"MOD_API_{slug.upper()}_MOUNT",
                name=f"Montaje del Router de {slug.capitalize()} en el Servidor FastAPI Principal",
                target_file="templates/golden_polyglot_starter/api/src/main.py",
                test_file="tests/test_starter_decoupled_routers_integration.py",
                layer="backend_mount",
                purpose=f"Importa {slug}_router y lo monta en app.include_router() usando el marcador de anclaje",
                invariants=[
                    f"Registrar app.include_router({slug}_router)",
                    "No alterar los routers ni endpoints preexistentes",
                ],
                dependencies=[f"MOD_API_{slug.upper()}"],
            ),
            ModuleExecutionStep(
                id=f"MOD_CONTRACT_{slug.upper()}",
                name=f"Declaración de la Vista {slug.capitalize()} en el Contrato de Dominio",
                target_file="templates/golden_polyglot_starter/web/src/domain_contract.json",
                test_file="tests/test_domain_compiler.py",
                layer="contract_declaration",
                purpose=f"Declara formalmente la vista '{slug}' en workspace_views de domain_contract.json para exponerla en /api/config",
                invariants=[
                    f"Añadir vista con id='{slug}', name='{comp_name}', component_name='{comp_name}'",
                    "Preservar todas las vistas y campos preexistentes de domain_contract.json",
                    "Emitir JSON sintácticamente válido conforme a RFC 8259",
                ],
                dependencies=[f"MOD_API_{slug.upper()}_MOUNT"],
            ),
            ModuleExecutionStep(
                id=f"MOD_UI_{comp_name.upper()}",
                name=f"Componente React {comp_name} con Primitivas Nativas",
                target_file=f"templates/golden_polyglot_starter/web/src/components/primitives/{comp_name}.tsx",
                test_file=f"templates/golden_polyglot_starter/web/src/components/primitives/{comp_name}.test.tsx",
                layer="frontend_ui",
                purpose=f"Renderiza la interfaz de usuario interactiva para {task}",
                invariants=[
                    "Implementar soluciones asimétricas de Pareto sin dependencias pesadas",
                    "Tipado estricto en TypeScript sin uso de any",
                    "Exportar tanto export { Component } como export default Component",
                ],
                dependencies=[f"MOD_CONTRACT_{slug.upper()}"],
            ),
            ModuleExecutionStep(
                id=f"MOD_SHELL_{slug.upper()}_INTEGRATION",
                name=f"Enlace de la Vista {slug.capitalize()} en el Shell Universal de App.tsx",
                target_file="templates/golden_polyglot_starter/web/src/App.tsx",
                test_file="tests/test_portal_contract_and_universal_client.py",
                layer="shell_integration",
                purpose=f"Registra la vista en el switch de pestañas en App.tsx usando marcadores de anclaje",
                invariants=[
                    "Permitir acceso a roles declarados",
                    "Compilación limpia en npm run build",
                ],
                dependencies=[f"MOD_UI_{comp_name.upper()}"],
            ),
        ]

        return TopologicalDagPlan(
            ordered_steps=steps,
            dag_rationale=f"Secuencia topológica estricta para {task}: API -> Mount -> Contract -> UI -> Shell.",
        )

    def step_8_tdd_oracles(self, dag: TopologicalDagPlan) -> TddOracleSpecification:
        """Specify essential concrete tests to certify non-regression."""
        api_step = next((s for s in dag.ordered_steps if s.layer == "backend_api"), None)
        ui_step = next((s for s in dag.ordered_steps if s.layer == "frontend_ui"), None)

        unit_tests = [api_step.test_file] if api_step else []
        comp_commands = ["cd templates/golden_polyglot_starter/web && npx tsc -b"]
        if api_step:
            comp_commands.insert(0, f"python -m py_compile {api_step.target_file}")

        return TddOracleSpecification(
            unit_test_targets=unit_tests,
            compilation_commands=comp_commands,
            required_assertions=[
                "assert response.status_code == 200 en endpoint principal",
                "Verificación limpia de tipos sin 'any' en TypeScript",
                "Compilación limpia con Exit Code 0 en Vite y Python",
            ],
        )

    # MAIN METHOD: SEQUENTIAL EXECUTION OF THE 9 STEPS
    def deliberate(
        self,
        task: str,
        target_hint: str | None = None,
        sector: str = "Analytics & Telemetry",
        force_fallback: bool = False,
    ) -> SocraticDeliberationReport:
        """Execute the sequential 9-step pipeline ensuring strict chaining."""
        logger.info(f"[SocraticDeliberator] === INICIANDO DELIBERACIÓN SOCRÁTICA EN 9 PASOS: '{task}' ===")

        step_0 = self.step_0_symbolic_anchor(task=task, target_hint=target_hint)
        logger.info(f"[Paso 0/8] Símbolos anclados: {len(step_0.existing_symbols)} | Tablas: {len(step_0.existing_tables)}")

        step_1 = self.step_1_teleological_boundary(task=task, anchor=step_0, force_fallback=force_fallback)
        logger.info(f"[Paso 1/8] Frontera: {step_1.domain_scope}")

        step_2 = self.step_2_sota_epistemic_grounding(task=task, boundary=step_1, sector=sector, force_fallback=force_fallback)
        logger.info(f"[Paso 2/8] Líderes: {step_2.industry_benchmarks} | Invariantes: {len(step_2.must_have_invariants)}")

        step_3 = self.step_3_skeptic_probe(boundary=step_1, sota=step_2, force_fallback=force_fallback)
        logger.info(f"[Paso 3/8] Trampas identificadas: {len(step_3.hidden_traps)}")

        step_4 = self.step_4_reuse_audit()
        logger.info(f"[Paso 4/8] Paquetes frontend: {len(step_4.installed_frontend_packages)} | UI: {len(step_4.existing_ui_components)}")

        step_5 = self.step_5_situational_gauge(reuse=step_4)
        logger.info(f"[Paso 5/8] Restricciones de gobernanza: {len(step_5.hard_constraints)}")

        step_6 = self.step_6_asymmetric_synthesis(skeptic=step_3, gauge=step_5, reuse=step_4, force_fallback=force_fallback)
        logger.info(f"[Paso 6/8] Soluciones Pareto diseñadas: {len(step_6.pareto_solutions)}")

        step_7 = self.step_7_topological_dag(task=task, boundary=step_1, pareto=step_6, anchor=step_0, force_fallback=force_fallback)
        logger.info(f"[Paso 7/8] Módulos ordenados topológicamente: {len(step_7.ordered_steps)}")

        step_8 = self.step_8_tdd_oracles(dag=step_7)
        logger.info(f"[Paso 8/8] Oráculos de verificación formal especificados: {len(step_8.compilation_commands)}")

        return SocraticDeliberationReport(
            task=task,
            sector=sector,
            step_0=step_0,
            step_1=step_1,
            step_2=step_2,
            step_3=step_3,
            step_4=step_4,
            step_5=step_5,
            step_6=step_6,
            step_7=step_7,
            step_8=step_8,
        )


socratic_deliberator = SocraticDeliberator()
