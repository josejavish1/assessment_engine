"""
Audit legal compliance, copyleft licenses, and GDPR requirements against SPDX ISO 5962 and AEPD guidelines. Implement:
- Copyleft contamination detection (GPL, AGPL, SSPL) in Python dependencies.
- GDPR data governance verification (Art. 17 Right to Erasure and Art. 20 Portability).
- Column-level encryption at rest auditing (GDPR Art. 32).
- Proprietary LICENSE file verification.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files

EXCLUDE_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "build", "archive"
}

KNOWN_COPYLEFT_PACKAGES = {
    "pygpl", "gpl_lib", "agpl_tool", "pyqt5", "pyqt6"
}

VIRAL_COPYLEFT_PATTERNS = [
    re.compile(r"""(?i)\b(GNU\s+General\s+Public\s+License|GPL|AGPL|Affero|SSPL)\b"""),
]


def _check_package_license(package_name: str) -> str | None:
    """Query the declared license in the active environment using importlib.metadata."""
    try:
        import importlib.metadata
        meta = importlib.metadata.metadata(package_name)
        lic = meta.get("License")
        if lic and lic.strip() and lic.lower() != "unknown":
            return lic.strip()
        classifiers = meta.get_all("Classifier") or []
        for c in classifiers:
            if "License ::" in c:
                return c.split("::")[-1].strip()
    except (importlib.metadata.PackageNotFoundError, KeyError, ValueError):
        pass
    return None


def _audit_copyleft_dependencies(req_file: Path) -> tuple[dict[str, str], list[str], list[AuditFinding]]:
    """Analiza dependencias en requirements.txt buscando licencias virales Copyleft."""
    analyzed_licenses: dict[str, str] = {}
    copyleft_violations: list[str] = []
    findings: list[AuditFinding] = []

    if not req_file.exists():
        return analyzed_licenses, copyleft_violations, findings

    content = req_file.read_text(encoding="utf-8", errors="ignore")
    for line_idx, line in enumerate(content.splitlines(), 1):
        line_str = line.strip()
        if not line_str or line_str.startswith("#"):
            continue

        pkg_name = line_str.split("==")[0].split(">=")[0].split("<=")[0].strip()
        if not pkg_name:
            continue

        if pkg_name.lower() in KNOWN_COPYLEFT_PACKAGES:
            copyleft_violations.append(pkg_name)
            findings.append(AuditFinding(
                category="LEGAL",
                severity="CRITICAL",
                file_path="requirements.txt",
                line_number=line_idx,
                rule_id="LEGAL-COPYLEFT-CONTAMINATION",
                message=f"Dependency '{pkg_name}' subject to viral Copyleft license (GPL/AGPL): restricts proprietary distribution",
                recommendation="Replace with permissive commercial alternative (MIT / Apache-2.0 / BSD)."
            ))
            continue

        lic_meta = _check_package_license(pkg_name)
        if lic_meta:
            analyzed_licenses[pkg_name] = lic_meta
            for pat in VIRAL_COPYLEFT_PATTERNS:
                if pat.search(lic_meta) and "LGPL" not in lic_meta:
                    copyleft_violations.append(pkg_name)
                    findings.append(AuditFinding(
                        category="LEGAL",
                        severity="CRITICAL",
                        file_path="requirements.txt",
                        line_number=line_idx,
                        rule_id="LEGAL-COPYLEFT-CONTAMINATION",
                        message=f"Copyleft/viral license detected in '{pkg_name}': {lic_meta} (IP contamination risk)",
                        recommendation="Replace with a permissive library (MIT, Apache-2.0, BSD) for enterprise compliance."
                    ))

    return analyzed_licenses, copyleft_violations, findings


def _audit_rgpd_compliance(target_dir: Path) -> tuple[bool, bool, bool, bool, list[AuditFinding]]:
    """Inspect source code for PII entities and GDPR technical enforcement mechanisms."""
    has_pii_entities = False
    has_art17_erasure = False
    has_art20_portability = False
    has_column_encryption = False
    findings: list[AuditFinding] = []

    for py_file in find_target_files(target_dir, (".py",)):
        try:
            code = py_file.read_text(encoding="utf-8", errors="ignore").lower()
        except (OSError, UnicodeDecodeError):
            continue

        if any(kw in code for kw in ("users", "clientes", "pacientes", "customers", "auth_hash", "email")):
            has_pii_entities = True
        if any(kw in code for kw in ("data_erasure_cascade", "erase_user_pii", "derecho_olvido", "anonymize_user")):
            has_art17_erasure = True
        if any(kw in code for kw in ("data_portability_exporter", "export_full_user_archive", "export_user_data", "portabilidad")):
            has_art20_portability = True
        if any(kw in code for kw in ("column_encryption", "encrypt_field", "fernet", "aes_256", "decrypt_field")):
            has_column_encryption = True

    if has_pii_entities:
        if not has_art17_erasure:
            findings.append(AuditFinding(
                category="RGPD",
                severity="HIGH",
                file_path="api/src/main.py",
                line_number=None,
                rule_id="LEGAL-GDPR-ART17-MISSING",
                message="Technical mechanism for irreversible erasure of personal data missing (GDPR Art. 17 Right to Erasure)",
                recommendation="Integrate 'data_erasure_cascade' primitive to purge PII and anonymize transactions."
            ))
        if not has_art20_portability:
            findings.append(AuditFinding(
                category="RGPD",
                severity="MEDIUM",
                file_path="api/src/main.py",
                line_number=None,
                rule_id="LEGAL-GDPR-ART20-MISSING",
                message="Technical mechanism for structured data export missing (GDPR Art. 20 Portability)",
                recommendation="Integrar la primitiva 'data_portability_exporter' para emitir paquetes JSON interoperables."
            ))

    return has_pii_entities, has_art17_erasure, has_art20_portability, has_column_encryption, findings


def _calculate_legal_score(
    copyleft_count: int,
    has_pii: bool,
    has_art17: bool,
    has_art20: bool,
    has_license: bool
) -> tuple[float, bool]:
    """Calculate the weighted legal score and determine whether it passes the quality gate."""
    score = 100.0
    score -= copyleft_count * 40.0
    if has_pii and not has_art17:
        score -= 20.0
    if has_pii and not has_art20:
        score -= 10.0
    if not has_license:
        score -= 5.0

    score = max(0.0, min(100.0, round(score, 1)))
    passed = copyleft_count == 0 and (not has_pii or has_art17) and score >= 70.0
    return score, passed


def run_legal_compliance_probe(target_dir: Path) -> ProbeResult:
    """Execute a comprehensive audit of intellectual property licenses and GDPR compliance."""
    findings: list[AuditFinding] = []

    analyzed_licenses, copyleft_violations, copyleft_finds = _audit_copyleft_dependencies(target_dir / "requirements.txt")
    findings.extend(copyleft_finds)

    has_root_license = (target_dir / "LICENSE").exists() or (target_dir / "LICENSE.md").exists()
    if not has_root_license:
        findings.append(AuditFinding(
            category="LEGAL",
            severity="LOW",
            file_path="LICENSE",
            line_number=None,
            rule_id="LEGAL-NO-ROOT-LICENSE",
            message="Repository root lacks a 'LICENSE' file",
            recommendation="Define software license (e.g. Proprietary or MIT) for legal certainty."
        ))

    has_pii, has_art17, has_art20, has_enc, rgpd_finds = _audit_rgpd_compliance(target_dir)
    findings.extend(rgpd_finds)

    score, passed = _calculate_legal_score(
        len(copyleft_violations), has_pii, has_art17, has_art20, has_root_license
    )

    return ProbeResult(
        probe_name="Legal Compliance & GDPR (SPDX / AEPD / CRA)",
        score_pct=score,
        passed=passed,
        metrics={
            "copyleft_violations_count": len(copyleft_violations),
            "copyleft_packages": copyleft_violations,
            "has_root_license": has_root_license,
            "has_pii_entities": has_pii,
            "has_gdpr_art17_erasure": has_art17,
            "has_gdpr_art20_portability": has_art20,
            "has_column_encryption": has_enc,
            "analyzed_dependencies_count": len(analyzed_licenses)
        },
        findings=findings
    )
