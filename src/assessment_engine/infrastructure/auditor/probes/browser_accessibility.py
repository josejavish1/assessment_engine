"""
Audit web accessibility (W3C WCAG 2.2 AA) and user experience for European Accessibility Act (EAA) compliance. Implement checks for:
- WCAG 1.3.1 / 4.1.2: Inputs with programmatic labels (<label htmlFor>, aria-label, or title).
- Distinction between HTML <input> tags and React <Input {...props}> components.
- Recognition of implicit labels within <label> ... <input> ... </label> blocks.
- WCAG 1.1.1: Images with 'alt' text.
- WCAG 4.1.2: Buttons with accessible names or aria-hidden.
- Placeholder fallback recognition and exclusion of hidden elements.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

# Match only native lowercase HTML <input tags, ignoring JSX arrow operators (e) =>.
INPUT_TAG_REGEX = re.compile(r"<input\b(.*?(?<!=))>", re.DOTALL)
IMG_TAG_REGEX = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
BUTTON_TAG_REGEX = re.compile(r"<button\b([^>]*)>(.*?)</button>", re.IGNORECASE | re.DOTALL)
LABEL_FOR_REGEX = re.compile(r"""(?:for|htmlFor)\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE)

VIEWPORT_TAG_REGEX = re.compile(r"""<meta\b[^>]*name=['"]viewport['"][^>]*content=['"]([^'"]+)['"]""", re.IGNORECASE)
THEME_SCRIPT_REGEX = re.compile(r"""(theme|dark|darkMode|localStorage\.getItem\(['"]theme['"]\))""")


def _audit_inputs_accessibility(content: str, rel_path: str, declared_label_targets: set[str]) -> list[AuditFinding]:
    """Audita regla WCAG 1.3.1 / 4.1.2: Inputs con etiquetas accesibles."""
    findings: list[AuditFinding] = []
    for match in INPUT_TAG_REGEX.finditer(content):
        attrs = match.group(1)

        # Skip wrapper components that forward props (e.g., shadcn <input {...props} />).
        if "{...props}" in attrs or "{...rest}" in attrs:
            continue

        type_match = re.search(r"""type\s*=\s*['"]?([a-zA-Z0-9_\-]+)['"]?""", attrs, re.IGNORECASE)
        input_type = type_match.group(1).lower() if type_match else "text"

        if input_type in ("hidden", "submit", "button", "reset"):
            continue

        before_text = content[:match.start()]
        is_inside_label = (before_text.count("<label") - before_text.count("</label>")) > 0

        has_aria_label = "aria-label" in attrs or "aria-labelledby" in attrs
        has_title = "title=" in attrs or "title =" in attrs
        has_placeholder = "placeholder=" in attrs or "placeholder =" in attrs
        id_match = re.search(r"""id\s*=\s*['"]([^'"]+)['"]""", attrs, re.IGNORECASE)
        has_paired_label = bool(id_match and id_match.group(1) in declared_label_targets)

        if not has_aria_label and not has_paired_label and not has_title and not is_inside_label:
            lineno = before_text.count("\n") + 1
            severity = "LOW" if has_placeholder else "HIGH"
            findings.append(AuditFinding(
                category="ACCESSIBILITY",
                severity=severity,
                file_path=rel_path,
                line_number=lineno,
                rule_id="A11Y-INPUT-NO-LABEL",
                message=f"Campo <input type='{input_type}'> carece de <label> asociado o atributo 'aria-label'",
                recommendation="Vincular con '<label htmlFor=\"id\">' o añadir 'aria-label=\"Descripción\"' para lectores de pantalla."
            ))
    return findings


def _audit_images_accessibility(content: str, rel_path: str) -> list[AuditFinding]:
    """Audit WCAG 1.1.1: images with 'alt' text."""
    findings: list[AuditFinding] = []
    for match in IMG_TAG_REGEX.finditer(content):
        attrs = match.group(1)
        if "alt=" not in attrs and "alt =" not in attrs:
            lineno = content[:match.start()].count("\n") + 1
            findings.append(AuditFinding(
                category="ACCESSIBILITY",
                severity="MEDIUM",
                file_path=rel_path,
                line_number=lineno,
                rule_id="A11Y-IMG-NO-ALT",
                message="Etiqueta <img /> carece del atributo obligatorio 'alt' (WCAG 1.1.1)",
                recommendation="Añadir 'alt=\"Descripción visual\"' o 'alt=\"\"' si es puramente decorativa."
            ))
    return findings


