"""
Orchestrate the asymmetric dialectic loop. Coordinate two primary roles:
- Synthesizer: Propose minimal implementation and tests.
- Skeptic: Audit vulnerabilities, concurrency, and overengineering using web search grounding.
Enforce a strict two-iteration limit and validate against deterministic certification gates (AST, Pytest, Radon CC V(G) <= 10, Mutation CTF >= 0.80, Zero-Dep-Drift).
"""
from __future__ import annotations


import ast
import logging
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.evolution.ast_signature_guard import (
    CognitiveArbiterReport,
    SignatureViolation,
    VerdictStatus,
    diff_module_signatures,
)
from assessment_engine.infrastructure.evolution.complexity_guard import audit_code_complexity
from assessment_engine.infrastructure.evolution.mutation_ctf_probe import run_mutation_ctf
from assessment_engine.infrastructure.genai_client import ModelTier, get_model
from assessment_engine.infrastructure.evolution.worktree_runner import EphemeralWorktree, worktree_runner

logger = logging.getLogger("assessment_engine.infrastructure.evolution.cognitive_arbiter")

MAX_DIALECTIC_ROUNDS = 5
MIN_MUTATION_SCORE_THRESHOLD = 0.80
MAX_CYCLOMATIC_COMPLEXITY_THRESHOLD = 10


class LLMTruncationError(RuntimeError):
    """Raised when a GenAI response is truncated due to token output limits (finish_reason=MAX_TOKENS)."""


class SurgicalPatchError(RuntimeError):
    """Raised when a surgical search-and-replace patch cannot be applied deterministically."""


