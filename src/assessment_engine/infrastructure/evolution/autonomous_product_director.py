"""
Autonomous Product Director — Meta-Cognitive Architecture Engine (SOTA 2026).
Orchestrates the E2E lifecycle of an autonomous feature development.
Governs the 5-phase FSM, prescriptive refactoring engine, and prevents infinite loops via cryptographic ledger.
"""
from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import re
import sys
import time
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.evolution.ast_signature_guard import (
    AstSignatureGuard,
    ast_signature_guard,
)
from assessment_engine.infrastructure.genai_client import ModelTier, get_model
from assessment_engine.infrastructure.evolution.epistemic_distiller import (
    EpistemicDistiller,
    ProductStrategyDossier,
    epistemic_distiller,
)
from assessment_engine.infrastructure.evolution.sota_sourcer import (
    CleanRoomFile,
    CleanRoomPayload,
    EphemeralRepo,
    SotaIntelligenceReport,
    SotaSourcer,
    sota_sourcer,
)
from assessment_engine.infrastructure.evolution.worktree_runner import (
    GitWorktreeRunner,
    worktree_runner,
)
from assessment_engine.infrastructure.evolution.orthogonal_gates import (
    OrthogonalGatesEvaluator,
    orthogonal_gates,
)
from assessment_engine.infrastructure.evolution.reflexion_ledger import (
    ReflexionLedger,
    reflexion_ledger,
)
from assessment_engine.infrastructure.genai_client import create_genai_client
from assessment_engine.infrastructure.primitives.may_impact_planner import (
    ImpactAnalysisResult,
    MayImpactPlannerPrimitive,
    may_impact_planner,
)
from assessment_engine.infrastructure.primitives.repomap import (
    RepoMapPrimitive,
    repomap,
)

from .director_models import (
    FOWLER_RECIPE_BOOK,
    LOCAL_CAPABILITIES,
    LocalBoundaryScope,
    LocalCapability,
    MissionReport,
    ModulePlan,
    PrescriptiveRecipe,
    ProductGap,
)
from .director_consolidator import consolidate_code_map_to_disk
from .director_comparator import (
    evaluate_orthogonal_gaps,
    run_cognitive_red_team_audit,
    run_heuristic_invariants_fallback,
)
from .director_planner import plan_and_apply_yagni
from .director_synthesizer import (
    apply_search_replace_blocks,
    build_synthesis_prompt,
    find_relevant_primitives_skeletons,
    generate_and_parse_candidate,
    strip_markdown_fences,
    synthesize_file_best_of_n,
)
from .director_refactor import FunctionNodeReplacer, PrescriptiveRefactoringEngine
from .product_ledger import ProductLedger

logger = logging.getLogger("assessment_engine.infrastructure.evolution.autonomous_product_director")


def _score_candidate_file(f: str, rel_p: str, clean_words: list[str]) -> int:
    """Score candidate source file against clean task keywords."""
    score = sum(2 for kw in clean_words if kw in f.lower()) + sum(1 for kw in clean_words if kw in rel_p.lower())
    if rel_p.startswith(("templates/", "core/", "routers/")):
        score += 5
    elif rel_p.startswith("workspaces/"):
        score -= 2
    return score


