"""
Manage hermetic workspaces (ProjectWorkspace). Extracted from adk_lean_factory.py via the Strangler Fig pattern.
Encapsulate Bubblewrap (bwrap) sandbox isolation, Git version control,
AST inspection, surgical editing tools, and telemetry collection.
"""
from __future__ import annotations

import ast
import json
import logging
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("foundry_workspace")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FACTORY_ROOT = ROOT_DIR
WORKSPACES_ROOT = ROOT_DIR / "workspaces"
TEMPLATES_DIR = ROOT_DIR / "templates"
MEMORY_BANK_DIR = ROOT_DIR / "memory_bank"

from assessment_engine.infrastructure.config import runtime_settings
from assessment_engine.infrastructure.foundry.daemon_supervisor import (
    build_daemon_environment as _ds_build_daemon_env,
    resolve_daemon_port as _ds_resolve_daemon_port,
    poll_daemon_readiness as _ds_poll_daemon_readiness,
    start_background_service_process as _ds_start_bg_service,
    stop_background_service_process as _ds_stop_bg_service,
    http_health_check_endpoint as _ds_http_health_check,
)
from assessment_engine.infrastructure.foundry.closed_loop_evals import (
    resolve_closed_loop_target_url as _cl_resolve_target_url,
    execute_browser_snapshots as _cl_execute_snapshots,
    audit_vision_heuristics as _cl_audit_vision,
    run_closed_loop_evals_harness as _cl_run_evals,
)
from assessment_engine.infrastructure.foundry.bubblewrap_executor import (
    check_bash_security_rules as _bwrap_check_security,
    prepare_sanitized_bash_env as _bwrap_prepare_env,
    build_bubblewrap_command as _bwrap_build_cmd,
    execute_sandboxed_bash as _bwrap_execute_bash,
)
from assessment_engine.infrastructure.foundry.components.scaffold_builder import ensure_workspace_scaffold as _ensure_workspace_scaffold

PROJECT_ID = runtime_settings.cloud.project_id
LOCATION = runtime_settings.cloud.location

DEFAULT_EXECUTION_TIMEOUT = runtime_settings.factory.exec_timeout
MAX_FILE_READ_BYTES = runtime_settings.factory.max_file_read_bytes
MAX_REPO_MAP_CHARS = runtime_settings.factory.max_repo_map_chars


