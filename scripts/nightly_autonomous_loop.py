#!/usr/bin/env python3
"""
Autonomous Nightly Tribunal Loop (The Frontier SOTA Governor).

Internalizes the user's executive governance role to drive the codebase
to Tier-1 World-Class Excellence (Target Score: >= 9.5 / 10 across all 10 towers).

Non-Negotiable Architecture:
1. TARGET THRESHOLD: Strictly >= 9.5 / 10 (Zero compromise).
2. SOTA LITERATURE GROUNDING: Solutions must cite and implement peer-reviewed
   literature and RFCs (Open FAIR, Tasche 1999 Euler allocation, RFC 7938 BGP,
   RFC 8365 EVPN, ASHRAE TC 9.9, Google SRE Toil, Purdue ISA-95).
3. 9 FRONTIER LAWS: Zero hardcoding, 100% English, 100-enterprise scale invariance,
   dimensional homogeneity, zero fluff, empirical intake boundary.
4. CONTINUOUS RE-VERIFICATION: Every mutation must pass 70 pytest tests and the
   100-Enterprise Universal Crucible Fuzzer before being accepted.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nightly_frontier_loop")

TARGET_SCORE_THRESHOLD: float = 9.50

TIER1_FRONTIER_GOVERNANCE_LAWS = """
================================================================================
MANDATOS FUNDACIONALES DE INGENIERÍA TOP TIER-1 (ESTADO DEL ARTE MUNDIAL)
================================================================================
1. EXCELENCIA ABSOLUTA (OBJETIVO 9.5/10): Prohibido conformarse con aprobados justos (8.5). El objetivo es publicación y peritaje unánime sin reservas ante el Board of Directors.
2. ZERO HARDCODING: Cero nombres de clientes ('Molins'), marcas ('VMware', 'Broadcom') o constantes específicas. Toda ecuación y plantilla debe servir para 100 empresas de cualquier sector mundial.
3. LANGUAGE DECOUPLING: 100% Technical English en código Python, docstrings, logs, variables y nombres de funciones. Cero español en código (solo permitido en locales.json).
4. GROUNDING EN PAPERS Y ESTÁNDARES SOTA: Prohibido inventar heurísticas ad-hoc o reglas de consultoría barata. Las soluciones deben derivarse formalmente de la literatura:
   - Riesgo Actuarial: Open FAIR (ISO/IEC 27005), Tasche (1999) Euler Allocation Principle, Beta-PERT & Lognormal distributions.
   - Redes y Datacenter: RFC 7938 (BGP Clos IP Fabrics), RFC 8365 (EVPN-VXLAN), ASHRAE TC 9.9 Environmental Guidelines.
   - Resiliencia y OT: Purdue Model (ISA-95 / IEC 62443), Google SRE Error & Toil Budgets, RTO de física de transferencia de datos.
