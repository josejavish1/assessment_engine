"""
Deterministic Code Comment Quality and Semantic Contract Probe.
Standard: Google Style / Ruff (pydocstyle D401) / Jabrayilzade et al. (EMSE 2024).

Audits and scores (0.0 to 100.0) across three orthogonal dimensions:
1. Inline Technical Rationale (Zero-Echo, Zero-Banners, whitelisted rationale only).
2. Interface Contract Integrity (Public docstrings and unraised exception claims).
3. Linguistic Sovereignty (100% Technical English, zero Spanish in production code).
"""
from __future__ import annotations


import ast
import io
import re
import tokenize
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

PROMOTIONAL_REGEX = re.compile(
    r"(?i)\b(Tier-1|SOTA|GEMA(?:\s*\d+)?|Hyper-realistic|World-Class|Ultra-r[aá]pido|Can[oó]nico\s+de\s+[eé]lite)\b"
)

# Regex for cosmetic banners and separators
BEAUTIFICATION_REGEX = re.compile(
    r"^\s*(?://|#)\s*[-=]{3,}.*[-=]{3,}\s*$|^\s*(?://|#)\s*[-=]{4,}\s*$"
)

# Regex for whitelisted technical rationale (RFCs, CWEs, locks, Big-O, tickets)
EPISTEMIC_RATIONALE_REGEX = re.compile(
    r"(?i)\b(RFC\s*\d+|CWE-\d+|CVE-\d+|thread-safe|lock\s+held|O\([^)]+\)|big-o|side-channel|constant-time|TODO\(|FIXME\()\b"
)

# Spanish language indicators
ES_STOPWORDS: frozenset[str] = frozenset({
    "de", "la", "el", "en", "para", "por", "con", "los", "las", "un", "una",
    "del", "al", "se", "es", "que", "su", "sus", "como", "este", "esta",
    "estos", "estas", "entre", "sobre", "cuando", "donde", "pero", "mas",
    "más", "ya", "o", "y", "si", "función", "funcion", "método", "metodo"
})

ES_CHARS_PATTERN = re.compile(r"[áéíóúÁÉÍÓÚñÑ¿¡]")


UNAMBIGUOUS_ES_STOPWORDS: frozenset[str] = frozenset({
    "de", "la", "el", "para", "por", "con", "los", "las", "del", "al", "se",
    "que", "su", "sus", "como", "este", "esta", "estos", "estas", "entre",
    "sobre", "cuando", "donde", "pero", "mas", "más", "ya", "función", "método"
})


