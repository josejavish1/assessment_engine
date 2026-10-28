"""
Validate software across four independent, non-overlapping orthogonal gates:
1. Gate 1: Functional Correctness (Pytest/Playwright empirical oracles and Ochiai SBFL).
2. Gate 2: Structural Simplicity (McCabe cyclomatic complexity V(G) <= 10 and YAGNI ratio).
3. Gate 3: Security and Sovereignty (AST analysis, client tampering detection, and zero any types).
4. Gate 4: Platform Contracts (Just-in-Time TypeScript compilation, W3C ARIA, and Apple HIG).
"""
from __future__ import annotations

import ast
import json
import logging
import os
import re
import subprocess
import sys
import textwrap
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.probes.sre_observability import SREObservabilityVisitor
from assessment_engine.infrastructure.evolution.complexity_guard import complexity_guard
from assessment_engine.infrastructure.evolution.closure_tribunal import (
    ForensicASTSecurityVisitor,
    SurgicalCorrectionTicket,
)
from .orthogonal_models import GateResult, OrthogonalAuditReport
from .orthogonal_visitors import (
    ArchitecturalHygieneVisitor,
    check_react_frontend_contracts,
    check_sisp_action_contract,
    check_taste_engine_contract,
    check_typescript_compiler_contract,
    check_zero_hex_contract,
    restore_mounted_files,
    run_isolated_behavioral_smoke_oracle,
)

logger = logging.getLogger("assessment_engine.infrastructure.evolution.orthogonal_gates")


def _find_orphan_ts_symbols(code: str) -> str | None:
    """Find declared non-exported interfaces/types with <= 1 occurrence."""
    for match in re.finditer(r"^(?:(?!\bexport\b)\s*)(?:interface|type)\s+([A-Za-z0-9_]+)\b", code, re.MULTILINE):
        sym = match.group(1)
        if len(re.findall(rf"\b{sym}\b", code)) <= 1:
            return sym
    return None


def _find_orphan_py_functions(code: str) -> str | None:
    """Find private Python functions never referenced within the module AST."""
    try:
        tree = ast.parse(textwrap.dedent(code))
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        all_names = [n.id for n in ast.walk(tree) if isinstance(n, ast.Name)]
        for fn in funcs:
            if fn.startswith("_") and not fn.startswith("__") and all_names.count(fn) <= 1:
                return fn
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.debug(f"[Gate2] Python syntax error inspecting orphan symbols: {ex}")
    return None