5. HOMOGENEIDAD DIMENSIONAL (BUCKINGHAM-PI): Una tasa horaria [C * T^-1] JAMÁS puede sumarse a un impacto por evento [C] o a una pérdida anual [C * T^-1] sin factor de conversión dimensional riguroso.
6. LÍMITE FÁCTICO DE ENTRADA (NO HALLUCINATED TELEMETRY): Solo disponemos de 2 fuentes: cuestionario y entrevista cualitativa. Prohibido fingir revisiones de código o volcados CLI. Las carencias empíricas se modelan como incertidumbre bayesiana / brecha de gobernanza.
7. VETO A LA JERGA DE CONSULTORÍA VACÍA (ANTI-FLUFF): Prohibido usar frases huecas ('solución moderna', 'robusta', 'escalable'). La prosa debe ser pericial, aséptica y matemática.
8. CAUSA COMÚN VS PARCHES LOCALES: Erradicar el defecto en el núcleo del compilador/dominio, nunca aplicar parches cosméticos para un cliente.
9. INVARIANTE DE NO REGRESIÓN: Toda mutación debe superar los 70 tests de pytest y el Fuzzer de 100 empresas globales. Si 1 torre baja de nota -> ROLLBACK INMEDIATO.
================================================================================
"""

def compile_deliverables() -> bool:
    logger.info("Compiling deliverables...")
    proc = subprocess.run(
        [sys.executable, "scripts/regenerate_molins_pure_from_raw_inputs.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        logger.error(f"Compilation failed:\n{proc.stderr}")
        return False
    return True

def run_tribunal() -> bool:
    logger.info("Running Top Tier-1 Tribunal (10 World-Class Experts)...")
    proc = subprocess.run(
        [sys.executable, "scripts/audit_ten_towers_top_tier_tribunal.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        logger.error(f"Tribunal execution failed:\n{proc.stderr}")
        return False
    return True

def run_tests_and_crucible() -> bool:
    logger.info("Executing 70 unit tests and 100-Enterprise Universal Crucible...")
    p1 = subprocess.run(
        [".venv/bin/pytest", "tests/unit/domain/actuarial/test_continuous_risk_allocator.py", "tests/unit/test_all_ten_towers_internal_coherence.py", "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if p1.returncode != 0:
        logger.error(f"Unit coherence tests failed:\n{p1.stdout}\n{p1.stderr}")
        return False

    p2 = subprocess.run(
        [sys.executable, "scripts/run_universal_crucible_fuzzer.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if p2.returncode != 0:
        logger.error(f"100-Enterprise Crucible Fuzzer failed:\n{p2.stdout}\n{p2.stderr}")
        return False

    return True

def extract_tribunal_feedback() -> Tuple[float, List[dict]]:
    results = []
    sum_grades = 0.0
    for i in range(1, 11):
        p = REPO_ROOT / f"docs/audits/tribunal_10_towers/AUDIT_EXPERT_T{i}.md"
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")

        s5 = text.find("5. FINAL GRADE")
        block = text[s5:] if s5 != -1 else text
        m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", block)
        grade = float(m.group(1)) if m else 0.0
        sum_grades += grade

        if grade < TARGET_SCORE_THRESHOLD:
            s2 = text.find("2. TECHNICAL")
            s4 = text.find("4. WHAT")
            critique = text[s2:s4].strip() if s2 != -1 and s4 != -1 else text[:2500]
            results.append({"tower": f"T{i}", "grade": grade, "critique": critique})

    avg = sum_grades / 10.0
    return avg, results

def determine_target_files_and_sota_strategy(failing_towers: List[dict]) -> Tuple[List[str], str]:
    logger.info("Consulting Gemini-4-Argon for 10-Tower Common Cause Analysis & SOTA Blueprint...")
    client = create_genai_client()
    model = get_model(ModelTier.REASONING)

    cons_file = REPO_ROOT / "docs/audits/ARGON_10_TOWERS_TOP_TIER_TRIBUNAL_CONSOLIDATED.md"
    cons_text = cons_file.read_text(encoding="utf-8") if cons_file.exists() else json.dumps(failing_towers, indent=2)

    prompt = f"""You are the Chief Scientist and Principal Systems Architect of an elite Tier-1 R&D Lab (operating at the caliber of OpenAI, Anthropic, or DeepMind Infrastructure).

We are auditing our Assessment Engine against the Top Tier-1 World Expert Tribunal across all 10 capability domains.
Our non-negotiable target is >= 9.5 / 10 across all 10 domains simultaneously.

CONSOLIDATED 10-TOWER AUDITOR TRIBUNAL REPORT:
{cons_text[:28000]}

GOVERNANCE LAWS:
{TIER1_FRONTIER_GOVERNANCE_LAWS}

YOUR CORE SCIENTIFIC MANDATE:
Do NOT treat these 10 domains in isolation. You must find the SINGLE OVERARCHING COMMON CAUSE that explains why these observations occur across multiple towers (e.g. monolithic server downtime formulas forced on non-availability domains like FinOps/Cyber, static shared glossaries, unaligned dynamic heatmap coordinates, lack of blast-radius modulation for branch vs core).

1. Identify the foundational peer-reviewed literature, RFCs, or formal industry standards that solve this common cause (e.g. Tasche 1999 Euler allocation, RFC 7938 Clos IP Fabrics, RFC 8365 EVPN-VXLAN, Open FAIR ISO 27005, Google SRE Toil, Purdue ISA-95).
2. Formulate the unified architectural solution in the compiler/domain core that solves the common cause for all 10 towers and all 100 simulated enterprises simultaneously without hardcoding.
3. Return a JSON structure containing:
   - "common_cause_diagnosis": unambiguous root-cause explanation
   - "sota_references": list of cited papers/RFCs
   - "target_files": list of relative file paths in repo to modify
   - "architectural_blueprint": clear, rigorous instructions for the synthesizer