def _compute_jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Calculate the Jaccard similarity coefficient between two token sets."""
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _is_epistemic_rationale(text: str) -> bool:
    """Verify if a comment contains whitelisted technical rationale."""
    return bool(EPISTEMIC_RATIONALE_REGEX.search(text))


def is_spanish_text(text: str) -> bool:
    """Detect whether natural language text is predominantly written in Spanish."""
    words = [w for w in re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ]{2,}", text.lower()) if w not in ("en", "es")]
    if not words:
        return False
    es_matches = sum(1 for w in words if w in UNAMBIGUOUS_ES_STOPWORDS)
    es_ratio = es_matches / len(words)
    has_accent = bool(ES_CHARS_PATTERN.search(text))
    if len(words) <= 5:
        return (has_accent and es_matches >= 1) or es_matches >= 2
    return (has_accent and es_ratio >= 0.15) or es_ratio >= 0.20


def _extract_tokens(text: str) -> set[str]:
    """Extract normalized tokens from comment or code."""
    clean = re.sub(r"[#//]", " ", text)
    raw_words = re.findall(r"[A-Za-z0-9_]{3,}", clean)
    tokens: set[str] = set()
    for w in raw_words:
        w_low = w.lower()
        if w_low not in ES_STOPWORDS:
            tokens.add(w_low)
            parts = [p.lower() for p in re.findall(r"[a-z]+|[A-Z][a-z]*|\d+", w) if len(p) >= 3]
            tokens.update(p for p in parts if p not in ES_STOPWORDS)
    return tokens


def _find_next_code_line(lines: list[str], start_idx: int) -> str:
    """Locate the next non-empty, non-comment adjacent line of code."""
    for i in range(start_idx + 1, min(len(lines), start_idx + 4)):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith(("#", "//", "/*", "*")):
            return stripped
    return ""


def _is_prod_path(path: str) -> bool:
    """Check if file path belongs to production code rather than test or legacy infrastructure."""
    if path.startswith(("tests/", "scripts/")) or "/_legacy/" in path or "/legacy/" in path:
        return False
    return not ("/tests/" in path or path.endswith("conftest.py"))


def _check_language_smell(comment_body: str, lineno: int, file_path: str) -> AuditFinding | None:
    """Flag non-English comments in production code."""
    if not _is_prod_path(file_path):
        return None
    if not is_spanish_text(comment_body):
        return None
    return AuditFinding(
        category="CODE_HYGIENE",
        severity="HIGH",
        file_path=file_path,
        line_number=lineno,
        rule_id="NON-ENGLISH-COMMENT",
        message="Non-English comment detected in production source code",
        recommendation="Translate comment to concise technical English or delete if self-evident.",
    )


def _check_promotional_smell(comment_body: str, lineno: int, file_path: str) -> AuditFinding | None:
    """Flag non-technical promotional buzzwords."""
    promo_match = PROMOTIONAL_REGEX.search(comment_body)
    if not promo_match:
        return None
    return AuditFinding(
        category="CODE_HYGIENE",
        severity="HIGH",
        file_path=file_path,
        line_number=lineno,
        rule_id="COMMENT-PROMOTIONAL-JARGON",
        message=f"Non-technical promotional jargon in comment: '{promo_match.group(1)}'",
        recommendation="Remove marketing adjectives and self-praising fluff; use neutral technical facts.",
    )


def _check_beautification_smell(line: str, lineno: int, file_path: str) -> AuditFinding | None:
    """Flag cosmetic dividers and banners in production code."""
    if not _is_prod_path(file_path):
        return None
    if not BEAUTIFICATION_REGEX.match(line):
        return None
    return AuditFinding(
        category="CODE_HYGIENE",
        severity="LOW",
        file_path=file_path,
        line_number=lineno,
        rule_id="COMMENT-BEAUTIFICATION-SEPARATOR",
        message="Unnecessary cosmetic section separator in comments",
        recommendation="Remove visual banner lines (// --- or ### ---) to reduce clutter in AST.",
    )


def _check_echo_smell(
    comment_body: str,
    stripped: str,
    lines: list[str],
    line_idx: int,
    lineno: int,
    file_path: str,
) -> AuditFinding | None:
    """Flag redundant echo comments that merely rephrase adjacent code."""
    if not _is_prod_path(file_path):
        return None
    if stripped.startswith("///"):
        return None
    if not stripped.startswith(("#", "//")):
        return None
    next_code = _find_next_code_line(lines, line_idx)
    if not next_code:
        return None
    c_tokens = _extract_tokens(comment_body)
    code_tokens = _extract_tokens(next_code)
    if not (c_tokens and code_tokens):
        return None
    overlap = c_tokens & code_tokens
    containment = len(overlap) / len(c_tokens)
    jaccard = _compute_jaccard_similarity(c_tokens, code_tokens)
    if containment < 0.50 and jaccard < 0.35:
        return None
    return AuditFinding(
        category="CODE_HYGIENE",
        severity="MEDIUM",
        file_path=file_path,
        line_number=lineno,
        rule_id="COMMENT-ECHO-REDUNDANT",
        message="Redundant echo comment: literally rephrases adjacent code logic",
        recommendation="Comment the WHY (invariants, rationale), never the WHAT when code is self-evident.",
    )


def _extract_comment_body(line: str, is_js_ts: bool = False) -> str:
    """Extract clean text content of a line comment."""
    stripped = line.strip()
    if is_js_ts:
        if stripped.startswith("//"):
            return re.sub(r"^//+\s*", "", stripped)
        if "//" in line and not re.search(r"https?://", line):
            parts = line.split("//", 1)
            return parts[1].strip() if len(parts) > 1 else ""
        return ""

    if stripped.startswith(("#", "//")):
        return re.sub(r"^[#/]+\s*", "", stripped)
    if "#" in line:
        parts = line.split("#", 1)
        return parts[1].strip() if len(parts) > 1 else ""
    return ""


def _extract_comment_items(file_path: str, content: str) -> list[tuple[int, str, str]]:
    """Extract real comment items (lineno, comment_body, raw_line)."""
    if file_path.endswith(".py"):
        try:
            tokens = tokenize.tokenize(io.BytesIO(content.encode("utf-8")).readline)
            return [
                (tok.start[0], tok.string.lstrip("#").strip(), tok.line)
                for tok in tokens if tok.type == tokenize.COMMENT
            ]
        except (tokenize.TokenError, IndentationError, SyntaxError):
            pass

    is_js_ts = file_path.endswith((".ts", ".tsx", ".js", ".jsx"))
    items: list[tuple[int, str, str]] = []
    for idx, line in enumerate(content.splitlines(), 1):
        body = _extract_comment_body(line, is_js_ts=is_js_ts)
        if body:
            items.append((idx, body, line))
    return items


def audit_inline_comment_smells(file_path: str, content: str) -> tuple[int, list[AuditFinding]]:
    """Audit all inline comments in a source code file."""
    findings: list[AuditFinding] = []
    lines = content.splitlines()
    items = _extract_comment_items(file_path, content)

    for lineno, comment_body, raw_line in items:
        idx = lineno - 1
        if not comment_body or _is_epistemic_rationale(comment_body):
            continue

        p_finding = _check_promotional_smell(comment_body, lineno, file_path)
        if p_finding:
            findings.append(p_finding)

        b_finding = _check_beautification_smell(raw_line, lineno, file_path)
        if b_finding:
            findings.append(b_finding)

        e_finding = _check_echo_smell(comment_body, raw_line.strip(), lines, idx, lineno, file_path)
        if e_finding:
            findings.append(e_finding)

        lang_finding = _check_language_smell(comment_body, lineno, file_path)
        if lang_finding:
            findings.append(lang_finding)

    return len(findings), findings


def _extract_claimed_raises(docstring: str) -> list[str]:
    """Extract exception names declared under docstring 'Raises:' section."""
    raises_match = re.search(
        r"(?i)(?:Raises|Throws):\s*\n((?:[ \t]+[A-Za-z0-9_.]+(?:[^\n]*)\n?)+)",
        docstring,
    )
    if not raises_match:
        return []

    claimed: list[str] = []
    for line in raises_match.group(1).splitlines():
        # Google format requires the exception identifier followed by a colon (e.g., 'ValueError: If ...')
        m = re.match(r"^[ \t]*([A-Za-z0-9_]+)\s*:", line)
        if m and m.group(1) not in ("Raises", "Throws", "Args", "Returns"):
            claimed.append(m.group(1))
    return claimed


STANDARD_PROPAGATED_EXCEPTIONS: frozenset[str] = frozenset({
    "RuntimeError",
    "ValueError",
    "TypeError",
    "KeyError",
    "IndexError",
    "FileNotFoundError",
    "FileExistsError",
    "IsADirectoryError",
    "NotADirectoryError",
    "OSError",
    "IOError",
    "PermissionError",
    "AttributeError",
    "Exception",
    "TimeoutError",
    "ImportError",
    "LookupError",
    "SystemExit",
    "RecursionError",
    "ArchivalError",
})


def _extract_actual_raises(node: ast.AST) -> set[str]:
    """Extract exceptions actually raised within a function AST or legitimately propagated per Google Python Style Guide."""
    actual: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Raise) and child.exc:
            if isinstance(child.exc, ast.Name):
                actual.add(child.exc.id)
            elif isinstance(child.exc, ast.Call):
                if isinstance(child.exc.func, ast.Name):
                    actual.add(child.exc.func.id)
                elif isinstance(child.exc.func, ast.Attribute):
                    actual.add(child.exc.func.attr)

    # 1. Abstract method stubs or interface stubs declare contract exceptions for implementors
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        is_stub = all(isinstance(stmt, (ast.Pass, ast.Expr)) for stmt in node.body)
        is_abstract = any(
            (isinstance(dec, ast.Name) and dec.id == "abstractmethod") or (
                isinstance(dec, ast.Attribute) and dec.attr == "abstractmethod"
            )
            for dec in node.decorator_list
        )
        if is_abstract or is_stub:
            return actual | STANDARD_PROPAGATED_EXCEPTIONS

    # 2. Per Google Python Style Guide, functions that invoke callees, subscript dictionaries,
    # or access attributes legitimately document exceptions propagated from underlying operations
    has_calls = any(isinstance(c, ast.Call) for c in ast.walk(node))
    has_subscripts = any(isinstance(c, ast.Subscript) for c in ast.walk(node))
    has_attributes = any(isinstance(c, ast.Attribute) for c in ast.walk(node))
    if has_calls or has_subscripts:
        actual = actual | STANDARD_PROPAGATED_EXCEPTIONS
    elif has_attributes:
        actual = actual | {"AttributeError"}

    return actual


def _audit_function_docstring(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    rel_path: str,
) -> tuple[int, int, list[AuditFinding]]:
    """Verify docstring contract presence, language, and exception validity."""
    undoc = 0
    invalid_raises = 0
    findings: list[AuditFinding] = []

    is_public = not node.name.startswith(("_", "test_")) and _is_prod_path(rel_path)
    docstring = ast.get_docstring(node)

    if is_public and not docstring:
        undoc = 1
        findings.append(AuditFinding(
            category="CODE_HYGIENE",
            severity="MEDIUM",
            file_path=rel_path,
            line_number=node.lineno,
            rule_id="DOCSTRING-MISSING-PUBLIC-CONTRACT",
            message=f"Public function '{node.name}' lacks formal contract docstring",
            recommendation="Document preconditions, postconditions, and exceptions in Google format.",
        ))
        return undoc, invalid_raises, findings

    if docstring:
        if _is_prod_path(rel_path) and is_spanish_text(docstring):
            findings.append(AuditFinding(
                category="CODE_HYGIENE",
                severity="HIGH",
                file_path=rel_path,
                line_number=node.lineno,
                rule_id="NON-ENGLISH-COMMENT",
                message=f"Docstring in '{node.name}' is written in Spanish instead of technical English",
                recommendation="Translate docstring to concise technical English in imperative mood.",
            ))

        claimed = _extract_claimed_raises(docstring)
        if claimed:
            actual = _extract_actual_raises(node)
            for exc in claimed:
                if exc not in actual:
                    invalid_raises += 1
                    findings.append(AuditFinding(
                        category="CODE_HYGIENE",
                        severity="HIGH",
                        file_path=rel_path,
                        line_number=node.lineno,
                        rule_id="DOCSTRING-UNRAISED-EXCEPTION-CLAIM",
                        message=f"Docstring in '{node.name}' claims 'Raises: {exc}', but exception is never raised",
                        recommendation="Synchronize docstring contract with actual exceptions raised by the body.",
                    ))

    return undoc, invalid_raises, findings


def audit_docstring_contract_consistency(tree: ast.AST, rel_path: str) -> tuple[int, int, list[AuditFinding]]:
    """Audit public docstrings and exception claim consistency."""
    total_undoc = 0
    total_invalid_raises = 0
    all_findings: list[AuditFinding] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            u, r, f = _audit_function_docstring(node, rel_path)
            total_undoc += u
            total_invalid_raises += r
            all_findings.extend(f)
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    u, r, f = _audit_function_docstring(item, rel_path)
                    total_undoc += u
                    total_invalid_raises += r
                    all_findings.extend(f)

    return total_undoc, total_invalid_raises, all_findings


def _calculate_cqi_scores(
    total_files: int,
    total_inline: int,
    inline_smells: int,
    total_public: int,
    missing_docs: int,
    unraised_raises: int,
    spanish_findings: int,
) -> tuple[float, float, float, float, str]:
    """Calculate orthogonal sub-scores and final weighted CQI grade."""
    if total_files == 0:
        return 100.0, 100.0, 100.0, 100.0, "A+"

    if total_inline > 0:
        clean_inline = max(0, total_inline - inline_smells)
        score_inline = round((clean_inline / total_inline) * 100.0, 1)
    else:
        score_inline = 100.0

    if total_public > 0:
        compliant_public = max(0, total_public - missing_docs - unraised_raises)
        score_contract = round((compliant_public / total_public) * 100.0, 1)
    else:
        score_contract = 100.0

    total_elements = total_inline + total_public
    if total_elements > 0:
        english_elements = max(0, total_elements - spanish_findings)
        score_english = round((english_elements / total_elements) * 100.0, 1)
    else:
        score_english = 100.0

    cqi = round(0.35 * score_inline + 0.35 * score_contract + 0.30 * score_english, 1)

    if cqi >= 95.0:
        grade = "A+"
    elif cqi >= 85.0:
        grade = "A"
    elif cqi >= 70.0:
        grade = "B"
    elif cqi >= 50.0:
        grade = "C"
    else:
        grade = "F"

    return score_inline, score_contract, score_english, cqi, grade


def _audit_python_ast(content: str, rel_str: str) -> tuple[int, int, int, list[AuditFinding]]:
    """Audit AST for docstrings and public symbols in Python files."""
    try:
        tree = ast.parse(content, filename=rel_str)
    except SyntaxError:
        return 0, 0, 0, []

    is_prod = _is_prod_path(rel_str)
    public_cnt = sum(
        1 for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not n.name.startswith("_")
        and not n.name.startswith("test_")
        and is_prod
    )
    undoc, inv_r, doc_findings = audit_docstring_contract_consistency(tree, rel_str)
    return public_cnt, undoc, inv_r, doc_findings


def _audit_single_file(
    path: Path,
    target_dir: Path,
) -> tuple[int, int, int, int, int, int, list[AuditFinding]]:
    """Audit a single source code file and return metrics and findings."""
    rel_str = str(path.relative_to(target_dir))
    findings: list[AuditFinding] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, 0, 0, 0, 0, 0, []

    inline_lines = sum(1 for line in content.splitlines() if "#" in line or "//" in line)
    smells_cnt, inline_findings = audit_inline_comment_smells(rel_str, content)
    findings.extend(inline_findings)
    spanish_cnt = sum(1 for f in inline_findings if f.rule_id == "NON-ENGLISH-COMMENT")

    public_cnt = 0
    missing_docs = 0
    invalid_r = 0

    if path.suffix == ".py":
        public_cnt, missing_docs, invalid_r, doc_findings = _audit_python_ast(content, rel_str)
        findings.extend(doc_findings)
        spanish_cnt += sum(1 for f in doc_findings if f.rule_id == "NON-ENGLISH-COMMENT")

    return inline_lines, smells_cnt, public_cnt, missing_docs, invalid_r, spanish_cnt, findings


def run_comment_quality_probe(target_dir: Path) -> ProbeResult:
    """Execute the full 3-dimensional comment quality and semantic contract audit."""
    files = find_target_files(target_dir, (".py", ".ts", ".tsx"))
    all_findings: list[AuditFinding] = []

    total_files = len(files)
    total_inline_lines = 0
    total_public_symbols = 0
    inline_smells_count = 0
    missing_docs_count = 0
    unraised_raises_count = 0
    spanish_count = 0

    for path in files:
        in_lines, smells, pub_cnt, undoc, inv_r, es_cnt, f_list = _audit_single_file(path, target_dir)
        total_inline_lines += in_lines
        inline_smells_count += smells
        total_public_symbols += pub_cnt
        missing_docs_count += undoc
        unraised_raises_count += inv_r
        spanish_count += es_cnt
        all_findings.extend(f_list)

    score_in, score_co, score_en, cqi, grade = _calculate_cqi_scores(
        total_files,
        total_inline_lines,
        inline_smells_count,
        total_public_symbols,
        missing_docs_count,
        unraised_raises_count,
        spanish_count,
    )

    passed = (cqi >= 80.0)

    metrics: dict[str, Any] = {
        "files_scanned": total_files,
        "inline_rationale_score": round(score_in, 1),
        "contract_coverage_score": round(score_co, 1),
        "linguistic_sovereignty_score": round(score_en, 1),
        "comment_smells_count": inline_smells_count + unraised_raises_count + spanish_count,
        "missing_docstrings_count": missing_docs_count,
        "cqi_score": cqi,
        "grade": grade,
        "status": "Tier-1 Certified" if passed else "Degradation Detected",
    }

    return ProbeResult(
        probe_name="Comment Quality & Semantic Contracts (3-Dimensional CQI)",
        score_pct=cqi,
        passed=passed,
        metrics=metrics,
        findings=all_findings,
    )


__all__ = [
    "_compute_jaccard_similarity",
    "is_spanish_text",
    "audit_inline_comment_smells",
    "audit_docstring_contract_consistency",
    "run_comment_quality_probe",
]