@dataclass(frozen=True)
class OracleAuditReport:
    """Report from deterministic scrutiny of the test oracle."""
    passed: bool
    findings: list[str]
    assertions_count: int
    test_functions_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary format."""
        return asdict(self)


def _is_tautological_test(test_expr: ast.expr) -> bool:
    """Check if test expression is a trivial truthy constant like assert True or assert 1."""
    if isinstance(test_expr, ast.Constant):
        return bool(test_expr.value) is True
    return False


def _is_raises_call(call_node: ast.Call) -> bool:
    """Check if call is pytest.raises."""
    fn = call_node.func
    if isinstance(fn, ast.Attribute) and fn.attr == "raises":
        return True
    if isinstance(fn, ast.Name) and fn.id == "raises":
        return True
    return False


def _match_target_module(arg_str: str, target_mod_names: list[str]) -> str | None:
    """Return matched module if arg_str targets any system under test."""
    for mod in target_mod_names:
        if mod and mod in arg_str:
            return mod
    return None


def _detect_sut_mocking(call_node: ast.Call, target_mod_names: list[str]) -> str | None:
    """Detect if a call to patch mocks the system under test."""
    fn_name = ""
    if isinstance(call_node.func, ast.Attribute):
        fn_name = call_node.func.attr
    elif isinstance(call_node.func, ast.Name):
        fn_name = call_node.func.id

    if fn_name not in ("patch", "patch_object"):
        return None

    for arg in call_node.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            matched = _match_target_module(arg.value, target_mod_names)
            if matched:
                return matched
    return None


def _inspect_test_function(
    fn_node: ast.FunctionDef | ast.AsyncFunctionDef,
    target_mod_names: list[str],
) -> tuple[int, list[str]]:
    """Inspect a single test function for assert presence, tautologies, and sut mocking."""
    asserts_found = 0
    findings: list[str] = []

    for node in ast.walk(fn_node):
        if isinstance(node, ast.Assert):
            asserts_found += 1
            if _is_tautological_test(node.test):
                findings.append(
                    f"Aserción tautológica trivial en '{fn_node.name}': 'assert True' no verifica comportamiento real."
                )
        elif isinstance(node, ast.Call):
            if _is_raises_call(node):
                asserts_found += 1
            mocked = _detect_sut_mocking(node, target_mod_names)
            if mocked:
                findings.append(
                    f"Anti-Mocking detectado en '{fn_node.name}': mockea la propia unidad bajo prueba '{mocked}'."
                )

    if asserts_found == 0:
        findings.append(
            f"El test '{fn_node.name}' no contiene aserciones reales (ast.Assert o pytest.raises)."
        )

    return asserts_found, findings


def _convert_unified_diff_to_surgical_blocks(diff_text: str) -> str:
    """Convert unified diff hunks (--- a/ +++ b/ @@) into canonical SEARCH/REPLACE blocks."""
    if "@@" not in diff_text:
        return diff_text

    blocks: list[str] = []
    hunks = re.split(r"^@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@.*$", diff_text, flags=re.MULTILINE)
    for hunk in hunks[1:]:
        old_lines: list[str] = []
        new_lines: list[str] = []
        for line in hunk.splitlines():
            if line.startswith("-"):
                old_lines.append(line[1:])
            elif line.startswith("+"):
                new_lines.append(line[1:])
            elif line.startswith(" "):
                old_lines.append(line[1:])
                new_lines.append(line[1:])
        if old_lines and new_lines:
            blocks.append(f"<<<< SEARCH\n{chr(10).join(old_lines)}\n====\n{chr(10).join(new_lines)}\n>>>>")

    return "\n\n".join(blocks) if blocks else diff_text


def _match_line_slices(
    base_lines: list[str], target_lines: list[str], key_fn: Callable[[str], str]
) -> int | None:
    """Find unique occurrence of target_lines within base_lines under key_fn normalization."""
    n = len(target_lines)
    if n == 0 or n > len(base_lines):
        return None
    matches = [
        i for i in range(len(base_lines) - n + 1)
        if [key_fn(l) for l in base_lines[i : i + n] if l.strip()] == target_lines
    ]
    return matches[0] if len(matches) == 1 else None


def _find_and_replace_by_stripped_lines(base: str, old: str, new: str) -> str | None:
    """Attempt line-by-line replacement ignoring leading and trailing whitespace."""
    base_lines = base.splitlines()
    old_rstrip = [l.rstrip() for l in old.splitlines() if l.strip()]
    idx = _match_line_slices(base_lines, old_rstrip, lambda l: l.rstrip())
    if idx is not None:
        return "\n".join(base_lines[:idx] + [new] + base_lines[idx + len(old_rstrip) :])

    old_stripped = [l.strip() for l in old.splitlines() if l.strip()]
    idx = _match_line_slices(base_lines, old_stripped, lambda l: l.strip())
    if idx is None:
        return None

    orig_indent = len(base_lines[idx]) - len(base_lines[idx].lstrip())
    reindented = [
        (" " * orig_indent + l if l.strip() and not l.startswith(" ") else l)
        for l in new.splitlines()
    ]
    return "\n".join(base_lines[:idx] + reindented + base_lines[idx + len(old_stripped) :])


def apply_surgical_patch(baseline_code: str, patch_text: str) -> str:
    """
    Apply atomic search-and-replace blocks to baseline_code with strict uniqueness validation.

    Supported formats:
    <<<< SEARCH (or OLD)
    <exact unique code to match>
    ====
    <replacement code>
    >>>> (or REPLACE)
    """
    if "@@" in patch_text and ("---" in patch_text or "+++" in patch_text):
        patch_text = _convert_unified_diff_to_surgical_blocks(patch_text)

    pattern = re.compile(
        r"<+\s*(?:SEARCH|OLD|HEAD)?\s*\n(.*?)\n=+\s*\n(.*?)\n>+(?:\s*REPLACE|\s*PATCH)?",
        re.DOTALL
    )
    matches = list(pattern.finditer(patch_text))
    if not matches:
        return baseline_code

    modified_code = baseline_code
    for idx, match in enumerate(matches, 1):
        old_block = match.group(1)
        new_block = match.group(2)

        occurrences = modified_code.count(old_block)
        if occurrences == 0:
            fuzzy_replaced = _find_and_replace_by_stripped_lines(modified_code, old_block, new_block)
            if fuzzy_replaced is not None:
                modified_code = fuzzy_replaced
                continue
            raise SurgicalPatchError(
                f"Bloque quirúrgico #{idx} no encontrado en el archivo objetivo (0 coincidencias). "
                f"Verifica la coincidencia exacta de líneas y sangría."
            )
        if occurrences > 1:
            raise SurgicalPatchError(
                f"Bloque quirúrgico #{idx} es ambiguo ({occurrences} coincidencias encontradas). "
                f"Añade más líneas de contexto circundante para garantizar unicidad estricta."
            )

        modified_code = modified_code.replace(old_block, new_block, 1)

    return modified_code


def _build_synthesizer_system_instruction(line_count: int) -> str:
    """Build canonical system instruction, requiring surgical patches only for files exceeding 500 lines."""
    if line_count > 500:
        return (
            "Eres el Sintetizador de Código Autónomo Tier-1 de Autonomuos.\n"
            f"El archivo objetivo es extenso ({line_count} líneas). Queda TERMINANTEMENTE PROHIBIDO reescribir el archivo completo.\n"
            "DEBES emitir un parche quirúrgico atómico con formato SEARCH/REPLACE unívoco:\n"
            "```python\n"
            "<<<< SEARCH\n"
            "# Incluye siempre la cabecera de la función/clase circundante y 3 a 5 líneas de contexto para garantizar coincidencia única\n"
            "====\n"
            "# nuevo código refinado\n"
            ">>>>\n"
            "```\n"
            "REGLA CRÍTICA DE UNICIDAD: Cada bloque SEARCH debe coincidir EXACTAMENTE UNA SOLA VEZ en el archivo. "
            "Prohibido buscar líneas cortas genéricas aisladas (como 'return False' o pass). Añade siempre el contexto circundante de la función o clase.\n"
            "Devuelve EXACTAMENTE dos bloques de código en Markdown:\n"
            "1. El primer bloque con los reemplazos quirúrgicos SEARCH/REPLACE.\n"
            "2. El segundo bloque con la suite de pruebas unitarias pytest completa.\n"
            "Cumple con tipado estricto, McCabe V(G) <= 10, Zero-Print y máxima cobertura.\n"
            "REGLA DE ARQUITECTURA PLANA (Anti-Nesting): Prohibido anidar más de 3 niveles (if/try/while/for). Usa cláusulas de guardia y extrae funciones auxiliares."
        )

    return (
        "Eres el Sintetizador de Código Autónomo Tier-1 de Autonomuos.\n"
        f"El archivo objetivo es compacto ({line_count} líneas). DEBES emitir el CÓDIGO DE PRODUCCIÓN COMPLETO REFINADO desde cero "
        "(queda terminantemente prohibido emitir parches parciales SEARCH/REPLACE).\n"
        "Si se proporciona EXISTING_TEST_ORACLE, tu código DEBE satisfacer el 100% de las pruebas y contratos definidos en dicho oráculo.\n"
        "Devuelve EXACTAMENTE dos bloques de código en Markdown:\n"
        "1. El primer bloque con el código de producción completo en Python.\n"
        "2. El segundo bloque con la suite de pruebas unitarias pytest completa.\n"
        "Cumple con tipado estricto, McCabe V(G) <= 10, Zero-Print y máxima cobertura.\n"
        "REGLA DE ARQUITECTURA PLANA (Anti-Nesting): Prohibido anidar más de 3 niveles (if/try/while/for). Usa cláusulas de guardia y extrae funciones auxiliares."
    )


def _validate_response_truncation(resp: Any) -> None:
    """Validate that the GenAI candidate did not encounter a token overflow."""
    if not hasattr(resp, "candidates") or not resp.candidates:
        return
    cand = resp.candidates[0]
    finish_reason = getattr(cand, "finish_reason", None)
    if finish_reason and "MAX_TOKENS" in str(finish_reason).upper():
        logger.error("[Synthesizer] Respuesta truncada por límite de tokens de salida (finish_reason=MAX_TOKENS).")
        raise LLMTruncationError("Respuesta de LLM truncada por límite de tokens de salida (finish_reason=MAX_TOKENS).")


def _is_test_block(b_clean: str) -> bool:
    """Identify if a code block contains unit test keywords without false positives on .test() JS methods."""
    if "def test_" in b_clean or "@pytest" in b_clean:
        return True
    for line in b_clean.splitlines():
        stripped = line.strip()
        if stripped.startswith(("describe(", "it(", "test(", "test.describe(", "expect(")):
            return True
    return False


def _partition_code_blocks(blocks: list[str]) -> tuple[list[str], list[str]]:
    """Partition extracted markdown blocks into candidates and tests."""
    candidate_blocks: list[str] = []
    test_blocks: list[str] = []
    for b in blocks:
        b_clean = b.strip()
        if _is_test_block(b_clean):
            test_blocks.append(b_clean)
        else:
            candidate_blocks.append(b_clean)
    return candidate_blocks, test_blocks


def _resolve_candidate_code(
    has_surgical_blocks: bool,
    candidate_blocks: list[str],
    blocks: list[str],
    raw_text: str,
    fallback_code: str,
) -> str:
    """Resolve the production code from surgical patches, candidate blocks, or raw fallback."""
    if not fallback_code.strip():
        if candidate_blocks:
            return candidate_blocks[0]
        if blocks:
            return blocks[0].strip()
        return raw_text.strip()

    if has_surgical_blocks:
        patch_source = candidate_blocks[0] if candidate_blocks else raw_text
        return apply_surgical_patch(fallback_code, patch_source)
    if candidate_blocks:
        return candidate_blocks[0]
    if blocks:
        return blocks[0].strip()
    return raw_text.strip() or fallback_code


def _invoke_single_model(
    client: Any,
    model_name: str,
    prompt: str,
    system_instruction: str,
    timeout_ms: int,
    thinking_budget: int | None = None,
    temperature: float = 0.2,
) -> str:
    """Execute a single model call with specified timeout and optional thinking budget."""
    from google.genai import types
    cfg = types.GenerateContentConfig(
        temperature=temperature,
        http_options=types.HttpOptions(timeout=timeout_ms),
    )
    if thinking_budget:
        cfg.thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget)
    if system_instruction:
        cfg.system_instruction = system_instruction

    logger.info(f"[Heartbeat] 💓 Invocando inferencia {model_name} (timeout={timeout_ms // 1000}s)...")
    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=cfg,
    )
    _validate_response_truncation(resp)
    logger.info(f"[Heartbeat] 💓 Inferencia {model_name} completada con éxito.")
    return resp.text or ""


def _merge_test_suites(base_test_code: str, new_test_code: str) -> str:
    """Preserve existing test oracle and append only novel test functions and imports from the synthesizer."""
    if not new_test_code or not new_test_code.strip():
        return base_test_code
    existing_fns = set(re.findall(r"def\s+(test_[a-zA-Z0-9_]+)\s*\(", base_test_code))
    new_fns = re.findall(r"def\s+(test_[a-zA-Z0-9_]+)\s*\(", new_test_code)
    to_append: list[str] = []
    for fn in new_fns:
        if fn not in existing_fns:
            pattern = rf"(def\s+{fn}\s*\(.*?(?=\ndef\s+test_|\Z))"
            m = re.search(pattern, new_test_code, re.DOTALL)
            if m:
                to_append.append(m.group(1).strip())
    if not to_append:
        return base_test_code

    # Extract and inject missing required imports into base_test_code
    new_imports = [
        line.strip()
        for line in new_test_code.splitlines()
        if (line.strip().startswith("import ") or line.strip().startswith("from "))
        and line.strip() not in base_test_code
    ]
    header = ("\n".join(new_imports) + "\n\n") if new_imports else ""
    return header + base_test_code.rstrip() + "\n\n\n" + "\n\n".join(to_append) + "\n"



class SynthesizerRole:
    """Propose the minimal decoupled implementation and refine code to address Skeptic objections."""

    def __init__(
        self,
        client: Any = None,
        llm_fn: Callable[[str], str] | None = None,
        initial_temperature: float = 0.7,
        refine_temperature: float = 0.1,
    ) -> None:
        self.client = client
        self.llm_fn = llm_fn
        self.initial_temperature = initial_temperature
        self.refine_temperature = refine_temperature

    def _invoke_llm(self, prompt: str, system_instruction: str = "", temperature: float = 0.2) -> str:
        """Invoke cognitive engine via injected llm_fn or native GenAI client with fallback."""
        if self.llm_fn:
            return self.llm_fn(prompt)
        if not self.client or not hasattr(self.client, "models"):
            return ""

        try:
            return _invoke_single_model(
                self.client,
                get_model(ModelTier.REASONING),
                prompt,
                system_instruction,
                120000,
                2048,
                temperature=temperature,
            )
        except LLMTruncationError:
            raise
        except Exception as ex:
            logger.warning(f"[Synthesizer] Fallback a ModelTier.FAST tras error en Reasoning: {ex}")

        try:
            return _invoke_single_model(
                self.client,
                get_model(ModelTier.FAST),
                prompt,
                system_instruction,
                90000,
                None,
                temperature=temperature,
            )
        except LLMTruncationError:
            raise
        except Exception as ex_fast:
            logger.warning(f"[Synthesizer] Error en inferencia GenAI: {ex_fast}")
            return ""

    def propose_initial_patch(
        self,
        task_description: str,
        baseline_code: str,
        target_file_rel: str = "",
        fallback_test_code: str = "def test_baseline(): assert True\n",
    ) -> dict[str, str]:
        """Generate candidate code and associated tests using contextual memory."""
        prompt_parts: list[str] = []
        if target_file_rel:
            module_name = target_file_rel.replace("/", ".").replace(".py", "")
            prompt_parts.append(f"TARGET_FILE: {target_file_rel} (Python module import: '{module_name}')")
        prompt_parts.append(f"TASK:\n{task_description}")
        if target_file_rel and "REFLEXION LEDGER" not in task_description:
            try:
                from assessment_engine.infrastructure.evolution.reflexion_ledger import reflexion_ledger
                preflight_memory = reflexion_ledger.format_preflight_prompt_block(target_file_rel)
                if preflight_memory:
                    prompt_parts.append(preflight_memory)
            except Exception as ex:
                logger.debug(f"[Synthesizer] Error consultando ReflexionLedger: {ex}")
        prompt_parts.append(f"BASELINE:\n{baseline_code}")
        if fallback_test_code and "def test_baseline(): assert True" not in fallback_test_code:
            prompt_parts.append(f"EXISTING_TEST_ORACLE:\n{fallback_test_code}")

        line_count = len(baseline_code.splitlines()) if baseline_code else 0
        sys_inst = _build_synthesizer_system_instruction(line_count)
        raw = self._invoke_llm("\n\n".join(prompt_parts), system_instruction=sys_inst, temperature=self.initial_temperature)
        if raw:
            return self._safe_parse_with_disambiguation(raw, baseline_code, fallback_test_code, sys_inst)

        # Fallback determinista cuando no hay LLM mock o API externa
        return {
            "candidate_code": baseline_code,
            "test_code": fallback_test_code,
        }

    def _safe_parse_with_disambiguation(
        self,
        raw_text: str,
        code_to_patch: str,
        fallback_test_code: str,
        sys_inst: str,
    ) -> dict[str, str]:
        """Parse LLM output with autonomous single-shot retry if a surgical patch is ambiguous."""
        try:
            return self._parse_llm_output(raw_text, code_to_patch, fallback_test_code=fallback_test_code)
        except SurgicalPatchError as patch_err:
            logger.warning(f"[Synthesizer] Ambigüedad en parche quirúrgico: {patch_err}. Solicitando desambiguación...")
            retry_prompt = (
                f"{raw_text}\n\n"
                f"ERROR EN PARCHE QUIRÚRGICO: {patch_err}\n"
                "Por favor, reemite el parche SEARCH/REPLACE incluyendo la cabecera de la función/clase circundante "
                "y 3 a 5 líneas de código de contexto para que cada bloque SEARCH coincida EXACTAMENTE UNA SOLA VEZ en el archivo."
            )
            raw_retry = self._invoke_llm(retry_prompt, system_instruction=sys_inst, temperature=self.refine_temperature)
            if raw_retry:
                return self._parse_llm_output(raw_retry, code_to_patch, fallback_test_code=fallback_test_code)
            raise

    def refine_patch(
        self,
        task_description: str,
        current_code: str,
        skeptic_critique: str,
        current_test_code: str = "",
    ) -> dict[str, str]:
        """Refine candidate code in response to skeptic objections."""
        line_count = len(current_code.splitlines()) if current_code else 0
        if line_count > 500:
            prompt = (
                f"TASK: {task_description}\n"
                f"CURRENT_CODE (EXTENSO: {line_count} líneas, PROHIBIDO reescribir completo):\n{current_code}\n"
                f"CURRENT_TEST:\n{current_test_code}\n"
                f"SKEPTIC_CRITIQUE_OR_SURGICAL_TICKET:\n{skeptic_critique}\n"
                "Refina el código mediante parches quirúrgicos SEARCH/REPLACE (<<<< SEARCH / ==== / >>>>) para resolver los tickets.\n"
                "Devuelve exactamente dos bloques de código en Markdown: el primero con las sustituciones SEARCH/REPLACE y el segundo con los tests."
            )
            sys_inst = "Eres el Sintetizador de Código Autónomo Tier-1. Emite parches quirúrgicos SEARCH/REPLACE unívocos y mantén V(G) <= 10."
        else:
            prompt = (
                f"TASK: {task_description}\n"
                f"CURRENT_CODE:\n{current_code}\n"
                f"CURRENT_TEST:\n{current_test_code}\n"
                f"SKEPTIC_CRITIQUE_OR_SURGICAL_TICKET:\n{skeptic_critique}\n"
                "Refina el código de producción y la suite de tests para resolver TODAS las objeciones y tickets forenses.\n"
                "Devuelve exactamente dos bloques de código en Markdown:\n"
                "1. El primer bloque con el código de producción COMPLETO REFINADO (queda estrictamente prohibido emitir parches SEARCH/REPLACE).\n"
                "2. El segundo bloque con la suite de tests completa (con funciones 'def test_...')."
            )
            sys_inst = "Eres el Sintetizador de Código Autónomo Tier-1. Emite el código de producción completo refinado sin anidamientos > 3 y mantén V(G) <= 10."

        raw = self._invoke_llm(prompt, system_instruction=sys_inst, temperature=self.refine_temperature)
        if raw:
            return self._safe_parse_with_disambiguation(raw, current_code, current_test_code, sys_inst)

        return {
            "candidate_code": current_code,
            "test_code": current_test_code or "def test_refined(): assert True\n",
        }

    def _parse_llm_output(
        self,
        raw_text: str,
        fallback_code: str,
        fallback_test_code: str = "",
    ) -> dict[str, str]:
        """Extract polyglot code blocks from LLM response, applying surgical search/replace patches when present."""
        has_surgical_blocks = bool(
            re.search(r"<+\s*(?:SEARCH|OLD|HEAD)?\s*\n.*?\n=+\s*\n", raw_text, re.DOTALL)
            or ("@@" in raw_text and ("+++" in raw_text or "---" in raw_text))
        )

        blocks = re.findall(
            r"```(?:python|py|typescript|tsx|ts|javascript|jsx|js|json)?\s*\n?(.*?)\s*```",
            raw_text,
            re.DOTALL
        )

        candidate_blocks, test_blocks = _partition_code_blocks(blocks)
        code = _resolve_candidate_code(has_surgical_blocks, candidate_blocks, blocks, raw_text, fallback_code)
        if code and code.startswith("x\n"):
            code = code[2:].lstrip()

        if test_blocks and "def test_" in test_blocks[0]:
            if fallback_test_code and "def test_" in fallback_test_code:
                test_code = fallback_test_code
            else:
                test_code = test_blocks[0]
        else:
            test_code = fallback_test_code

        return {
            "candidate_code": code or fallback_code,
            "test_code": test_code,
        }


class SkepticRole:
    """Audit the diff, research RFC/W3C standards, and issue a critical report highlighting concurrency risks, overengineering, and edge cases."""

    def __init__(
        self,
        client: Any = None,
        search_fn: Callable[[str], str] | None = None,
        llm_fn: Callable[[str], str] | None = None,
    ) -> None:
        self.client = client
        self.search_fn = search_fn
        self.llm_fn = llm_fn
        self.recorded_queries: list[str] = []
        self._search_cache: dict[str, str] = {}

    def query_web_standards(self, query: str) -> str:
        """Query official documentation via Google Search grounding with in-memory caching."""
        if query in self._search_cache:
            return self._search_cache[query]

        self.recorded_queries.append(query)
        if self.search_fn:
            res = self.search_fn(query)
            self._search_cache[query] = res
            return res

        # Si hay cliente GenAI real configurado
        if self.client and hasattr(self.client, "models"):
            try:
                from google.genai import types
                logger.info("[Heartbeat] 💓 Skeptic consultando estándares web...")
                resp = self.client.models.generate_content(
                    model=get_model(ModelTier.FAST),
                    contents=f"Technical inquiry on current RFC or standards: {query}",
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                        http_options=types.HttpOptions(timeout=20000),
                    ),
                )
                res = resp.text or "Sin resultados de búsqueda."
                self._search_cache[query] = res
                return res
            except Exception as e:
                logger.debug(f"[Skeptic] Web grounding search note: {e}")
                res = f"Nota de búsqueda: {e}"
                self._search_cache[query] = res
                return res

        res = f"Estándar simulado para: {query}"
        self._search_cache[query] = res
        return res

    def critique_patch(
        self,
        task_description: str,
        diff_code: str,
        search_context: str = "",
    ) -> str:
        """Generate the skeptic technical objections report."""
        trimmed_diff = diff_code[:2500] if len(diff_code) > 2500 else diff_code
        prompt = (
            f"TAREA: {task_description}\n"
            f"DIFF PROPUESTO:\n{trimmed_diff}\n"
            f"CONTEXTO WEB (RFCs/Estándares):\n{search_context}\n"
            "Eres un Consejo de Expertos Tier-1 (Staff UI Perf, Lead Accesibilidad, Principal Security). "
            "Emite una crítica implacable señalando sobreingeniería, riesgos de carrera o casos borde. "
            "Si el código es React/UI, exige: 1. useMemo/useDeferredValue para no bloquear el hilo principal. "
            "2. AbortController en useEffects. 3. WAI-ARIA (aria-live, roles semánticos). 4. Virtualización si hay listas largas."
        )
        if self.llm_fn:
            return self.llm_fn(prompt)
        if self.client and hasattr(self.client, "models"):
            try:
                from google.genai import types
                logger.info("[Heartbeat] 💓 Skeptic generando crítica técnica...")
                resp = self.client.models.generate_content(
                    model=get_model(ModelTier.FAST),
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        http_options=types.HttpOptions(timeout=30000),
                    ),
                )
                return resp.text or ""
            except Exception as ex:
                logger.debug(f"[Skeptic] Error en crítica GenAI: {ex}")

        return (
            "CRÍTICA DEL ESCÉPTICO: Verificar idempotencia ante reintentos de red, "
            "manejo de timeouts en operaciones externas y ausencia de mutaciones en firmas públicas."
        )

    def audit_test_oracle(
        self,
        test_code: str,
        target_rel_path: str = "",
        must_have_invariants: list[str] | None = None,
    ) -> OracleAuditReport:
        """Deterministic scrutiny of test oracle to prevent reward hacking and vacuous tests."""
        try:
            tree = ast.parse(test_code)
        except SyntaxError as ex:
            return OracleAuditReport(
                passed=False,
                findings=[f"Error sintáctico en el oráculo de pruebas: {ex}"],
                assertions_count=0,
                test_functions_count=0,
            )

        target_stem = Path(target_rel_path).stem if target_rel_path else ""
        target_mod_names = [target_stem] if target_stem else []
        if target_rel_path:
            clean_rel = target_rel_path.replace("/", ".").replace("\\", ".").removesuffix(".py")
            if clean_rel and clean_rel not in target_mod_names:
                target_mod_names.append(clean_rel)

        total_asserts = 0
        total_test_fns = 0
        all_findings: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                total_test_fns += 1
                cnt, fnds = _inspect_test_function(node, target_mod_names)
                total_asserts += cnt
                all_findings.extend(fnds)

        if total_test_fns == 0:
            all_findings.append("No se detectó ninguna función de prueba que comience con 'test_'.")

        passed = len(all_findings) == 0
        return OracleAuditReport(
            passed=passed,
            findings=all_findings,
            assertions_count=total_asserts,
            test_functions_count=total_test_fns,
        )


def _audit_ast_nesting_depth(tree: ast.AST, max_depth: int = 3) -> list[str]:
    """Deterministic AST preflight linter detecting control flow nesting > max_depth in < 2ms."""
    violations: list[str] = []

    def _check(node: ast.AST, depth: int, fn_name: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                _check(child, 0, child.name)
            elif isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith)):
                d = depth + 1
                if d > max_depth:
                    lineno = getattr(child, "lineno", 0)
                    node_type = type(child).__name__
                    violations.append(
                        f"ARCH-DEEP-NESTING en función '{fn_name}' (línea {lineno}): anidamiento {d} > {max_depth} (bloque {node_type}). "
                        f"Extrae la lógica a una función auxiliar atómica o usa retornos tempranos."
                    )
                _check(child, d, fn_name)
            else:
                _check(child, depth, fn_name)

    _check(tree, 0, "modulo")
    return violations


class DeterministicHarnessEvaluator:
    """Verify the six boolean hard gates deterministically and without subjectivity."""

    @staticmethod
    def audit_dependencies(diff_text: str) -> bool:
        """Verify that no external dependencies were added without prior authorization (Gate 4: Zero-New-Dependencies)."""
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                clean = line[1:].strip()
                if clean and not clean.startswith("#"):
                    return False
        return True

    @staticmethod
    def evaluate_candidate(
        baseline_code: str,
        candidate_code: str,
        candidate_test_code: str,
        target_file: Path,
        test_file: Path,
        require_clean_deps: bool = True,
        dep_diff_text: str = "",
        work_dir: Path | None = None,
    ) -> tuple[VerdictStatus, list[SignatureViolation], int, float, bool]:
        """Execute deterministic gates on the proposed code and return (status, ast_violations, max_complexity, mutation_score, tests_passed)."""
        # Determine the execution root directory with isolated Git worktree support.
        if work_dir is None:
            work_dir = target_file.parent
            for parent in [target_file] + list(target_file.parents):
                if (parent / "core").is_dir() or (parent / "pytest.ini").is_file() or (parent / "pyproject.toml").is_file() or (parent / ".git").is_dir():
                    work_dir = parent
                    break
        is_python_target = target_file.name.endswith(".py")
        if is_python_target:
            try:
                tree_cand = ast.parse(candidate_code)
                ast.parse(candidate_test_code)
            except SyntaxError as syn_err:
                first_lines = "\n".join(candidate_code.splitlines()[:5])
                logger.warning(f"[Harness] Error sintáctico en candidato: {syn_err}\n--- PRIMERAS LÍNEAS ---\n{first_lines}\n--- FIN ---")
                return (
                    VerdictStatus.REJECTED_AST_SIGNATURE,
                    [SignatureViolation(symbol_name="<syntax>", violation_type="SYNTAX_ERROR", details=str(syn_err))],
                    999,
                    0.0,
                    False,
                    f"SyntaxError: {syn_err}",
                )

            nesting_violations = _audit_ast_nesting_depth(tree_cand, max_depth=3)
            if nesting_violations:
                first_nv = nesting_violations[0]
                logger.warning(f"[Harness] Fast-Fail Preflight AST detectado: {first_nv}")
                return (
                    VerdictStatus.REJECTED_COMPLEXITY,
                    [SignatureViolation(symbol_name="ARCH-DEEP-NESTING", violation_type="DEEP_NESTING", details=first_nv)],
                    1,
                    0.0,
                    False,
                    first_nv,
                )

            ast_violations = diff_module_signatures(baseline_code, candidate_code, allow_additive=True)
            if ast_violations:
                logger.warning(f"[Harness] Violaciones AST detectadas: {len(ast_violations)}")
                return (VerdictStatus.REJECTED_AST_SIGNATURE, ast_violations, 1, 0.0, False, "Violación de firmas AST públicas")

            comp_rep = audit_code_complexity(candidate_code, max_allowed=MAX_CYCLOMATIC_COMPLEXITY_THRESHOLD)
            if not comp_rep.passed:
                base_rep = audit_code_complexity(baseline_code, max_allowed=MAX_CYCLOMATIC_COMPLEXITY_THRESHOLD) if baseline_code else None
                base_c_map = base_rep.function_complexities if base_rep else {}

                worsened_violations = [
                    v for v in comp_rep.violations
                    if v.function_name not in base_c_map or v.complexity > base_c_map[v.function_name]
                ]

                if worsened_violations:
                    first_v = worsened_violations[0]
                    logger.warning(f"[Harness] Complejidad excesiva introducida en función '{first_v.function_name}': {first_v.complexity} > 10")
                    return (
                        VerdictStatus.REJECTED_COMPLEXITY,
                        [],
                        comp_rep.max_complexity,
                        0.0,
                        False,
                        f"Complejidad CC {first_v.complexity} > 10 introducida en función '{first_v.function_name}'",
                    )
                logger.info(f"[Harness] Deuda técnica heredada en baseline permitida (Boy Scout Rule): max_c={comp_rep.max_complexity}")
        else:
            try:
                ast.parse(candidate_test_code)
            except SyntaxError as syn_err:
                return (
                    VerdictStatus.REJECTED_AST_SIGNATURE,
                    [SignatureViolation(symbol_name="<test_syntax>", violation_type="SYNTAX_ERROR", details=str(syn_err))],
                    999,
                    0.0,
                    False,
                    f"SyntaxError in test file: {syn_err}",
                )

        if require_clean_deps and dep_diff_text and not DeterministicHarnessEvaluator.audit_dependencies(dep_diff_text):
            logger.warning("[Harness] Rechazo por deriva de dependencias externas.")
            return (VerdictStatus.REJECTED_DEPENDENCY_DRIFT, [], comp_rep.max_complexity, 0.0, False, "Deriva de dependencias externas no autorizadas")

        # 4.5 SRE and async-blocking gate (ASYNC221, zero-print, blind exceptions).
        from assessment_engine.infrastructure.auditor.probes.sre_observability import SREObservabilityVisitor
        try:
            tree_cand = ast.parse(candidate_code)
            visitor = SREObservabilityVisitor(target_file.name)
            visitor.visit(tree_cand)
            critical_sre = [f for f in visitor.findings if f.severity in ("CRITICAL", "HIGH")]
            if critical_sre:
                first = critical_sre[0]
                logger.warning(f"[Harness] Violación SRE detectada ({first.rule_id}): {first.message}")
                return (
                    VerdictStatus.REJECTED_COMPLEXITY,
                    [SignatureViolation(symbol_name=first.rule_id, violation_type="SRE_VIOLATION", details=first.message)],
                    comp_rep.max_complexity,
                    0.0,
                    False,
                    f"SRE {first.rule_id}: {first.message}",
                )
        except (SyntaxError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.debug(f"[Harness] Pre-check SRE omitido: {ex}")

        # Write code and tests temporarily for empirical validation.
        target_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(candidate_code, encoding="utf-8")
        test_file.write_text(candidate_test_code, encoding="utf-8")

        test_cmd = [sys.executable, "-B", "-m", "pytest", str(test_file), "-q"]
        src_path = str(work_dir / "src") if (work_dir / "src").is_dir() else str(work_dir)
        test_env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": f"{src_path}:{work_dir}:{os.environ.get('PYTHONPATH', '')}",
        }
        res_test = subprocess.run(
            test_cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(work_dir),
            env=test_env,
        )
        tests_passed = (res_test.returncode == 0)

        target_max_c = comp_rep.max_complexity if (is_python_target and 'comp_rep' in locals() and comp_rep) else 1

        if not tests_passed:
            err_out = (res_test.stdout + "\n" + res_test.stderr).strip()
            logger.warning(f"[Harness] Falló la suite de tests (Exit Code {res_test.returncode}):\n{err_out}")
            return (VerdictStatus.REJECTED_REGRESSION, [], target_max_c, 0.0, False, err_out)

        if is_python_target:
            mut_res = run_mutation_ctf(
                target_file=target_file,
                test_target=test_file,
                min_score=MIN_MUTATION_SCORE_THRESHOLD,
                work_dir=work_dir,
            )
            if not mut_res.passed:
                logger.warning(f"[Harness] Mutación CTF suspensa: Score={mut_res.mutation_score:.2f}")
                return (
                    VerdictStatus.REJECTED_MUTATION_SCORE,
                    [],
                    target_max_c,
                    mut_res.mutation_score,
                    True,
                    f"Mutation score {mut_res.mutation_score:.2f} < {MIN_MUTATION_SCORE_THRESHOLD}",
                )
            final_mut_score = mut_res.mutation_score
        else:
            final_mut_score = 1.0

        return (VerdictStatus.CERTIFIED, [], target_max_c, final_mut_score, True, "")


def _setup_arbiter_workspace(root: Path, use_worktree: bool) -> tuple[EphemeralWorktree | None, Path]:
    """Prepare an isolated workspace for arbitration."""
    if not use_worktree:
        return None, root
    try:
        worktree = worktree_runner.create_worktree(repo_root=root, branch_prefix="arb_task_")
        return worktree, worktree.worktree_path
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as e:
        logger.warning(f"[CognitiveArbiter] Falló worktree, operando localmente: {e}")
        return None, root


def _extract_target_function_node(code: str, target_fn_name: str) -> tuple[str, ast.AST] | None:
    """Extract the focal AST function node source code and its AST node."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target_fn_name:
                seg = ast.get_source_segment(code, node)
                if seg:
                    return seg, node
    except (SyntaxError, ValueError, TypeError) as ex:
        logger.debug(f"[CognitiveArbiter] Fallo al aislar nodo focal '{target_fn_name}': {ex}")
    return None


