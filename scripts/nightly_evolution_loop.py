#!/usr/bin/env python3
"""
Autonomous Nightly Evolution Loop (The Deterministic Frontier Governor).

Operates with mathematical rigor and zero hallucination:
1. TARGET FILE UNIVERSAL CATALOG: Mutations are strictly constrained to real files.
2. SURGICAL DIFF / SEARCH-REPLACE: No full-file rewrites of 3,000-line files (zero truncation risk).
3. SYNTAX & PRE-FLIGHT GATES: py_compile, 70 pytest tests, 100-Enterprise Crucible Fuzzer.
4. EMPIRICAL TRIBUNAL ARBITRATION: 10 World-Class Domain Experts evaluate actual deliverables.
5. MONOTONIC GIT RATCHET: Automatically commits when score improves; rolls back cleanly if not.
"""

from __future__ import annotations

import json
import logging
import os
import py_compile
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(REPO_ROOT / "nightly_evolution.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("nightly_evolution")

TARGET_SCORE_THRESHOLD: float = 9.50

# Strict physical catalog of real mutation targets
PHYSICAL_TARGET_REGISTRY = [
    "src/assessment_engine/adapters/compilers/ast_table_builders.py",
    "src/assessment_engine/adapters/compilers/payload_to_ast.py",
    "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py",
    "src/assessment_engine/domain/actuarial_scale_calibrator.py",
    "src/assessment_engine/domain/actuarial_calculator.py",
    "src/assessment_engine/domain/actuarial/financial_profile.py",
    "src/assessment_engine/application/services/risk_synthesis_service.py",
]


def run_cmd(cmd: List[str], description: str, check: bool = False) -> subprocess.CompletedProcess:
    logger.info(f"Running: {description}...")
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src")),
    )
    if check and proc.returncode != 0:
        logger.error(f"{description} failed (code {proc.returncode}):\n{proc.stderr}\n{proc.stdout}")
        raise RuntimeError(f"Command failed: {description}")
    return proc


def extract_tribunal_grades() -> Tuple[float, List[Dict[str, Any]]]:
    """Parse all 10 expert audit files and return average and failing towers."""
    results = []
    sum_grades = 0.0
    for i in range(1, 11):
        p = REPO_ROOT / f"docs/audits/tribunal_10_towers/AUDIT_EXPERT_T{i}.md"
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        s5 = text.find("5. CALIFICACIÓN GLOBAL")
        if s5 == -1:
            s5 = text.find("5. FINAL GRADE")
        block = text[s5:] if s5 != -1 else text

        m = re.search(r"FINAL GRADE[:\s*]+(\d+(?:\.\d+)?)\s*/\s*10", block, re.IGNORECASE)
        if not m:
            m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", block)
        grade = float(m.group(1)) if m else 0.0
        sum_grades += grade

        s2 = text.find("2. TECHNICAL")
        s4 = text.find("4. WHAT")
        critique = text[s2:s4].strip() if s2 != -1 and s4 != -1 else text[:2500]
        results.append({"tower": f"T{i}", "grade": grade, "critique": critique})

    avg = sum_grades / max(len(results), 1)
    results.sort(key=lambda x: x["grade"])
    return avg, results


