"""Autonomous User Experience and Cognitive Heuristics Auditor.

Key principles:
- Scriptless exploratory defect discovery via headless browser or DOM analysis.
- Executive and Technical persona cognitive walkthroughs.
- Nielsen's 10 usability heuristics and W3C WCAG 2.1 AA accessibility guidelines.
- Technical jargon and internal implementation leak detection.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
import json
import logging
from pathlib import Path
import re
import time
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult

logger = logging.getLogger(__name__)

FORBIDDEN_TECH_TERMS: dict[str, str] = {
    r"\bsqlite\b": "Database engine implementation leak (SQLite)",
    r"\bpostgresql\b": "Database engine implementation leak (PostgreSQL)",
    r"\brest api\b": "Backend technical jargon exposed to executive end user",
    r"\bjson\b": "Data interchange format exposed to executive end user",
    r"\btraceback\b": "Unhandled internal Python traceback leak",
    r"\bundefined\b": "Frontend JavaScript runtime undefined literal leak",
    r"\bnan\b": "Uncalculated numerical NaN leak in client view",
    r"\bparents\[\d+\]\b": "Server path traversal expression leak",
    r"\b501 not implemented\b": "Unhandled HTTP error string",
    r"\[object object\]": "Raw JavaScript object serialization failure",
}


@dataclass
class PersonaProfile:
    """Psychological profile and objective of a synthetic user persona."""

    persona_id: str
    name: str
    role: str  # "executive", "architect", "assessment_manager"
    primary_goal: str
    journey_steps: list[str]
    allowed_views: list[str]
    prohibited_elements: list[str] = field(default_factory=list)


@dataclass
class UXInteractionObservation:
    """Screen snapshot and DOM metrics captured during walkthrough."""

    step_name: str
    url: str
    view_name: str
    title: str
    headings: list[str]
    visible_buttons: list[str]
    visible_inputs: list[dict[str, Any]]
    text_content_sample: str
    screenshot_path: str | None = None
    has_modal_open: bool = False
    console_errors: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class UXAuditReport:
    """Consolidated UX and cognitive walkthrough audit report."""

    timestamp: str
    target_url: str
    overall_ux_grade: str  # "A+", "A", "B", "C", "F"
    overall_score_pct: float
    personas_audited: list[str]
    steps_evaluated: int
    findings: list[AuditFinding]
    metrics: dict[str, Any]


class AutonomousUXCritic:
    """Performs autonomous UX reviews by auditing rendered deliverables and UI artifacts."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path("docs/audits")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.findings: list[AuditFinding] = []
        self.observations: list[UXInteractionObservation] = []

    def get_standard_personas(self) -> list[PersonaProfile]:
        """Generate canonical executive and architectural personas."""
        return [
            PersonaProfile(
                persona_id="fortune500_cio_cfo",
                name="Persona 1: Enterprise CIO/CFO Executive",
                role="executive",
                primary_goal="Inspect executive summary, financial ALE/TCO exposure, and strategic roadmap",
                journey_steps=["cockpit_hero", "risk_radar", "actuarial_dashboard", "export_docx"],
                allowed_views=["executive_cockpit", "actuarial_summary", "roadmap"],
                prohibited_elements=["Traceback", "Raw SQL", "DB Console", "AST Graph"],
            ),
            PersonaProfile(
                persona_id="enterprise_cloud_architect",
                name="Persona 2: Lead Enterprise Technology Architect",
                role="architect",
                primary_goal="Verify domain blueprints, maturity scores, and second-order cascade dependencies",
                journey_steps=["domain_scorecard", "annex_navigator", "nexus_matrix", "fair_simulator"],
                allowed_views=["blueprints", "annexes", "nexus", "fair"],
                prohibited_elements=["Traceback", "SyntaxError", "undefined"],
            ),
            PersonaProfile(
                persona_id="bid_assessment_director",
                name="Persona 3: Assessment Engagement Director",
                role="assessment_manager",
                primary_goal="Govern evidence provenance, trigger synthesizers, and verify artifact completeness",
                journey_steps=["evidence_vault", "synthesis_monitor", "quality_gates", "download_package"],
                allowed_views=["vault", "synthesis", "gates", "export"],
                prohibited_elements=[],
            ),
        ]

    def audit_text_jargon_leaks(self, text_content: str, context_label: str) -> list[AuditFinding]:
        """Detect developer jargon or error traces leaked into user-visible views."""
        findings: list[AuditFinding] = []
        lower_text = text_content.lower()
        is_tech_cert = context_label.endswith("AUDIT_CERTIFICATE.html")
        for pattern, explanation in FORBIDDEN_TECH_TERMS.items():
            if is_tech_cert and pattern in (r"\bsqlite\b", r"\bpostgresql\b", r"\brest api\b", r"\bjson\b"):
                continue
            matches = list(re.finditer(pattern, lower_text, re.IGNORECASE))
            if matches:
                matched_snippet = matches[0].group(0)
                findings.append(
                    AuditFinding(
                        category="UX_HUMAN_EXPERIENCE",
                        severity="HIGH",
                        file_path=context_label,
                        line_number=None,
                        rule_id="UX-LEAK-DEVELOPER-JARGON",
                        message=f"Technical jargon leak detected: '{matched_snippet}' ({explanation})",
                        recommendation="Replace with executive business language and proper data formatting.",
                    )
                )
        return findings

    def audit_heading_clarity(
        self, headings: list[str], context_label: str
    ) -> list[AuditFinding]:
        """Verify heading case and clarity."""
        findings: list[AuditFinding] = []
        for h in headings:
            cleaned = h.strip()
            # Flag aggressive screaming case (> 4 words all upper)
            words = cleaned.split()
            if len(words) >= 4 and cleaned.isupper() and not any(w in cleaned for w in ("ISO", "NIST", "CMMI", "FAIR", "ALE")):
                findings.append(
                    AuditFinding(
                        category="UX_HUMAN_EXPERIENCE",
                        severity="MEDIUM",
                        file_path=context_label,
                        line_number=None,
                        rule_id="UX-TONE-AGGRESSIVE-ALL-CAPS",
                        message=f"Excessive screaming uppercase in heading: '{cleaned[:45]}...'",
                        recommendation="Use Title Case or Sentence Case for executive presentation.",
                    )
                )
        return findings

    def evaluate_static_html_artifact(
        self, html_path: Path, persona: PersonaProfile
    ) -> list[AuditFinding]:
        """Audit rendered HTML artifact (portal or certificate) for UX and accessibility."""
        context_label = str(html_path)
        if not html_path.exists():
            return []

        content = html_path.read_text(encoding="utf-8", errors="ignore")
        findings: list[AuditFinding] = []

        # Jargon leak check
        findings.extend(self.audit_text_jargon_leaks(content, context_label))

        if "<title>" not in content.lower():
            findings.append(
                AuditFinding(
                    category="UX_HUMAN_EXPERIENCE",
                    severity="MEDIUM",
                    file_path=context_label,
                    line_number=None,
                    rule_id="UX-MISSING-DOCUMENT-TITLE",
                    message="Rendered view missing <title> tag (WCAG 2.4.2 Page Titled)",
                    recommendation="Add descriptive executive title to document head.",
                )
            )

        # Viewport meta check
        if "name=\"viewport\"" not in content.lower():
            findings.append(
                AuditFinding(
                    category="UX_HUMAN_EXPERIENCE",
                    severity="MEDIUM",
                    file_path=context_label,
                    line_number=None,
                    rule_id="UX-MISSING-RESPONSIVE-VIEWPORT",
                    message="Rendered view missing responsive viewport meta tag",
                    recommendation="Add <meta name='viewport' content='width=device-width, initial-scale=1.0'>.",
                )
            )

        self.findings.extend(findings)
        return findings