def _resolve_infringing_function_name(
    err_detail: str, violations: list[SignatureViolation] | None
) -> str | None:
    """Identify the offending function name from harness diagnostic or violation list."""
    if err_detail:
        m = re.search(r"función ['\"]([a-zA-Z0-9_]+)['\"]", err_detail)
        if m:
            return m.group(1)
    if violations:
        for v in violations:
            if v.symbol_name and v.symbol_name != "ARCH-DEEP-NESTING" and not v.symbol_name.startswith("Bloque"):
                return v.symbol_name
            if v.details:
                m_det = re.search(r"función ['\"]([a-zA-Z0-9_]+)['\"]", v.details)
                if m_det:
                    return m_det.group(1)
    return None


def _attempt_focal_ast_refactoring(
    synthesizer: Any,
    candidate_code: str,
    test_code: str,
    target_fn_name: str,
    err_detail: str,
) -> str | None:
    """Execute focal AST node refactoring on the offending function in isolation (<400 tokens, <3s)."""
    extracted = _extract_target_function_node(candidate_code, target_fn_name)
    if not extracted:
        return None

    fn_segment, _ = extracted
    loc_fn = len(fn_segment.splitlines())
    loc_total = len(candidate_code.splitlines())
    logger.info(
        f"[Focal AST] 🎯 Nodo aislado: '{target_fn_name}' ({loc_fn} LOC vs {loc_total} LOC del archivo). Refactorizando en aislamiento..."
    )

    prompt = (
        f"FUNCIÓN OBJETIVO A REFACTORIZAR: '{target_fn_name}'\n"
        f"CÓDIGO DE LA FUNCIÓN ({loc_fn} líneas):\n```python\n{fn_segment}\n```\n"
        f"CRÍTICA DEL HARNESS:\n{err_detail}\n\n"
        "Refactoriza ÚNICAMENTE esta función para eliminar el anidamiento profundo y la complejidad ciclomática.\n"
        "REGLAS OBLIGATORIAS:\n"
        "1. Anidamiento máximo <= 2 niveles en cualquier bloque if/for/try.\n"
        "2. Complejidad ciclomática McCabe V(G) <= 6 por función.\n"
        "3. Si necesitas descomponer la lógica, extrae funciones auxiliares a nivel de módulo y llámalas desde la función principal.\n"
        "4. Devuelve EXACTAMENTE un bloque de código Markdown ```python ... ``` con las funciones resultantes listas para reemplazar el nodo original."
    )
    sys_inst = (
        "Eres el Optimizador AST Quirúrgico Tier-1. Reescribe exclusivamente la función dada con arquitectura plana y V(G) <= 6."
    )

    raw = synthesizer._invoke_llm(prompt, system_instruction=sys_inst) if hasattr(synthesizer, "_invoke_llm") else ""
    if not raw:
        return None

    blocks = re.findall(
        r"```(?:python|py)?\s*\n?(.*?)\s*```",
        raw,
        re.DOTALL
    )
    replacement_code = blocks[0].strip() if blocks else raw.strip()

    try:
        ast.parse(replacement_code)
    except SyntaxError:
        return None

    new_candidate = candidate_code.replace(fn_segment, replacement_code, 1)
    try:
        ast.parse(new_candidate)
        logger.info(
            f"[Focal AST] ✅ Nodo '{target_fn_name}' refactorizado y ensamblado con éxito en el módulo."
        )
        return new_candidate
    except SyntaxError:
        return None


