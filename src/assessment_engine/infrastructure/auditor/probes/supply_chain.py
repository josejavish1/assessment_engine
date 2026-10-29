"""
Perform Software Composition Analysis (SCA) and generate CycloneDX 1.6 SBOMs using Google OSV.dev. Features:
- Analyze pinned dependencies and build reproducibility.
- Query the Google OSV.dev API for live CVE detection.
- Generate immutable SBOM manifests compliant with the EU Cyber Resilience Act (CRA).
"""
from __future__ import annotations

import json
import logging
import re
import urllib.request
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult

logger = logging.getLogger("assessment_engine.infrastructure.auditor.supply_chain")

OSV_BATCH_QUERY_URL = "https://api.osv.dev/v1/querybatch"


def query_osv_vulnerabilities(queries: list[dict[str, Any]], timeout: float = 4.0) -> list[dict[str, Any]]:
    """Batch query the Google OSV.dev vulnerability database."""
    if not queries:
        return []
    payload = json.dumps({"queries": queries[:100]}).encode("utf-8")
    req = urllib.request.Request(
        OSV_BATCH_QUERY_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Soverik-Quality-Engine/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("results", [])
    except (urllib.error.URLError, ValueError, OSError, RuntimeError) as ex:
        logger.debug(f"[SupplyChain] Error en consulta OSV.dev: {ex}")
        return []


def generate_cyclonedx_sbom(components: list[dict[str, Any]], project_name: str = "project") -> dict[str, Any]:
    """Generate a standard CycloneDX v1.6 SBOM manifest compliant with the EU Cyber Resilience Act (CRA)."""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{project_name}-sbom-2026",
        "version": 1,
        "metadata": {
            "component": {
                "name": project_name,
                "type": "application"
            }
        },
        "components": [
            {
                "type": "library",
                "name": c["name"],
                "version": c["version"] or "unspecified",
                "purl": f"pkg:{c['ecosystem'].lower()}/{c['name']}@{c['version'] or 'latest'}",
                "scope": "required"
            }
            for c in components
        ]
    }


def _parse_requirements_file(req_file: Path) -> tuple[int, int, list[dict[str, Any]], list[dict[str, Any]], list[AuditFinding]]:
    deps_count = 0
    pinned_count = 0
    components: list[dict[str, Any]] = []
    osv_queries: list[dict[str, Any]] = []
    findings: list[AuditFinding] = []

    if not req_file.exists():
        return deps_count, pinned_count, components, osv_queries, findings

    content = req_file.read_text(encoding="utf-8", errors="ignore")
    for line_idx, line in enumerate(content.splitlines(), 1):
        line_str = line.strip()
        if not line_str or line_str.startswith("#"):
            continue

        deps_count += 1
        if "==" in line_str:
            parts = line_str.split("==")
            pkg_name = parts[0].strip()
            pkg_ver = parts[1].split(";")[0].split()[0].strip()
            pinned_count += 1
            components.append({"name": pkg_name, "version": pkg_ver, "ecosystem": "PyPI", "file": "requirements.txt"})
            osv_queries.append({"package": {"name": pkg_name, "ecosystem": "PyPI"}, "version": pkg_ver})
        else:
            pkg_name = re.split(r"[><=~;]", line_str)[0].strip()
            components.append({"name": pkg_name, "version": None, "ecosystem": "PyPI", "file": "requirements.txt"})
            findings.append(AuditFinding(
                category="SUPPLY_CHAIN",
                severity="LOW",
                file_path="requirements.txt",
                line_number=line_idx,
                rule_id="SCA-UNPINNED-DEP",
                message=f"Unpinned dependency: '{line_str}'",
                recommendation="Pin exact version with '==' to ensure deterministic reproducibility."
            ))

    return deps_count, pinned_count, components, osv_queries, findings


def _parse_package_json_file(pkg_file: Path, target_dir: Path) -> tuple[int, int, list[dict[str, Any]], list[dict[str, Any]], list[AuditFinding]]:
    deps_count = 0
    pinned_count = 0
    components: list[dict[str, Any]] = []
    osv_queries: list[dict[str, Any]] = []
    findings: list[AuditFinding] = []

    if not pkg_file.exists():
        return deps_count, pinned_count, components, osv_queries, findings

    try:
        pkg_data = json.loads(pkg_file.read_text(encoding="utf-8"))
        deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
        rel_pkg = str(pkg_file.relative_to(target_dir))

        for dep_name, version in deps.items():
            deps_count += 1
            clean_ver = re.sub(r"[\^~]", "", str(version)).strip()
            is_pinned = not (version.startswith(("^", "~", "*", ">", "<")) or version == "*")

            if is_pinned:
                pinned_count += 1
                components.append({"name": dep_name, "version": clean_ver, "ecosystem": "npm", "file": rel_pkg})
                osv_queries.append({"package": {"name": dep_name, "ecosystem": "npm"}, "version": clean_ver})
            else:
                components.append({"name": dep_name, "version": clean_ver, "ecosystem": "npm", "file": rel_pkg})
                findings.append(AuditFinding(
                    category="SUPPLY_CHAIN",
                    severity="LOW",
                    file_path=rel_pkg,
                    line_number=None,
                    rule_id="SCA-LOOSE-SEMVER",
                    message=f"Dependencia npm '{dep_name}' usa rango flotante '{version}'",
                    recommendation="Use pnpm-lock.yaml or pin exact versions for reproducible builds."
                ))
    except (json.JSONDecodeError, OSError):
        pass

    return deps_count, pinned_count, components, osv_queries, findings


