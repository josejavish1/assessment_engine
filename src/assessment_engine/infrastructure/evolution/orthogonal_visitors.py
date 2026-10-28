"""
Provide AST visitors and behavioral probes for orthogonal gates. Decoupled from orthogonal_gates.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

import ast
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from .orthogonal_models import GateResult

logger = logging.getLogger("assessment_engine.infrastructure.evolution.orthogonal_visitors")


class ArchitecturalHygieneVisitor(ast.NodeVisitor):
    """Audit Python AST for architectural hygiene. 1. Detect in-memory mutable state in API routers (statelessness violations).
2. Detect artificial truncation in function inputs (stub slices)."""

    def __init__(self, is_router: bool):
        self.is_router = is_router
        self.findings: list[tuple[str, str, str]] = []
        self.module_level_containers: set[str] = set()

    @staticmethod
    def _is_container_expr(val: ast.AST | None) -> bool:
        if val is None:
            return False
        if isinstance(val, (ast.Dict, ast.List)):
            return True
        return isinstance(val, ast.Call) and isinstance(val.func, ast.Name) and val.func.id in ("dict", "list", "set")

    def visit_Module(self, node: ast.Module):
        """Visit an AST module node."""
        if not self.is_router:
            self.generic_visit(node)
            return

        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and self._is_container_expr(stmt.value):
                        self.module_level_containers.add(target.id)
            elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                if self._is_container_expr(stmt.value):
                    self.module_level_containers.add(stmt.target.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit an AST function definition node."""
        self._check_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit an AST asynchronous function definition node."""
        self._check_function(node)
        self.generic_visit(node)

    def _check_volatile_mutation(self, node: ast.AST) -> bool:
        if not (self.is_router and self.module_level_containers):
            return False

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                        if target.value.id in self.module_level_containers:
                            self.findings.append((
                                "ANTI_PATTERN_VOLATILE_STATE",
                                target.value.id,
                                (
                                    f"Violación de Arquitectura Stateless: Se detectó mutación de estado volátil en memoria "
                                    f"('{target.value.id}') dentro de un endpoint. Toda persistencia de entidades debe "
                                    f"utilizar la base de datos relacional (SQLite WAL) para no perder datos al reiniciar."
                                ),
                            ))
                            return True
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if isinstance(child.func.value, ast.Name) and child.func.value.id in self.module_level_containers:
                    if child.func.attr in ("append", "add", "extend", "insert", "update"):
                        self.findings.append((
                            "ANTI_PATTERN_VOLATILE_STATE",
                            child.func.value.id,
                            (
                                f"Violación de Arquitectura Stateless: Se detectó mutación de lista/set volátil en memoria "
                                f"('{child.func.value.id}') dentro de un endpoint. Toda persistencia de entidades debe "
                                f"utilizar la base de datos relacional (SQLite WAL) para no perder datos al reiniciar."
                            ),
                        ))
                        return True
        return False

    def _check_stub_slices(self, node: ast.AST) -> None:
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Subscript)
                and isinstance(child.slice, ast.Slice)
                and isinstance(child.slice.upper, ast.Constant)
                and isinstance(child.slice.upper.value, int)
                and 0 < child.slice.upper.value <= 400
            ):
                self.findings.append((
                    "ANTI_PATTERN_TRUNCATION_STUB",
                    f"[:{child.slice.upper.value}]",
                    (
                        f"Sobreingeniería inversa / Stub detectado: El contenido se trunca artificialmente "
                        f"a {child.slice.upper.value} caracteres. En producción, debes procesar el contenido real o delegar "
                        f"en la primitiva especializada sin truncamientos arbitrarios."
                    ),
                ))
                return

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        if not self._check_volatile_mutation(node):
            self._check_stub_slices(node)


def restore_mounted_files(mounted_state: dict[Path, tuple[bool, bytes | None]]) -> None:
    """Atomically and safely restore mounted workspace files."""
    for t_p, (existed, old_b) in mounted_state.items():
        try:
            if existed and old_b is not None:
                t_p.write_bytes(old_b)
            elif not existed and t_p.exists():
                t_p.unlink()
        except OSError:
            pass


def _mount_batch_files_for_tsc(
    ws: Path, files_to_mount: dict[str, str]
) -> dict[Path, tuple[bool, bytes | None]]:
    """Mount in-memory batch files on disk before running TSC."""
    mounted_state: dict[Path, tuple[bool, bytes | None]] = {}
    for rel_p, code_txt in files_to_mount.items():
        if "web/" in rel_p or rel_p.endswith((".ts", ".tsx")):
            t_p = ws / rel_p
            existed = t_p.exists()
            old_b = t_p.read_bytes() if existed else None
            mounted_state[t_p] = (existed, old_b)
            t_p.parent.mkdir(parents=True, exist_ok=True)
            t_p.write_text(code_txt, encoding="utf-8")
    return mounted_state


def _run_and_evaluate_tsc(
    web_dir: Path, files_to_mount: dict[str, str], target_file_rel: str
) -> GateResult | None:
    """Run TSC in subprocess and return GateResult on compilation errors."""
    try:
        res_tsc = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=str(web_dir),
            capture_output=True,
            text=True,
            timeout=35,
            check=False,
        )
        if res_tsc.returncode != 0:
            lines = [l for l in res_tsc.stdout.splitlines() if any(Path(p).name in l for p in files_to_mount)]
            err_msg = "\n".join(lines[:5]) if lines else res_tsc.stdout[:400]
            return GateResult(
                gate_name="GATE_4_CONTRACT",
                passed=False,
                failure_signature="TS_COMPILATION_ERROR",
                prescriptive_action=(
                    f"Fallo en contrato de tipos TypeScript ({Path(target_file_rel).name}):\n{err_msg}\n"
                    f"Corrige las interfaces y elimina paquetes externos no declarados en package.json."
                ),
                details={"tsc_output": res_tsc.stdout[:500]},
            )
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.debug(f"[Gate4] Skip TSC subprocess: {ex}")
    return None


def check_typescript_compiler_contract(
    ws: Path, target_file_rel: str, candidate_code: str, batch_files: dict[str, str] | None
) -> GateResult | None:
    """Validate TypeScript types and contracts by running batch 'npx tsc --noEmit'."""
    web_dir = ws / "templates" / "golden_polyglot_starter" / "web"
    if not web_dir.exists():
        web_dir = ws

    if not ((web_dir / "tsconfig.json").exists() and (
        target_file_rel.startswith("templates/golden_polyglot_starter/web/")
        or target_file_rel.startswith("web/")
        or "web/src/" in target_file_rel
    )):
        return None

    files_to_mount = dict(batch_files or {})
    files_to_mount[target_file_rel] = candidate_code
    mounted_state = _mount_batch_files_for_tsc(ws, files_to_mount)

    try:
        return _run_and_evaluate_tsc(web_dir, files_to_mount, target_file_rel)
    finally:
        restore_mounted_files(mounted_state)


def check_react_frontend_contracts(candidate_code: str) -> GateResult | None:
    """Validate React.memo closures and Apple HIG design guidelines."""
    import re
    if re.search(r"React\.memo\s*\([^;]+;\s*\}\s*;", candidate_code):
        return GateResult(
            gate_name="GATE_4_CONTRACT",
            passed=False,
            failure_signature="SYNTAX_MEMO_CLOSURE_ERROR",
            prescriptive_action="Sintaxis corrupta en React.memo: se cerró con '};' en vez de '});'. Corrige el cierre de la función.",
        )

    try:
        from assessment_engine.infrastructure.primitives.apple_design_gate import (
            _audit_color_budget,
            _audit_spacing_and_rhythm,
            _audit_typography_scale,
        )
        findings: list[dict[str, Any]] = []
        pen = _audit_typography_scale(candidate_code, findings, 0)
        pen = _audit_spacing_and_rhythm(candidate_code, findings, pen)
        pen = _audit_color_budget(candidate_code, findings, pen)

        if pen > 40:
            top_issue = findings[0]["issue"] if findings else "Caos visual"
            return GateResult(
                gate_name="GATE_4_CONTRACT",
                passed=False,
                failure_signature="APPLE_HIG_CHAOS",
                prescriptive_action=f"Violación de contrato visual Apple HIG: {top_issue}. Respeta la escala armónica y la rejilla de 8pt.",
                details={"findings": findings},
            )
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.debug(f"[Gate4] Skip Apple HIG audit: {ex}")
    return None


def check_zero_hex_contract(candidate_code: str, target_file_rel: str) -> GateResult | None:
    """Validate Tailwind CSS usage by prohibiting arbitrary bracketed hex classes."""
    if not target_file_rel.endswith((".tsx", ".jsx", ".html")):
        return None

    import re
    hex_pattern = re.compile(r'(?:bg|text|border|ring|fill|stroke)-\[#([0-9a-fA-F]{3,8})\]')
    matches = hex_pattern.findall(candidate_code)
    if matches:
        return GateResult(
            gate_name="GATE_4_CONTRACT",
            passed=False,
            failure_signature="ARBITRARY_HEX_CLASSES_DETECTED",
            prescriptive_action=(
                f"Violación del Zero-Hex Mandate SOTA: Se detectaron {len(matches)} clases fijas arbitrarias con corchetes (ej. #{matches[0]}). "
                "Debes sustituirlas exclusivamente por tokens semánticos inyectados (bg-primary, text-on-surface, border-outline, bg-surface-container)."
            ),
            details={"violations_count": len(matches), "first_hexes": matches[:5]},
        )
    return None


def check_sisp_action_contract(candidate_code: str, target_file_rel: str) -> GateResult | None:
    """Validate that view and landing visual components declare contractual events and contain no dead buttons."""
    is_view = target_file_rel.endswith((".tsx", ".jsx")) and any(
        k in target_file_rel.lower() for k in ("landing", "view", "portal", "screen")
    )
    if not is_view:
        return None

    import re
    button_tags = re.findall(r"<button\b[^>]*>", candidate_code, re.IGNORECASE)
    unwired = [b for b in button_tags if "onClick" not in b and 'type="submit"' not in b]
    if unwired:
        return GateResult(
            gate_name="GATE_4_CONTRACT",
            passed=False,
            failure_signature="SISP_UNWIRED_BUTTONS_DETECTED",
            prescriptive_action=(
                f"Violación de Contrato SISP Full-Stack: Se detectaron {len(unwired)} botones sin evento de acción enlazado. "
                "Enlaza cada botón con su prop contractual (onOpenBooking, onOpenCheckout, onOpenAuth) o fallback hash (#view=booking)."
            ),
            details={"unwired_count": len(unwired)},
        )
    return None


def check_taste_engine_contract(candidate_code: str, target_file_rel: str) -> GateResult | None:
    """Validate craft and micro-interaction contracts."""
    is_view = target_file_rel.endswith((".tsx", ".jsx")) and any(
        k in target_file_rel.lower() for k in ("landing", "view", "portal", "screen", "component")
    )
    if not is_view:
        return None

    try:
        from assessment_engine.infrastructure.primitives.taste_engine import taste_engine
        report = taste_engine.audit_taste_contracts(candidate_code)
        if not report.passed:
            first_err = next((v for v in report.violations if v.severity == "ERROR"), report.violations[0])
            return GateResult(
                gate_name="GATE_4_CONTRACT",
                passed=False,
                failure_signature=f"TASTE_ENGINE_VIOLATION_{first_err.rule_id}",
                prescriptive_action=(
                    f"Violación de Craft Visual SOTA ({first_err.rule_id}): {first_err.description}. "
                    f"Remediación: {first_err.remediation}"
                ),
                details={"violations_count": len(report.violations), "score": report.score},
            )
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.debug(f"[Gate4] Skip TasteEngine audit: {ex}")

    return None


def _evaluate_smoke_runner_json_output(stdout: str) -> GateResult | None:
    """Evaluate JSON status payload emitted by the ephemeral smoke runner."""
    if not stdout.strip():
        return None
    try:
        data = json.loads(stdout.strip().splitlines()[-1])
        st = data.get("status")
        if st == "collision":
            bad_path = data.get("path", "")
            return GateResult(
                gate_name="GATE_1_CORRECTNESS",
                passed=False,
                failure_signature="DUPLICATE_ROUTER_PREFIX_COLLISION",
                prescriptive_action=(
                    f"Fallo de arquitectura de rutas: La ruta '{bad_path}' contiene el prefijo '/api' duplicado. "
                    f"Define prefijos relativos limpios en el router (ej. prefix='' o prefix='/maps')."
                ),
                details={"path": bad_path},
            )
        if st == "500":
            path = data.get("path", "")
            resp_text = data.get("text", "")
            return GateResult(
                gate_name="GATE_1_CORRECTNESS",
                passed=False,
                failure_signature="BEHAVIORAL_CRASH_HTTP_500",
                prescriptive_action=(
                    f"Fallo de ejecución conductual: El endpoint GET '{path}' arrojó un error HTTP 500 "
                    f"al invocarse en la sonda en memoria. Corrige la lógica del handler para responder correctamente."
                ),
                details={"status_code": 500, "path": path, "response": resp_text},
            )
        if st == "exception":
            path = data.get("path", "")
            err = data.get("error", "")
            return GateResult(
                gate_name="GATE_1_CORRECTNESS",
                passed=False,
                failure_signature="BEHAVIORAL_CRASH_EXCEPTION",
                prescriptive_action=f"Fallo de ejecución conductual: La invocación de GET '{path}' lanzó excepción: {err}.",
                details={"exception": err, "path": path},
            )
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex_json:
        logger.debug(f"[BehavioralOracle] Error parseando salida JSON de subproceso: {ex_json}")
    return None


def run_isolated_behavioral_smoke_oracle(
    target_file_rel: str,
    candidate_code: str,
    repo_root: Path,
) -> GateResult | None:
    """Execute the router in an isolated subprocess using FastAPI TestClient to verify that endpoints return valid data and do not fail with HTTP 500 errors."""
    if not candidate_code or len(candidate_code.strip()) < 40:
        return None

    if "APIRouter" not in candidate_code and "router" not in candidate_code:
        return None

    tmp_file: Path | None = None
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
            f.write(candidate_code)
            tmp_file = Path(f.name)

        py_bin = sys.executable
        venv_py = repo_root / "venv" / "bin" / "python"
        if venv_py.exists():
            py_bin = str(venv_py)

        runner_script = (
            "import sys, json\n"
            "from fastapi import FastAPI\n"
            "from fastapi.testclient import TestClient\n"
            "import importlib.util\n"
            "\n"
            "try:\n"
            "    spec = importlib.util.spec_from_file_location('candidate_router', sys.argv[1])\n"
            "    if not spec or not spec.loader:\n"
            "        print(json.dumps({'status': 'none'}))\n"
            "        sys.exit(0)\n"
            "    mod = importlib.util.module_from_spec(spec)\n"
            "    sys.modules['candidate_router'] = mod\n"
            "    spec.loader.exec_module(mod)\n"
            "    router = getattr(mod, 'router', None)\n"
            "    if not router or not hasattr(router, 'routes'):\n"
            "        print(json.dumps({'status': 'none'}))\n"
            "        sys.exit(0)\n"
            "    app = FastAPI()\n"
            "    app.include_router(router)\n"
            "    client = TestClient(app)\n"
            "    for route in router.routes:\n"
            "        methods = getattr(route, 'methods', set())\n"
            "        path = getattr(route, 'path', '')\n"
            "        if '{' in path:\n"
            "            continue\n"
            "        if path.count('/api') > 1:\n"
            "            print(json.dumps({\n"
            "                'status': 'collision',\n"
            "                'path': path,\n"
            "            }))\n"
            "            sys.exit(0)\n"
            "        if 'GET' in methods:\n"
            "            try:\n"
            "                res = client.get(path)\n"
            "                if res.status_code == 500:\n"
            "                    print(json.dumps({\n"
            "                        'status': '500',\n"
            "                        'path': path,\n"
            "                        'text': res.text[:200],\n"
            "                    }))\n"
            "                    sys.exit(0)\n"
            "            except Exception as ex:\n"
            "                print(json.dumps({\n"
            "                    'status': 'exception',\n"
            "                    'path': path,\n"
            "                    'error': str(ex),\n"
            "                }))\n"
            "                sys.exit(0)\n"
            "    print(json.dumps({'status': 'ok'}))\n"
            "except Exception as ex_load:\n"
            "    print(json.dumps({'status': 'load_error', 'error': str(ex_load)}))\n"
        )

        res = subprocess.run(
            [py_bin, "-c", runner_script, str(tmp_file)],
            capture_output=True,
            text=True,
            timeout=10.0,
            check=False,
        )

        if res.returncode == 0:
            sub_res = _evaluate_smoke_runner_json_output(res.stdout)
            if sub_res:
                return sub_res
    except subprocess.TimeoutExpired:
        return GateResult(
            gate_name="GATE_1_CORRECTNESS",
            passed=False,
            failure_signature="BEHAVIORAL_PROBE_TIMEOUT",
            prescriptive_action=(
                f"Fallo de resiliencia conductual: La inicialización o invocación del router '{target_file_rel}' "
                f"excedió el límite de 10s (bucle infinito o bloqueo de red en subproceso)."
            ),
        )
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.debug(f"[BehavioralOracle] Nota durante evaluación conductual de {target_file_rel}: {ex}")
        return None
    finally:
        if tmp_file and tmp_file.exists():
            try:
                tmp_file.unlink()
            except OSError as ex_unl:
                logger.debug(f"[BehavioralOracle] Error eliminando archivo temporal {tmp_file}: {ex_unl}")

    return None