def _attempt_mcts_refactoring(
    synthesizer: Any,
    candidate_code: str,
    test_code: str,
    err_detail: str = "",
    violations: list[SignatureViolation] | None = None,
) -> str | None:
    """Attempt surgical focal AST node refactoring and MCTS search over AST to reduce complexity."""
    target_fn = _resolve_infringing_function_name(err_detail, violations)
    if target_fn:
        focal_res = _attempt_focal_ast_refactoring(
            synthesizer, candidate_code, test_code, target_fn, err_detail
        )
        if focal_res:
            return focal_res

    try:
        from assessment_engine.infrastructure.evolution.mcts_refactor_engine import MCRefactoringSearch, default_reward_function
        logger.info("[CognitiveArbiter] 🌲 Disparando MCTS Refactor Engine sobre AST para resolver complejidad...")
        searcher = MCRefactoringSearch(
            get_actions=lambda code: ["decompose_functions", "extract_helpers"],
            apply_action=lambda code, act: synthesizer.refine_patch(
                task_description=f"Refactorizar y aplanar funciones descomponiendo en helpers puros con V(G) <= 5: {act}",
                current_code=code,
                skeptic_critique="Complejidad ciclomática excesiva (V(G) > 10). Extrae funciones auxiliares pequeñas y elimina anidamientos.",
                current_test_code=test_code,
            ).get("candidate_code", code),
            reward_function=default_reward_function,
            max_iterations=1,
        )
        best_code = searcher.search(candidate_code)
        return best_code if (best_code and best_code != candidate_code) else None
    except Exception as mcts_ex:
        logger.debug(f"[CognitiveArbiter][MCTS] Búsqueda MCTS omitida: {mcts_ex}")
        return None


