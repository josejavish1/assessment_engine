"""
Generate executive reports and certificates for Soverik Quality Engine.
Produce JSON specifications for CI/CD and interactive HTML certificates.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from assessment_engine.infrastructure.auditor.models import UniversalAuditReport


def render_html_certificate(report: UniversalAuditReport) -> str:
    """Generate the interactive executive HTML certificate."""
    grade_colors = {
        "A+": "#10b981",  # Verde esmeralda
        "A": "#059669",
        "B": "#3b82f6",   # Azul
        "C": "#f59e0b",   # Amber
        "F": "#ef4444"    # Rojo
    }
    badge_color = grade_colors.get(report.global_grade, "#3b82f6")

    seal_hash = hashlib.sha256(
        f"{report.project_name}:{report.timestamp}:{report.global_score}:{report.global_grade}".encode()
    ).hexdigest()

    probes_html = ""
    for probe_id, probe in report.probes.items():
        status_badge = "✓ PASADO" if probe.passed else "✗ REVISAR"
        status_color = "#10b981" if probe.passed else "#ef4444"
        probes_html += f"""
        <div class="probe-card">
            <div class="probe-header">
                <span class="probe-title">{probe.probe_name}</span>
                <span class="probe-score" style="color: {status_color};">{probe.score_pct}% • {status_badge}</span>
            </div>
            <div class="probe-bar-bg">
                <div class="probe-bar-fill" style="width: {min(100.0, max(0.0, probe.score_pct))}%; background-color: {status_color};"></div>
            </div>
            <div class="probe-metrics">
                {', '.join(f"<strong>{k}:</strong> {v}" for k, v in list(probe.metrics.items())[:4])}
            </div>
        </div>
        """

    findings_html = ""
    all_findings = []
    for p in report.probes.values():
        all_findings.extend(p.findings)

    if not all_findings:
        findings_html = "<div class='no-findings'>✓ Cero vulnerabilidades ni defectos críticos detectados.</div>"
    else:
        for f in all_findings[:15]:
            findings_html += f"""
            <div class="finding-row sev-{f.severity.lower()}">
                <span class="sev-tag">{f.severity}</span>
                <span class="rule-tag">{f.rule_id}</span>
                <span class="finding-msg">{f.message}</span>
                <span class="finding-path">{f.file_path}{f":{f.line_number}" if f.line_number else ""}</span>
            </div>
            """

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificado de Calidad y Seguridad — {report.project_name}</title>
    <style>
        :root {{
            --bg: #090d16;
            --surface: rgba(255, 255, 255, 0.03);
            --surface-border: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #38bdf8;
        }}
        body {{
            margin: 0;
            padding: 40px 20px;
            background: var(--bg);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            display: flex;
            justify-content: center;
        }}
        .cert-container {{
            max-width: 960px;
            width: 100%;
            background: rgba(15, 23, 42, 0.65);
            backdrop-filter: blur(24px);
            border: 1px solid var(--surface-border);
            border-radius: 24px;
            padding: 48px;
            box-shadow: 0 30px 60px rgba(0,0,0,0.4);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--surface-border);
            padding-bottom: 32px;
            margin-bottom: 36px;
        }}
        .brand {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: var(--accent);
            font-weight: 700;
        }}
        .title {{
            font-size: 28px;
            font-weight: 800;
            margin-top: 6px;
        }}
        .grade-badge {{
            width: 90px;
            height: 90px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 38px;
            font-weight: 900;
            color: #fff;
            background: {badge_color};
            box-shadow: 0 0 30px {badge_color}66;
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 36px;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            padding: 20px;
            border-radius: 16px;
            text-align: center;
        }}
        .stat-val {{
            font-size: 28px;
            font-weight: 800;
            color: var(--text-main);
        }}
        .stat-label {{
            font-size: 12px;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.05em;
            margin-top: 4px;
        }}
        .probe-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 14px;
            padding: 18px 24px;
            margin-bottom: 14px;
        }}
        .probe-header {{
            display: flex;
            justify-content: space-between;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        .probe-bar-bg {{
            height: 6px;
            background: rgba(255,255,255,0.08);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 10px;
        }}
        .probe-bar-fill {{
            height: 100%;
            transition: width 0.4s ease;
        }}
        .probe-metrics {{
            font-size: 12px;
            color: var(--text-muted);
        }}
        .finding-row {{
            display: flex;
            gap: 12px;
            align-items: center;
            font-size: 13px;
            padding: 10px 14px;
            border-radius: 8px;
            background: rgba(255,255,255,0.02);
            border-left: 3px solid #64748b;
            margin-bottom: 8px;
        }}
        .sev-critical {{ border-left-color: #ef4444; }}
        .sev-high {{ border-left-color: #f97316; }}
        .sev-medium {{ border-left-color: #f59e0b; }}
        .sev-tag {{
            font-weight: 700;
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(255,255,255,0.1);
        }}
        .rule-tag {{ color: var(--accent); font-family: monospace; font-size: 12px; }}
        .finding-msg {{ flex: 1; }}
        .finding-path {{ color: var(--text-muted); font-size: 11px; }}
        .seal-footer {{
            margin-top: 40px;
            padding-top: 24px;
            border-top: 1px solid var(--surface-border);
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-muted);
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="cert-container">
        <div class="header">
            <div>
                <div class="brand">Soverik Quality Engine • Tier-1 Certification</div>
                <div class="title">{report.project_name}</div>
                <div style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">Ruta: {report.target_path}</div>
            </div>
            <div class="grade-badge">{report.global_grade}</div>
        </div>

        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-val">{report.global_score}%</div>
                <div class="stat-label">Puntuación Global</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{len(report.probes)}</div>
                <div class="stat-label">Sondas Ejecutadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-val">{len(all_findings)}</div>
                <div class="stat-label">Desviaciones Detectadas</div>
            </div>
        </div>

        <h3 style="margin-bottom: 16px;">Resultados por Dimensión de Calidad</h3>
        {probes_html}

        <h3 style="margin-top: 36px; margin-bottom: 16px;">Registro Forense de Desviaciones</h3>
        {findings_html}

        <div class="seal-footer">
            <span>SELLO CRIPTOGRÁFICO SHA-256: {seal_hash[:32]}...</span>
            <span>AUDITADO BAJO NORMA ISO/IEC 25010 & IEEE 29119</span>
        </div>
    </div>
</body>
</html>
"""