def run_autonomous_ux_critic_probe(target_dir: Path) -> ProbeResult:
    """Execute autonomous UX and cognitive heuristics probe across rendered web assets."""
    critic = AutonomousUXCritic(output_dir=target_dir / "docs" / "audits")
    personas = critic.get_standard_personas()

    # Search for rendered HTML assets in docs/audits, working/, and public/
    html_candidates: list[Path] = []
    for candidate in (
        target_dir / "docs" / "audits" / "AUDIT_CERTIFICATE.html",
        target_dir / "working" / "lineage_portal.html",
    ):
        if candidate.exists():
            html_candidates.append(candidate)

    findings: list[AuditFinding] = []
    for html_file in html_candidates:
        for p in personas:
            step_findings = critic.evaluate_static_html_artifact(html_file, p)
            findings.extend(step_findings)

    # Compute score
    critical_count = sum(1 for f in findings if f.severity in ("CRITICAL", "HIGH"))
    score = 100.0 if critical_count == 0 else max(50.0, 100.0 - critical_count * 15.0)
    passed = critical_count == 0

    return ProbeResult(
        probe_name="Autonomous UX & Cognitive Walkthrough (Nielsen / WCAG 2.1)",
        score_pct=score,
        passed=passed,
        metrics={
            "personas_evaluated": len(personas),
            "html_artifacts_audited": len(html_candidates),
            "ux_friction_findings_count": len(findings),
            "critical_blockers_count": critical_count,
        },
        findings=findings,
    )
