from __future__ import annotations

import ast
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from google import genai

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src" / "assessment_engine"
COVERAGE_FILE = ROOT / "working" / "coverage.json"
REPORT_OUTPUT = ROOT / "docs" / "audits" / "NEUROSYMBOLIC_CODEBASE_AUDIT_REPORT.md"


@dataclass
class FileMetric:
    rel_path: str
    abs_path: Path
    loc: int
    functions_count: int
    classes_count: int
    in_degree: int
    out_degree: int
    string_refs_count: int
    percent_covered: float
    verdict: str = "PENDING"
    rationale: str = ""


def get_all_python_files(base_dir: Path) -> list[Path]:
    return sorted(
        [
            p
            for p in base_dir.rglob("*.py")
            if not p.name.startswith("__")
            and "_legacy" not in p.parts
            and ".venv" not in p.parts
        ]
    )


def extract_imports(file_path: Path) -> set[str]:
    """Parse AST to extract imported module names."""
    imported_modules: set[str] = set()
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return imported_modules

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
    return imported_modules


def extract_ast_stats(file_path: Path) -> tuple[int, int, int]:
    """Returns (loc, functions_count, classes_count)."""
    text = file_path.read_text(encoding="utf-8")
    loc = len([line for line in text.splitlines() if line.strip()])
    try:
        tree = ast.parse(text)
        funcs = len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        return loc, funcs, classes
    except Exception:
        return loc, 0, 0


def build_import_graph(all_files: list[Path]) -> tuple[nx.DiGraph, dict[str, Path]]:
    graph = nx.DiGraph()
    path_to_mod: dict[Path, str] = {}
    mod_to_path: dict[str, Path] = {}

    for p in all_files:
        rel = p.relative_to(ROOT)
        # e.g. src/assessment_engine/application/cli.py -> assessment_engine.application.cli
        parts = list(p.relative_to(SRC_DIR.parent).parts)
        if parts[-1].endswith(".py"):
            parts[-1] = parts[-1][:-3]
        mod_name = ".".join(parts)
        path_to_mod[p] = mod_name
        mod_to_path[mod_name] = p
        graph.add_node(mod_name, path=p)

    for p in all_files:
        src_mod = path_to_mod[p]
        imports = extract_imports(p)
        for imp in imports:
            # Check direct or prefix match
            for target_mod in mod_to_path:
                if imp == target_mod or imp.startswith(target_mod + ".") or target_mod.endswith("." + imp):
                    graph.add_edge(src_mod, target_mod)

    return graph, mod_to_path


def count_string_references(target_stem: str, all_files: list[Path], current_path: Path) -> int:
    """Check how often a file's name/stem appears in other files as a string literal."""
    count = 0
    pattern = re.compile(rf"\b{re.escape(target_stem)}\b")
    for p in all_files:
        if p == current_path:
            continue
        try:
            content = p.read_text(encoding="utf-8")
            if pattern.search(content):
                count += 1
        except Exception:
            continue
    return count


def load_dynamic_coverage() -> dict[str, float]:
    if not COVERAGE_FILE.exists():
        return {}
    try:
        cov_data = json.loads(COVERAGE_FILE.read_text(encoding="utf-8"))
        res = {}
        for fpath, data in cov_data.get("files", {}).items():
            norm_path = str(Path(fpath).resolve())
            pct = data.get("summary", {}).get("percent_covered", 0.0)
            res[norm_path] = pct
        return res
    except Exception:
        return {}