def _is_version_vulnerable(version_str: str, vuln: dict[str, Any]) -> bool:
    """Evaluate whether version_str is strictly within the affected ranges of the OSV advisory."""
    if not version_str or version_str in ("latest", "unspecified"):
        return True

    def parse_semver(v_str: str) -> tuple[int, ...]:
        clean = re.sub(r"[^\d.]", "", v_str.split("+")[0].split("-")[0])
        parts = []
        for p in clean.split("."):
            if p.isdigit():
                parts.append(int(p))
        return tuple(parts)

    try:
        cur_v = parse_semver(version_str)
    except Exception:
        return True

    for aff in vuln.get("affected", []):
        if "versions" in aff and version_str in aff["versions"]:
            return True

        for r in aff.get("ranges", []):
            events = r.get("events", [])
            intro = None
            fixed = None
            for ev in events:
                if "introduced" in ev and ev["introduced"] != "0":
                    intro = parse_semver(ev["introduced"])
                if "fixed" in ev:
                    fixed = parse_semver(ev["fixed"])

            is_in_range = True
            if intro and cur_v < intro:
                is_in_range = False
            if fixed and cur_v >= fixed:
                is_in_range = False
            if is_in_range and (intro is not None or fixed is not None):
                return True

    return False


def _check_osv_vulnerabilities(osv_queries: list[dict[str, Any]]) -> tuple[int, list[AuditFinding]]:
    findings: list[AuditFinding] = []
    known_cves_count = 0
    if not osv_queries:
        return known_cves_count, findings

    osv_results = query_osv_vulnerabilities(osv_queries, timeout=4.0)
    for idx, res in enumerate(osv_results):
        vulns = res.get("vulns", [])
        if vulns and idx < len(osv_queries):
            target_query = osv_queries[idx]
            p_name = target_query["package"]["name"]
            p_ver = target_query.get("version", "latest")
            for v in vulns:
                if not _is_version_vulnerable(p_ver, v):
                    continue
                known_cves_count += 1
                vuln_id = v.get("id", "OSV-VULN")
                aliases = ", ".join(v.get("aliases", [])) or vuln_id
                summary = v.get("summary", "Vulnerabilidad conocida en componente de terceros")
                findings.append(AuditFinding(
                    category="SUPPLY_CHAIN",
                    severity="CRITICAL" if "RCE" in summary or "Arbitrary" in summary else "HIGH",
                    file_path="requirements.txt" if target_query["package"]["ecosystem"] == "PyPI" else "package.json",
                    line_number=None,
                    rule_id=f"SCA-{vuln_id}",
                    message=f"Vulnerabilidad conocida en {p_name}=={p_ver}: {summary} ({aliases})",
                    recommendation=f"Upgrade {p_name} to patched version according to advisory {vuln_id}."
                ))
    return known_cves_count, findings


def run_supply_chain_probe(target_dir: Path) -> ProbeResult:
    """Execute a comprehensive dependency audit, query CVEs, and emit a CycloneDX SBOM."""
    findings: list[AuditFinding] = []
    components: list[dict[str, Any]] = []
    osv_queries: list[dict[str, Any]] = []

    r_deps, r_pinned, r_comps, r_queries, r_finds = _parse_requirements_file(target_dir / "requirements.txt")
    components.extend(r_comps)
    osv_queries.extend(r_queries)
    findings.extend(r_finds)

    pkg_file = target_dir / "package.json"
    if not pkg_file.exists():
        pkg_file = target_dir / "web" / "package.json"

    p_deps, p_pinned, p_comps, p_queries, p_finds = _parse_package_json_file(pkg_file, target_dir)
    components.extend(p_comps)
    osv_queries.extend(p_queries)
    findings.extend(p_finds)

    dependencies_count = r_deps + p_deps
    pinned_count = r_pinned + p_pinned

    known_cves_count, osv_finds = _check_osv_vulnerabilities(osv_queries)
    findings.extend(osv_finds)

    sbom_data = generate_cyclonedx_sbom(components, project_name=target_dir.name)
    out_dir = target_dir / "docs" / "audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "SBOM_CYCLONEDX.json").write_text(
        json.dumps(sbom_data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    score = 100.0
    if dependencies_count > 0:
        pinning_ratio = pinned_count / dependencies_count
        score = 40.0 * pinning_ratio + 60.0
    score -= known_cves_count * 25.0
    score = max(0.0, min(100.0, round(score, 1)))

    passed = known_cves_count == 0 and score >= 60.0

    return ProbeResult(
        probe_name="Supply Chain, OSV.dev & SBOM (CycloneDX 1.6 / CRA)",
        score_pct=score,
        passed=passed,
        metrics={
            "total_dependencies": dependencies_count,
            "pinned_dependencies": pinned_count,
            "pinning_ratio": round(pinned_count / max(1, dependencies_count), 2),
            "known_cves_detected": known_cves_count,
            "sbom_format": "CycloneDX v1.6",
            "sbom_path": str(out_dir / "SBOM_CYCLONEDX.json")
        },
        findings=findings
    )