def _format_prescriptive_instructions(status: VerdictStatus) -> str:
    """Format prescriptive architectural instructions based on the harness failure mode."""
    if status == VerdictStatus.REJECTED_COMPLEXITY:
        return (
            "\n[INSTRUCCIÓN PRESCRIPTIVA DE COMPLEJIDAD RADON / AST]:\n"
            "- Identifica la función o método con V(G) > 10 o anidamiento > 3.\n"
            "- DEBES descomponerla extrayendo la lógica interna en funciones auxiliares independientes a nivel de módulo con V(G) <= 6.\n"
            "- Usa retornos tempranos (cláusulas de guardia) para aplanar los bloques 'if' y 'for' a un anidamiento máximo de 2 niveles.\n"
            "- La función principal debe limitarse a orquestar las llamadas a los helpers sin anidamiento profundo.\n"
        )
    if status == VerdictStatus.REJECTED_AST_SIGNATURE:
        return (
            "\n[INSTRUCCIÓN PRESCRIPTIVA DE FIRMAS AST / SINTAXIS]:\n"
            "- Se han detectado violaciones de firmas o errores de sintaxis en el código generado.\n"
            "- Si el archivo se reescribe completo, ASEGÚRATE de incluir TODAS las clases, funciones, dataclasses y constantes originales del archivo sin omitir ninguna.\n"
            "- Si utilizas parches SEARCH/REPLACE, incluye la cabecera de la función/clase y 3 a 5 líneas de contexto circundante para garantizar unicidad estricta.\n"
            "- Queda PROHIBIDO emitir formato git diff (--- a/ +++ b/).\n"
        )
    if status == VerdictStatus.REJECTED_REGRESSION:
        return (
            "\n[INSTRUCCIÓN PRESCRIPTIVA DE REGRESIÓN / TESTS]:\n"
            "- El oráculo de pruebas original provisto en EXISTING_TEST_ORACLE es INMUTABLE y define los criterios de aceptación.\n"
            "- Céntrate en reparar el código de producción para que satisfaga el oráculo sin romper pruebas existentes.\n"
            "- Si añades nuevas pruebas unitarias, éstas deben complementar el oráculo sin sustituirlo ni eliminar aserciones.\n"
        )
    return ""