def audit_with_gemini_argon(
    metrics: list[FileMetric], client: genai.Client
) -> dict[str, tuple[str, str]]:
    """Arbitrates borderline files (0% coverage or in-degree <= 1) using Gemini 4 Argon."""
    suspicious = [
        m for m in metrics
        if m.in_degree <= 1 and m.percent_covered < 20.0
    ]
    print(f"\n🧠 Evaluando {len(suspicious)} archivos dudosos con Gemini 4 Argon...")

    results: dict[str, tuple[str, str]] = {}
    chunk_size = 8

    for i in range(0, len(suspicious), chunk_size):
        chunk = suspicious[i : i + chunk_size]
        items_text = []
        for m in chunk:
            head = m.abs_path.read_text(encoding="utf-8")[:1200]
            items_text.append(
                f"### FILE: {m.rel_path}\n"
                f"- LOC: {m.loc}, Funcs: {m.functions_count}, Classes: {m.classes_count}\n"
                f"- In-Degree (imported by): {m.in_degree}, Out-Degree: {m.out_degree}, String Refs: {m.string_refs_count}\n"
                f"- Dynamic Test Coverage: {m.percent_covered:.1f}%\n"
                f"--- EXTRACT ---\n{head}\n"
            )

        prompt = f"""Eres un Principal Systems Architect de Google / Palantir.
Evalúa estos {len(chunk)} archivos de un motor de arquitectura empresarial (Assessment Engine).
Para cada archivo, determina si es:
- CANONICAL_CORE (Componente esencial que debe mantenerse)
- ACTIVE_LEAF (CLI, script de renderizado o punto de entrada válido aunque no tenga importadores directos)
- SHADOW_DUPLICATE (Copia o módulo redundante con otro existente)
- CONFIRMED_ORPHAN (Código muerto sin función ni cobertura que debe ser eliminado)

Archivos a auditar:
{chr(10).join(items_text)}

Responde estrictamente en formato JSON con la siguiente estructura:
{{
  "evaluations": [
    {{
      "file": "ruta/al/archivo.py",
      "verdict": "CANONICAL_CORE | ACTIVE_LEAF | SHADOW_DUPLICATE | CONFIRMED_ORPHAN",
      "rationale": "Explicación técnica en 1 frase directa"
    }}
  ]
}}
"""
        try:
            resp = client.models.generate_content(
                model=get_model(ModelTier.REASONING),
                contents=prompt,
                config={"response_mime_type": "application/json", "temperature": 0.1},
            )
            data = json.loads(resp.text)
            for item in data.get("evaluations", []):
                results[item["file"]] = (item["verdict"], item["rationale"])
        except Exception as ex:
            print(f"⚠️ Error arbitraje chunk {i}: {ex}")

    return results


