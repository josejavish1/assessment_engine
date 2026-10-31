"""Ironclad Adversarial Quality Gate Architecture.

Enforces deterministic AST pre-screening and stateless adversarial verification
via gemini-4-argon (ModelTier.REASONING) before any code block can be committed.
"""

from __future__ import annotations

import ast
import hashlib
import hmac
import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Final, List, Optional, Sequence

from google.genai import types
from pydantic import BaseModel, Field

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

logger = logging.getLogger(__name__)


class AuditVerdict(str, Enum):
    """Strict binary outcome for the quality gate."""
    PASS = "PASS"
    FAIL = "FAIL"


class ViolationCategory(str, Enum):
    """Taxonomic classification of code audit failures."""
    BUG_OR_LOGIC_ERROR = "BUG_OR_LOGIC_ERROR"
    ARCHITECTURAL_ANTIPATTERN = "ARCHITECTURAL_ANTIPATTERN"
    HARDCODED_VALUE_OR_ASSUMPTION = "HARDCODED_VALUE_OR_ASSUMPTION"
    NON_ENGLISH_LEXICON = "NON_ENGLISH_LEXICON"
    SINGLE_TENANT_OR_VERTICAL_COUPLING = "SINGLE_TENANT_OR_VERTICAL_COUPLING"
    SECURITY_OR_CONCURRENCY_FLAW = "SECURITY_OR_CONCURRENCY_FLAW"


class AuditFinding(BaseModel):
    """Granular representation of a single defect identified during review."""
    file_path: str = Field(
        ..., description="Relative path to the file containing the defect."
    )
    line_number: int = Field(
        ..., description="Approximate line number where the violation occurs."
    )
    category: ViolationCategory = Field(
        ..., description="Strict classification of the violation."
    )
    offending_snippet: str = Field(
        ..., description="Exact code snippet exhibiting the flaw."
    )
    technical_critique: str = Field(
        ..., description="Deep forensic explanation of why this violates Tier-1 standards."
    )
    mandatory_remediation: str = Field(
        ..., description="Exact engineering instruction required to fix the defect."
    )


class ArgonAuditReport(BaseModel):
    """Deterministic structured output contract required from gemini-4-argon."""
    verdict: AuditVerdict = Field(
        ..., description="Final gate decision. Must be FAIL if any finding exists."
    )
    zero_bugs_or_antipatterns: bool = Field(
        ..., description="True if and only if zero bugs, race conditions, or antipatterns exist."
    )
    zero_hardcoding_verified: bool = Field(
        ..., description="True if and only if zero magic numbers, hardcoded URLs, or fixed tenant rules exist."
    )
    universal_tier1_enterprise_ready: bool = Field(
        ..., description="True if and only if the code scales from mid-market to global Tier-1 across any vertical and locale."
    )
    strict_english_only_verified: bool = Field(
        ..., description="True if and only if 100% of identifiers, comments, docstrings, and schemas are in formal English."
    )
    findings: List[AuditFinding] = Field(
        default_factory=list,
        description="Exhaustive list of all defects discovered. Must be empty for PASS."
    )
    forensic_summary: str = Field(
        ..., description="Executive architectural assessment of the submitted changes."
    )