def _parse_python_file_ast(content: str, summary: list[str]) -> None:
    tree = ast.parse(content)
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases]
            summary.append(f"  class {node.name}({', '.join(bases)}):")
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in item.args.args]
                    ret = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                    summary.append(f"    def {item.name}({', '.join(args)}){ret}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            summary.append(f"  def {node.name}({', '.join(args)}){ret}")


def _parse_generic_file_ast(content: str, summary: list[str]) -> None:
    """Extrae declaraciones clave de archivos TypeScript, JavaScript, Go o Rust."""
    lines = content.splitlines()
    for line in lines[:60]:
        stripped = line.strip()
        if stripped.startswith((
            "export function", "export const", "export class", "export interface",
            "export type", "function ", "func ", "pub fn ", "pub struct ", "fn "
        )):
            summary.append(f"  {stripped[:100]}")


def _append_file_ast_to_summary(full_path: str, file: str, rel_path: str, summary: list[str]) -> None:
    summary.append(f"\n## File: {rel_path}")
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if file.endswith(".py"):
            _parse_python_file_ast(content, summary)
        else:
            _parse_generic_file_ast(content, summary)
    except (SyntaxError, ValueError, OSError):
        pass


class ProjectWorkspace:
    """
    Encapsulates the state, directory boundaries, physical sandboxing,
    and surgical file operations for a dedicated project workspace.
    Completely eliminates global mutable state.
    """

    def __init__(self, slug: str, root_dir: Path = WORKSPACES_ROOT):
        self.slug = slug
        self.workspace_dir = (root_dir / slug).resolve()
        self.cycle_counter = 0
        self.active_pids: set[int] = set()
        self._ensure_scaffold()
        self.last_verified_commit: str = self.get_head_sha()

    def get_head_sha(self) -> str:
        """Retrieves the current Git commit SHA of the project workspace."""
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout.strip() or "HEAD"

    def get_current_branch(self) -> str:
        """Retrieves the active Git branch name."""
        res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return res.stdout.strip() or "main"

    def create_feature_branch(self, branch_name: str) -> bool:
        """Creates and checks out an isolated feature branch for safe software evolution."""
        self.checkout_branch("main")
        res = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0

    def checkout_branch(self, branch_name: str) -> bool:
        """Checks out an existing branch."""
        res = subprocess.run(
            ["git", "checkout", branch_name],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        return res.returncode == 0

    def get_diff_against_main(self) -> str:
        """Calculates unified git diff of current branch against main."""
        res = subprocess.run(
            ["git", "--no-pager", "diff", "--no-ext-diff", "main...HEAD"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if not res.stdout.strip():
            res = subprocess.run(
                ["git", "--no-pager", "diff", "--no-ext-diff", "main"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=False
            )
        return res.stdout

    def merge_feature_to_main(self, branch_name: str) -> str:
        """Merges certified feature branch into main and updates verified checkpoint."""
        subprocess.run(["git", "add", "-A"], cwd=self.workspace_dir, capture_output=True, check=False)
        subprocess.run(["git", "commit", "-m", "chore: stage uncommitted telemetry before merge"], cwd=self.workspace_dir, capture_output=True, check=False)
        self.checkout_branch("main")
        res = subprocess.run(
            ["git", "merge", "--no-ff", branch_name, "-m", f"feat: merge {branch_name} into main"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        self.last_verified_commit = self.get_head_sha()
        subprocess.run(["git", "branch", "-d", branch_name], cwd=self.workspace_dir, capture_output=True, check=False)
        return res.stdout or f"Merged {branch_name} into main."

    def discard_feature_branch(self, branch_name: str) -> bool:
        """Discards an unapproved feature branch and restores main cleanly."""
        self.checkout_branch("main")
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self.workspace_dir, capture_output=True, check=False)
        res = subprocess.run(["git", "branch", "-D", branch_name], cwd=self.workspace_dir, capture_output=True, check=False)
        return res.returncode == 0

    def get_blast_radius(self) -> dict[str, Any]:
        """Calculates the exact blast radius of current working tree changes via Git telemetry."""
        res_files = subprocess.run(
            ["git", "diff", "HEAD", "--name-only"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        res_stat = subprocess.run(
            ["git", "diff", "HEAD", "--shortstat"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        files = [f for f in res_files.stdout.splitlines() if f.strip()]
        stat = res_stat.stdout.strip()
        return {"changed_files": files, "shortstat": stat or "0 files changed"}

    def cleanup_background_processes(self) -> None:
        """Reaps all active background child daemons launched during execution (Zero Zombies)."""
        for pid in list(self.active_pids):
            self.stop_background_service(pid)
        self.active_pids.clear()

    def _ensure_scaffold(self) -> None:
        """Initializes the enterprise repository layout and baseline Git structure."""
        _ensure_workspace_scaffold(self.workspace_dir, TEMPLATES_DIR)

    def _resolve_safe_path(self, relative_path: str) -> Path | None:
        """Prevents CWE-22 Path Traversal by ensuring the resolved target is within the workspace."""
        try:
            target = (self.workspace_dir / relative_path).resolve()
            return target if target.is_relative_to(self.workspace_dir) else None
        except (ValueError, OSError):
            return None

    def append_veritas_receipt(self, event_type: str, details: dict[str, Any], status: str) -> None:
        """Appends an immutable audit receipt to the project's Veritas Ledger."""
        ledger_path = self.workspace_dir / "docs" / "VERITAS_LEDGER.jsonl"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        receipt = {
            "timestamp": int(time.time()),
            "event_type": event_type,
            "status": status,
            "details": details
        }
        try:
            with open(ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(receipt, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.debug(f"Failed to append Veritas receipt: {e}")

    def ensure_virtualenv(self) -> Path:
        """Provisions a hermetic .venv in the workspace in <50ms using Astral uv if available."""
        venv_dir = self.workspace_dir / ".venv"
        if not venv_dir.exists():
            uv_bin = FACTORY_ROOT / "venv" / "bin" / "uv"
            if uv_bin.exists():
                subprocess.run([str(uv_bin), "venv", str(venv_dir)], cwd=self.workspace_dir, capture_output=True, check=False)
            else:
                subprocess.run(["python3", "-m", "venv", str(venv_dir)], cwd=self.workspace_dir, capture_output=True, check=False)
        return venv_dir

    def install_dependencies(self, packages: list[str]) -> str:
        """Installs dependencies into workspace .venv hermetically using uv pip in milliseconds."""
        venv_dir = self.ensure_virtualenv()
        if not packages:
            return "No packages requested"
        uv_bin = FACTORY_ROOT / "venv" / "bin" / "uv"
        python_bin = venv_dir / "bin" / "python"
        if uv_bin.exists():
            cmd = [str(uv_bin), "pip", "install", "--python", str(python_bin)] + packages
        else:
            cmd = [str(venv_dir / "bin" / "pip"), "install"] + packages
        res = subprocess.run(cmd, cwd=self.workspace_dir, capture_output=True, text=True, check=False)
        return res.stdout or res.stderr


    def _check_bash_security_rules(self, command: str) -> str | None:
        """Check for destructive commands, GCP metadata SSRF, and host credentials."""
        err_msg, reason = _bwrap_check_security(command)
        if err_msg and reason:
            self.append_veritas_receipt("SECURITY_ALERT", {"reason": reason, "command": command[:100]}, "BLOCKED")
        return err_msg

    def _prepare_sanitized_bash_env(self) -> dict[str, str]:
        """Sanitize environment variables and route local virtual environment PATHs."""
        return _bwrap_prepare_env(self.workspace_dir, FACTORY_ROOT)

    def _build_bubblewrap_command(self, bwrap_bin: str, command: str) -> list[str]:
        """Build the hermetic Bubblewrap command with tmpfs over sensitive paths."""
        return _bwrap_build_cmd(bwrap_bin, self.workspace_dir, FACTORY_ROOT, command)

    def execute_bash(self, command: str) -> str:
        """Executes a bash shell command within the project workspace using Linux Bubblewrap isolation and Execution Guard."""
        sec_err = self._check_bash_security_rules(command)
        if sec_err:
            return sec_err
        return _bwrap_execute_bash(self.workspace_dir, FACTORY_ROOT, command, DEFAULT_EXECUTION_TIMEOUT)

    def write_file(self, relative_path: str, content: str) -> str:
        """Writes complete content to a file in the workspace. Best for creating new files."""
        target = self._resolve_safe_path(relative_path)
        if not target:
            return "SECURITY_ERROR: Access outside workspace denied (Path Traversal)."

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        if relative_path.startswith("scripts/"):
            target.chmod(0o755)
        return f"SUCCESS: File '{relative_path}' written ({len(content)} characters)."

    def replace_in_file(self, relative_path: str, old_string: str, new_string: str) -> str:
        """Surgically replaces an exact code block in an existing file with tolerant line matching fallback."""
        target = self._resolve_safe_path(relative_path)
        if not target:
            return "SECURITY_ERROR: Access outside workspace denied (Path Traversal)."
        if not target.exists():
            return f"ERROR: File '{relative_path}' does not exist."

        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        content_norm = content.replace("\r\n", "\n")
        old_norm = old_string.replace("\r\n", "\n")
        new_norm = new_string.replace("\r\n", "\n")

        # 1. Exact matching (Fast path)
        count = content_norm.count(old_norm)
        if count == 1:
            new_content = content_norm.replace(old_norm, new_norm, 1)
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_content)
            saved_chars = len(content) - len(new_string)
            return f"SUCCESS: Surgical patch applied to '{relative_path}' (Saved {max(0, saved_chars)} output characters)."
        if count > 1:
            return f"ERROR: 'old_string' matched {count} times in '{relative_path}'. Provide additional surrounding context."

        content_lines = content_norm.splitlines(keepends=True)
        old_lines = [line.strip() for line in old_norm.splitlines() if line.strip()]

        if not old_lines:
            return f"ERROR: 'old_string' contains no non-empty lines in '{relative_path}'."

        match_start = -1
        match_end = -1
        matches_found = 0

        for i in range(len(content_lines) - len(old_lines) + 1):
            window = [content_lines[i + j].strip() for j in range(len(old_lines))]
            if window == old_lines:
                matches_found += 1
                match_start = i
                match_end = i + len(old_lines)

        if matches_found == 1:
            replacement_lines = new_norm.splitlines(keepends=True)
            if replacement_lines and not replacement_lines[-1].endswith("\n"):
                replacement_lines[-1] += "\n"
            new_lines = content_lines[:match_start] + replacement_lines + content_lines[match_end:]
            new_content = "".join(new_lines)
            with open(target, "w", encoding="utf-8") as f:
                f.write(new_content)
            saved_chars = len(content) - len(new_string)
            return f"SUCCESS: Tolerant whitespace patch applied to '{relative_path}' (Saved {max(0, saved_chars)} output characters)."

        if matches_found > 1:
            return f"ERROR: Tolerant line search matched {matches_found} locations in '{relative_path}'. Provide additional surrounding context."

        return f"ERROR: 'old_string' not found in '{relative_path}' even with tolerant line matching. Check exact code content."

    def read_file(self, relative_path: str) -> str:
        """Reads the content of a file in the workspace, with explicit truncation alert if exceeds boundary."""
        target = self._resolve_safe_path(relative_path)
        if not target:
            return "SECURITY_ERROR: Access outside workspace denied (Path Traversal)."
        if not target.exists():
            return f"ERROR: File '{relative_path}' does not exist."

        with open(target, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(MAX_FILE_READ_BYTES)
            if f.read(1):
                content += f"\n... [WARNING: File truncated at {MAX_FILE_READ_BYTES} bytes. Use targeted reads/searches] ..."
            return content

    def list_files(self, relative_path: str = ".") -> str:
        """Lists directory structure and tracked files within the workspace."""
        target = self._resolve_safe_path(relative_path)
        if not target:
            return "SECURITY_ERROR: Access outside workspace denied."
        tree = []
        for root, _, files in os.walk(target):
            if any(p in root for p in [".git", "__pycache__", "venv", ".venv"]):
                continue
            rel = os.path.relpath(root, self.workspace_dir)
            for fl in sorted(files):
                tree.append(os.path.join(rel, fl))
        return json.dumps(tree[:150], indent=2)

    def get_repo_map(self, target_dir: str = ".") -> str:
        """Extracts a compact semantic symbol map of the repository using AST parsing."""
        target = self._resolve_safe_path(target_dir)
        if not target or not target.exists():
            return "SECURITY_ERROR: Target path does not exist or is outside workspace."

        summary = ["# REPOSITORY AST SYMBOL MAP:"]
        for root, _, files in os.walk(target):
            if any(p in root for p in [".git", "__pycache__", "venv", ".venv", "node_modules"]):
                continue
            for file in sorted(files):
                if not file.endswith((".py", ".ts", ".js", ".go", ".rs")):
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), self.workspace_dir)
                full_path = os.path.join(root, file)
                _append_file_ast_to_summary(full_path, file, rel_path, summary)

        return "\n".join(summary)[:MAX_REPO_MAP_CHARS]

    def _extract_ast_signatures(self, code: str) -> dict[str, dict[str, Any]]:
        """Extract AST signatures of public classes and functions."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {}
        sigs: dict[str, dict[str, Any]] = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_"):
                        all_args = [a.arg for a in item.args.args if a.arg not in ("self", "cls")]
                        def_cnt = len(item.args.defaults)
                        req_args = all_args[:-def_cnt] if def_cnt > 0 else all_args
                        sigs[f"{node.name}.{item.name}"] = {"all_args": all_args, "required_args": req_args}
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                all_args = [a.arg for a in node.args.args]
                def_cnt = len(node.args.defaults)
                req_args = all_args[:-def_cnt] if def_cnt > 0 else all_args
                sigs[node.name] = {"all_args": all_args, "required_args": req_args}
        return sigs

    def _check_symbol_drift(
        self, symbol: str, old_meta: dict[str, Any], new_meta: dict[str, Any], rel: str
    ) -> list[str]:
        """Detect backward compatibility breaks in required arguments."""
        violations: list[str] = []
        old_req = old_meta["required_args"]
        new_req = new_meta["required_args"]
        if len(new_req) > len(old_req):
            violations.append(
                f"BREAKING_SIGNATURE_EXPANSION: In '{rel}', '{symbol}' added new required arguments without defaults (was {old_req}, now {new_req})."
            )
        elif old_req != new_req[:len(old_req)]:
            violations.append(
                f"SIGNATURE_CONTRACT_MUTATION: In '{rel}', '{symbol}' required parameters changed from {old_req} to {new_req}."
            )
        return violations

    def verify_public_api_invariants(self) -> list[str]:
        """
        Verify that no public interface in HEAD has mutated or been removed.
        """
        violations: list[str] = []
        src_dir = self.workspace_dir / "src"
        if not src_dir.exists():
            return []

        for py_file in src_dir.rglob("*.py"):
            rel = py_file.relative_to(self.workspace_dir).as_posix()
            res = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=self.workspace_dir, capture_output=True, text=True, check=False)
            if res.returncode != 0 or not res.stdout.strip():
                continue

            old_sigs = self._extract_ast_signatures(res.stdout)
            try:
                new_code = py_file.read_text(encoding="utf-8", errors="ignore")
                new_sigs = self._extract_ast_signatures(new_code)
            except OSError:
                continue

            for symbol, old_meta in old_sigs.items():
                if symbol not in new_sigs:
                    violations.append(f"REMOVED_PUBLIC_API: In '{rel}', public symbol '{symbol}' was deleted.")
                else:
                    violations.extend(self._check_symbol_drift(symbol, old_meta, new_sigs[symbol], rel))
        return violations

    def purge_ephemeral_debris(self) -> list[str]:
        """Zero-Entropy Guard: Automatically purges root scratchpad scripts and temporary files before committing to Git."""
        purged = []
        for fl in self.workspace_dir.iterdir():
            if not fl.is_file():
                continue
            is_scratchpad = fl.name.startswith("test_") and fl.name.endswith(".py")
            is_temp = fl.suffix in (".tmp", ".temp", ".swp", ".bak")
            if is_scratchpad or is_temp:
                try:
                    fl.unlink()
                    purged.append(fl.name)
                    if is_scratchpad:
                        logger.info(f"Purged root scratchpad script: {fl.name}")
                except OSError:
                    pass
        return purged

    def _resolve_closed_loop_target_url(self) -> str | None:
        """Determine the local daemon URL or static file to audit with Playwright."""
        return _cl_resolve_target_url(self.workspace_dir)

    def _execute_browser_snapshots(
        self, target_url: str, desktop_shot: Path, mobile_shot: Path
    ) -> tuple[dict[str, Any], int, str, list[str], list[str], list[str]]:
        """Launch headless Chromium, capture desktop/mobile views, and collect telemetry."""
        return _cl_execute_snapshots(target_url, desktop_shot, mobile_shot)

    def _audit_vision_heuristics(self, desktop_shot: Path, mobile_shot: Path, docs_dir: Path) -> dict[str, Any]:
        """Execute the heuristic multimodal audit with Gemini Vision."""
        return _cl_audit_vision(desktop_shot, mobile_shot, docs_dir)

    def run_closed_loop_evals(self) -> dict[str, Any]:
        """Tier 1 Closed-Loop Multimodal Evals Harness (Anthropic / DeepMind Standard)."""
        return _cl_run_evals(self.workspace_dir)

    def verify_harness_integrity(self) -> list[str]:
        """Anti-Workaround Guard: Ensures scripts/verify.sh was not weakened by patching inline permissive flags."""
        verify_script = self.workspace_dir / "scripts" / "verify.sh"
        if not verify_script.exists():
            return ["MISSING_HARNESS: scripts/verify.sh does not exist."]

        res = subprocess.run(
            ["git", "--no-pager", "diff", "--no-ext-diff", "HEAD", "--", "scripts/verify.sh"],
            cwd=self.workspace_dir,
            capture_output=True,
            text=True,
            check=False
        )
        if not res.stdout:
            return []

        violations = []
        for line in res.stdout.splitlines():
            if not line.startswith("+") or line.startswith("+++"):
                continue
            trimmed = line[1:].strip()
            if "|| true" in trimmed or ("--ignore" in trimmed and "--ignore S101" not in trimmed):
                violations.append(
                    f"HARNESS_WORKAROUND_MUTATION: Unauthorized weakening of scripts/verify.sh: '{trimmed}'. "
                    "Linters and rules must be configured in pyproject.toml, never patched in verify.sh."
                )
        return violations

    def synthesize_antibody(self, failure_trace: str) -> str | None:
        """Autopsy Engine: Synthesizes a real minimal regression antibody test from failure traces."""
        if "Traceback (most recent call last)" not in failure_trace and "FAILED " not in failure_trace:
            return None

        autopsy_dir = self.workspace_dir / "tests" / "autopsy"
        autopsy_dir.mkdir(parents=True, exist_ok=True)
        antibody_path = autopsy_dir / "test_antibody_regression.py"

        try:
            flash_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
            prompt = (
                "You are an Elite SRE & Test Synthesis Engine. Given the following failure trace from a test run, "
                "write a minimal, standalone Pytest test function (in Python) that reproduces the failure scenario "
                "so that it acts as a regression antibody.\n"
                "Requirements:\n"
                "- Write ONLY valid Python code inside standard pytest format.\n"
                "- Import necessary modules from 'src' or standard library.\n"
                "- Clearly label '# --- ARRANGE ---', '# --- ACT ---', and '# --- ASSERT ---'.\n"
                "- Do NOT use markdown code fences.\n\n"
                f"FAILURE TRACE:\n{failure_trace[:2000]}"
            )
            resp = flash_client.models.generate_content(
                model=get_model(ModelTier.FAST),
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1)
            )
            raw_code = (resp.text or "").strip()
            raw_code = re.sub(r"^```python\s*|^```\s*|```$", "", raw_code, flags=re.MULTILINE).strip()
            ast.parse(raw_code)

            header = (
                f'"""\n'
                f'AUTOPSY REPRODUCTION ANTIBODY (CYCLE {self.cycle_counter})\n'
                f'Synthesized by Gemini Flash from Quality Gate failure.\n'
                f'"""\n'
            )
            antibody_path.write_text(header + raw_code + "\n", encoding="utf-8")
            return "tests/autopsy/test_antibody_regression.py"
        except (RuntimeError, ValueError, OSError, SyntaxError) as e:
            logger.debug(f"Autopsy antibody synthesis skipped: {e}")
            return None

    def _build_daemon_environment(self) -> dict[str, str]:
        """Build a clean environment for background processes by purging secrets."""
        return _ds_build_daemon_env(self.workspace_dir, FACTORY_ROOT)

    def _resolve_daemon_port(self, command: str, port: int | None) -> tuple[int | None, str]:
        """Detect or dynamically reassign an available port if the requested port is occupied."""
        return _ds_resolve_daemon_port(command, port)

    def _poll_daemon_readiness(
        self, proc: Any, target_port: int, log_path: Path, log_file: str, timeout_seconds: int
    ) -> str:
        """Poll the daemon TCP socket until initialization completes."""
        return _ds_poll_daemon_readiness(proc, target_port, log_path, log_file, timeout_seconds)

    def start_background_service(self, command: str, port: int | None = None, log_file: str = "service.log", timeout_seconds: int = 15) -> str:
        """Starts a background server/daemon with active TCP socket readiness polling."""
        return _ds_start_bg_service(self.workspace_dir, FACTORY_ROOT, self.active_pids, command, port, log_file, timeout_seconds)

    def stop_background_service(self, pid: int) -> str:
        """Gracefully terminates a process group with SIGTERM and automatic SIGKILL escalation."""
        return _ds_stop_bg_service(self.active_pids, pid)

    def http_health_check(self, url: str, expected_status: int = 200, timeout_seconds: int = 10) -> str:
        """Performs a grounded HTTP GET check against a local service to verify real response payload."""
        return _ds_http_health_check(url, expected_status, timeout_seconds)
