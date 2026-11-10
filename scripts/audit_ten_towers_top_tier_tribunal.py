#!/usr/bin/env python3
"""Adversarial Tribunal: Top-Tier World Experts Audit of all 10 Molins Deliverable Annexes.

Simulates 10 Tier-1 World SME auditors evaluating the actual generated Word deliverables:
- T1: Uptime Institute Senior Data Center Auditor
- T2: Global Head of Compute & Virtualization Architect
- T3: Principal Enterprise Network Architect (CCIE/SD-WAN)
- T4: Head of Enterprise Storage & Backup Engineering
- T5: Chief Continuity & Industrial Resilience Officer
- T6: Industrial CISO & NIS2 Lead Auditor (IEC 62443)
- T7: Global ITIL 4 Master & Principal SRE Director
- T8: FinOps Foundation Fellow & Principal Software Licensing Auditor
- T9: Global Head of Digital Workplace & End-User Computing
- T10: Heavy Industrial Automation & Plant Operations Director
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
import docx

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

client = create_genai_client()
model_name = get_model(ModelTier.REASONING)

ANNEX_DIR = REPO_ROOT / "working" / "out" / "Molins_Entrega_Cliente_Final" / "02_DIAGNOSTICOS_ASIS"

TOWER_EXPERT_PROFILES = {
    "T1": {
        "num": "01",
        "role": "Principal Data Center Infrastructure Auditor (Uptime Institute Tier-IV Senior Fellow)",
        "lens": "Physical redundancy, ATS switching, cooling capacity, electrical single-points-of-failure, physical security.",
    },
    "T2": {
        "num": "02",
        "role": "Global Head of Compute & Platforms (HPE SimpliVity & VMware Certified Design Expert)",
        "lens": "RAM/CPU saturation, N+1 tolerance, hyperconverged cluster health, OS obsolescence, virtualization sprawl.",
    },
    "T3": {
        "num": "03",
        "role": "Principal Enterprise Network Architect (Dual CCIE / SD-WAN Specialist)",
        "lens": "WAN latency, SD-WAN failover, plant switch lifecycle, dynamic routing, edge firewall bottlenecks.",
    },
    "T4": {
        "num": "04",
        "role": "Head of Enterprise Storage & Backup Architecture (SNIA Fellow / Cohesity & NetApp SME)",
        "lens": "IOPS saturation, snapshot retention debt, immutable air-gapped backup, RPO compliance, storage tiering.",
    },
    "T5": {
        "num": "05",
        "role": "Chief Continuity Officer & Industrial Disaster Recovery Lead (DRI International Fellow)",
        "lens": "RTO reality, cross-site disaster recovery drills, failover orchestration, business impact analysis.",
    },
    "T6": {
        "num": "06",
        "role": "Industrial CISO & European Cybersecurity Regulatory Examiner (NIS2 / IEC 62443 / CISM)",
        "lens": "PAM/secrets governance, lateral movement, ransomware containment, OT boundary segregation, regulatory fine realism.",
    },
    "T7": {
        "num": "07",
        "role": "Global Head of IT Service Management & SRE Director (ITIL 4 Master)",
        "lens": "SLA management, incident triage toil, CMDB accuracy, monitoring fragmentation (Zabbix/Prometheus/Loki).",
    },
    "T8": {
        "num": "08",
        "role": "FinOps Foundation Principal & Enterprise Software Licensing Auditor (Broadcom/SAP Defense SME)",
        "lens": "Broadcom 2027 per-core subscription hike, shadow cloud drift, SECIL M&A contract duplication, OpEx reclamation.",
    },
    "T9": {
        "num": "09",
        "role": "Global Head of End-User Computing & Modern Workplace (Intune / Autopilot / DEX Lead)",
        "lens": "Fleet obsolescence, remote worker experience, endpoint patching friction, onboarding velocity.",
    },
    "T10": {
        "num": "10",
        "role": "Heavy Process Plant Automation & Operations Director (Cement & Quarry Industry Lead)",
        "lens": "Weighbridge continuity, silo buffering, SCADA/DCS reliability, dispatch manual workarounds, plant downtime cost.",
    },
}


def extract_tower_content(num_str: str) -> str:
    """Extracts the complete deliverable text and tables sequentially from the physical docx."""
    files = list(ANNEX_DIR.glob(f"*Anexo_{num_str}_*.docx"))
    if not files:
        return f"File for tower {num_str} not found in {ANNEX_DIR}"

    doc = docx.Document(files[0])
    lines = []
    lines.append(f"DOCUMENTO COMPLETO OFICIAL: {files[0].name}\n")

    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if p.style.name.startswith("Heading 1") or p.style.name.startswith("Appendix Heading 1"):
            lines.append(f"\n# {t}\n")
        elif p.style.name.startswith("Heading 2") or p.style.name.startswith("Appendix Heading 2"):
            lines.append(f"\n## {t}\n")
        elif p.style.name.startswith("Heading 3"):
            lines.append(f"\n### {t}\n")
        elif p.style.name.startswith("Bullet") or p.style.name.startswith("List"):
            lines.append(f"* {t}")
        else:
            lines.append(t)

    lines.append("\n\n--- TABLAS OFICIALES DEL DOCUMENTO ---\n")
    for t_idx, table in enumerate(doc.tables):
        if not table.rows:
            continue
        header = [c.text.strip().replace("\n", " ") for c in table.rows[0].cells]
        lines.append(f"\n[Tabla {t_idx + 1}]: {' | '.join(header)}")
        for r in table.rows[1:]:
            row_str = " | ".join(c.text.strip().replace("\n", " ") for c in r.cells)
            lines.append(f"  {row_str}")

    return "\n".join(lines)


def audit_single_tower(tower_id: str, profile: Dict[str, str], raw_content: str) -> str:
    prompt = f"""You are acting as an external, world-class Top Tier-1 expert hired by the Board of Directors of Cementos Molins to audit this deliverable:
Role: {profile['role']}
Audit Focus & Lens: {profile['lens']}

CLIENT CONTEXT:
Cementos Molins is a multinational building materials manufacturer (cement, concrete, aggregates) headquartered in Spain with 1.144 Billion EUR revenue and ~3,900 employees. Operations in Spain, Portugal (SECIL integration), Latin America, and North Africa.

THE AUDITED DELIVERABLE CONTENT (Extracted directly from the client's official Word report):
{raw_content}

YOUR ASSIGNMENT:
Provide an unflinching, brutally honest, peer-reviewed evaluation of this technical diagnostic and its risk quantification:
1. OVERALL VERDICT: Would you APPROVE this report, REJECT it, or DEMAND REVISIONS? State your decision clearly in the first sentence.
2. TECHNICAL REALISM OF THE DIAGNOSTIC: Does the technical analysis reflect the true operational reality of an enterprise at this scale, or does it sound like a generic consulting template?
3. SCRUTINY OF RISK FORMULATION & NUMBERS:
   - What is your opinion of the numbers (ALE, Single Severe Event / P90)?
   - How are the risk scenarios articulated? Are they credible, or can a smart client engineer shoot them down?
   - What objections would you raise if you were defending the company's budget?
4. WHAT IS GENUINELY IMPRESSIVE ABOUT THIS REPORT?
5. FINAL GRADE (1 to 10) & ONE ACTIONABLE RECOMMENDATION.

Respond in 100% Technical English with senior executive gravitas.
"""
    import time
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if attempt == 3:
                raise
            print(f"    [Retry {attempt}/3] API call encountered {e}, waiting 5s...")
            time.sleep(5)
    return "Error generating response"


def main() -> None:
    print("=" * 80)
    print("STARTING TOP TIER-1 WORLD EXPERT TRIBUNAL FOR ALL 10 MOLINS TOWERS")
    print("=" * 80)
    
    out_dir = REPO_ROOT / "docs" / "audits" / "tribunal_10_towers"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    master_report = []
    master_report.append("# TOP TIER-1 WORLD EXPERT TRIBUNAL: CEMENTOS MOLINS DELIVERABLE AUDIT\n")
    master_report.append("**Authority:** Independent External Expert Panel convened by the Board of Directors\n")
    master_report.append("**Target Suite:** Official AS-IS Deliverables (`Molins_Entrega_Cliente_Final`)\n\n")
    
    for tower_id, profile in sorted(TOWER_EXPERT_PROFILES.items(), key=lambda x: int(x[0][1:])):
        print(f"\nEvaluating {tower_id} ({profile['role']})...")
        raw_text = extract_tower_content(profile["num"])
        expert_review = audit_single_tower(tower_id, profile, raw_text)
        
        tower_file = out_dir / f"AUDIT_EXPERT_{tower_id}.md"
        tower_file.write_text(expert_review, encoding="utf-8")
        print(f"  ✓ Review written to: {tower_file.name}")
        
        master_report.append(f"## {tower_id}: {profile['role']}\n")
        master_report.append(expert_review)
        master_report.append("\n---\n\n")
        
    master_file = REPO_ROOT / "docs" / "audits" / "ARGON_10_TOWERS_TOP_TIER_TRIBUNAL_CONSOLIDATED.md"
    master_file.write_text("".join(master_report), encoding="utf-8")
    print(f"\n✓ Consolidated Master Tribunal Report written to: {master_file}")


if __name__ == "__main__":
    main()