class AutonomousProductDirector:
    """Govern the five-phase pipeline to complete complex software tasks with integrated prescriptive auditing."""

    DEFAULT_INVARIANTS: tuple[str, ...] = (
        "Coste de infraestructura recurrente $0.00.",
        "Persistencia transaccional ACID en SQLite modo WAL.",
        "Tipado estricto sin casts 'any' en TypeScript y Python.",
        "Cero dependencias pesadas de SaaS o microservicios externos.",
        "Complejidad ciclomática McCabe V(G) <= 10 por función.",
    )

    def __init__(
        self,
        repo_root: Path | None = None,
        repomap_primitive: RepoMapPrimitive | None = None,
        impact_planner: MayImpactPlannerPrimitive | None = None,
        distiller: EpistemicDistiller | None = None,
        sota_sourcer_engine: SotaSourcer | None = None,
        refactoring_engine: PrescriptiveRefactoringEngine | None = None,
        client: Any | None = "DEFAULT",
        max_iterations: int = 3,
    ) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.repomap = repomap_primitive or repomap
        self.impact_planner = impact_planner or may_impact_planner
        self.distiller = distiller or epistemic_distiller
        self.sota_sourcer = sota_sourcer_engine or sota_sourcer
        self.refactoring_engine = refactoring_engine or PrescriptiveRefactoringEngine()

        if client == "DEFAULT":
            try:
                self.client = create_genai_client()
            except (RuntimeError, ValueError, KeyError, OSError, TypeError):
                self.client = None
        else:
            self.client = client

        self.ledger = ProductLedger(max_iterations=max_iterations)
        self.worktree = worktree_runner
        self.gates = orthogonal_gates
        self.reflexion = reflexion_ledger
        self._baseline_code_map: dict[str, str] = {}
        self._current_mission_cache: Any | None = None

    def _generate_content_with_retry(
        self, prompt: str, stream: bool = False, cache_name: Any | None = None
    ) -> Any:
        """Invoke Gemini with retries and exponential backoff error handling."""
        if not self.client:
            return None
        attempts = 3
        delay = 2.0
        for i in range(attempts):
            try:
                if stream:
                    return self.client.models.generate_content_stream(
                        model=get_model(ModelTier.REASONING),
                        contents=prompt,
                    )
                return self.client.models.generate_content(
                    model=get_model(ModelTier.REASONING),
                    contents=prompt,
                )
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.warning(f"[APD-LLM] Error en intento {i+1}/{attempts}: {ex}")
                time.sleep(delay)
                delay *= 2.0
        return None

    def step_0_local_boundary(
        self, task: str, target_hint: str | None = None
    ) -> LocalBoundaryScope:
        """STEP 0: Extract boundaries and local impact via RepoMap and May-Impact DAG."""
        logger.info(f"[APD-Paso0] Mapeando contorno local para tarea: '{task[:60]}'...")
        try:
            symbol_map = self.repomap.build_symbol_map(self.repo_root, max_tokens=1024)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.warning(f"[APD-Paso0] Error al construir RepoMap: {ex}")
            symbol_map = "# RepoMap fallback: Repositorio en raíz"

        effective_target = target_hint or self._auto_localize_target_file(task)
        impacted_files: list[str] = []
        topological_order: list[str] = []
        baseline_code: str | None = None

        if effective_target and (self.repo_root / effective_target).exists():
            try:
                target_file_path = self.repo_root / effective_target
                baseline_code = target_file_path.read_text(encoding="utf-8", errors="ignore")
                self._baseline_code_map[effective_target] = baseline_code
                logger.info(f"[APD-Paso0] Código base preexistente cargado desde '{effective_target}'.")
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.warning(f"[APD-Paso0] Error leyendo código base de '{effective_target}': {ex}")

            try:
                impact_res: ImpactAnalysisResult = self.impact_planner.analyze_impact(self.repo_root, effective_target)
                impacted_files = impact_res.impacted_files
                topological_order = impact_res.topological_order
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.warning(f"[APD-Paso0] Error en análisis de impacto: {ex}")

        return LocalBoundaryScope(
            task=task,
            symbol_map_summary=symbol_map[:1500],
            impacted_files=impacted_files,
            topological_order=topological_order,
            invariants=list(self.DEFAULT_INVARIANTS),
            baseline_code=baseline_code,
        )

    def step_1_sota_discovery(
        self,
        task: str,
        sector: str = "Fintech & Web Architecture",
        reference_repo: str | Path | None = None,
        force_fallback: bool = False,
    ) -> SotaIntelligenceReport:
        """STEP 1: Discover knowledge and mine reference implementations (Three-Cube Matrix and Clean-Room /tmp)."""
        logger.info(f"[APD-Paso1] Minando SOTA y Clean-Room Sourcing para sector '{sector}'...")
        return self.sota_sourcer.discover_and_mine(
            task=task,
            sector=sector,
            reference_repo=reference_repo,
            force_fallback=force_fallback,
        )

    def step_2_plan_and_yagni(
        self,
        task: str,
        scope: LocalBoundaryScope,
        dossier: ProductStrategyDossier | SotaIntelligenceReport,
        planned_modules: list[dict[str, Any]] | None = None,
        target_hint: str | None = None,
    ) -> list[ModulePlan]:
        """PASO 2: Desglose Modular y Filtro YAGNI (Zero-Dependency Gate sin topes artificiales)."""
        logger.info("[APD-Paso2] Desglosando arquitectura modular y aplicando Filtro YAGNI...")
        actual_dossier = dossier.dossier if isinstance(dossier, SotaIntelligenceReport) else dossier
        effective_target = target_hint or self._auto_localize_target_file(task)
        raw_modules = planned_modules or self._synthesize_default_modules(
            task, scope, dossier, target_hint=effective_target
        )

        return plan_and_apply_yagni(
            task=task,
            scope=scope,
            dossier=actual_dossier,
            raw_modules=raw_modules,
            client=self.client,
            generate_content_fn=self._generate_content_with_retry,
        )

    def _auto_localize_target_file(self, task: str) -> str | None:
        """Locate the most relevant project file for the task when target_hint is None."""
        pascal_matches = re.findall(r"\b[A-Z][a-zA-Z0-9]+(?:Dashboard|Stage|Matrix|Drawer|Viewer|Configurator|Tree|Canvas|Grid|View|Modal|Hub|Feed)\b", task)
        if pascal_matches:
            comp_name = pascal_matches[0]
            target_candidate = f"templates/golden_polyglot_starter/web/src/components/primitives/{comp_name}.tsx"
            logger.info(f"[APD-Paso0] Archivo objetivo deducido deterministamente: '{target_candidate}'")
            return target_candidate

        clean_words = [w.lower() for w in re.findall(r"[a-zA-Z0-9_\-]+", task) if len(w) > 3]
        if not clean_words:
            return None

        candidate_paths: list[tuple[str, int]] = []
        for root, dirs, files in os.walk(str(self.repo_root)):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}]
            for f in files:
                if not f.endswith((".tsx", ".ts", ".py", ".jsx", ".js")) or f.startswith("test_") or f.endswith((".spec.ts", ".test.ts")):
                    continue
                rel_p = str(Path(root, f).relative_to(self.repo_root))
                score = _score_candidate_file(f, rel_p, clean_words)
                if score > 0:
                    candidate_paths.append((rel_p, score))

        if candidate_paths:
            candidate_paths.sort(key=lambda x: x[1], reverse=True)
            best_match, best_score = candidate_paths[0]
            if best_score >= 2:
                logger.info(f"[APD-Paso0] Archivo objetivo auto-localizado: '{best_match}'")
                return best_match

        return None

    def _synthesize_default_modules(
        self,
        task: str,
        scope: LocalBoundaryScope,
        dossier: Any,
        target_hint: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate an initial proposed list of modules to evaluate through the YAGNI filter."""
        target_file = target_hint or (scope.impacted_files[0] if scope.impacted_files else "core/primitives/feature.py")
        test_file = f"tests/test_{Path(target_file).stem}.py"
        return [
            {
                "id": "mod_core_01",
                "name": f"Core {Path(target_file).stem.capitalize()}",
                "target_file": target_file,
                "test_file": test_file,
                "purpose": task,
                "invariants": scope.invariants[:3],
            }
        ]

    def _accumulate_module_capability(self, current_code: str, mod: ModulePlan) -> str:
        """Integrate an approved modular capability into the existing codebase without skipping modules."""
        if mod.target_file.endswith(".json"):
            return current_code

        is_ts_js = mod.target_file.endswith((".ts", ".tsx", ".js", ".jsx"))
        comment_prefix = "//" if is_ts_js else "#"
        header = f"\n\n{comment_prefix} --- [CAPACIDAD ACUMULADA: {mod.id}] {mod.name} ---\n"
        desc = f"{comment_prefix} Propósito: {mod.purpose}\n"
        marker = f"{comment_prefix} [CAPABILITY_MARKER_{mod.id}]\n"
        if marker in current_code:
            return current_code
        return current_code + header + desc + marker

    def _cognitive_synthesize_file(
        self,
        target_file: str,
        current_code: str,
        file_mods: list[ModulePlan],
        clean_room_payloads: list[CleanRoomPayload] | None = None,
        batch_files: dict[str, str] | None = None,
    ) -> str:
        """Invoke Gemini with the codebase and clean-room reference to synthesize production code."""
        if not self.client:
            res = current_code
            for m in file_mods:
                res = self._accumulate_module_capability(res, m)
            return res

        prompt = build_synthesis_prompt(target_file, current_code, file_mods, clean_room_payloads, self.repo_root)
        target_path_obj = self.repo_root / target_file
        is_new = not target_path_obj.exists() or current_code.strip().startswith(("// Autonomuos Module:", "# Autonomuos Module:"))

        try:
            return synthesize_file_best_of_n(
                prompt=prompt,
                target_file=target_file,
                current_code=current_code,
                is_new_file=is_new,
                repo_root=self.repo_root,
                batch_files=batch_files,
                generate_content_fn=self._generate_content_with_retry,
                apply_search_replace_fn=apply_search_replace_blocks,
                cache_name=getattr(self, "_current_mission_cache", None),
            )
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.warning(f"[APD-Paso3] Fallo en síntesis cognitiva: {ex}. Preservando código intacto.")
            return current_code

    def _cognitive_heal_gaps(
        self,
        target_file: str,
        current_code: str,
        gaps: list[ProductGap],
    ) -> str:
        """Invoke Gemini to refactor and remediate gaps identified by the Red Team."""
        if not self.client or not gaps:
            return current_code

        gap_descriptions = "\n".join(f"- [{g.id}] {g.description}" for g in gaps if g.is_yagni_approved)
        prompt = (
            f"Eres el Ingeniero Principal de Autonomuos (SOTA 2026).\n"
            f"Subgana quirúrgicamente las siguientes deficiencias en '{target_file}':\n\n"
            f"DEFICIENCIAS A SUBSANAR:\n{gap_descriptions}\n\n"
            f"CÓDIGO ACTUAL:\n```\n{current_code[:40000]}\n```\n\n"
            "INSTRUCCIONES DE CORRECCIÓN:\n"
            "1. Implementa la lógica de negocio completa sin stubs.\n"
            "2. Aplica Guard Clauses para aplanar el flujo.\n"
            "3. Conecta el frontend con la API local ('/api/...').\n"
            "4. Devuelve bloques SEARCH/REPLACE (<<<< / ==== / >>>>) o el archivo completo si es nuevo.\n"
        )
        target_path_obj = self.repo_root / target_file
        is_new = not target_path_obj.exists()

        try:
            cand_code, _ = generate_and_parse_candidate(
                prompt=prompt,
                target_file=target_file,
                current_code=current_code,
                is_new_file=is_new,
                generate_content_fn=self._generate_content_with_retry,
                apply_search_replace_fn=apply_search_replace_blocks,
                cache_name=getattr(self, "_current_mission_cache", None),
            )
            return cand_code if len(cand_code.strip()) > 30 else current_code
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.warning(f"[APD-Healer] Error subsanando GAPs: {ex}")
            return current_code

    def _synthesize_target_file_modules(
        self,
        target_file: str,
        file_mods: list[ModulePlan],
        code_map: dict[str, str],
        baseline_code: str | None,
        clean_room_payloads: list[CleanRoomPayload] | None,
        force_fallback: bool,
    ) -> None:
        """Synthesize capabilities for an individual target file."""
        current_file_code = code_map.get(target_file)
        if not current_file_code:
            t_path = self.repo_root / target_file
            if t_path.exists():
                current_file_code = t_path.read_text(encoding="utf-8")
            elif baseline_code and Path(target_file).name in target_file:
                current_file_code = baseline_code
            else:
                is_ts = target_file.endswith((".ts", ".tsx", ".js", ".jsx"))
                prefix = "//" if is_ts else "#"
                current_file_code = f"{prefix} Autonomuos Module: {target_file}\n"

        if self.client and not force_fallback:
            for m in file_mods:
                current_file_code = self._cognitive_synthesize_file(
                    target_file=target_file,
                    current_code=current_file_code,
                    file_mods=[m],
                    clean_room_payloads=clean_room_payloads,
                    batch_files=code_map,
                )
        else:
            for m in file_mods:
                current_file_code = self._accumulate_module_capability(current_file_code, m)

        code_map[target_file] = current_file_code

    def _verify_sandbox_syntax(
        self,
        code_map: dict[str, str],
        sandbox: Any,
        gaps_to_fix: list[ProductGap] | None,
        force_fallback: bool,
    ) -> None:
        """Verify syntax integrity in worktree sandbox and heal detected gaps."""
        preflight_gaps: list[ProductGap] = []
        for target_file, code_content in list(code_map.items()):
            if sandbox:
                sandboxed_file = sandbox.worktree_path / target_file
                sandboxed_file.parent.mkdir(parents=True, exist_ok=True)
                sandboxed_file.write_text(code_content, encoding="utf-8")

            if target_file.endswith(".py"):
                try:
                    ast.parse(code_content, filename=target_file)
                except SyntaxError as syn_err:
                    logger.warning(f"[APD-Paso3] Error sintáctico en sandbox ({target_file}): {syn_err}")
                    preflight_gaps.append(ProductGap(
                        id=f"SYNTAX_ERR_{Path(target_file).name}",
                        description=f"Error sintáctico Python en línea {syn_err.lineno}: {syn_err.msg}",
                        target_module=target_file,
                        is_yagni_approved=True,
                    ))

        all_gaps = (gaps_to_fix or []) + preflight_gaps
        if all_gaps:
            self._heal_file_gaps(code_map, all_gaps, force_fallback)

    def step_3_build_in_sandbox(
        self,
        modules: list[ModulePlan],
        code_map: dict[str, str],
        baseline_code: str | None = None,
        clean_room_payloads: list[CleanRoomPayload] | None = None,
        gaps_to_fix: list[ProductGap] | None = None,
        force_fallback: bool = False,
    ) -> None:
        """STEP 3: Build modules in a Git worktree sandbox (anti-mock and clean-room)."""
        logger.info("[APD-Paso3] Construyendo módulos en Git Worktree Sandbox...")
        is_git = (self.repo_root / ".git").exists()
        sandbox_ctx = self.worktree.create_worktree(self.repo_root) if is_git else nullcontext(None)

        with sandbox_ctx as sandbox:
            if sandbox:
                logger.debug(f"[APD-Paso3] Sandbox efímero activo en: {sandbox.worktree_path}")

            files_to_modules: dict[str, list[ModulePlan]] = {}
            for mod in modules:
                if mod.is_yagni_approved:
                    files_to_modules.setdefault(mod.target_file, []).append(mod)

            for target_file, file_mods in files_to_modules.items():
                self._synthesize_target_file_modules(
                    target_file, file_mods, code_map, baseline_code, clean_room_payloads, force_fallback
                )

            self._verify_sandbox_syntax(code_map, sandbox, gaps_to_fix, force_fallback)

    def _heal_file_gaps(
        self,
        code_map: dict[str, str],
        gaps_to_fix: list[ProductGap],
        force_fallback: bool,
    ) -> None:
        """Apply remediation to files identified with active gaps."""
        for target_file in list(code_map.keys()):
            t_norm = Path(target_file).as_posix().lstrip("./")
            file_gaps = [
                g for g in gaps_to_fix
                if g.is_yagni_approved and (
                    Path(g.target_module).as_posix().lstrip("./") == t_norm
                    or t_norm.endswith(Path(g.target_module).as_posix().lstrip("./"))
                    or Path(g.target_module).name == Path(target_file).name
                )
            ]
            if not file_gaps:
                continue

            if self.client and not force_fallback:
                code_map[target_file] = self._cognitive_heal_gaps(target_file, code_map[target_file], file_gaps)
            else:
                is_ts = target_file.endswith((".ts", ".tsx", ".js", ".jsx"))
                prefix = "//" if is_ts else "#"
                for g in file_gaps:
                    code_map[target_file] += f"\n{prefix} Fix for {g.id}: {g.description}\n"

    def _calculate_max_nesting_depth(self, node: ast.AST) -> int:
        """Calculate the maximum control nesting depth in an AST."""
        max_depth = 0
        def _walk_depth(curr: ast.AST, depth: int) -> None:
            nonlocal max_depth
            if depth > max_depth:
                max_depth = depth
            for child in ast.iter_child_nodes(curr):
                new_d = depth + 1 if isinstance(child, (ast.If, ast.For, ast.While, ast.AsyncFor, ast.Try)) else depth
                _walk_depth(child, new_d)
        _walk_depth(node, 0)
        return max_depth

    def _audit_python_ast_for_recipes(
        self,
        code_content: str,
        target_file_rel: str,
        recipes: list[PrescriptiveRecipe],
        gaps: list[ProductGap],
    ) -> None:
        """Inspect Python AST for deep nesting and untyped functions."""
        try:
            tree = ast.parse(code_content)
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.debug(f"[APD-Paso3B] Error en análisis estático Python de '{target_file_rel}': {ex}")
            return

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            max_depth = self._calculate_max_nesting_depth(node)
            if max_depth > 3:
                recipe = self.refactoring_engine.get_recipe_for_rule("ARCH-DEEP-NESTING", target_symbol=node.name)
                recipes.append(recipe)
                gaps.append(ProductGap(
                    id=f"AUDIT_NESTING_{node.name}",
                    description=f"Anidamiento excesivo ({max_depth} niveles) en '{node.name}'. Aplicar Guard Clauses.",
                    target_module=target_file_rel,
                    is_yagni_approved=True,
                ))

            untyped_args = [a.arg for a in node.args.args if a.annotation is None and a.arg != "self"]
            if untyped_args or (node.returns is None and not node.name.startswith("__")):
                recipe = self.refactoring_engine.get_recipe_for_rule("CODE-HYGIENE-UNTYPED", target_symbol=node.name)
                recipes.append(recipe)
                gaps.append(ProductGap(
                    id=f"AUDIT_UNTYPED_{node.name}",
                    description=f"Faltan anotaciones de tipo en '{node.name}'. Aplicar PEP 484 estricto.",
                    target_module=target_file_rel,
                    is_yagni_approved=True,
                ))

    def _audit_ts_for_recipes(
        self,
        code_content: str,
        target_file_rel: str,
        recipes: list[PrescriptiveRecipe],
        gaps: list[ProductGap],
    ) -> None:
        """Inspect TypeScript lines for any types or deep indentation."""
        for idx, line in enumerate(code_content.splitlines(), 1):
            if ": any" in line or "as any" in line:
                recipes.append(self.refactoring_engine.get_recipe_for_rule("CODE-HYGIENE-UNTYPED", target_symbol=f"Línea {idx}"))
                gaps.append(ProductGap(
                    id=f"AUDIT_TS_ANY_{idx}",
                    description=f"Uso de tipo 'any' detectado en línea {idx} de '{target_file_rel}'. Exigir tipado estricto.",
                    target_module=target_file_rel,
                    is_yagni_approved=True,
                ))
                break

            stripped = line.lstrip()
            indent_spaces = len(line) - len(stripped)
            is_markup = stripped.startswith(("//", "/*", "*", "<", "</", "{/*", "{", "}", ">")) or stripped.endswith((">", "/>", "{", "}"))
            if indent_spaces >= 24 and not is_markup:
                recipes.append(self.refactoring_engine.get_recipe_for_rule("ARCH-DEEP-NESTING", target_symbol=f"Bloque línea {idx}"))
                gaps.append(ProductGap(
                    id=f"AUDIT_TS_NESTING_{idx}",
                    description=f"Anidamiento excesivo en línea {idx} de '{target_file_rel}'. Aplicar Guard Clauses.",
                    target_module=target_file_rel,
                    is_yagni_approved=True,
                ))
                break

    def step_3b_audit_and_heal_module(
        self,
        target_file_rel: str,
        code_content: str,
    ) -> tuple[str, list[PrescriptiveRecipe], list[ProductGap]]:
        """Step 3B: Prescriptive audit gate.
Inspect code against quality rules (nesting, complexity, SAST). Generate prescriptive remediation recipes and log them as gaps if deviations are detected."""
        recipes: list[PrescriptiveRecipe] = []
        gaps: list[ProductGap] = []

        if target_file_rel.endswith(".py"):
            self._audit_python_ast_for_recipes(code_content, target_file_rel, recipes, gaps)
        elif target_file_rel.endswith((".ts", ".tsx", ".js", ".jsx")):
            self._audit_ts_for_recipes(code_content, target_file_rel, recipes, gaps)

        return code_content, recipes, gaps

    def step_4_differential_comparison(
        self,
        modules: list[ModulePlan],
        dossier: ProductStrategyDossier | SotaIntelligenceReport,
        implemented_code_map: dict[str, str],
        ref_repo_dir: Path | None = None,
        force_fallback: bool = False,
    ) -> list[ProductGap]:
        """STEP 4: Run module-by-module differential comparison (Red Team Auditor)."""
        logger.info("[APD-Paso4] Ejecutando Tribunal Comparador contra Cubo 1 y referencia...")
        actual_dossier = dossier.dossier if isinstance(dossier, SotaIntelligenceReport) else dossier
        all_code = "\n".join(implemented_code_map.values()).lower()

        orthogonal_gaps = evaluate_orthogonal_gaps(
            implemented_code_map=implemented_code_map,
            modules=modules,
            baseline_code_map=self._baseline_code_map,
            repo_root=self.repo_root,
        )
        if orthogonal_gaps:
            return orthogonal_gaps

        if self.client and not force_fallback:
            cognitive_gaps = run_cognitive_red_team_audit(
                all_code=all_code,
                actual_dossier=actual_dossier,
                modules=modules,
                generate_content_fn=self._generate_content_with_retry,
                strip_markdown_fn=strip_markdown_fences,
            )
            if cognitive_gaps is not None:
                return cognitive_gaps

        anti_features_lower = [af.lower() for af in actual_dossier.deliberate_anti_features]
        return run_heuristic_invariants_fallback(
            all_code=all_code,
            actual_dossier=actual_dossier,
            modules=modules,
            anti_features_lower=anti_features_lower,
        )

    def _execute_mission_convergence_loop(
        self,
        modules: list[ModulePlan],
        code_map: dict[str, str],
        scope: LocalBoundaryScope,
        sota_report: SotaIntelligenceReport,
        dossier: Any,
        force_fallback: bool,
    ) -> tuple[str, list[ProductGap], list[PrescriptiveRecipe]]:
        """Execute iterative build-audit-compare convergence loop."""
        halt_reason = ""
        final_gaps: list[ProductGap] = []
        all_recipes: list[PrescriptiveRecipe] = []
        candidate_gaps: list[ProductGap] = []
        iteration_num = 0

        while True:
            iteration_num += 1
            logger.info(f"[Iteración {iteration_num}] Sintetizando código en Git Worktree...")
            self.step_3_build_in_sandbox(
                modules=modules,
                code_map=code_map,
                baseline_code=scope.baseline_code,
                clean_room_payloads=sota_report.clean_room_payloads,
                gaps_to_fix=candidate_gaps if final_gaps else None,
                force_fallback=force_fallback,
            )

            logger.info(f"[Iteración {iteration_num}] Pasando Auditoría Políglota de Calidad...")
            audit_gaps: list[ProductGap] = []
            for target_path, code in list(code_map.items()):
                healed, recipes, mod_gaps = self.step_3b_audit_and_heal_module(target_path, code)
                code_map[target_path] = healed
                all_recipes.extend(recipes)
                audit_gaps.extend(mod_gaps)

            logger.info(f"[Iteración {iteration_num}] Ejecutando Tribunal Comparador Red Team...")
            sota_gaps = self.step_4_differential_comparison(
                modules=modules,
                dossier=dossier,
                implemented_code_map=code_map,
                ref_repo_dir=None,
                force_fallback=force_fallback,
            )

            candidate_gaps = sota_gaps + audit_gaps
            logger.info(f"[Iteración {iteration_num}] Brechas detectadas por el Red Team: {len(candidate_gaps)}")

            should_halt, reason = self.ledger.evaluate_gaps(candidate_gaps)
            halt_reason = reason
            final_gaps = candidate_gaps

            if should_halt:
                logger.info(f"[Iteración {iteration_num}] Condición de parada alcanzada: {reason}")
                break

            logger.info(f"[Iteración {iteration_num}] Auto-reintentando para subsanar brechas...")

        return halt_reason, final_gaps, all_recipes

    def execute_mission(
        self,
        task: str,
        target_hint: str | None = None,
        sector: str = "Fintech & Web Architecture",
        reference_repo: str | Path | None = None,
        force_fallback: bool = False,
        planned_modules: list[dict[str, Any]] | list[ModulePlan] | None = None,
        simulated_code_map: dict[str, str] | None = None,
        precomputed_scope: LocalBoundaryScope | None = None,
        precomputed_sota: SotaIntelligenceReport | None = None,
    ) -> MissionReport:
        """Serve as the end-to-end entry point for the orchestrator."""
        logger.info(f"[APD] === INICIANDO MISIÓN E2E: '{task}' ===")

        effective_target = target_hint or self._auto_localize_target_file(task)
        scope = precomputed_scope or self.step_0_local_boundary(task=task, target_hint=effective_target)
        sota_report = precomputed_sota or self.step_1_sota_discovery(
            task=task,
            sector=sector,
            reference_repo=reference_repo,
            force_fallback=force_fallback,
        )
        dossier = sota_report.dossier
        if planned_modules and all(isinstance(m, ModulePlan) for m in planned_modules):
            modules = planned_modules
        else:
            modules = self.step_2_plan_and_yagni(
                task=task,
                scope=scope,
                dossier=dossier,
                planned_modules=planned_modules,
                target_hint=effective_target,
            )

        code_map = simulated_code_map or {}
        self._current_mission_cache = None

        halt_reason, final_gaps, all_recipes = self._execute_mission_convergence_loop(
            modules=modules,
            code_map=code_map,
            scope=scope,
            sota_report=sota_report,
            dossier=dossier,
            force_fallback=force_fallback,
        )

        status = "CERTIFIED" if "Convergencia perfecta" in halt_reason else "HALTED"

        if not simulated_code_map:
            consolidate_code_map_to_disk(
                code_map=code_map,
                repo_root=self.repo_root,
                status=status,
                halt_reason=halt_reason,
                final_gaps=final_gaps,
            )

        self.reflexion.record_episode(
            task=task,
            component_rel=effective_target or "unknown",
            status=status,
            iterations=self.ledger.current_iteration,
        )

        return MissionReport(
            task=task,
            status=status,
            iterations=self.ledger.current_iteration,
            halt_reason=halt_reason,
            modules_planned=modules,
            dossier=dossier,
            final_gaps=final_gaps,
            history_hashes=self.ledger.hash_history,
            recipes_applied=all_recipes,
        )


product_director = AutonomousProductDirector()

__all__ = [
    "AutonomousProductDirector",
    "CleanRoomFile",
    "CleanRoomPayload",
    "FOWLER_RECIPE_BOOK",
    "FunctionNodeReplacer",
    "LOCAL_CAPABILITIES",
    "LocalBoundaryScope",
    "LocalCapability",
    "MissionReport",
    "ModulePlan",
    "PrescriptiveRecipe",
    "PrescriptiveRefactoringEngine",
    "ProductGap",
    "ProductLedger",
    "apply_search_replace_blocks",
    "product_director",
    "strip_markdown_fences",
]
