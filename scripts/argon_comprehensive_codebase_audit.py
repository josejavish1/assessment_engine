#!/usr/bin/env python3
"""Execute a comprehensive, adversarial codebase-wide anti-pattern audit using gemini-4-argon."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

SRC_DIR = REPO_ROOT / "src/assessment_engine"

TENANT_TOKENS = (
    "molins",
    "secil",
    "sant vicen",
    "cemento",
    "cement",
    "sant vicenc",
    "sant vicenç",
)

SPANISH_DIACRITICS = re.compile(r"[áéíóúÁÉÍÓÚñÑüÜ]")

SUSPICIOUS_KEYWORD_PATTERNS = re.compile(
    r"\b(in\s+text\.lower\(\)|in\s+finding_text|in\s+str\(hc\.get\(\"finding\"\)\))",
    re.IGNORECASE,
)


def run_static_codebase_scan() -> Dict[str, Any]:
    """Scans all Python files in src/assessment_engine for anti-patterns."""
    scan_results = {
        "tenant_leakage": [],
        "spanish_diacritics": [],
        "keyword_scraping": [],
        "hardcoded_tower_ids": [],
        "suppressed_exceptions": [],
        "total_files_scanned": 0,
        "scanned_files": [],
    }

    py_files = sorted(SRC_DIR.glob("**/*.py"))
    scan_results["total_files_scanned"] = len(py_files)

    for py_file in py_files:
        rel_path = str(py_file.relative_to(REPO_ROOT))
        scan_results["scanned_files"].append(rel_path)
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        # 1. Tenant token search
        for line_idx, line in enumerate(lines, 1):
            line_lower = line.lower()
            for tok in TENANT_TOKENS:
                if tok in line_lower and "tenant_tokens" not in line_lower and "#" not in line[:line.find(tok) if tok in line else 0]:
                    scan_results["tenant_leakage"].append({
                        "file": rel_path,
                        "line": line_idx,
                        "token": tok,
                        "snippet": line.strip()[:100],
                    })

            # 2. Spanish diacritics in python code (excluding comments)
            stripped_line = line.split("#")[0]
            if SPANISH_DIACRITICS.search(stripped_line):
                scan_results["spanish_diacritics"].append({
                    "file": rel_path,
                    "line": line_idx,
                    "snippet": line.strip()[:100],
                })

            # 3. Keyword scraping
            if SUSPICIOUS_KEYWORD_PATTERNS.search(line):
                scan_results["keyword_scraping"].append({
                    "file": rel_path,
                    "line": line_idx,
                    "snippet": line.strip()[:100],
                })

            # 4. Hardcoded tower IDs in conditional logic (e.g. if code == "T1")
            if re.search(r'\b(if|elif)\s+.*["\']T[1-9]|["\']T10["\']', line) and "DOMAIN_PHYSICAL_ARCHETYPES" not in line:
                scan_results["hardcoded_tower_ids"].append({
                    "file": rel_path,
                    "line": line_idx,
                    "snippet": line.strip()[:100],
                })

        # 5. AST scan for bare except / pass
        try:
            tree = ast.parse(content, filename=rel_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    # Check if body is just 'pass'
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        scan_results["suppressed_exceptions"].append({
                            "file": rel_path,
                            "line": node.lineno,
                            "type": "bare_pass_exception",
                        })
        except SyntaxError:
            pass

    return scan_results


def main() -> None:
    print("=" * 80)
    print("STARTING COMPREHENSIVE STATIC SCAN ACROSS SRC/ASSESSMENT_ENGINE...")
    print("=" * 80)

    scan = run_static_codebase_scan()
    print(f"Total files scanned: {scan['total_files_scanned']}")
    print(f"Tenant token leakages: {len(scan['tenant_leakage'])}")
    print(f"Spanish diacritics occurrences: {len(scan['spanish_diacritics'])}")
    print(f"Suspicious keyword scraping matches: {len(scan['keyword_scraping'])}")
    print(f"Hardcoded tower ID conditionals: {len(scan['hardcoded_tower_ids'])}")
    print(f"Suppressed pass exceptions: {len(scan['suppressed_exceptions'])}")

    # Format prompt for gemini-4-argon
    audit_summary_json = json.dumps(
        {
            "tenant_leakage": scan["tenant_leakage"][:20],
            "spanish_diacritics": scan["spanish_diacritics"][:20],
            "keyword_scraping": scan["keyword_scraping"][:20],
            "hardcoded_tower_ids": scan["hardcoded_tower_ids"][:25],
            "suppressed_exceptions": scan["suppressed_exceptions"][:20],
        },
        indent=2,
    )

    prompt = f"""You are gemini-4-argon, acting as the Distinguished Staff/Principal Distributed Systems Architect, Lead Enterprise Ontologist, and Chief Adversarial Quality Auditor.

THE CONTEXT:
The user is concerned about the architectural integrity of the entire Assessment Engine codebase (`src/assessment_engine/`).
We just eradicated an anti-pattern where text-scraping was used to assign RTOs, but the user is demanding a full, deep adversarial review of ALL remaining anti-patterns in the codebase before proceeding to any new phase.

USER MANDATES:
1. Zero Hardcoding: The codebase must be 100% scale-agnostic ($20M SMB to $500B+ Global Tier-1) across ANY vertical. No client names, no fixed numbers, no hidden magic multipliers.
2. 100% Technical English: Zero Spanish words, stems, or regex patterns in any `.py` file. Localization is strictly in `locales.json`.
3. Architecture Purity: No split-brain states, no suppressed exceptions, no heuristic string scraping, and no arbitrary tower hardcoding.

STATIC CODEBASE AUDIT TELEMETRY:
Total files scanned in `src/assessment_engine`: {scan['total_files_scanned']}
Telemetry findings:
{audit_summary_json}

YOUR TASK:
Conduct an exhaustive, deep adversarial audit of the entire codebase based on this telemetry and architectural design.
1. Categorize all detected anti-patterns into Severity Tiers (CRITICAL, HIGH, MEDIUM, LOW).
2. For each anti-pattern:
   - Identify the exact architectural smell / defect.
   - Explain WHY it threatens multi-tenancy, scale invariance, or language decoupling.
   - Provide the clean, idiomatic Tier-1 remediation plan.
3. Formulate an Executive Roadmap of remediations to achieve 10.0/10 Global Production Certification.

Provide the report in strictly 100% Technical English, formatted with YAML front matter for docs governance.
"""

    client = create_genai_client()
    model = get_model(ModelTier.REASONING)
    print("\nConsulting Argon for Comprehensive Codebase Audit...")
    response = client.models.generate_content(model=model, contents=prompt)

    out_file = REPO_ROOT / "docs/audits/ARGON_COMPREHENSIVE_CODEBASE_ANTIPATTERN_AUDIT.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    front_matter = (
        "---\n"
        "status: Verified\n"
        "owner: docs-governance\n"
        "source_of_truth:\n"
        "- docs/README.md\n"
        "last_verified_against: 2026-11-08\n"
        "applies_to:\n"
        "- gemini\n"
        "- architecture\n"
        "doc_type: operational\n"
        "diataxis: reference\n"
        "verification_mode: editorial\n"
        "---\n"
    )
    out_file.write_text(front_matter + response.text, encoding="utf-8")

    print("=" * 80)
    lines = response.text.splitlines()
    for line in lines[:80]:
        print(line)
    if len(lines) > 80:
        print(f"... ({len(lines) - 80} more lines in {out_file.name})")
    print("=" * 80)


if __name__ == "__main__":
    main()