@dataclass(frozen=True)
class CryptographicClearanceToken:
    """Unforgeable proof of audit passage bound to the exact git diff state."""
    block_id: str
    diff_sha256: str
    model_used: str
    timestamp_utc: float
    signature: str

    def verify(self, secret_key: bytes, current_diff_sha256: str) -> bool:
        """Verifies token authenticity and ensures working tree has not mutated post-audit."""
        if not hmac.compare_digest(self.diff_sha256, current_diff_sha256):
            return False
        payload = f"{self.block_id}:{self.diff_sha256}:{self.model_used}:{self.timestamp_utc}".encode("utf-8")
        expected_sig = hmac.new(secret_key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(self.signature, expected_sig)


class QualityGateBypassAttemptError(RuntimeError):
    """Raised when a state transition is attempted without a valid clearance token."""


class QualityGateExhaustedError(RuntimeError):
    """Raised when the coder fails to satisfy gemini-4-argon within max remediation cycles."""


class DeterministicPreFlightSieve:
    """Executes fast, deterministic AST and lexical checks on modified files prior to LLM audit."""

    _PROHIBITED_DIACRITICS: Final[re.Pattern[str]] = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
    _PROHIBITED_SPANISH_TOKENS: Final[re.Pattern[str]] = re.compile(
        r"\b(función|clase|retornar|usuario|empresa|configuración|datos|archivo|"
        r"procesar|calcular|obtener|lista|diccionario|error_de|validar|ejecutar|"
        r"respuesta|solicitud|cliente|proveedor|facturación|impuesto|moneda)\b",
        re.IGNORECASE,
    )
    _HARDCODED_ARTIFACT_PATTERN: Final[re.Pattern[str]] = re.compile(
        r"(https?://(?!localhost|127\.0\.0\.1)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})|"
        r"(/Users/[a-zA-Z0-9_-]+/)|(/home/[a-zA-Z0-9_-]+/)"
    )

    @classmethod
    def inspect_files(cls, repo_root: Path, modified_files: Sequence[str]) -> List[AuditFinding]:
        """Runs lexical and AST inspections across all touched files."""
        findings: List[AuditFinding] = []

        for rel_path in modified_files:
            full_path = repo_root / rel_path
            if not full_path.exists() or not full_path.is_file():
                continue
            if full_path.suffix not in {".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".sql"}:
                continue

            try:
                content = full_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            findings.extend(cls._check_lines(rel_path, content))
            if full_path.suffix == ".py":
                findings.extend(cls._check_python_ast(rel_path, content))

        return findings

    @classmethod
    def _check_lines(cls, rel_path: str, content: str) -> List[AuditFinding]:
        findings: List[AuditFinding] = []
        for idx, line in enumerate(content.splitlines(), start=1):
            if cls._PROHIBITED_DIACRITICS.search(line) or cls._PROHIBITED_SPANISH_TOKENS.search(line):
                findings.append(
                    AuditFinding(
                        file_path=rel_path,
                        line_number=idx,
                        category=ViolationCategory.NON_ENGLISH_LEXICON,
                        offending_snippet=line.strip()[:120],
                        technical_critique="Detected non-English characters or Spanish vocabulary in source file.",
                        mandatory_remediation="Translate all identifiers, comments, docstrings, and literals to 100% formal English.",
                    )
                )
            if cls._HARDCODED_ARTIFACT_PATTERN.search(line) and "schema.org" not in line and "w3.org" not in line:
                findings.append(
                    AuditFinding(
                        file_path=rel_path,
                        line_number=idx,
                        category=ViolationCategory.HARDCODED_VALUE_OR_ASSUMPTION,
                        offending_snippet=line.strip()[:120],
                        technical_critique="Detected hardcoded external URI or absolute local filesystem path.",
                        mandatory_remediation="Externalize endpoints and paths into injected configuration or environment settings.",
                    )
                )
        return findings

    @classmethod
    def _check_python_ast(cls, rel_path: str, content: str) -> List[AuditFinding]:
        findings: List[AuditFinding] = []
        try:
            tree = ast.parse(content, filename=rel_path)
        except SyntaxError as exc:
            findings.append(
                AuditFinding(
                    file_path=rel_path,
                    line_number=exc.lineno or 1,
                    category=ViolationCategory.BUG_OR_LOGIC_ERROR,
                    offending_snippet=exc.text.strip() if exc.text else "SyntaxError",
                    technical_critique=f"File fails Python AST compilation: {exc.msg}",
                    mandatory_remediation="Fix syntax error so module compiles cleanly.",
                )
            )
            return findings

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                findings.append(
                    AuditFinding(
                        file_path=rel_path,
                        line_number=node.lineno,
                        category=ViolationCategory.ARCHITECTURAL_ANTIPATTERN,
                        offending_snippet="except:",
                        technical_critique="Bare 'except:' clause swallows system signals and masks critical bugs.",
                        mandatory_remediation="Catch explicit exception subclasses and preserve stack trace context.",
                    )
                )
        return findings


class ArgonIroncladQualityGate:
    """Zero-Bypass Adversarial Audit Gate powered by gemini-4-argon (ModelTier.REASONING)."""

    _ADVERSARIAL_SYSTEM_PROMPT: Final[str] = """
You are a Hostile Principal Systems Architect and Chief Code Auditor (Google Tier-1 / Anthropic Infrastructure grade).
Your sole objective is to perform an uncompromising, forensic audit of the submitted code changes and REJECT anything that is less than 100% production-perfect.

Do NOT be polite. Do NOT give the benefit of the doubt. Do NOT rubber-stamp code.

You must evaluate the code against four non-negotiable mandates:
1. ZERO BUGS, FLAWS, OR ANTIPATTERNS:
   - Hunt down race conditions, unhandled edge cases, silent failures, N+1 queries, memory leaks, improper exception handling, type unsafety, and tight coupling.
2. ZERO HARDCODING (100% DYNAMIC & CONFIG-DRIVEN):
   - Reject any magic numbers, hardcoded business thresholds, fixed company names, static currency codes, hardcoded prompts where configuration belongs, or fixed file paths.
3. UNIVERSAL GLOBAL ENTERPRISE APPLICABILITY:
   - The software MUST seamlessly serve any company in the world—from mid-market to Global Fortune 500 Tier-1—across ANY industry vertical, jurisdiction, and output language/locale.
   - Reject any logic that assumes a single country's tax/legal framework, a single industry's terminology, or single-tenant execution.
4. 100% STRICT ENGLISH CODEBASE MANDATE:
   - Every single variable name, function identifier, class name, docstring, inline comment, log message, exception string, and schema key MUST be in 100% formal Technical English.
   - Zero Spanish words are permitted anywhere in the code or schemas. (Spanish is exclusively one of the dynamic runtime deliverable output languages, never a codebase language).

DECISION PROTOCOL:
- If you find even a SINGLE violation of any mandate above, you MUST set `verdict` to "FAIL", set the corresponding boolean invariant to `false`, and populate `findings` with the exact file, line number, offending snippet, technical critique, and mandatory fix.
- You may ONLY set `verdict` to "PASS" if and only if `findings` is completely empty and all four boolean invariants are `true`.
""".strip()

    def __init__(
        self,
        repo_root: Path,
        secret_key: bytes,
        max_remediation_attempts: int = 5,
    ) -> None:
        self._repo_root = repo_root.resolve()
        self._secret_key = secret_key
        self._max_attempts = max_remediation_attempts
        self._client = create_genai_client()
        self._model_name = get_model(ModelTier.REASONING)

    def enforce_gate(
        self,
        block_id: str,
        block_specification: str,
        remediation_callback: Callable[[str], None],
    ) -> CryptographicClearanceToken:
        """Executes the audit-remediation loop for a completed work block."""
        for attempt in range(1, self._max_attempts + 1):
            logger.info(
                "Initiating Argon Ironclad Audit for block '%s' (Attempt %d/%d) using model '%s'.",
                block_id,
                attempt,
                self._max_attempts,
                self._model_name,
            )

            diff_text, modified_files, diff_hash = self._extract_working_tree_state()
            if not diff_text.strip():
                raise QualityGateBypassAttemptError(
                    f"Block '{block_id}' produced an empty git diff. Cannot audit empty changeset."
                )

            # Step 1: Deterministic Static Pre-Sieve
            static_findings = DeterministicPreFlightSieve.inspect_files(self._repo_root, modified_files)
            if static_findings:
                logger.warning(
                    "Deterministic Pre-Flight Sieve rejected block '%s' with %d violation(s).",
                    block_id,
                    len(static_findings),
                )
                remediation_prompt = self._build_remediation_prompt(
                    block_id=block_id,
                    attempt=attempt,
                    summary="Rejected by Deterministic AST & Lexical Pre-Flight Sieve prior to LLM audit.",
                    findings=static_findings,
                )
                self._handle_rejection(block_id, attempt, remediation_prompt, remediation_callback)
                continue

            # Step 2: Stateless Adversarial Audit via gemini-4-argon
            audit_report = self._invoke_argon_auditor(
                block_id=block_id,
                block_specification=block_specification,
                diff_text=diff_text,
                modified_files=modified_files,
            )

            # Step 3: Mechanical Verification of the Audit Report
            if self._is_mathematically_approved(audit_report):
                _, _, post_audit_diff_hash = self._extract_working_tree_state()
                if not hmac.compare_digest(diff_hash, post_audit_diff_hash):
                    raise QualityGateBypassAttemptError(
                        "Working tree mutated during Argon audit execution (TOCTOU violation)."
                    )

                logger.info(
                    "Block '%s' FORMALLY APPROVED by %s on attempt %d.",
                    block_id,
                    self._model_name,
                    attempt,
                )
                return self._mint_clearance_token(block_id, diff_hash)

            # Step 4: Rejection & Self-Healing Remediation Trigger
            logger.warning(
                "Argon rejected block '%s' on attempt %d with %d finding(s). Summary: %s",
                block_id,
                attempt,
                len(audit_report.findings),
                audit_report.forensic_summary,
            )
            remediation_prompt = self._build_remediation_prompt(
                block_id=block_id,
                attempt=attempt,
                summary=audit_report.forensic_summary,
                findings=audit_report.findings,
            )
            self._handle_rejection(block_id, attempt, remediation_prompt, remediation_callback)

        raise QualityGateExhaustedError(f"Exhausted remediation attempts for block '{block_id}'.")

    def _invoke_argon_auditor(
        self,
        block_id: str,
        block_specification: str,
        diff_text: str,
        modified_files: Sequence[str],
    ) -> ArgonAuditReport:
        full_file_contexts = self._read_full_files_context(modified_files)

        user_audit_payload = (
            f"### ARCHITECTURAL BLOCK ID: {block_id}\n\n"
            f"### TARGET SPECIFICATION:\n{block_specification}\n\n"
            f"### UNIFIED GIT DIFF:\n```diff\n{diff_text}\n```\n\n"
            f"### COMPLETE CONTENT OF MODIFIED FILES (FOR FULL CONTEXT):\n{full_file_contexts}\n\n"
            "Execute a complete forensic review now. Search exhaustively for bugs, race conditions, "
            "antipatterns, hardcoded values, single-tenant assumptions, or any non-English words."
        )

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=user_audit_payload,
            config=types.GenerateContentConfig(
                system_instruction=self._ADVERSARIAL_SYSTEM_PROMPT,
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=ArgonAuditReport,
            ),
        )

        if not response.text:
            raise RuntimeError(f"Empty response received from {self._model_name} during audit.")

        data = json.loads(response.text)
        return ArgonAuditReport.model_validate(data)

    @staticmethod
    def _is_mathematically_approved(report: ArgonAuditReport) -> bool:
        return (
            report.verdict == AuditVerdict.PASS
            and report.zero_bugs_or_antipatterns is True
            and report.zero_hardcoding_verified is True
            and report.universal_tier1_enterprise_ready is True
            and report.strict_english_only_verified is True
            and len(report.findings) == 0
        )

    def _handle_rejection(
        self,
        block_id: str,
        attempt: int,
        remediation_prompt: str,
        remediation_callback: Callable[[str], None],
    ) -> None:
        if attempt >= self._max_attempts:
            logger.error(
                "Block '%s' failed audit after maximum (%d) attempts. Executing immutable git rollback.",
                block_id,
                self._max_attempts,
            )
            self._rollback_working_tree()
            raise QualityGateExhaustedError(
                f"Block '{block_id}' failed to achieve 100% approval from {self._model_name} "
                f"after {self._max_attempts} attempts. Working tree rolled back."
            )

        remediation_callback(remediation_prompt)

    @staticmethod
    def _build_remediation_prompt(
        block_id: str,
        attempt: int,
        summary: str,
        findings: Sequence[AuditFinding],
    ) -> str:
        lines = [
            f"CRITICAL AUDIT REJECTION — BLOCK: {block_id} (Attempt {attempt})",
            f"AUDITOR SUMMARY: {summary}",
            "",
            "Your implementation was REJECTED by the gemini-4-argon Quality Gate.",
            "You MUST resolve every single finding listed below without introducing regressions,",
            "hardcoded values, or non-English tokens:",
            "",
        ]
        for idx, finding in enumerate(findings, start=1):
            lines.extend([
                f"--- FINDING #{idx} [{finding.category.value}] ---",
                f"File: {finding.file_path} (Line ~{finding.line_number})",
                f"Offending Code: `{finding.offending_snippet}`",
                f"Critique: {finding.technical_critique}",
                f"Mandatory Fix: {finding.mandatory_remediation}",
                "",
            ])
        return "\n".join(lines)

    def _extract_working_tree_state(self) -> tuple[str, List[str], str]:
        subprocess.run(
            ["git", "add", "-N", "."],
            cwd=self._repo_root,
            check=True,
            capture_output=True,
        )
        diff_proc = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=self._repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        names_proc = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=self._repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
        diff_text = diff_proc.stdout
        modified_files = [line.strip() for line in names_proc.stdout.splitlines() if line.strip()]
        diff_hash = hashlib.sha256(diff_text.encode("utf-8")).hexdigest()
        return diff_text, modified_files, diff_hash

    def _read_full_files_context(self, modified_files: Sequence[str]) -> str:
        blocks: List[str] = []
        for rel_path in modified_files:
            full_path = self._repo_root / rel_path
            if not full_path.exists() or not full_path.is_file():
                continue
            try:
                raw_lines = full_path.read_text(encoding="utf-8").splitlines()
                numbered = "\n".join(f"{i:04d} | {line}" for i, line in enumerate(raw_lines, start=1))
                blocks.append(f"#### FILE: {rel_path}\n```\n{numbered}\n```")
            except UnicodeDecodeError:
                continue
        return "\n\n".join(blocks)

    def _rollback_working_tree(self) -> None:
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=self._repo_root, check=True)
        subprocess.run(["git", "clean", "-fd"], cwd=self._repo_root, check=True)

    def _mint_clearance_token(self, block_id: str, diff_sha256: str) -> CryptographicClearanceToken:
        timestamp = time.time()
        payload = f"{block_id}:{diff_sha256}:{self._model_name}:{timestamp}".encode("utf-8")
        signature = hmac.new(self._secret_key, payload, hashlib.sha256).hexdigest()
        return CryptographicClearanceToken(
            block_id=block_id,
            diff_sha256=diff_sha256,
            model_used=self._model_name,
            timestamp_utc=timestamp,
            signature=signature,
        )
