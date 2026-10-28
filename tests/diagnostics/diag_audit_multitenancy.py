#!/usr/bin/env python3
"""
Multi-Tenant Architecture Auditor for Assessment Engine.

This script performs a mathematical AST-based (Abstract Syntax Tree) and regex-based scan
over the entire codebase (specifically 'src/assessment_engine/') to identify any potential
architectural coupling, hardcoded client references, or static sector-based logic branching.
It classifies findings based on whether they pose a real multi-tenant risk.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set


class TenancyAuditor:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.src_dir = root_dir / "src/assessment_engine"
        
        # Forbidden client words and sector words to scan
        self.client_words = {"redeia", "eurovision", "reintel", "redinter", "eléctrica"}
        self.sector_words = {"energía", "energy", "retail", "banca", "banking", "healthcare", "salud"}
        
        # Files/directories that are exempt from strict tenant decoupling (e.g., specific ingest tools)
        self.exempt_files = {
            "ingest_redeia.py",
            "ingest_eurovision.py",
        }
        
        # Track all findings
        self.findings: List[Dict[str, Any]] = []

    def scan(self) -> None:
        """Scan core directories (src, templates, engine_config) recursively."""
        # 1. AST scan on Python core engine
        if self.src_dir.exists():
            for root, _, files in os.walk(self.src_dir):
                for file in files:
                    if not file.endswith(".py") or file in self.exempt_files:
                        continue
                    file_path = Path(root) / file
                    self._audit_file(file_path)

        # 2. Text scan on templates and engine configs
        for dir_name in ["templates", "engine_config"]:
            target_dir = self.root_dir / dir_name
            if not target_dir.exists():
                continue
            for root, _, files in os.walk(target_dir):
                for file in files:
                    if not file.lower().endswith((".json", ".yaml", ".yml", ".html")):
                        continue
                    file_path = Path(root) / file
                    self._audit_text_file(file_path)

    def _audit_text_file(self, file_path: Path) -> None:
        """Perform line-by-line text scans for templates and JSON/YAML configs."""
        relative_path = file_path.relative_to(self.root_dir)
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[-] Error reading {relative_path}: {e}")
            return

        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            matched_clients = [w for w in self.client_words if w in line_lower]
            if matched_clients:
                self._add_finding(
                    file=str(relative_path),
                    line_num=i,
                    category="TEMPLATE_COUPLING",
                    match=", ".join(matched_clients),
                    line_text=line.strip(),
                    severity="HIGH",
                    explanation=f"Template or configuration contains client-specific word(s): {matched_clients}."
                )

    def _audit_file(self, file_path: Path) -> None:
        """Perform AST and text-level audits on a specific Python file."""
        relative_path = file_path.relative_to(self.root_dir)
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[-] Error reading {relative_path}: {e}")
            return

        lines = content.splitlines()
        
        # Part 1: AST-Based Structural Scan
        # This allows us to find actual logical expressions, string constants, and comparisons.
        try:
            tree = ast.parse(content, filename=str(file_path))
            self._audit_ast(tree, relative_path, lines)
        except SyntaxError as e:
            # Fallback to pure regex if AST parsing fails (unlikely in verified code)
            self._add_finding(
                file=str(relative_path),
                line_num=e.lineno or 1,
                category="SYNTAX_ERROR",
                match=f"AST parsing failed: {e.msg}",
                line_text=lines[e.lineno - 1] if e.lineno and e.lineno <= len(lines) else "",
                severity="HIGH",
                explanation="File has syntax errors, cannot perform deep AST validation."
            )

    def _audit_ast(self, tree: ast.AST, relative_path: Path, lines: List[str]) -> None:
        """Traverse the AST to find string constants and comparisons containing forbidden keywords."""
        for node in ast.walk(tree):
            # 1. Search for string constants
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val_lower = node.value.lower()
                
                # Check for clients
                matched_clients = [w for w in self.client_words if w in val_lower]
                if matched_clients:
                    lineno = getattr(node, "lineno", 1)
                    line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
                    
                    # Ignore comment blocks or docstrings at the module level or function level
                    # AST constants that are just docstrings are usually located under an ast.Expr.
                    # Let's assess severity based on context.
                    severity = "MEDIUM"
                    explanation = f"String literal contains client-specific word(s): {matched_clients}."
                    
                    # If this is part of an assignment or a comparison, raise severity
                    if self._is_logical_context(node, tree):
                        severity = "HIGH"
                        explanation += " Detected within a logical expression or assignment."
                    
                    self._add_finding(
                        file=str(relative_path),
                        line_num=lineno,
                        category="CLIENT_COUPLING",
                        match=", ".join(matched_clients),
                        line_text=line_text,
                        severity=severity,
                        explanation=explanation
                    )

            # 2. Search for logical comparisons with sector/client keywords
            if isinstance(node, ast.Compare):
                # Check if we are comparing an expression to a constant string
                # e.g., if self.industry_profile == "energy"
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                        comp_val = comparator.value.lower()
                        matched_sectors = [w for w in self.sector_words if w in comp_val]
                        matched_clients = [w for w in self.client_words if w in comp_val]
                        
                        if matched_sectors or matched_clients:
                            lineno = getattr(node, "lineno", 1)
                            line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
                            
                            category = "SECTOR_BRANCHING" if matched_sectors else "CLIENT_BRANCHING"
                            match_str = ", ".join(matched_sectors or matched_clients)
                            
                            self._add_finding(
                                file=str(relative_path),
                                line_num=lineno,
                                category=category,
                                match=match_str,
                                line_text=line_text,
                                severity="MEDIUM",
                                explanation=(
                                    f"Logical comparison against static word '{match_str}'. "
                                    f"Ensure this is handled via configuration (industry_profile) or a generic policy class."
                                )
                            )

    def _is_logical_context(self, node: ast.AST, tree: ast.AST) -> bool:
        """Helper to determine if an AST Constant node is used in a logical context (not a docstring)."""
        # We traverse parents using a simple ancestor map.
        parent_map = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parent_map[child] = parent
                
        curr = node
        while curr in parent_map:
            parent = parent_map[curr]
            # If the parent is an Expression (docstring placeholder) or Module or FunctionDef
            # and the node is the body of it, it's likely a docstring.
            if isinstance(parent, ast.Expr) and parent in parent_map:
                grandparent = parent_map[parent]
                if isinstance(grandparent, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                    return False  # Docstring
            if isinstance(parent, (ast.Assign, ast.Compare, ast.Call, ast.If, ast.Dict)):
                return True
            curr = parent
        return False

    def _add_finding(
        self, file: str, line_num: int, category: str, match: str, line_text: str, severity: str, explanation: str
    ) -> None:
        # Avoid duplicate findings on the exact same line
        for f in self.findings:
            if f["file"] == file and f["line_num"] == line_num and f["category"] == category:
                return
                
        # Filter false positives:
        # Spanish word 'salud' meaning service health (e.g., 'salud del servicio', 'salud de los servicios')
        # is a valid IT operations metaphor and not a hardcoded Healthcare sector coupling.
        if "salud" in match.lower() and any(
            phrase in line_text.lower()
            for phrase in ["salud de los", "salud del", "salud de la", "salud operacional", "salud de servicios"]
        ):
            return  # Filtered out as service health operational vocabulary
            
        # Filter false positives for 'eléctrica' when it is part of generic data center electrical engineering
        # (UPS, ATS, generators, CPD capacity/conmutacion) and not referring to 'Red Eléctrica' or similar client names
        if "eléctrica" in match.lower():
            is_client_ref = any(
                ref in line_text.lower()
                for ref in ["red eléctrica", "grupo eléctrica", "ree", "corporación eléctrica"]
            )
            if not is_client_ref and any(
                term in line_text.lower()
                for term in [
                    "consumo", "resiliencia", "conmutación", "autonomía", "capacidad", 
                    "cadena", "alimentación", "instalada", "generador", "ups", "cpd", "facilities", "eléctricos", "continuidad", "pillar_name"
                ]
            ):
                return  # Filtered out as generic electrical facilities vocabulary
            
        # Filter comments explaining standards (e.g. Basel III, etc.) if they are only in comments/docstrings
        if category == "SECTOR_BRANCHING" and "basilea" in line_text.lower() and line_text.strip().startswith("#"):
            return

        self.findings.append({
            "file": file,
            "line_num": line_num,
            "category": category,
            "match": match,
            "line_text": line_text,
            "severity": severity,
            "explanation": explanation
        })

    def print_report(self) -> None:
        """Display a comprehensive mathematical audit report."""
        print("=" * 100)
        print("🔍 REPORTE DE AUDITORÍA MATEMÁTICA DE MULTI-TENANCY")
        print("=" * 100)
        
        if not self.findings:
            print("✅ EXCELENTE: El código core (src/assessment_engine) es 100% GENÉRICO y MULTI-TENANT.")
            print("   No se han detectado referencias acopladas a clientes, sectores o tamaños en la lógica activa.")
            print("=" * 100)
            return

        # Sort by severity (HIGH, MEDIUM, LOW) and file name
        severity_weight = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        sorted_findings = sorted(
            self.findings,
            key=lambda x: (severity_weight.get(x["severity"], 0), x["file"], x["line_num"]),
            reverse=True
        )

        high_count = sum(1 for f in self.findings if f["severity"] == "HIGH")
        med_count = sum(1 for f in self.findings if f["severity"] == "MEDIUM")
        
        print(f"📌 Resumen: Se encontraron {len(self.findings)} coincidencias de interés.")
        print(f"   🔴 Severidad ALTA: {high_count}")
        print(f"   🟡 Severidad MEDIA: {med_count}")
        print("-" * 100)

        current_file = ""
        for f in sorted_findings:
            if f["file"] != current_file:
                print(f"\n📁 Archivo: {f['file']}")
                current_file = f["file"]
            
            sev_indicator = "🔴 [ALTA]" if f["severity"] == "HIGH" else "🟡 [MEDIA]"
            print(f"   Línea {f['line_num']} {sev_indicator} ({f['category']}) - Encontrado: '{f['match']}'")
            print(f"      Código: {f['line_text']}")
            print(f"      Análisis: {f['explanation']}")
            print("-" * 60)
        
        print("\n💡 Recomendación de Gobernanza:")
        print("   1. Los hallazgos de severidad ALTA deben migrarse de inmediato a 'engine_config/brand_profile.json'.")
        print("   2. Los de severidad MEDIA en ramificaciones de sector son correctos siempre que consulten 'self.industry_profile'")
        print("      de forma condicional (lo cual es un patrón de diseño correcto y parametrizado).")
        print("=" * 100)


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent
    auditor = TenancyAuditor(repo_root)
    auditor.scan()
    auditor.print_report()