def main() -> None:
    print("=" * 80)
    print("  NEURO-SYMBOLIC CODEBASE AUDITOR (OCTUBRE 2026)")
    print("  AST Topology + Dynamic Execution Trace + Gemini 4 Argon")
    print("=" * 80)

    all_py_files = get_all_python_files(SRC_DIR)
    print(f"\n[1/4] 📦 Rastreados {len(all_py_files)} archivos Python en src/assessment_engine/...")

    graph, mod_to_path = build_import_graph(all_py_files)
    print(f"[2/4] 🕸️ Grafo de importaciones construido ({graph.number_of_nodes()} nodos, {graph.number_of_edges()} aristas)...")

    coverage_map = load_dynamic_coverage()
    print(f"[3/4] ⚡ Cobertura dinámica cargada ({len(coverage_map)} archivos con trazas)...")

    metrics: list[FileMetric] = []
    for p in all_py_files:
        rel = str(p.relative_to(ROOT))
        loc, funcs, classes = extract_ast_stats(p)
        mod_name = [m for m, path in mod_to_path.items() if path == p][0]
        in_deg = graph.in_degree(mod_name)
        out_deg = graph.out_degree(mod_name)
        string_refs = count_string_references(p.stem, all_py_files, p)
        cov_pct = coverage_map.get(str(p.resolve()), 0.0)

        # Baseline heuristic categorization
        if in_deg >= 3 and cov_pct > 0.0:
            verdict = "CANONICAL_CORE"
            rationale = f"Módulo nuclear altamente acoplado ({in_deg} dependientes) y ejecutado dinámicamente ({cov_pct:.1f}%)."
        elif "cli" in p.name or "run_" in p.name or "main" in p.name:
            verdict = "ACTIVE_LEAF"
            rationale = "Punto de entrada CLI o script de fase de orquestación."
        else:
            verdict = "PENDING"
            rationale = ""

        metrics.append(
            FileMetric(
                rel_path=rel,
                abs_path=p,
                loc=loc,
                functions_count=funcs,
                classes_count=classes,
                in_degree=in_deg,
                out_degree=out_deg,
                string_refs_count=string_refs,
                percent_covered=cov_pct,
                verdict=verdict,
                rationale=rationale,
            )
        )

    # Invoke Gemini 4 Argon for pending/borderline files
    client = genai.Client()
    arbitrage_results = audit_with_gemini_argon(metrics, client)

    for m in metrics:
        if m.rel_path in arbitrage_results:
            m.verdict, m.rationale = arbitrage_results[m.rel_path]
        elif m.verdict == "PENDING":
            if m.in_degree == 0 and m.string_refs_count == 0 and m.percent_covered == 0.0:
                m.verdict = "CONFIRMED_ORPHAN"
                m.rationale = "Sin dependientes estáticos, sin menciones en string y 0% de ejecución dinámica."
            else:
                m.verdict = "ACTIVE_LEAF"
                m.rationale = "Módulo hoja auxiliar o adaptador secundario."

    # Generate Markdown Report
    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as out:
        out.write("""---
status: Verified
owner: docs-governance
source_of_truth:
- ../../scripts/audit_neurosymbolic_codebase.py
- ../../src/assessment_engine/
last_verified_against: '2026-06-26'
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: explanation
verification_mode: editorial
---
# 🏛️ Auditoría Neuro-Simbólica de la Base de Código\n\n""")
        out.write("**Fecha:** Octubre 2026 | **Metodología:** Topología AST (NetworkX) + Trazabilidad Dinámica (`coverage.py`) + Árbitro Cognitivo (`gemini-4-argon`)\n\n")

        # Summary KPIs
        canonical = [m for m in metrics if m.verdict == "CANONICAL_CORE"]
        active_leaf = [m for m in metrics if m.verdict == "ACTIVE_LEAF"]
        shadow = [m for m in metrics if m.verdict == "SHADOW_DUPLICATE"]
        orphans = [m for m in metrics if m.verdict == "CONFIRMED_ORPHAN"]

        out.write("## 1. Resumen Ejecutivo de Salud del Código\n\n")
        out.write(f"- **Total de Archivos Auditados:** {len(metrics)}\n")
        out.write(f"- **Núcleo Canónico (Vital):** {len(canonical)} ({len(canonical)/len(metrics)*100:.1f}%)\n")
        out.write(f"- **Hojas Activas / Adaptadores:** {len(active_leaf)} ({len(active_leaf)/len(metrics)*100:.1f}%)\n")
        out.write(f"- **Módulos Sombra (Duplicados / Candidatos a Fusión):** {len(shadow)}\n")
        out.write(f"- **Huérfanos Confirmados (Código Muerto / Purga Segura):** {len(orphans)}\n\n")

        if orphans:
            out.write("## 2. ⚠️ Huérfanos Confirmados (Blast Radius = 0)\n\n")
            out.write("| Archivo | LOC | Cobertura | In-Degree | Razón Técnica de Purga |\n")
            out.write("| :--- | :---: | :---: | :---: | :--- |\n")
            for m in orphans:
                out.write(f"| `{m.rel_path}` | {m.loc} | {m.percent_covered:.1f}% | {m.in_degree} | {m.rationale} |\n")
            out.write("\n")

        if shadow:
            out.write("## 3. 👥 Módulos Sombra (Candidatos a Fusión / Refactor)\n\n")
            out.write("| Archivo | LOC | Cobertura | In-Degree | Diagnóstico de Fusión |\n")
            out.write("| :--- | :---: | :---: | :---: | :--- |\n")
            for m in shadow:
                out.write(f"| `{m.rel_path}` | {m.loc} | {m.percent_covered:.1f}% | {m.in_degree} | {m.rationale} |\n")
            out.write("\n")

        out.write("## 4. 📋 Inventario Exhaustivo Archivo a Archivo\n\n")
        out.write("| Archivo | Veredicto | LOC | Cobertura | In-Deg | Dictamen Funcional |\n")
        out.write("| :--- | :---: | :---: | :---: | :---: | :--- |\n")
        for m in sorted(metrics, key=lambda x: (x.verdict, x.rel_path)):
            out.write(f"| `{m.rel_path}` | **{m.verdict}** | {m.loc} | {m.percent_covered:.1f}% | {m.in_degree} | {m.rationale} |\n")

    print("\n" + "=" * 80)
    print("  RESULTADOS DE LA AUDITORÍA NEURO-SIMBÓLICA")
    print("=" * 80)
    print(f"  Total Archivos: {len(metrics)}")
    print(f"  ✅ Núcleo Canónico:       {len(canonical)}")
    print(f"  🍃 Hojas Activas / CLI:    {len(active_leaf)}")
    print(f"  👥 Módulos Sombra:         {len(shadow)}")
    print(f"  🗑️  Huérfanos Confirmados:  {len(orphans)}")
    print(f"\n📄 Informe exhaustivo guardado en: {REPORT_OUTPUT}")
    print("=" * 80)


if __name__ == "__main__":
    main()