Respond ONLY with valid JSON.
"""
    resp = client.models.generate_content(model=model, contents=prompt)
    txt = resp.text.strip()
    try:
        start = txt.find("{")
        end = txt.rfind("}") + 1
        if start != -1 and end != 0:
            parsed = json.loads(txt[start:end])
            candidates = parsed.get("target_files", [])
            valid_files = [f for f in candidates if (REPO_ROOT / f).is_file()]
            if not valid_files:
                valid_files = [
                    "src/assessment_engine/adapters/compilers/payload_to_ast.py",
                    "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py",
                ]
            return valid_files, json.dumps(parsed, indent=2)
    except Exception as e:
        logger.warning(f"Error parsing SOTA strategy: {e}")

    return ["src/assessment_engine/adapters/compilers/payload_to_ast.py", "src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py"], "Default SOTA Fallback"

def run_frontier_nightly_loop():
    iteration = 1
    best_avg = 0.0

    logger.info("🚀 INITIALIZING AUTONOMOUS FRONTIER NIGHTLY OPTIMIZER (TARGET: >= 9.5/10)")

    while True:
        logger.info(f"\n{'='*78}\n>>> FRONTIER ITERATION {iteration} | CURRENT TARGET: >= {TARGET_SCORE_THRESHOLD}/10\n{'='*78}")

        # Step 1: Pre-flight validation
        if not run_tests_and_crucible():
            logger.error("Pre-flight unit tests or 100-enterprise crucible failed! Refusing to proceed until baseline is green.")
            time.sleep(20)
            continue

        if not compile_deliverables():
            logger.error("Compilation failed. Cooldown and retry...")
            time.sleep(20)
            continue

        if not run_tribunal():
            logger.error("Tribunal execution failed. Cooldown and retry...")
            time.sleep(20)
            continue

        avg_grade, failing_towers = extract_tribunal_feedback()
        logger.info(f"📊 Global Tribunal Average: {avg_grade:.2f} / 10.0 (Best: {best_avg:.2f})")

        if avg_grade > best_avg:
            best_avg = avg_grade

        if not failing_towers:
            logger.info("🏆 PERFECTION ACHIEVED! ALL 10 TOWERS SCORED >= 9.5 / 10 UNANIMOUSLY.")
            logger.info("Mission certified. Nightly optimizer safely terminating.")
            break

        logger.info(f"Towers below 9.5 threshold: {len(failing_towers)}/10. Lowest: {min(f['grade'] for f in failing_towers):.1f}/10")

        # Synthesize common root cause across all failing towers simultaneously
        target_files, sota_blueprint = determine_target_files_and_sota_strategy(failing_towers)

        logger.info(f"Target files selected for mutation: {target_files}")
        logger.info(f"SOTA Architectural Blueprint generated:\n{sota_blueprint[:400]}...")

        # Delegate execution to Cognitive Orchestrator
        task_desc = f"""
        TASK: Elevate tower deliverables to >= 9.5/10 Top Tier-1 Excellence based on SOTA literature.

        SOTA BLUEPRINT & REFERENCES:
        {sota_blueprint}

        COMMON CAUSE CRITIQUES TO ERADICATE ACROSS ALL DOMAINS:
        {json.dumps(failing_towers, indent=2)}

        {TIER1_FRONTIER_GOVERNANCE_LAWS}
        """

        cmd = [
            sys.executable, "scripts/run_cognitive_orchestrator.py",
            "--task", task_desc,
            "--auto-merge"
        ]
        for tf in target_files:
            cmd.extend(["--target-file", tf])

        logger.info("Executing Cognitive Orchestrator in Ephemeral Worktree...")
        proc = subprocess.run(cmd, cwd=REPO_ROOT)
        if proc.returncode == 0:
            logger.info("✓ Mutation passed all worktree gates and successfully merged to main.")
        else:
            logger.warning(f"⚠️ Mutation rejected by worktree gates (code {proc.returncode}). Reverting to clean baseline.")

        iteration += 1
        time.sleep(15)

if __name__ == "__main__":
    run_frontier_nightly_loop()