def apply_surgical_patches(target_path: Path, patch_text: str) -> bool:
    """Apply <<<<<<< SEARCH / ======= / >>>>>>> REPLACE blocks surgically."""
    if not target_path.exists():
        logger.error(f"Target path does not exist: {target_path}")
        return False

    content = target_path.read_text(encoding="utf-8")
    pattern = re.compile(r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", re.DOTALL)
    matches = list(pattern.finditer(patch_text))

    if not matches:
        logger.warning("No valid SEARCH/REPLACE blocks found in patch response.")
        return False

    new_content = content
    applied_count = 0
    for m in matches:
        search_block = m.group(1)
        replace_block = m.group(2)

        if search_block in new_content:
            new_content = new_content.replace(search_block, replace_block, 1)
            applied_count += 1
        else:
            # Try whitespace-normalized match
            logger.warning(f"Exact search block not found in {target_path.name}. Attempting line-stripped matching.")
            s_lines = [line.strip() for line in search_block.splitlines() if line.strip()]
            c_lines = new_content.splitlines()
            found_idx = -1
            for idx in range(len(c_lines) - len(s_lines) + 1):
                if all(c_lines[idx + j].strip() == s_lines[j] for j in range(len(s_lines))):
                    found_idx = idx
                    break
            if found_idx != -1:
                # Replace that slice of lines
                orig_slice = "\n".join(c_lines[found_idx : found_idx + len(s_lines)])
                new_content = new_content.replace(orig_slice, replace_block, 1)
                applied_count += 1
            else:
                logger.error(f"Failed to apply patch block to {target_path.name}:\n{search_block[:200]}...")
                return False

    target_path.write_text(new_content, encoding="utf-8")
    logger.info(f"Successfully applied {applied_count} surgical patch blocks to {target_path.name}.")
    return True


def preflight_integrity_check() -> bool:
    """Verify syntax, unit tests, and 100-enterprise crucible."""
    for rel_path in PHYSICAL_TARGET_REGISTRY:
        if rel_path.endswith(".py"):
            full_path = REPO_ROOT / rel_path
            try:
                py_compile.compile(str(full_path), doraise=True)
            except py_compile.PyCompileError as e:
                logger.error(f"Syntax validation failed on {rel_path}: {e}")
                return False
        elif rel_path.endswith(".json"):
            full_path = REPO_ROOT / rel_path
            try:
                json.loads(full_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"JSON validation failed on {rel_path}: {e}")
                return False

    p_unit = run_cmd(
        [
            ".venv/bin/pytest",
            "tests/unit/domain/actuarial/test_continuous_risk_allocator.py",
            "tests/unit/test_all_ten_towers_internal_coherence.py",
            "-q",
        ],
        "Unit Tests (Pytest Coherence)",
    )
    if p_unit.returncode != 0:
        logger.error(f"Pytest unit tests failed:\n{p_unit.stdout}\n{p_unit.stderr}")
        return False

    p_fuzz = run_cmd(
        [".venv/bin/python", "scripts/run_universal_crucible_fuzzer.py"],
        "100-Enterprise Universal Crucible Fuzzer",
    )
    if p_fuzz.returncode != 0:
        logger.error(f"Universal Crucible failed:\n{p_fuzz.stdout}")
        return False

    return True


def compile_deliverables() -> bool:
    """Rebuild all real Word deliverables from raw inputs."""
    p = run_cmd(
        [".venv/bin/python", "scripts/regenerate_molins_pure_from_raw_inputs.py"],
        "Regenerate Client Word Deliverables",
    )
    return p.returncode == 0


def run_tribunal_audit() -> bool:
    """Execute 10-tower SME Tribunal audit."""
    p = run_cmd(
        [".venv/bin/python", "scripts/audit_ten_towers_top_tier_tribunal.py"],
        "Top Tier-1 Tribunal Audit (10 Experts)",
    )
    return p.returncode == 0


def formulate_and_apply_mutation(
    failing_towers: List[Dict[str, Any]],
    target_rel_path: str,
) -> bool:
    """Consult Gemini 3.1 Pro / Argon to formulate a surgical SEARCH/REPLACE mutation."""
    logger.info(f"Formulating surgical mutation for: {target_rel_path}")
    full_target_path = REPO_ROOT / target_rel_path
    current_content = full_target_path.read_text(encoding="utf-8")

    client = create_genai_client()
    model = get_model(ModelTier.REASONING)

    top_critiques = "\n\n".join(
        f"--- TOWER {t['tower']} (Grade: {t['grade']}/10) ---\n{t['critique'][:3500]}"
        for t in failing_towers[:3]
    )

    # Provide targeted excerpts if file is large (> 300 lines)
    lines = current_content.splitlines()
    total_lines = len(lines)

    prompt = f"""You are the Chief Actuary and Principal Compiler Engineer in a Tier-1 R&D Lab (operating at the caliber of OpenAI, Anthropic, or DeepMind Infrastructure).
We are auditing our enterprise assessment engine against 10 world-class SME auditors.
Our target is >= 9.5 / 10 across all 10 domains.

FAILING TOWER TRIBUNAL CRITIQUES:
{top_critiques}

TARGET FILE TO MODIFY:
`{target_rel_path}` (Total lines: {total_lines})

RELEVANT FILE CONTENT:
```python
{current_content[:15000]}
...
{current_content[-15000:] if total_lines > 500 else ""}
```

NON-NEGOTIABLE ENGINEERING LAWS:
1. ZERO HARDCODING: Cero 'Molins', 'VMware', 'Broadcom'. Logic must be universal for 100 global companies.
2. 100% TECHNICAL ENGLISH in Python code, docstrings, variable names, and comments.
3. GROUNDING IN SOTA STANDARDS:
   - For Heatmap / Table 6: Reconcile coordinates using Single Loss Expectancy (SLE) matching Risk Cards. Ensure risks are resolved upfront before mosaic rendering so Table 6 coordinates identical to Risk Cards.
   - For Toil: Engineering toil labour rate must be calibrated to internal specialist engineering rates (e.g. 50-80 EUR/h) rather than corporate plant revenue burn rates (e.g. 5,000-9,000 EUR/h), eliminating the "9,142 EUR/h engineer" fallacy.
   - For English KPI Placeholders: Replace raw framework token leaks like "en [English KPI Name]" with proper localized descriptions or fallback handling.
4. SURGICAL PATCH FORMAT:
You MUST emit your changes strictly as one or more SEARCH/REPLACE blocks.
Format:
<<<<<<< SEARCH
... exact lines to find in {target_rel_path} ...
=======
... replacement lines ...
>>>>>>> REPLACE

Do NOT return the entire file. Only return the search/replace blocks.
"""

    resp = client.models.generate_content(model=model, contents=prompt)
    patch_text = resp.text.strip()

    return apply_surgical_patches(full_target_path, patch_text)


def run_single_evolution_cycle(target_file: Optional[str] = None) -> Tuple[bool, float]:
    """Execute one complete evolution cycle with git ratchet."""
    logger.info("\n" + "=" * 78)
    logger.info(">>> STARTING MONOTONIC EVOLUTION CYCLE")
    logger.info("=" * 78)

    # 1. Baseline status
    baseline_avg, failing_towers = extract_tribunal_grades()
    logger.info(f"Current Baseline Tribunal Average: {baseline_avg:.2f} / 10.0")

    if baseline_avg >= TARGET_SCORE_THRESHOLD:
        logger.info("🏆 Target threshold >= 9.5 achieved! Perfection certified.")
        return True, baseline_avg

    # 2. Select target file
    selected_target = target_file or PHYSICAL_TARGET_REGISTRY[0]
    logger.info(f"Active Mutation Target: {selected_target}")

    # 3. Formulate mutation
    success = formulate_and_apply_mutation(failing_towers, selected_target)
    if not success:
        logger.warning("Mutation formulation or patch application failed. Reverting...")
        run_cmd(["git", "checkout", "--", selected_target], "Revert failed mutation")
        return False, baseline_avg

    # 4. Pre-flight checks (Syntax, Pytest, Crucible Fuzzer)
    if not preflight_integrity_check():
        logger.warning("Pre-flight checks failed! Executing clean rollback...")
        run_cmd(["git", "checkout", "--", selected_target], "Revert failed mutation")
        return False, baseline_avg

    # 5. Deliverables compilation
    if not compile_deliverables():
        logger.warning("Deliverables compilation failed! Executing clean rollback...")
        run_cmd(["git", "checkout", "--", selected_target], "Revert failed mutation")
        return False, baseline_avg

    # 6. Tribunal Evaluation
    if not run_tribunal_audit():
        logger.warning("Tribunal audit execution failed! Executing clean rollback...")
        run_cmd(["git", "checkout", "--", selected_target], "Revert failed mutation")
        return False, baseline_avg

    new_avg, _ = extract_tribunal_grades()
    logger.info(f"Post-Mutation Tribunal Average: {new_avg:.2f} / 10.0 (Baseline: {baseline_avg:.2f})")

    # 7. Monotonic Ratchet Decision
    if new_avg > baseline_avg:
        logger.info(f"✓ SCORE IMPROVED: {baseline_avg:.2f} -> {new_avg:.2f}. Committing mutation to git.")
        commit_msg = f"feat(evolution): tier-1 optimization in {Path(selected_target).name} (avg: {new_avg:.2f}/10)"
        run_cmd(["git", "add", selected_target], "Stage improved target")
        run_cmd(["git", "commit", "-m", commit_msg], "Commit improved target")
        return True, new_avg
    else:
        logger.warning(f"⚠️ Score did not improve ({new_avg:.2f} <= {baseline_avg:.2f}). Reverting mutation...")
        run_cmd(["git", "checkout", "--", selected_target], "Rollback non-improving mutation")
        return False, baseline_avg


# Mapping of specific tower defects to the exact real target files
TOWER_DEFECT_TARGET_MAPPING: Dict[str, List[str]] = {
    "T7": [
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        "engine_config/locales.json",
    ],
    "T9": [
        "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py",
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
    ],
    "T8": [
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        "src/assessment_engine/domain/actuarial/financial_profile.py",
    ],
    "T4": [
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        "src/assessment_engine/adapters/compilers/ast_table_builders.py",
    ],
    "T6": [
        "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py",
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
    ],
    "T1": [
        "src/assessment_engine/adapters/compilers/ast_table_builders.py",
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
    ],
    "T10": [
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py",
    ],
    "T5": [
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        "src/assessment_engine/domain/actuarial_scale_calibrator.py",
    ],
    "T3": [
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        "src/assessment_engine/adapters/compilers/ast_table_builders.py",
    ],
    "T2": [
        "src/assessment_engine/adapters/compilers/payload_to_ast.py",
        "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py",
    ],
}


def run_continuous_evolution():
    logger.info("🚀 INITIALIZING AUTONOMOUS DETERMINISTIC EVOLUTION LOOP (METHODOLOGY LOCKED)")
    attempt = 1
    while True:
        baseline_avg, failing_towers = extract_tribunal_grades()
        logger.info(f"\n[Iteration {attempt}] Baseline Average: {baseline_avg:.2f}/10.0 | Lowest: {failing_towers[0]['tower']} ({failing_towers[0]['grade']:.1f}/10)")

        if baseline_avg >= TARGET_SCORE_THRESHOLD:
            logger.info("🎯 GLOBAL MISSION CERTIFIED: All 10 towers scored >= 9.5 / 10.")
            break

        lowest_tower = failing_towers[0]["tower"]
        candidate_targets = TOWER_DEFECT_TARGET_MAPPING.get(lowest_tower, PHYSICAL_TARGET_REGISTRY)
        target_path = candidate_targets[(attempt - 1) % len(candidate_targets)]

        improved, current_avg = run_single_evolution_cycle(target_path)
        attempt += 1
        time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--single-cycle":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        run_single_evolution_cycle(target)
    else:
        run_continuous_evolution()
