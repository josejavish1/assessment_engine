"""
Enforce final quality and security gates before delivery (RFC-015 Phase 4). 1. Invariant Parity (Bucket 1): Verify all specified requirements are met.
2. Anti-Feature Veto (Bucket 3): Verify no prohibited dependencies or overengineering were introduced (e.g., Redis, S3, Twilio SDK).
3. Forensic Security Probes: Audit the AST for SQL injections, missing timeouts, unsafe calls, and leaks.
4. Surgical Ticket Issuance: Issue a SurgicalCorrectionTicket on failure without discarding existing code.
"""
from __future__ import annotations


import ast
import logging
import re
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.probes.code_hygiene import EMOJI_PATTERN, INFORMAL_SLANG_PATTERN
from assessment_engine.infrastructure.evolution.epistemic_distiller import ProductStrategyDossier

logger = logging.getLogger("assessment_engine.infrastructure.evolution.closure_tribunal")


@dataclass(frozen=True)
class TargetScopedAuditReport:
    """Represent an audit report with strict target attribution and differential ratchet enforcement."""
    target_clean: bool
    target_findings: tuple[str, ...]
    unrelated_findings_count: int
    global_regression_detected: bool
    summary: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class SurgicalCorrectionTicket:
    """Represent a prescriptive correction ticket issued by the Forensic Tribunal to Phase 2."""
    ticket_id: str
    timestamp: float
    gate_status: str  # "REJECTED_CLOSURE_GAP" | "APPROVED"
    missing_invariants: tuple[str, ...]
    forbidden_anti_features: tuple[str, ...]
    forensic_findings: tuple[str, ...]
    actionable_instructions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    trace_diagnostic_md: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary representation."""
        return asdict(self)

    def to_prompt_context(self) -> str:
        """Serialize the ticket into a surgical correction instruction block for the synthesizer."""
        inst_md = "\n".join(f"- {act}" for act in self.actionable_instructions)
        forb_md = "\n".join(f"- {act}" for act in self.forbidden_actions)
        findings_md = "\n".join(f"- {f}" for f in (self.missing_invariants + self.forbidden_anti_features + self.forensic_findings))
        trace_section = f"\n{self.trace_diagnostic_md}\n" if self.trace_diagnostic_md else ""

        return (
            f"### SURGICAL CORRECTION TICKET (PHASE 4: FORENSIC CLOSURE TRIBUNAL)\n"
            f"**Ticket ID:** {self.ticket_id} | **Gate Status:** {self.gate_status}\n\n"
            f"#### DEFICIENCIES DETECTED BY FORENSIC AUDITOR\n{findings_md}\n"
            f"{trace_section}\n"
            f"#### MANDATORY ACTIONABLE INSTRUCTIONS\n{inst_md}\n\n"
            f"#### STRICTLY PROHIBITED ACTIONS (ANTI-REGRESSION)\n{forb_md}\n"
        )


@dataclass(frozen=True)
class ClosureTribunalReport:
    """Represent the final forensic audit and parity report."""
    approved: bool
    score_percentage: float
    parity_cubo_1_passed: bool
    veto_cubo_3_passed: bool
    forensic_security_passed: bool
    react_structural_passed: bool
    summary: str
    surgical_ticket: SurgicalCorrectionTicket | None = None
    target_scoped_audit_passed: bool = True
    unrelated_findings_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the instance to a dictionary."""
        return {
            "approved": self.approved,
            "score_percentage": self.score_percentage,
            "parity_cubo_1_passed": self.parity_cubo_1_passed,
            "veto_cubo_3_passed": self.veto_cubo_3_passed,
            "forensic_security_passed": self.forensic_security_passed,
            "react_structural_passed": self.react_structural_passed,
            "target_scoped_audit_passed": self.target_scoped_audit_passed,
            "unrelated_findings_count": self.unrelated_findings_count,
            "summary": self.summary,
            "surgical_ticket": self.surgical_ticket.to_dict() if self.surgical_ticket else None,
        }