def _enrich_feedback_with_diagnostics(
    feedback: str,
    status: VerdictStatus,
    err_detail: str,
    target_file: Path,
    test_file: Path,
) -> str:
    """Enrich skeptic critique with deterministic harness diagnostics, SBFL Ochiai bug localization and W3C traces."""
    enriched = feedback
    if err_detail:
        enriched += f"\n[DIAGNÓSTICO DETERMINISTA DEL HARNESS ({status.value})]:\n{err_detail[:2000]}\n"

    enriched += _format_prescriptive_instructions(status)

    if status == VerdictStatus.REJECTED_REGRESSION:
        try:
            from assessment_engine.infrastructure.evolution.fault_localizer import fault_localizer
            sbfl = fault_localizer.localize_from_pytest(target_file, test_file)
            if sbfl.most_likely_line:
                enriched += (
                    f"\n[DIAGNÓSTICO SBFL OCHIAI]: Máxima probabilidad de bug concentrada "
                    f"en línea {sbfl.most_likely_line} ({target_file.name}): "
                    f"'{sbfl.most_likely_snippet}'."
                )
        except Exception as sbfl_ex:
            logger.debug(f"[CognitiveArbiter][SBFL] Diagnóstico omitido: {sbfl_ex}")

    try:
        from assessment_engine.infrastructure.evolution.trace_conditioner import trace_conditioner
        from assessment_engine.infrastructure.chassis.context import get_current_trace_id
        trace_diag = trace_conditioner.analyze_trace_profile(
            trace_id=get_current_trace_id(),
            total_latency_ms=0.0,
        )
        trace_md = trace_diag.to_prompt_markdown()
        if trace_md:
            enriched += f"\n{trace_md}\n"
    except Exception as trace_ex:
        logger.debug(f"[CognitiveArbiter][Trace] Telemetría omitida: {trace_ex}")

    return enriched