def _audit_buttons_accessibility(content: str, rel_path: str) -> list[AuditFinding]:
    """Audita regla WCAG 4.1.2: Botones con nombres accesibles."""
    findings: list[AuditFinding] = []
    for match in BUTTON_TAG_REGEX.finditer(content):
        attrs = match.group(1)
        body = match.group(2).strip()

        # Botones ocultos deliberadamente de accesibilidad
        if "aria-hidden=\"true\"" in attrs or "aria-hidden='true'" in attrs or 'tabindex="-1"' in attrs.lower():
            continue

        has_aria = "aria-label" in attrs or "aria-labelledby" in attrs or "title=" in attrs
        clean_text = re.sub(r"<[^>]+>", "", body).strip()

        if not has_aria and not clean_text:
            lineno = content[:match.start()].count("\n") + 1
            findings.append(AuditFinding(
                category="ACCESSIBILITY",
                severity="HIGH",
                file_path=rel_path,
                line_number=lineno,
                rule_id="A11Y-BUTTON-NO-NAME",
                message="Botón interactivo <button> no contiene texto accesible ni 'aria-label'",
                recommendation="Añadir texto visible o atributo 'aria-label=\"Acción\"' para lectores de pantalla."
            ))
    return findings


def audit_component_accessibility(ui_file: Path, rel_path: str) -> list[AuditFinding]:
    """Audit WCAG 2.2 AA rules on the component markup tree."""
    try:
        content = ui_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    declared_label_targets = set(LABEL_FOR_REGEX.findall(content))
    findings: list[AuditFinding] = []
    findings.extend(_audit_inputs_accessibility(content, rel_path, declared_label_targets))
    findings.extend(_audit_images_accessibility(content, rel_path))
    findings.extend(_audit_buttons_accessibility(content, rel_path))
    return findings


def audit_html_head_standards(index_html: Path, rel_path: str) -> list[AuditFinding]:
    """Audit viewport best practices and zero-FOUC in index.html."""
    findings: list[AuditFinding] = []
    try:
        content = index_html.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    vp_match = VIEWPORT_TAG_REGEX.search(content)
    if vp_match:
        vp_val = vp_match.group(1).lower()
        if "maximum-scale=1" in vp_val or "user-scalable=no" in vp_val or "user-scalable=0" in vp_val:
            findings.append(AuditFinding(
                category="ACCESSIBILITY",
                severity="HIGH",
                file_path=rel_path,
                line_number=content[:vp_match.start()].count("\n") + 1,
                rule_id="A11Y-VIEWPORT-ZOOM-DISABLED",
                message="Etiqueta viewport bloquea el zoom del usuario ('user-scalable=no' o 'maximum-scale=1')",
                recommendation="Permitir zoom accesible eliminando restricciones de escala máxima (WCAG 1.4.4)."
            ))

    head_match = re.search(r"<head\b[^>]*>(.*?)</head>", content, re.IGNORECASE | re.DOTALL)
    if head_match:
        head_content = head_match.group(1)
        has_fouc_script = bool(THEME_SCRIPT_REGEX.search(head_content))
        if not has_fouc_script and "dark" in content.lower():
            findings.append(AuditFinding(
                category="ACCESSIBILITY",
                severity="LOW",
                file_path=rel_path,
                line_number=content[:head_match.start()].count("\n") + 1,
                rule_id="A11Y-MISSING-ZERO-FOUC",
                message="No se detectó script síncrono en <head> para evitar destello de tema (Zero-FOUC)",
                recommendation="Inyectar script inline que lea localStorage de tema antes del primer renderizado de CSS."
            ))

    return findings


def run_browser_accessibility_probe(target_dir: Path) -> ProbeResult:
    """Run a comprehensive W3C WCAG 2.2 accessibility and user experience audit."""
    findings: list[AuditFinding] = []
    scanned_ui_files = 0

    ui_files = find_target_files(target_dir, (".html", ".tsx", ".jsx", ".vue"))
    for ui_file in ui_files:
        scanned_ui_files += 1
        rel_path = str(ui_file.relative_to(target_dir))

        comp_findings = audit_component_accessibility(ui_file, rel_path)
        findings.extend(comp_findings)

        if ui_file.name == "index.html":
            head_findings = audit_html_head_standards(ui_file, rel_path)
            findings.extend(head_findings)

    if scanned_ui_files == 0:
        return ProbeResult(
            probe_name="Accessibility & UI Standards (WCAG 2.2 AA / EAA)",
            score_pct=100.0,
            passed=True,
            metrics={"status": "BACKEND_ONLY_NO_UI", "ui_files_scanned": 0}
        )

    score = 100.0
    for f in findings:
        if f.severity == "HIGH":
            score -= 10.0
        elif f.severity == "MEDIUM":
            score -= 2.0
        elif f.severity == "LOW":
            score -= 0.2

    score = max(0.0, min(100.0, round(score, 1)))
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    passed = high_count == 0 and score >= 70.0

    return ProbeResult(
        probe_name="Accessibility & UI Standards (WCAG 2.2 AA / EAA)",
        score_pct=score,
        passed=passed,
        metrics={
            "ui_files_scanned": scanned_ui_files,
            "findings_count": len(findings),
            "high_severity_a11y_count": high_count,
            "wcag_compliance_level": "WCAG 2.2 AA Conforme" if passed else "No Conforme"
        },
        findings=findings
    )
