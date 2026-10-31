"""Automated Governance & Hygiene Test Suite.

Prevents technical debt, hardcoded magic numbers, client/brand leaks, and language guessing.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path


def test_no_hardcoded_consulting_brands() -> None:
    """ASSERTS that zero legacy consulting brands (NTT DATA, Everis) are hardcoded in src/."""
    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    banned_brands = [r"\bNTT DATA\b", r"\bEveris\b", r"\bWhyNttData\b"]
    
    violations = []
    for p in root.rglob("*.py"):
        # Skip audit probes and tests
        if "auditor" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            if sline.startswith("#"):
                continue
            for pat in banned_brands:
                if re.search(pat, sline, re.IGNORECASE):
                    violations.append(f"{p.relative_to(root)}:L{idx} -> {sline}")

    assert not violations, f"Found hardcoded consulting brands in codebase:\n" + "\n".join(violations)


def test_no_currency_guessing_by_language() -> None:
    """ASSERTS that no file guesses currency based on whether doc_lang == 'es'."""
    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    bad_patterns = [
        r'currency\s*=\s*["\']€["\']\s+if\s+doc_lang\s*==\s*["\']es["\']',
        r'if\s+doc_lang\s*==\s*["\']es["\']:\s*currency\s*=\s*["\']€["\']',
    ]

    violations = []
    for p in root.rglob("*.py"):
        if "auditor" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            for pat in bad_patterns:
                if re.search(pat, sline):
                    violations.append(f"{p.relative_to(root)}:L{idx} -> {sline}")

    assert not violations, f"Found currency guessing by language antipattern:\n" + "\n".join(violations)


def test_no_hardcoded_client_entities_in_prompts() -> None:
    """ASSERTS that generic prompts do not contain specific client names or plant locations."""
    prompts_dir = Path(__file__).resolve().parents[2] / "src" / "assessment_engine" / "domain" / "prompts"
    banned_entities = [r"\bmolins\b", r"\bsecil\b", r"\bsant vicen[çc]\b"]

    violations = []
    for p in prompts_dir.rglob("*.yaml"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            for pat in banned_entities:
                if re.search(pat, sline, re.IGNORECASE):
                    violations.append(f"{p.name}:L{idx} -> {sline}")

    assert not violations, f"Found client-specific entities in generic prompts:\n" + "\n".join(violations)


def test_no_raw_tower_dictionaries_in_global_payload_builder() -> None:
    """ASSERTS that build_global_report_payload does not contain hardcoded Spanish tower maps."""
    p = Path(__file__).resolve().parents[2] / "src" / "assessment_engine" / "application" / "build_global_report_payload.py"
    text = p.read_text(encoding="utf-8")
    assert "TOWER_NAMES_MAP" not in text, "Found legacy hardcoded TOWER_NAMES_MAP in build_global_report_payload.py"
    assert "TOWER_CRITICAL_DECISIONS" not in text, "Found legacy hardcoded TOWER_CRITICAL_DECISIONS in build_global_report_payload.py"


def test_no_spanish_in_yaml_prompts_registry() -> None:
    """ASSERTS that all YAML prompts in registry are 100% technical English."""
    prompts_dir = Path(__file__).resolve().parents[2] / "src" / "assessment_engine" / "domain" / "prompts" / "registry"
    spanish_char_pattern = re.compile(r'[\"\'][^\"\'\n]*[áéíóúÁÉÍÓÚñÑ¿¡][^\"\'\n]*[\"\']')

    violations = []
    for y in sorted(prompts_dir.glob("*.yaml")):
        for idx, l in enumerate(y.read_text(encoding="utf-8").splitlines(), 1):
            if spanish_char_pattern.search(l) and "CLICH" not in l.upper():
                violations.append(f"{y.name}:L{idx} -> {l.strip()}")

    assert not violations, f"Found Spanish sentences in YAML prompts:\n" + "\n".join(violations)


def test_no_inline_language_ternaries_in_document_adapters() -> None:
    """ASSERTS that core document adapters contain zero inline language conditionals or ternaries."""
    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine" / "adapters"
    cleansed_files = [
        "render_tower_blueprint.py",
        "render_commercial_report.py",
        "render_global_report_from_template.py",
        "render_tower_annex_from_template.py",
        "compilers/ast_table_builders.py",
        "compilers/payload_to_ast.py",
        "compilers/asis_fair_chapter.py",
        "compilers/asis_appendices_chapter.py",
        "compilers/asis_conclusions_chapter.py",
        "compilers/asis_maturity_chapter.py",
        "compile_asis_docx_from_modules.py",
        "generate_asis_markdown_modules.py",
    ]
    banned_patterns = [
        re.compile(r"\b(doc_lang|lang|meta_lang)\s*==\s*[\"'][a-zA-Z_\-]+[\"']"),
        re.compile(r"if\s+.*?(doc_lang|lang|meta_lang)\b.*?else"),
    ]

    violations = []
    for rel_path in cleansed_files:
        p = root / rel_path
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            if sline.startswith("#"):
                continue
            for pat in banned_patterns:
                if pat.search(sline):
                    violations.append(f"{rel_path}:L{idx} -> {sline}")

    assert not violations, f"Found inline language conditionals in document adapters:\n" + "\n".join(violations)


def test_no_optional_language_defaults_in_adapters() -> None:
    """Quality Gate AST: Verify no adapter or compiler function defines optional default language parameters."""
    import ast

    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    violations = []

    for rel_dir in ["adapters", "adapters/compilers"]:
        target_dir = root / rel_dir
        if not target_dir.exists():
            continue
        for p in target_dir.glob("*.py"):
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = node.args.args
                    defaults = node.args.defaults
                    num_defaults = len(defaults)
                    if num_defaults > 0:
                        default_args = args[-num_defaults:]
                        for arg, default in zip(default_args, defaults):
                            if arg.arg in ("doc_lang", "lang", "locale", "meta_lang", "target_lang"):
                                if isinstance(default, ast.Constant) and isinstance(default.value, str):
                                    rel_path = p.relative_to(root)
                                    violations.append(
                                        f"{rel_path}:{node.lineno} -> def {node.name}(..., {arg.arg} = '{default.value}')"
                                    )

    assert not violations, (
        f"Found forbidden optional language defaults in adapters/compilers (language must be mandatory):\n"
        + "\n".join(violations)
    )


def test_no_default_string_literals_in_translation_calls() -> None:
    """Quality Gate AST: Verify no t() or get_localized_string() call defines hardcoded default strings."""
    import ast

    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    violations = []

    for p in root.rglob("*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ("t", "get_localized_string"):
                    for kw in node.keywords:
                        if kw.arg == "default" and isinstance(kw.value, (ast.Constant, ast.JoinedStr)):
                            rel_path = p.relative_to(root)
                            violations.append(
                                f"{rel_path}:{node.lineno} -> {func_name}(..., default=...)"
                            )

    assert not violations, (
        f"Found forbidden hardcoded string defaults in translation calls (truth must reside in locales.json):\n"
        + "\n".join(violations)
    )


def test_no_hardcoded_locale_es_in_src() -> None:
    """ASSERTS that zero Python files in src/assessment_engine hardcode fallback to 'es'."""
    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    pat = re.compile(
        r"""(?:locale|doc_lang|language)\s*[:=]\s*["']es["']|or\s+["']es["']|default\s*=\s*["']es["']|Field\(["']es["']"""
    )
    violations = []
    for p in root.rglob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            if not (sline.startswith("#") or sline.startswith('"""') or sline.startswith("'''")):
                if pat.search(sline):
                    violations.append(f"{p.relative_to(root)}:L{idx} -> {sline}")

    assert not violations, (
        f"Found hardcoded 'es' fallback in src/assessment_engine (must default to 'en' or use variable):\n"
        + "\n".join(violations)
    )


def test_no_spanish_characters_in_python_code() -> None:
    """ASSERTS that production code in src/assessment_engine contains zero Spanish accented characters."""
    root = Path(__file__).resolve().parents[2] / "src" / "assessment_engine"
    spanish_accents = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
    
    # Exclude files where Spanish accents are intentional probe regexes, regional formatters, or legacy maturity bands
    whitelisted_files = {
        "comment_quality.py",
        "localization.py",
        "enforce_english_comments.py",
        "code_hygiene.py",
        "maturity_band.py",
        "argon_gate.py",
    }

    violations = []
    for p in root.rglob("*.py"):
        if p.name in whitelisted_files:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            sline = line.strip()
            if sline.startswith("#") or sline.startswith('"""') or sline.startswith("'''"):
                continue
            if spanish_accents.search(sline):
                # Ignore character-set regexes like [áéíóúñ]
                if not ("[áéíóúñ" in sline or "a-zá" in sline or "a-zà" in sline):
                    violations.append(f"{p.relative_to(root)}:L{idx} -> {sline}")

    assert not violations, (
        f"Found Spanish accented characters in Python production code:\n"
        + "\n".join(violations)
    )