class CognitiveArbiter:
    """Orchestrate the asymmetric dialectic, execute in an ephemeral sandbox, and emit a CognitiveArbiterReport."""

    def __init__(
        self,
        synthesizer: SynthesizerRole | None = None,
        skeptic: SkepticRole | None = None,
        harness: DeterministicHarnessEvaluator | None = None,
        max_rounds: int = MAX_DIALECTIC_ROUNDS,
    ) -> None:
        self.synthesizer = synthesizer or SynthesizerRole()
        self.skeptic = skeptic or SkepticRole()
        self.harness = harness or DeterministicHarnessEvaluator()
        self.max_rounds = max(1, max_rounds)

    def _run_dialectic_iteration(
        self,
        iteration: int,
        current_candidate: dict[str, str],
        task_description: str,
        baseline_code: str,
        target_file: Path,
        test_file: Path,
        search_context: str | None = None,
    ) -> tuple[dict[str, str], VerdictStatus, list[SignatureViolation], int, float, bool, str]:
        candidate_code = current_candidate["candidate_code"]
        test_code = current_candidate.get("test_code", "")

        status, violations, comp, mut_score, test_ok, err_detail = self.harness.evaluate_candidate(
            baseline_code=baseline_code, candidate_code=candidate_code, candidate_test_code=test_code,
            target_file=target_file, test_file=test_file,
        )

        if status == VerdictStatus.CERTIFIED:
            logger.info(f"[CognitiveArbiter] Certificado en la iteración {iteration}!")
            return current_candidate, status, violations, comp, mut_score, test_ok, ""

        search_ctx = (
            search_context
            if search_context is not None
            else self.skeptic.query_web_standards(f"Standards and edge cases for {task_description}")
        )
        skeptic_feedback = self.skeptic.critique_patch(task_description=task_description, diff_code=candidate_code, search_context=search_ctx)

        if iteration < self.max_rounds:
            skeptic_feedback = _enrich_feedback_with_diagnostics(
                skeptic_feedback, status, err_detail, target_file, test_file
            )

            if status == VerdictStatus.REJECTED_COMPLEXITY:
                best_mcts_code = _attempt_mcts_refactoring(
                    self.synthesizer, candidate_code, test_code, err_detail=err_detail, violations=violations
                )
                if best_mcts_code:
                    return {"candidate_code": best_mcts_code, "test_code": test_code}, status, violations, comp, mut_score, test_ok, skeptic_feedback

            try:
                refined_candidate = self.synthesizer.refine_patch(
                    task_description=task_description, current_code=candidate_code,
                    skeptic_critique=skeptic_feedback, current_test_code=test_code,
                )
                return refined_candidate, status, violations, comp, mut_score, test_ok, skeptic_feedback
            except SurgicalPatchError as sp_err:
                logger.warning(f"[CognitiveArbiter] Fallo aplicando parche en ronda {iteration}: {sp_err}")
                patch_err_feedback = f"{skeptic_feedback}\n\n[ERROR EN PARCHE ANTERIOR]: {sp_err}\nReemite el parche SEARCH/REPLACE copiando el bloque exacto con 3-5 líneas de contexto."
                return current_candidate, status, violations, comp, mut_score, test_ok, patch_err_feedback

        return current_candidate, status, violations, comp, mut_score, test_ok, skeptic_feedback

    def _execute_dialectic_loop(
        self,
        current_candidate: dict[str, str],
        task_description: str,
        baseline_code: str,
        target_file: Path,
        test_file: Path,
        progress_callback: Callable[[str], None] | None = None,
    ) -> tuple[int, VerdictStatus, list[SignatureViolation], int, float, bool]:
        """Execute dialectic evaluation and refinement rounds up to the maximum iteration limit."""
        iterations_used = 0
        final_status = VerdictStatus.REJECTED_REGRESSION
        ast_violations: list[SignatureViolation] = []
        max_complexity = 1
        mutation_score = 0.0
        regression_passed = False

        # Pre-fetch web standards once before entering closed loop
        frozen_search_ctx = self.skeptic.query_web_standards(f"Standards and edge cases for {task_description}")

        for iteration in range(1, self.max_rounds + 1):
            iterations_used = iteration
            if progress_callback:
                progress_callback(f"      - [Ronda {iteration}/{self.max_rounds}] Evaluando compuertas deterministas...")
            current_candidate, final_status, ast_violations, max_complexity, mutation_score, regression_passed, skeptic_feedback = self._run_dialectic_iteration(
                iteration, current_candidate, task_description, baseline_code, target_file, test_file, search_context=frozen_search_ctx
            )
            if progress_callback:
                progress_callback(f"      - [Ronda {iteration}/{self.max_rounds}] Veredicto: {final_status.value} (CC={max_complexity}, Mutación={mutation_score:.2f})")
            if final_status == VerdictStatus.CERTIFIED:
                break
            if iteration < self.max_rounds and progress_callback:
                progress_callback(f"      - [Ronda {iteration}/{self.max_rounds}] Refinando propuesta con objeciones del Escéptico...")

        return iterations_used, final_status, ast_violations, max_complexity, mutation_score, regression_passed

    def arbitrate_task(
        self,
        task_description: str,
        target_rel_path: str,
        test_rel_path: str,
        baseline_code: str,
        repo_root: Path | None = None,
        use_worktree: bool = True,
        initial_candidate: dict[str, str] | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> CognitiveArbiterReport:
        """Execute the complete dialectic pipeline with a strict limit of two iterations."""
        start_time = time.perf_counter()
        root = (repo_root or Path.cwd()).resolve()
        worktree, work_dir = _setup_arbiter_workspace(root, use_worktree)

        target_file = work_dir / target_rel_path
        test_file = work_dir / test_rel_path

        if progress_callback:
            progress_callback("      - Invocando propuesta inicial del Sintetizador (Gemini 3.1 Pro)...")

        existing_test = test_file.read_text(encoding="utf-8") if test_file.exists() else "def test_baseline(): assert True\n"
        fallback_test = initial_candidate.get("test_code", "") if (initial_candidate and initial_candidate.get("test_code")) else existing_test
        has_initial_code = bool(initial_candidate and initial_candidate.get("candidate_code"))

        final_status = VerdictStatus.REJECTED_REGRESSION
        ast_violations: list[SignatureViolation] = []
        max_complexity = 1
        mutation_score = 0.0
        regression_passed = False
        iterations_used = 1

        try:
            if not has_initial_code:
                current_candidate = self.synthesizer.propose_initial_patch(
                    task_description=task_description,
                    baseline_code=baseline_code,
                    target_file_rel=target_rel_path,
                    fallback_test_code=fallback_test,
                )
            else:
                current_candidate = initial_candidate

            iterations_used, final_status, ast_violations, max_complexity, mutation_score, regression_passed = self._execute_dialectic_loop(
                current_candidate, task_description, baseline_code, target_file, test_file, progress_callback
            )
        except (LLMTruncationError, SurgicalPatchError) as err:
            logger.error(f"[CognitiveArbiter] Fallo en síntesis de parche: {err}")
            iterations_used = 1
            is_trunc = isinstance(err, LLMTruncationError)
            final_status = VerdictStatus.REJECTED_TRUNCATION if is_trunc else VerdictStatus.REJECTED_AST_SIGNATURE
            v_type = "TRUNCATION_OVERFLOW" if is_trunc else "SURGICAL_PATCH_ERROR"
            ast_violations = [SignatureViolation(symbol_name="<llm_output>", violation_type=v_type, details=str(err))]
            max_complexity = 999
            mutation_score = 0.0
            regression_passed = False
        finally:
            if worktree and final_status != VerdictStatus.CERTIFIED:
                worktree.cleanup()

        execution_time = round(time.perf_counter() - start_time, 2)
        diff_stat = f"{len(ast_violations)} violations, {max_complexity} complexity, score={mutation_score}"

        return CognitiveArbiterReport(
            task_description=task_description, status=final_status, iterations_used=iterations_used,
            ast_violations=ast_violations, regression_tests_passed=regression_passed, total_tests_run=1 if regression_passed else 0,
            mutation_score=mutation_score, max_cyclomatic_complexity=max_complexity, diff_stat=diff_stat,
            worktree_path=worktree.worktree_path if worktree and worktree.is_active else None, execution_time_seconds=execution_time,
        )


cognitive_arbiter = CognitiveArbiter()

__all__ = [
    "LLMTruncationError",
    "MAX_CYCLOMATIC_COMPLEXITY_THRESHOLD",
    "MAX_DIALECTIC_ROUNDS",
    "MIN_MUTATION_SCORE_THRESHOLD",
    "OracleAuditReport",
    "SurgicalPatchError",
    "apply_surgical_patch",
    "CognitiveArbiter",
    "DeterministicHarnessEvaluator",
    "SkepticRole",
    "SynthesizerRole",
    "cognitive_arbiter",
]
