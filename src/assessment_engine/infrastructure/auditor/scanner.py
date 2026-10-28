"""
Execute multi-dimensional software certification audits on target project directories.
Compute the overall score and export executive reports and certificates.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import UniversalAuditReport
from assessment_engine.infrastructure.auditor.probes.ai_safety_llm import run_ai_safety_llm_probe
from assessment_engine.infrastructure.auditor.probes.ast_complexity import run_ast_complexity_probe
from assessment_engine.infrastructure.auditor.probes.browser_accessibility import run_browser_accessibility_probe
from assessment_engine.infrastructure.auditor.probes.code_hygiene import run_code_hygiene_probe
from assessment_engine.infrastructure.auditor.probes.comment_quality import run_comment_quality_probe
from assessment_engine.infrastructure.auditor.probes.concurrency_stress import run_concurrency_stress_probe
from assessment_engine.infrastructure.auditor.probes.contract_drift import run_contract_drift_probe
from assessment_engine.infrastructure.auditor.probes.documentation_quality import run_documentation_quality_probe
from assessment_engine.infrastructure.auditor.probes.hardcoded_artifacts import run_hardcoded_artifacts_probe
from assessment_engine.infrastructure.auditor.probes.legal_compliance import run_legal_compliance_probe
from assessment_engine.infrastructure.auditor.probes.mutation_gate import run_mutation_gate_probe
from assessment_engine.infrastructure.auditor.probes.performance_finops import run_performance_finops_probe
from assessment_engine.infrastructure.auditor.probes.resilience_chaos import run_resilience_chaos_probe
from assessment_engine.infrastructure.auditor.probes.security_dast import run_security_dast_probe
from assessment_engine.infrastructure.auditor.probes.security_sast import run_security_sast_probe
from assessment_engine.infrastructure.auditor.probes.sre_observability import audit_sre_observability
from assessment_engine.infrastructure.auditor.probes.structural_smells import run_structural_smells_probe
from assessment_engine.infrastructure.auditor.probes.supply_chain import run_supply_chain_probe
from assessment_engine.infrastructure.auditor.reporter import render_html_certificate


class SoverikQualityEngine:
    """
    Motor Soberano Universal de Calidad y Certificación.
    Agnóstico de framework: audita cualquier workspace o repositorio contra las 12 dimensiones SOTA.
    """

    def __init__(self, output_subdir: str = "docs/audits") -> None:
        self.output_subdir = output_subdir

    def audit_project(self, target_path: Path, project_name: str | None = None) -> UniversalAuditReport:
        """Execute the full multi-dimensional audit on the specified directory."""
        target_path = target_path.resolve()
        name = project_name or target_path.name

        report = UniversalAuditReport(
            project_name=name,
            target_path=str(target_path)
        )

        # 1. Dimension 1A: Cybersecurity SAST and secret scanning (15% weight)
        sast_res = run_security_sast_probe(target_path)
        report.probes["security_sast"] = sast_res

        # 2. Dimension 1B: Dynamic red team DAST (10% weight)
        dast_res = run_security_dast_probe(target_path)
        report.probes["security_dast"] = dast_res

        ast_res = run_ast_complexity_probe(target_path)
        report.probes["ast_complexity"] = ast_res

        mut_res = run_mutation_gate_probe(target_path)
        report.probes["mutation_gate"] = mut_res

        sca_res = run_supply_chain_probe(target_path)
        report.probes["supply_chain"] = sca_res

        legal_res = run_legal_compliance_probe(target_path)
        report.probes["legal_compliance"] = legal_res

        perf_res = run_performance_finops_probe(target_path)
        report.probes["performance_finops"] = perf_res

        a11y_res = run_browser_accessibility_probe(target_path)
        report.probes["browser_accessibility"] = a11y_res

        drift_res = run_contract_drift_probe(target_path)
        report.probes["contract_drift"] = drift_res

        resil_res = run_resilience_chaos_probe(target_path)
        report.probes["resilience_chaos"] = resil_res

        ai_res = run_ai_safety_llm_probe(target_path)
        report.probes["ai_safety_llm"] = ai_res

        hygiene_res = run_code_hygiene_probe(target_path)
        report.probes["code_hygiene"] = hygiene_res

        smells_res = run_structural_smells_probe(target_path)
        report.probes["structural_smells"] = smells_res

        stress_res = run_concurrency_stress_probe(target_path)
        report.probes["concurrency_stress"] = stress_res

        doc_res = run_documentation_quality_probe(target_path)
        report.probes["documentation_quality"] = doc_res

        sre_res = audit_sre_observability(target_path)
        report.probes["sre_observability"] = sre_res

        hardcoded_res = run_hardcoded_artifacts_probe(target_path)
        report.probes["hardcoded_artifacts"] = hardcoded_res

        comment_res = run_comment_quality_probe(target_path)
        report.probes["comment_quality"] = comment_res

        weighted_score = (
            sast_res.score_pct * 0.10 +
            dast_res.score_pct * 0.10 +
            ast_res.score_pct * 0.10 +
            mut_res.score_pct * 0.10 +
            sca_res.score_pct * 0.10 +
            legal_res.score_pct * 0.05 +
            hardcoded_res.score_pct * 0.025 +
            sre_res.score_pct * 0.05 +
            perf_res.score_pct * 0.05 +
            stress_res.score_pct * 0.05 +
            a11y_res.score_pct * 0.05 +
            drift_res.score_pct * 0.05 +
            resil_res.score_pct * 0.05 +
            ai_res.score_pct * 0.05 +
            doc_res.score_pct * 0.025 +
            hygiene_res.score_pct * 0.025 +
            smells_res.score_pct * 0.025 +
            comment_res.score_pct * 0.025
        )
        report.global_score = min(100.0, round(weighted_score, 1))

        has_critical_security_failure = not sast_res.passed or not dast_res.passed

        if report.global_score >= 90.0 and all(p.passed for p in report.probes.values()):
            report.global_grade = "A+"
        elif report.global_score >= 80.0 and not has_critical_security_failure:
            report.global_grade = "A"
        elif report.global_score >= 70.0 and not has_critical_security_failure:
            report.global_grade = "B"
        elif report.global_score >= 50.0:
            report.global_grade = "C"
        else:
            report.global_grade = "F"

        report.summary = (
            f"Proyecto '{name}' certificado con Grado {report.global_grade} "
            f"({report.global_score}%). Sondas pasadas: {sum(1 for p in report.probes.values() if p.passed)}/{len(report.probes)}."
        )

        # Exportar artefactos en docs/audit/
        out_dir = target_path / self.output_subdir
        out_dir.mkdir(parents=True, exist_ok=True)

        json_file = out_dir / "AUDIT_REPORT.json"
        json_file.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

        html_file = out_dir / "AUDIT_CERTIFICATE.html"
        html_file.write_text(render_html_certificate(report), encoding="utf-8")

        return report


quality_engine = SoverikQualityEngine()