def _check_secret_leaks(candidate_code: str) -> GateResult | None:
    """Detect hardcoded credentials or API tokens in source code."""
    secret_patterns = (
        re.compile(r"['\"][A-Za-z0-9_\-]{20,}['\"]\s*(?:#|//)?\s*(?:token|secret|key|password)", re.IGNORECASE),
        re.compile(r"(?:api_key|secret_key|private_key)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.IGNORECASE),
    )
    for pat in secret_patterns:
        if pat.search(candidate_code):
            return GateResult(
                gate_name="GATE_3_SECURITY",
                passed=False,
                failure_signature="HARDCODED_SECRET_LEAK",
                prescriptive_action="Fuga crítica: Se detectaron credenciales o secretos embebidos en el código fuente. Usa variables de entorno.",
            )
    return None


def _evaluate_frontend_security_gate(target_file_rel: str, candidate_code: str) -> GateResult | None:
    """Inspect frontend code for state tampering, type evasion, weak crypto, and mock stubs."""
    tamper_pattern = re.compile(
        r"localStorage\.setItem\s*\(\s*['\"][^'\"]*?(?:xp|level|points|streak|balance|coins|reputation)[^'\"]*?['\"]\s*,",
        re.IGNORECASE,
    )
    if tamper_pattern.search(candidate_code) and any(k in candidate_code for k in ("newXp = ", "newLevel = Math", "newStreak = parseInt")):
        return GateResult(
            gate_name="GATE_3_SECURITY",
            passed=False,
            failure_signature="CLIENT_SIDE_STATE_TAMPERING",
            prescriptive_action=(
                "Vulnerabilidad de Soberanía: Se detectó mutación y persistencia de estado autoritativo (XP/Nivel/Rachas) en localStorage. "
                "El cliente debe ser puramente reactivo y emitir la mutación hacia la API de backend, reflejando el estado devuelto."
            ),
        )

    if re.search(r":\s*any\b|\bas\s+any\b", candidate_code):
        return GateResult(
            gate_name="GATE_3_SECURITY",
            passed=False,
            failure_signature="TS_ANY_TYPE_LEAK",
            prescriptive_action="Violación de tipado estricto: Se detectó ': any' o 'as any'. Define interfaces tipadas completas sin evasión.",
        )

    if re.search(r"charCodeAt\b.*(?:<<|\^|\+).*(?:hash|hashVal)", candidate_code) or re.search(r"(?:function|const)\s+(?:generatePseudoHash|hashString|djb2)\b", candidate_code):
        return GateResult(
            gate_name="GATE_3_SECURITY",
            passed=False,
            failure_signature="HOMEMADE_CRYPTO_REINVENTION",
            prescriptive_action=(
                "Violación de Soberanía de Plataforma: Se detectó un algoritmo de hash manual en JavaScript/TypeScript. "
                "Usa la Web Crypto API nativa estándar: 'await window.crypto.subtle.digest(\"SHA-256\", ...)'."
            ),
        )

    if any(k in target_file_rel.lower() for k in ("qr", "matrix", "chart", "canvas", "heatmap", "tree", "seat")):
        has_substrate = any(k in candidate_code for k in ("<canvas", "<rect", "<path", "<circle", "<polyline", "<polygon", ".map("))
        if not has_substrate and re.search(r"<(?:QrCode|BarChart|PieChart|Activity|Grid|Table)\b", candidate_code):
            return GateResult(
                gate_name="GATE_3_SECURITY",
                passed=False,
                failure_signature="FIGURATIVE_ICON_MOCK_STUB",
                prescriptive_action=(
                    "Anti-Patrón de Maqueta Detectado: Se utilizó un icono decorativo estático en lugar de un "
                    "sustrato funcional real. Debes renderizar los datos reales mediante SVG paramétrico (<rect>, <path>), Canvas o matrices iteradas con .map()."
                ),
            )

    if re.search(r"setTimeout\s*\(\s*(?:\(\)\s*=>|function\s*\(\))\s*\{[^}]*set\w+\([^)]*(?:assistant|role|response|data|status)", candidate_code):
        return GateResult(
            gate_name="GATE_3_SECURITY",
            passed=False,
            failure_signature="MOCK_TIMEOUT_RESPONSE_STUB",
            prescriptive_action=(
                "Anti-Patrón de Maqueta Detectado: Se detectó una simulación de respuesta del servidor con setTimeout(). "
                "En producción, debes conectar el componente con el router backend mediante fetch() o EventSource real."
            ),
        )

    return None


def _evaluate_python_security_gate(target_file_rel: str, candidate_code: str) -> GateResult | None:
    """Inspect Python backend code for path-based auth bypass and AST vulnerabilities."""
    fragile_auth_pattern = re.compile(
        r"(?:request\.url\.path|path)\.startswith\s*\([^)]*['\"]/(?:api|admin)[^)]*\).*(?:401|403|Unauthorized|ADMIN_AUTH_REQUIRED)",
        re.DOTALL | re.IGNORECASE,
    )
    if fragile_auth_pattern.search(candidate_code):
        return GateResult(
            gate_name="GATE_3_SECURITY",
            passed=False,
            failure_signature="FRAGILE_PATH_BASED_AUTH",
            prescriptive_action=(
                "Vulnerabilidad de Enrutamiento: No uses inspección manual de cadenas en request.url.path para autorizar accesos. "
                "Usa la inyección declarativa de FastAPI: 'app.include_router(..., dependencies=[Depends(guard)])'."
            ),
        )

    clean_py = textwrap.dedent(candidate_code).strip()
    try:
        tree = ast.parse(clean_py)
        visitor = ForensicASTSecurityVisitor(rel_path=target_file_rel)
        visitor.visit(tree)
        if visitor.findings:
            return GateResult(
                gate_name="GATE_3_SECURITY",
                passed=False,
                failure_signature="FORENSIC_AST_SECURITY_VIOLATION",
                prescriptive_action=f"Vulnerabilidad de seguridad en backend: {visitor.findings[0]}. Resuélvela inmediatamente.",
                details={"findings": visitor.findings},
            )

        is_router = "router" in target_file_rel.lower() or "/api/" in target_file_rel.lower()
        hygiene = ArchitecturalHygieneVisitor(is_router=is_router)
        hygiene.visit(tree)
        if hygiene.findings:
            sig, sym, act = hygiene.findings[0]
            return GateResult(
                gate_name="GATE_3_SECURITY",
                passed=False,
                failure_signature=sig,
                prescriptive_action=act,
                details={"symbol": sym},
            )
    except SyntaxError as ex:
        return GateResult(
            gate_name="GATE_3_SECURITY",
            passed=False,
            failure_signature="PYTHON_SYNTAX_ERROR",
            prescriptive_action=f"Error de sintaxis Python en línea {ex.lineno}: {ex.msg}.",
        )

    return None


def _run_pytest_subprocess_oracle(test_path: Path, test_file_rel: str, ws: Path) -> GateResult | None:
    """Run pytest in a subprocess and translate failures into prescriptive actions."""
    try:
        res_test = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        if res_test.returncode != 0:
            lines = res_test.stdout.splitlines()[-12:]
            err_tail = "\n".join(lines).strip()
            return GateResult(
                gate_name="GATE_1_CORRECTNESS",
                passed=False,
                failure_signature="EMPIRICAL_ORACLE_FAILURE",
                prescriptive_action=f"El test de regresión '{test_file_rel}' ha fallado en el sandbox:\n{err_tail}\nCorrige la aserción.",
                details={"stdout": res_test.stdout[:600]},
            )
    except subprocess.TimeoutExpired:
        return GateResult(
            gate_name="GATE_1_CORRECTNESS",
            passed=False,
            failure_signature="TEST_TIMEOUT_EXPIRED",
            prescriptive_action=f"El test '{test_file_rel}' superó el tiempo límite (45s). Revisa bloqueos cíclicos o llamadas bloqueantes.",
        )
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.warning(f"[Gate1] Error ejecutando test oráculo: {ex}")
    return None


class OrthogonalGatesEvaluator:
    """Evaluate the four orthogonal engineering gates deterministically."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def _check_syntax_contracts(self, target_file_rel: str, candidate_code: str) -> GateResult | None:
        if target_file_rel.endswith(".py"):
            try:
                compile(candidate_code, target_file_rel, "exec")
            except SyntaxError as e:
                return GateResult(
                    gate_name="GATE_4_CONTRACT",
                    passed=False,
                    failure_signature="PYTHON_SYNTAX_ERROR",
                    prescriptive_action=f"Error de sintaxis Python en línea {e.lineno}: {e.msg}. Corrige la sintaxis.",
                    details={"lineno": e.lineno, "offset": e.offset, "text": e.text},
                )

        if target_file_rel.endswith(".json"):
            try:
                json.loads(candidate_code)
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:
                return GateResult(
                    gate_name="GATE_4_CONTRACT",
                    passed=False,
                    failure_signature="JSON_SYNTAX_ERROR",
                    prescriptive_action=f"Error de sintaxis JSON en {target_file_rel}: {e}. Devuelve un JSON sintácticamente válido conforme a RFC 8259.",
                )
        return None

    def _check_typescript_compiler_contract(
        self, ws: Path, target_file_rel: str, candidate_code: str, batch_files: dict[str, str] | None
    ) -> GateResult | None:
        return check_typescript_compiler_contract(ws, target_file_rel, candidate_code, batch_files)

    def _check_react_frontend_contracts(self, candidate_code: str) -> GateResult | None:
        return check_react_frontend_contracts(candidate_code)

    def _check_router_backend_contracts(self, target_file_rel: str, candidate_code: str) -> GateResult | None:
        is_router = target_file_rel.endswith(".py") and (
            "router" in target_file_rel.lower() or "/routers/" in target_file_rel.lower()
        )
        is_infrastructure_router = any(k in target_file_rel.lower() for k in ("auth", "webhook", "telemetry"))
        if not (is_router and not is_infrastructure_router):
            return None

        has_headless_stream = any(k in candidate_code for k in (
            "StreamingResponse", "FileResponse", "Response(content=", "Response(media_type=",
            "media_type=\"application/pdf\"", "media_type=\"text/csv\"", "media_type=\"application/geo+json\"",
            "media_type=\"application/octet-stream\"", "media_type=\"text/event-stream\"",
            "FileResponse("
        ))
        if not has_headless_stream:
            return GateResult(
                gate_name="GATE_4_CONTRACT",
                passed=False,
                failure_signature="ASYMMETRIC_HEADLESS_API_MISSING",
                prescriptive_action=(
                    "Violación de Simetría Headless Universal: El router no expone ningún endpoint de transmisión estructurada "
                    "o descarga desatendida (StreamingResponse, FileResponse o Response con media_type adecuado). "
                    "Añade un endpoint simétrico 'GET /export' o 'GET /{id}/download' para permitir consumo directo por máquinas."
                ),
            )

        if re.search(r"APIRouter\s*\(\s*[^)]*prefix\s*=\s*['\"]/(?:api|api/v1)\b", candidate_code):
            return GateResult(
                gate_name="GATE_4_CONTRACT",
                passed=False,
                failure_signature="DUPLICATE_API_PREFIX_IN_ROUTER",
                prescriptive_action=(
                    "Anti-Patrón de Prefijo de Router: Los routers modulares no deben incluir '/api' o '/api/v1' en su prefijo local "
                    "(usa prefix='' o prefix='/maps'). La raíz global '/api/v1' se asigna exclusivamente en el montaje de 'main.py' "
                    "para evitar rutas duplicadas como '/api/v1/geo/api/v1/maps/...'"
                ),
            )
        return None

    @staticmethod
    def _validate_batch_router_parity(candidate_code: str, batch_files: dict[str, str]) -> GateResult | None:
        """Verify client fetch calls match endpoints declared in batch router code."""
        router_code = next((code for path, code in batch_files.items() if ("router" in path.lower() or "/routers/" in path.lower())), None)
        if not router_code:
            return None
        declared_endpoints = set(re.findall(r"@router\.(?:get|post|put|delete|patch)\s*\(\s*['\"](/[^'\"]*)['\"]", router_code))
        if not declared_endpoints:
            return None
        fetch_calls = re.findall(r"(?:fetch|EventSource)\s*\(\s*['\"`]/api/v1/[^/'\"`]+(/[^/'\"`?]+)", candidate_code)
        for call_endpoint in fetch_calls:
            if call_endpoint not in declared_endpoints:
                return GateResult(
                    gate_name="GATE_4_CONTRACT",
                    passed=False,
                    failure_signature="URL_ENDPOINT_MISMATCH",
                    prescriptive_action=(
                        f"Desconexión de API Cliente-Servidor: El frontend llama al endpoint '{call_endpoint}', "
                        f"pero el router backend solo expone: {sorted(list(declared_endpoints))}. "
                        f"Alinea la URL del fetch() con los endpoints reales del router."
                    ),
                )
        return None

    def _check_client_wire_contracts(
        self, target_file_rel: str, candidate_code: str, batch_files: dict[str, str] | None
    ) -> GateResult | None:
        is_ts_js = target_file_rel.endswith((".ts", ".tsx", ".js", ".jsx"))
        is_client_component = is_ts_js and (
            "components/primitives/" in target_file_rel
            or any(k in target_file_rel.lower() for k in (
                "drawer", "chat", "copilot", "dashboard", "wizard", "configurator",
                "stage", "map", "matrix", "seating", "tree", "view"
            ))
        )
        if not is_client_component or target_file_rel.endswith((".test.tsx", ".test.ts")):
            return None

        has_local_wire = bool(re.search(
            r"(?:fetch|EventSource|new\s+WebSocket|window\.fetch)\s*\(\s*(?:['\"`]/api/|apiEndpoint|endpoint|\burl\b|`\${(?:apiEndpoint|endpoint|url|API_BASE)}`)",
            candidate_code
        ))
        if not has_local_wire:
            return GateResult(
                gate_name="GATE_4_CONTRACT",
                passed=False,
                failure_signature="DISCONNECTED_UI_WIRE_STUB",
                prescriptive_action=(
                    "Violación de Integridad Fullstack: El componente no consume la API local del sistema ('/api/...'). "
                    "Aunque descargue recursos de un CDN externo (ej. teselas OSM), DEBE conectarse mediante fetch() con los endpoints locales de la API para sincronizar datos de la base de datos."
                ),
            )

        if batch_files:
            parity_res = self._validate_batch_router_parity(candidate_code, batch_files)
            if parity_res:
                return parity_res
        return None

    def _evaluate_frontend_contracts(self, target_file_rel: str, candidate_code: str) -> GateResult | None:
        """Group frontend visual design and platform contracts."""
        if not target_file_rel.endswith((".tsx", ".jsx")):
            return None
        res = self._check_react_frontend_contracts(candidate_code)
        if res:
            return res
        res_hex = check_zero_hex_contract(candidate_code, target_file_rel)
        if res_hex:
            return res_hex
        res_sisp = check_sisp_action_contract(candidate_code, target_file_rel)
        if res_sisp:
            return res_sisp
        return check_taste_engine_contract(candidate_code, target_file_rel)

    def evaluate_gate_4_contract(
        self,
        target_file_rel: str,
        candidate_code: str,
        workspace_dir: Path | None = None,
        batch_files: dict[str, str] | None = None,
    ) -> GateResult:
        """Verify platform contract compliance (Just-in-Time TSC, W3C ARIA, and Apple HIG) before running tests."""
        ws = workspace_dir or self.repo_root

        res = self._check_syntax_contracts(target_file_rel, candidate_code)
        if res:
            return res

        res_fe = self._evaluate_frontend_contracts(target_file_rel, candidate_code)
        if res_fe:
            return res_fe

        if target_file_rel.endswith((".ts", ".tsx", ".js", ".jsx")):
            res = self._check_typescript_compiler_contract(ws, target_file_rel, candidate_code, batch_files)
            if res:
                return res

        res = self._check_router_backend_contracts(target_file_rel, candidate_code)
        if res:
            return res

        res = self._check_client_wire_contracts(target_file_rel, candidate_code, batch_files)
        if res:
            return res

        return GateResult(gate_name="GATE_4_CONTRACT", passed=True)

    def evaluate_gate_3_security(
        self,
        target_file_rel: str,
        candidate_code: str,
    ) -> GateResult:
        """Detect credential leaks, client-side state manipulation, and type evasion."""
        secret_res = _check_secret_leaks(candidate_code)
        if secret_res:
            return secret_res

        if target_file_rel.endswith((".ts", ".tsx", ".js", ".jsx")):
            fe_res = _evaluate_frontend_security_gate(target_file_rel, candidate_code)
            if fe_res:
                return fe_res

        if target_file_rel.endswith(".py"):
            py_res = _evaluate_python_security_gate(target_file_rel, candidate_code)
            if py_res:
                return py_res

        return GateResult(gate_name="GATE_3_SECURITY", passed=True)

    def _check_orphan_symbols(self, target_file_rel: str, candidate_code: str) -> GateResult | None:
        if target_file_rel.endswith((".ts", ".tsx", ".js", ".jsx")):
            first_orphan = _find_orphan_ts_symbols(candidate_code)
            if first_orphan:
                return GateResult(
                    gate_name="GATE_2_COMPLEXITY",
                    passed=False,
                    failure_signature="DEAD_CODE_ORPHAN_SYMBOL",
                    prescriptive_action=(
                        f"Sobreingeniería detectada (Código Muerto - Knip): El tipo o interfaz '{first_orphan}' "
                        f"está declarado pero nunca se utiliza en el componente. Elimina tipos y abstracciones no consumidas."
                    ),
                )

        if target_file_rel.endswith(".py"):
            first_orphan_fn = _find_orphan_py_functions(candidate_code)
            if first_orphan_fn:
                return GateResult(
                    gate_name="GATE_2_COMPLEXITY",
                    passed=False,
                    failure_signature="DEAD_CODE_ORPHAN_SYMBOL",
                    prescriptive_action=(
                        f"Sobreingeniería detectada (Código Muerto - Vulture): La función interna '{first_orphan_fn}' "
                        f"está declarada pero nunca es invocada en el módulo. Elimina código zombi."
                    ),
                )

        return None

    def _check_ast_density_bloat(self, candidate_code: str, baseline_code: str) -> GateResult | None:
        try:
            clean_py = textwrap.dedent(candidate_code)
            tree = ast.parse(clean_py)
            cand_nodes = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.If, ast.While, ast.For, ast.Call, ast.Assign, ast.Return))
            )

            clean_base = textwrap.dedent(baseline_code)
            base_tree = ast.parse(clean_base)
            base_nodes = sum(
                1 for n in ast.walk(base_tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.If, ast.While, ast.For, ast.Call, ast.Assign, ast.Return))
            )
            if base_nodes >= 5 and cand_nodes > (base_nodes * 2.5) and (cand_nodes - base_nodes) > 80:
                return GateResult(
                    gate_name="GATE_2_COMPLEXITY",
                    passed=False,
                    failure_signature="AST_DENSITY_BLOAT",
                    prescriptive_action=(
                        f"Dilatación AST detectada (MDL Violation): El volumen de nodos computacionales creció de "
                        f"{base_nodes} a {cand_nodes} (> 2.8x). Aplica la Navaja de Ockham y reduce la solución al camino crítico mínimo."
                    ),
                    metric_value=base_nodes / cand_nodes,
                )
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.debug(f"[Gate2] Nota en análisis de densidad AST: {ex}")
        return None

    def _check_yagni_inflation(self, candidate_code: str, baseline_code: str) -> GateResult | None:
        loc_base = len([l for l in baseline_code.splitlines() if l.strip() and not l.strip().startswith(("#", "//", "/*", "*"))])
        loc_cand = len([l for l in candidate_code.splitlines() if l.strip() and not l.strip().startswith(("#", "//", "/*", "*"))])

        max_allowed = max(int(loc_base * 1.6), loc_base + 250)
        if loc_cand > max_allowed and loc_base > 50:
            yagni_score = max(0.1, loc_base / loc_cand)
            return GateResult(
                gate_name="GATE_2_COMPLEXITY",
                passed=False,
                failure_signature="YAGNI_LOC_INFLATION",
                prescriptive_action=(
                    f"Inflación YAGNI detectada: el código creció de {loc_base} a {loc_cand} líneas útiles (máximo permitido: {max_allowed}). "
                    f"Elimina sobreingeniería, abstracciones prematuras y andamiaje redundante manteniendo la concisión."
                ),
                metric_value=yagni_score,
            )
        return None

    @staticmethod
    def _resolve_python_violation_signature(v: Any) -> str:
        """Resolve standard Gate 2 failure signature from complexity violation."""
        sig = getattr(v, "rule_id", "CYCLOMATIC_COMPLEXITY_EXCEEDED")
        dt = v.details.lower()
        if any(k in dt for k in ("nesting", "anidamiento", "depth")):
            return "DEEP_NESTING_EXCEEDED"
        if any(k in dt for k in ("coc", "cognitiv", "sobrecarga")):
            return "COGNITIVE_OVERLOAD"
        return sig

    def _check_mccabe_and_nesting(self, target_file_rel: str, candidate_code: str) -> GateResult | None:
        if target_file_rel.endswith(".py"):
            try:
                clean_py = textwrap.dedent(candidate_code)
                rep = complexity_guard.audit_code(clean_py, bimodal=True)
                if not rep.passed and rep.violations:
                    v = rep.violations[0]
                    sig = self._resolve_python_violation_signature(v)
                    return GateResult(
                        gate_name="GATE_2_COMPLEXITY",
                        passed=False,
                        failure_signature=sig,
                        prescriptive_action=(
                            f"[{sig}] Función '{v.function_name}': {v.details}. "
                            f"Descompón la función en submódulos o aplica early returns para aplanar la lógica."
                        ),
                        metric_value=float(v.complexity),
                        details={"violations": [x.to_dict() for x in rep.violations]},
                    )
            except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
                logger.debug(f"[Gate2] Fallo en complejidad Python: {ex}")

        if target_file_rel.endswith((".ts", ".tsx", ".js", ".jsx")):
            control_pattern = re.compile(r"^\s*(?:if|for|while|switch|try|catch)\b")
            lines = candidate_code.splitlines()
            for idx, line in enumerate(lines, 1):
                indent = len(line) - len(line.lstrip())
                if indent >= 18 and control_pattern.match(line):
                    return GateResult(
                        gate_name="GATE_2_COMPLEXITY",
                        passed=False,
                        failure_signature="EXCESSIVE_CONTROL_NESTING",
                        prescriptive_action=f"Anidamiento excesivo en línea {idx} ({line.strip()[:40]}). Aplica Guard Clauses para aplanar el flujo.",
                    )
        return None

    def evaluate_gate_5_sre(self, target_file_rel: str, candidate_code: str) -> GateResult:
        """Evaluate SRE, concurrency, and observability via AST analysis:
1. ASYNC221: Disallow blocking calls (subprocess.run, time.sleep) in async functions.
2. OBS-001: Disallow print() calls in backend and service code.
3. REL-001: Disallow silent exception suppression (except Exception: pass/continue)."""
        if not target_file_rel.endswith(".py"):
            return GateResult(gate_name="GATE_5_SRE", passed=True)

        if target_file_rel.startswith(("tests/", "scripts/", "core/fixtures/", "playbooks/")):
            return GateResult(gate_name="GATE_5_SRE", passed=True)

        try:
            tree = ast.parse(candidate_code, filename=target_file_rel)
        except SyntaxError:
            return GateResult(gate_name="GATE_5_SRE", passed=True)

        visitor = SREObservabilityVisitor(target_file_rel)
        visitor.visit(tree)

        critical_violations = [f for f in visitor.findings if f.severity in ("CRITICAL", "HIGH")]
        if critical_violations:
            first = critical_violations[0]
            return GateResult(
                gate_name="GATE_5_SRE",
                passed=False,
                failure_signature=first.rule_id,
                prescriptive_action=f"[{first.rule_id}] Línea {first.line_number}: {first.message} {first.recommendation}",
                details={"violations": [asdict(f) for f in critical_violations]}
            )

        return GateResult(gate_name="GATE_5_SRE", passed=True)

    def evaluate_gate_2_complexity(
        self,
        target_file_rel: str,
        baseline_code: str | None,
        candidate_code: str,
    ) -> GateResult:
        """Measure structural simplicity and YAGNI compliance, evaluating AST node density, dead code (Knip/Vulture), McCabe cyclomatic complexity (V(G) <= 10), and control depth."""
        res = self._check_orphan_symbols(target_file_rel, candidate_code)
        if res:
            return res

        if baseline_code:
            if target_file_rel.endswith(".py"):
                res = self._check_ast_density_bloat(candidate_code, baseline_code)
                if res:
                    return res

            res = self._check_yagni_inflation(candidate_code, baseline_code)
            if res:
                return res

        res = self._check_mccabe_and_nesting(target_file_rel, candidate_code)
        if res:
            return res

        return GateResult(gate_name="GATE_2_COMPLEXITY", passed=True)

    def _evaluate_behavioral_smoke_oracle(
        self,
        target_file_rel: str,
        candidate_code: str,
    ) -> GateResult | None:
        """Delegate isolated black-box behavioral probe checks to orthogonal_visitors."""
        return run_isolated_behavioral_smoke_oracle(target_file_rel, candidate_code, self.repo_root)

    def evaluate_gate_1_correctness(
        self,
        test_file_rel: str | None,
        workspace_dir: Path | None = None,
        target_file_rel: str = "",
        candidate_code: str = "",
        require_test: bool = False,
    ) -> GateResult:
        """Execute in-memory behavioral checks and sandbox tests to verify functional correctness."""
        # 1. Run in-memory black-box behavioral probe (Behavioral Smoke Oracle).
        if target_file_rel.endswith(".py") and ("router" in target_file_rel.lower() or "/api/" in target_file_rel.lower()):
            smoke_res = self._evaluate_behavioral_smoke_oracle(target_file_rel, candidate_code)
            if smoke_res and not smoke_res.passed:
                return smoke_res

        if not test_file_rel:
            if require_test:
                return GateResult(
                    gate_name="GATE_1_CORRECTNESS",
                    passed=False,
                    failure_signature="MISSING_TEST_FILE",
                    prescriptive_action="Modo estricto activo: Es obligatorio especificar un archivo de test para certificar la funcionalidad.",
                )
            return GateResult(gate_name="GATE_1_CORRECTNESS", passed=True)

        ws = workspace_dir or self.repo_root
        test_path = ws / test_file_rel
        if not test_path.exists():
            if require_test:
                return GateResult(
                    gate_name="GATE_1_CORRECTNESS",
                    passed=False,
                    failure_signature="TEST_FILE_NOT_FOUND",
                    prescriptive_action=f"El archivo de test '{test_file_rel}' no existe en el sandbox o no fue generado por el sintetizador.",
                )
            logger.debug(f"[Gate1] Archivo de test '{test_file_rel}' no encontrado; operando en modo tolerante.")
            return GateResult(gate_name="GATE_1_CORRECTNESS", passed=True)

        sub_res = _run_pytest_subprocess_oracle(test_path, test_file_rel, ws)
        if sub_res:
            return sub_res

        return GateResult(gate_name="GATE_1_CORRECTNESS", passed=True)

    def evaluate_all(
        self,
        target_file_rel: str,
        candidate_code: str,
        baseline_code: str | None = None,
        test_file_rel: str | None = None,
        workspace_dir: Path | None = None,
        batch_files: dict[str, str] | None = None,
        require_test: bool = False,
    ) -> OrthogonalAuditReport:
        """Execute the five gates in a deterministic fail-fast sequence:
Gate 4 (Contracts) -> Gate 3 (Security) -> Gate 5 (SRE) -> Gate 2 (Complexity) -> Gate 1 (Correctness)."""
        gates: dict[str, GateResult] = {}

        # 1. Compuerta 4: Contratos de Plataforma (Tipos, Cierres, Sintaxis y Lote Colectivo)
        g4 = self.evaluate_gate_4_contract(
            target_file_rel=target_file_rel,
            candidate_code=candidate_code,
            workspace_dir=workspace_dir,
            batch_files=batch_files,
        )
        gates["GATE_4_CONTRACT"] = g4
        if not g4.passed:
            return self._build_failure_report(gates, g4)

        g3 = self.evaluate_gate_3_security(target_file_rel, candidate_code)
        gates["GATE_3_SECURITY"] = g3
        if not g3.passed:
            return self._build_failure_report(gates, g3)

        # 3. Compuerta 5: SRE, Concurrencia y Observabilidad (RFC-016)
        g5 = self.evaluate_gate_5_sre(target_file_rel, candidate_code)
        gates["GATE_5_SRE"] = g5
        if not g5.passed:
            return self._build_failure_report(gates, g5)

        # 4. Compuerta 2: Simplicidad Estructural & YAGNI
        g2 = self.evaluate_gate_2_complexity(target_file_rel, baseline_code, candidate_code)
        gates["GATE_2_COMPLEXITY"] = g2
        if not g2.passed:
            return self._build_failure_report(gates, g2)

        g1 = self.evaluate_gate_1_correctness(
            test_file_rel,
            workspace_dir,
            target_file_rel=target_file_rel,
            candidate_code=candidate_code,
            require_test=require_test,
        )
        gates["GATE_1_CORRECTNESS"] = g1
        if not g1.passed:
            return self._build_failure_report(gates, g1)

        return OrthogonalAuditReport(
            passed=True,
            gates=gates,
            failed_gate=None,
            yagni_score=1.0,
            summary="Las 4 Compuertas Ortogonales fueron aprobadas al 100% de forma determinista.",
        )

    def _build_failure_report(
        self,
        gates: dict[str, GateResult],
        failed_gate: GateResult,
    ) -> OrthogonalAuditReport:
        """Build a prescriptive report and targeted ticket enriched with W3C telemetry."""
        ticket_id = f"TICK-{uuid.uuid4().hex[:8].upper()}"

        trace_diag_md = ""
        if failed_gate.details and "trace_diagnostic" in failed_gate.details:
            diag = failed_gate.details["trace_diagnostic"]
            if hasattr(diag, "to_prompt_markdown"):
                trace_diag_md = diag.to_prompt_markdown()
            elif isinstance(diag, str):
                trace_diag_md = diag

        ticket = SurgicalCorrectionTicket(
            ticket_id=ticket_id,
            timestamp=float(time.time() if "time" in globals() else 0.0),
            gate_status="REJECTED_CLOSURE_GAP",
            missing_invariants=(failed_gate.prescriptive_action or "Fallo en compuerta",),
            forbidden_anti_features=(),
            forensic_findings=(f"[{failed_gate.gate_name}] {failed_gate.failure_signature}",),
            actionable_instructions=(failed_gate.prescriptive_action or "Subsanar fallo",),
            forbidden_actions=("No destruir la funcionalidad previa", "No inventar dependencias"),
            trace_diagnostic_md=trace_diag_md,
        )
        return OrthogonalAuditReport(
            passed=False,
            gates=gates,
            failed_gate=failed_gate,
            summary=f"Fallo en {failed_gate.gate_name}: {failed_gate.failure_signature}",
            surgical_ticket=ticket,
        )


orthogonal_gates = OrthogonalGatesEvaluator()