class ForensicASTSecurityVisitor(ast.NodeVisitor):
    """Inspect the AST for critical vulnerabilities, resilience code smells, and hygiene violations."""

    def __init__(self, rel_path: str = "candidate.py") -> None:
        self.rel_path = rel_path
        self.findings: list[str] = []

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """Detect classical SQL injection in dynamic f-strings (CWE-89)."""
        static_parts = [val.value for val in node.values if isinstance(val, ast.Constant) and isinstance(val.value, str)]
        full_static = " ".join(static_parts).upper()

        if (
            any(kw in full_static for kw in ("SELECT ", "INSERT INTO", "UPDATE ", "DELETE FROM"))
            and "WHERE" in full_static
            and "?" not in full_static
            and len(node.values) > 1
        ):
            self.findings.append(
                f"SQL Injection (CWE-89) at line {node.lineno}: Dynamic SQL query constructed via f-string without parameterized '?'"
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Detect network calls without timeouts, command injections, and dangerous functions (eval, exec)."""
        func_name = ""
        caller_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                caller_name = node.func.value.id.lower()

        # Arbitrary code execution vulnerability (CWE-95)
        if func_name in ("eval", "exec"):
            self.findings.append(
                f"Arbitrary code execution (CWE-95) at line {node.lineno}: Prohibited use of '{func_name}()'"
            )

        # OS command injection vulnerability (CWE-78)
        if func_name == "system" and caller_name == "os":
            self.findings.append(
                f"OS command injection (CWE-78) at line {node.lineno}: Prohibited use of 'os.system()'"
            )
        elif func_name in ("run", "Popen", "call") and caller_name == "subprocess":
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append(
                        f"OS command injection (CWE-78) at line {node.lineno}: Subprocess executed with 'shell=True'"
                    )

        # Llamadas HTTP sin timeout (RESIL-UNBOUNDED-TIMEOUT)
        if func_name in ("get", "post", "put", "delete", "patch", "request"):
            has_timeout = any(kw.arg == "timeout" for kw in node.keywords)
            if caller_name in ("requests", "httpx", "http", "client", "session", "aiohttp") and not has_timeout:
                self.findings.append(
                    f"Resilience violation (RESIL-UNBOUNDED-TIMEOUT) at line {node.lineno}: HTTP call '{caller_name}.{func_name}()' without finite 'timeout' parameter"
                )

        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """Detecta silenciamiento ciego de excepciones (CWE-391)."""
        is_broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException"))
        if is_broad and len(node.body) == 1:
            first = node.body[0]
            if isinstance(first, ast.Pass) or (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and first.value.value is Ellipsis):
                self.findings.append(
                    f"Code hygiene violation (CWE-391) at line {node.lineno}: Generic exception silently swallowed via pass/..."
                )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a FunctionDef AST node."""
        self._check_nesting(node, 0)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit an AsyncFunctionDef AST node."""
        self._check_nesting(node, 0)
        self.generic_visit(node)

    def _check_nesting(self, parent: ast.AST, depth: int) -> None:
        """Detecta anidamiento de control excesivo (> 3 niveles) (ARCH-DEEP-NESTING)."""
        for child in ast.iter_child_nodes(parent):
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith)):
                d = depth + 1
                if d > 3:
                    self.findings.append(
                        f"Architectural complexity (ARCH-DEEP-NESTING) at line {getattr(child, 'lineno', 0)}: Excessive nesting ({d} levels > 3)"
                    )
                self._check_nesting(child, d)
            else:
                self._check_nesting(child, depth)


def audit_cubo_1_parity(code: str, test_code: str, invariants: tuple[str, ...]) -> tuple[bool, list[str]]:
    """
    Verify that each Bucket 1 invariant is represented in code or tests.
    """
    combined = (code + "\n" + test_code).lower()
    missing: list[str] = []

    # Map invariant types to required key terms.
    keyword_map = {
        "hmac": ("hmac", "signature", "sha256", "sign"),
        "idempotency": ("idempotenc", "idempotent", "idempotency_key", "deduplicat"),
        "utc": ("utc", "iso", "timezone", "timestamp", "datetime"),
        "centimos": ("cent", "cents", "centimo", "amount_cents", "integer"),
        "luhn": ("luhn", "pci", "card", "subtle", "digest"),
        "overbooking": ("hold", "lease", "atomic", "lock", "concurrency"),
        "concurrencia": ("etag", "if-match", "match", "version", "precondition"),
        "anonimizacion": ("hash", "sha256", "anonymiz", "redact"),
        "tipado": ("int", "str", "float", "bool", "dict", "list", "tuple", "return", "type", ":", "->"),
        "pura": ("def ", "return", "assert", "multiply", "add"),
        "numeric": ("int", "float", "number", "multiply", "amount", "return"),
        "honeypot": ("honeypot", "_hp", "hidden", "tabindex", "aria", "label", "input"),
        "speed trap": ("token", "hmac", "timestamp", "time", "speed", "trap", "elapsed"),
        "caducidad": ("expire", "max_seconds", "elapsed", "timeout", "valid", "expired"),
        "oklch": ("oklch", "token", "theme", "css", "variable", "color", "palette", "hex"),
        "wcag": ("wcag", "aria", "contrast", "axe", "accessibility", "label", "main", "h1"),
        "saliency": ("saliency", "prominenc", "foveal", "attention", "fixation", "contrast", "fitts", "crowding"),
        "attention": ("attention", "atencion", "fixation", "foveal", "saliency", "focus"),
        "prominencia": ("prominenc", "saliency", "contrast", "pop-out", "feature", "foveal"),
        "multimodal": ("multimodal", "vision", "screenshot", "prompt", "image", "defect", "aesthetic", "trust"),
        "visual": ("visual", "defect", "screenshot", "clipping", "overlapping", "distortion", "aesthetic", "trust"),
        "solapamiento": ("overlapping", "overlap", "z-index", "layer", "modal", "banner"),
        "truncamiento": ("clipping", "truncate", "ellipsis", "overflow", "corte"),
        "responsiv": ("responsive", "viewport", "mobile", "desktop", "overflow", "375", "1440", "w-full"),
        "fotograf": ("image", "photo", "unsplash", "asset", "src", "img", "fotograf"),
        "atmosfer": ("gradient", "radial", "glow", "depth", "glass", "backdrop", "shadow"),
        "mockup": ("mockup", "preview", "device", "simulator", "perspective", "widget"),
        "friction": ("friction", "rage_click", "hesitation", "dropoff", "beacon", "conversion", "variant"),
        "friccion": ("friction", "rage_click", "hesitation", "dropoff", "beacon", "conversion", "variant"),
        "rage": ("rage_click", "click", "clicks", "rapid", "threshold", "friction"),
        "hesitation": ("hesitation", "focus", "dwell", "timer", "delay", "friction"),
        "beacon": ("beacon", "sendbeacon", "keepalive", "visibilitychange", "pagehide"),
        "pii": ("pii", "redact", "password", "sanitize", "secret", "rgpd"),
        "wal": ("wal", "journal_mode", "synchronous", "sqlite", "pragma"),
        "aiosqlite": ("aiosqlite", "sqlite", "wal", "journal_mode", "synchronous"),
        "batches": ("batch", "batches", "executemany", "transaction", "transaccional"),
        "thompson": ("thompson", "betavariate", "bandit", "posterior", "prior", "sampling"),
        "bayesiano": ("bayes", "posterior", "prior", "beta", "thompson", "monte carlo"),
        "convergencia": ("convergence", "converg", "significance", "uplift", "prob"),
        "breaker": ("circuit", "breaker", "quarantine", "cuarentena", "cortocircuito"),
        "stickiness": ("sticky", "session", "assignment", "determinista"),
        "post-mortem": ("post-mortem", "postmortem", "causal", "defeat", "attribution", "autopsia"),
        "causal": ("causal", "attribution", "root_cause", "causa", "diagnostico"),
        "darwiniano": ("darwin", "distiller", "contrastive", "exemplar", "reflexion"),
        "reflexion": ("reflexion", "ledger", "antipattern", "exemplar", "axiom"),
        "sombra": ("shadow", "diffuse", "rgba", "multicapa", "sombra", "atenuacion", "decay"),
        "border": ("border", "inset", "translucent", "translucid", "micro", "stroke"),
        "craft": ("craft", "taste", "polish", "linear", "kowalski", "estetic", "calidad"),
        "taste": ("taste", "craft", "polish", "linear", "kowalski", "slop", "antipattern"),
        "repair": ("repair", "remediat", "fix", "replace", "sub", "morph", "reparacion"),
        "eslint": ("lint", "ast", "rule", "violation", "pattern", "audit", "linter", "check"),
        "ast": ("ast", "tree", "node", "re", "pattern", "parse", "visitor", "lint"),
        "physics": ("active", "scale", "spring", "fisic", "transition", "duration"),
        "resorte": ("spring", "bounce", "damping", "active", "scale"),
        "microinteraction": ("active", "scale", "transition", "hover", "interact", "touch"),
        "itu": ("itu", "e164", "e.164", "phone", "telefono", "regex", "email"),
        "5322": ("5322", "email", "correo", "regex"),
        "magic": ("magic", "uint8array", "canvas", "webp", "blob", "file", "image", "photo"),
    }

    for inv in invariants:
        inv_low = inv.lower()
        matched = False
        for trigger, required_keywords in keyword_map.items():
            if trigger in inv_low and any(kw in combined for kw in required_keywords):
                matched = True
                break
        # Check for the presence of substantive words if the invariant is not mapped.
        if not matched:
            words = [w for w in re.findall(r"[a-zA-Z]{4,}", inv_low) if w not in ("para", "cada", "debe", "estar", "como")]
            if words and any(w in combined for w in words):
                matched = True

        if not matched:
            missing.append(inv)

    return (len(missing) == 0, missing)


def _matches_veto_patterns(patterns: list[str], low_code: str) -> bool:
    """Check if any regex pattern in the veto list matches source code."""
    return any(re.search(pat, low_code, re.IGNORECASE) for pat in patterns)


def audit_cubo_3_anti_features(code: str, anti_features: tuple[str, ...]) -> tuple[bool, list[str]]:
    """Verify that no anti-features rejected in Bucket 3 were introduced into the code."""
    low_code = code.lower()
    forbidden_detected: list[str] = []

    veto_patterns = {
        "redis": [r"\bimport\s+redis\b", r"\bfrom\s+redis\b", r"\bredis\.Redis\b"],
        "s3": [r"\bboto3\b", r"\bs3\.upload\b", r"\baws_s3\b"],
        "twilio": [r"\bfrom\s+twilio\b", r"\bimport\s+twilio\b", r"\bTwilioRestClient\b"],
        "pan": [r"\bcard_number\s*=\s*['\"]?\d{16}", r"\bpan_number\b"],
        "sip": [r"\bimport\s+pjsua\b", r"\basterisk\b", r"\bsip_server\b"],
        "microservicios": [r"\bgrpc\b", r"\bconsul\b", r"\beureka\b"],
    }

    for af in anti_features:
        af_low = af.lower()
        for trigger, patterns in veto_patterns.items():
            if trigger in af_low and _matches_veto_patterns(patterns, low_code):
                forbidden_detected.append(f"Anti-Feature detected ({trigger.upper()}): Violation of '{af}'")

    return (len(forbidden_detected) == 0, forbidden_detected)


def audit_forensic_security(code: str, rel_path: str = "candidate.py") -> tuple[bool, list[str]]:
    """
    Run AST static security probes and code sobriety checks on the candidate.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return (False, [f"Fatal syntax error: {e}"])

    visitor = ForensicASTSecurityVisitor(rel_path=rel_path)
    visitor.visit(tree)
    findings = list(visitor.findings)

    for line_idx, line in enumerate(code.splitlines(), 1):
        clean = line.strip()
        if clean.startswith("#") or " #" in line:
            if INFORMAL_SLANG_PATTERN.search(clean):
                findings.append(
                    f"Code hygiene violation (HYGIENE-UNPROFESSIONAL-COMMENT) at line {line_idx}: Informal or non-technical comment detected"
                )
            if EMOJI_PATTERN.search(clean):
                findings.append(
                    f"Code hygiene violation (HYGIENE-EMOJI-IN-CODE) at line {line_idx}: Emojis prohibited in production code"
                )

    return (len(findings) == 0, findings)


def audit_react_structural_patterns(code: str) -> tuple[bool, list[str]]:
    """Detect frontend anti-patterns that degrade UX or violate React best practices (e.g., missing AbortController, memory leaks, or missing memoization)."""
    findings = []
    
    if "useEffect" in code and "fetch(" in code and "AbortController" not in code:
        findings.append("Memory Leak / Race Condition: fetch() inside useEffect without AbortController for cleanup on unmount.")
        
    if "filter(" in code and "map(" in code and "useMemo" not in code and "filtered" in code.lower():
        findings.append("Main Thread Jank: Array filtering/transformation in render body without useMemo. Blocks UI at 60 FPS.")

    if "onClick" in code and "aria-" not in code and "role=" not in code and re.search(r"<div[^>]*onClick", code):
        findings.append("Accessibility Failure (WCAG): Interactive <div> with onClick lacks role='button' or aria-* attributes.")
            
    if "any" in code and "as any" in code:
        findings.append("Typing Violation (TS): Explicit 'as any' or ': any' voids compile-time AOT type safety.")

    return (len(findings) == 0, findings)


def _audit_code_syntax_and_test(
    candidate_code: str, target_rel_path: str, candidate_test_code: str
) -> list[str]:
    """Audit source and test files for forensic security and React structural patterns."""
    findings: list[str] = []
    if target_rel_path.endswith(".py"):
        s_passed, sec_f = audit_forensic_security(candidate_code, rel_path=target_rel_path)
        if not s_passed:
            findings.extend(sec_f)
    elif target_rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
        r_passed, r_f = audit_react_structural_patterns(candidate_code)
        if not r_passed:
            findings.extend(r_f)

    if candidate_test_code and candidate_test_code.strip():
        test_rel = f"tests/test_{Path(target_rel_path).stem}.py"
        t_passed, t_f = audit_forensic_security(candidate_test_code, rel_path=test_rel)
        if not t_passed:
            findings.extend(t_f)
    return findings


def _evaluate_workspace_report_attribution(
    workspace_report: Any, target_rel_path: str, baseline_score: float | None
) -> tuple[list[str], int, bool]:
    """Aggregate workspace findings and evaluate baseline regression."""
    all_findings = []
    probes = getattr(workspace_report, "probes", {})
    for probe in probes.values():
        findings_list = getattr(probe, "findings", [])
        all_findings.extend(findings_list)

    target_stems = (Path(target_rel_path).stem.lower(),)
    target_ws_findings = [
        f"{getattr(f, 'rule_id', 'RULE')} en {getattr(f, 'file_path', '')}:{getattr(f, 'line_number', 0)}: {getattr(f, 'message', '')}"
        for f in all_findings
        if any(st in getattr(f, "file_path", "").lower() for st in target_stems)
    ]
    unrelated_count = len(all_findings) - len(target_ws_findings)

    regression = False
    current_score = getattr(workspace_report, "global_score", 100.0)
    if baseline_score is not None and current_score < baseline_score:
        regression = True
        target_ws_findings.append(
            f"Global Regression (RATCHET-VIOLATION): Project quality score decreased from {baseline_score}% to {current_score}%."
        )

    return target_ws_findings, unrelated_count, regression


def audit_target_scoped_quality(
    candidate_code: str,
    target_rel_path: str,
    candidate_test_code: str = "",
    workspace_report: Any | None = None,
    baseline_score: float | None = None,
) -> TargetScopedAuditReport:
    """Execute a differential audit with strict target attribution (Boy Scout rule). - Evaluate candidate_code and candidate_test_code against quality dimensions.
- Isolate unrelated pre-existing defects in other project files.
- Require zero findings in target_rel_path and disallow regression of the overall score."""
    target_findings = _audit_code_syntax_and_test(candidate_code, target_rel_path, candidate_test_code)
    unrelated_count = 0
    regression = False

    if workspace_report is not None:
        ws_findings, unrelated_count, regression = _evaluate_workspace_report_attribution(
            workspace_report, target_rel_path, baseline_score
        )
        target_findings.extend(ws_findings)

    target_clean = len(target_findings) == 0 and not regression
    summary = (
        f"Differential Audit: Target file '{target_rel_path}' 100% clean (0 findings). {unrelated_count} unrelated defects isolated."
        if target_clean
        else f"Differential Audit VETO: {len(target_findings)} defects in '{target_rel_path}'. {unrelated_count} unrelated defects omitted."
    )

    return TargetScopedAuditReport(
        target_clean=target_clean,
        target_findings=tuple(target_findings),
        unrelated_findings_count=unrelated_count,
        global_regression_detected=regression,
        summary=summary,
    )


class ClosureTribunal:
    """Evaluate parity, anti-features, and security during the final review gate, and issue either a final verdict or a non-destructive surgical correction ticket."""

    def __init__(self, llm_reviewer_fn: Callable[[str], str] | None = None) -> None:
        self.llm_reviewer_fn = llm_reviewer_fn

    def _create_surgical_ticket(self, p_passed: bool, missing_invs: list[str], v_passed: bool, forbidden_afs: list[str], s_passed: bool, security_findings: list[str], react_passed: bool, react_findings: list[str]) -> SurgicalCorrectionTicket:
        ticket_id = f"TICK-{uuid.uuid4().hex[:8].upper()}"
        actionable_instructions: list[str] = []
        forbidden_actions: list[str] = [
            "Do not rewrite from scratch functions that already passed AST gates.",
            "Do not introduce external libraries into requirements.txt or package.json without architectural justification.",
            "Maintain cyclomatic complexity strictly below V(G) <= 10.",
        ]

        if not p_passed:
            for inv in missing_invs:
                actionable_instructions.append(f"Implement explicit support for: {inv}")
        if not v_passed:
            for af in forbidden_afs:
                actionable_instructions.append(f"Eliminate prohibited dependency or pattern: {af}")
        if not s_passed:
            for sec in security_findings:
                actionable_instructions.append(f"Remediate security vulnerability or quality defect: {sec}")
        if not react_passed:
            for rf in react_findings:
                actionable_instructions.append(f"Fix frontend anti-pattern: {rf}")

        return SurgicalCorrectionTicket(
            ticket_id=ticket_id, timestamp=time.time(), gate_status="REJECTED_CLOSURE_GAP",
            missing_invariants=tuple(missing_invs), forbidden_anti_features=tuple(forbidden_afs),
            forensic_findings=tuple(security_findings + react_findings), actionable_instructions=tuple(actionable_instructions),
            forbidden_actions=tuple(forbidden_actions),
        )

    def evaluate(
        self,
        candidate_code: str,
        candidate_test_code: str,
        dossier: ProductStrategyDossier,
        rel_path: str = "candidate.py",
        workspace_report: Any | None = None,
        baseline_score: float | None = None,
    ) -> ClosureTribunalReport:
        """Run forensic audits on candidate code using a differential ratchet."""
        p_passed, missing_invs = audit_cubo_1_parity(code=candidate_code, test_code=candidate_test_code, invariants=dossier.must_have_invariants)
        v_passed, forbidden_afs = audit_cubo_3_anti_features(code=candidate_code, anti_features=dossier.deliberate_anti_features)
        
        scoped_audit = audit_target_scoped_quality(
            candidate_code=candidate_code,
            target_rel_path=rel_path,
            candidate_test_code=candidate_test_code,
            workspace_report=workspace_report,
            baseline_score=baseline_score,
        )

        s_passed = scoped_audit.target_clean
        security_findings = list(scoped_audit.target_findings)
        
        react_passed = True
        react_findings: list[str] = []
        if rel_path.endswith((".tsx", ".ts", ".jsx", ".js")):
            react_passed, react_findings = audit_react_structural_patterns(candidate_code)

        all_passed = p_passed and v_passed and s_passed and react_passed
        if all_passed:
            return ClosureTribunalReport(
                approved=True,
                score_percentage=100.0,
                parity_cubo_1_passed=True,
                veto_cubo_3_passed=True,
                forensic_security_passed=True,
                react_structural_passed=True,
                summary="Certified by Tier-1 Forensic Tribunal: 100% invariants passed, 0 anti-features, 0 vulnerabilities.",
                surgical_ticket=None,
                target_scoped_audit_passed=True,
                unrelated_findings_count=scoped_audit.unrelated_findings_count,
            )

        ticket = self._create_surgical_ticket(p_passed, missing_invs, v_passed, forbidden_afs, s_passed, security_findings, react_passed, react_findings)
        
        total_checks = len(dossier.must_have_invariants) + len(dossier.deliberate_anti_features) + 1 + (1 if not react_passed else 0)
        faults = len(missing_invs) + len(forbidden_afs) + len(security_findings) + len(react_findings)
        score = max(0.0, round(((total_checks - faults) / max(1, total_checks)) * 100, 1))

        return ClosureTribunalReport(
            approved=False,
            score_percentage=score,
            parity_cubo_1_passed=p_passed,
            veto_cubo_3_passed=v_passed,
            forensic_security_passed=s_passed,
            react_structural_passed=react_passed,
            summary=f"Rechazado en Fase 4 ({ticket.ticket_id}): {faults} deficiencias detectadas en '{rel_path}'. {scoped_audit.unrelated_findings_count} defectos ajenos aislados.",
            surgical_ticket=ticket,
            target_scoped_audit_passed=s_passed,
            unrelated_findings_count=scoped_audit.unrelated_findings_count,
        )


closure_tribunal = ClosureTribunal()

__all__ = [
    "ClosureTribunal",
    "ClosureTribunalReport",
    "ForensicASTSecurityVisitor",
    "SurgicalCorrectionTicket",
    "TargetScopedAuditReport",
    "audit_cubo_1_parity",
    "audit_cubo_3_anti_features",
    "audit_forensic_security",
    "audit_target_scoped_quality",
    "closure_tribunal",
]
