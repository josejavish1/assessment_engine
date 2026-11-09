"""Generates deep, high-fidelity synthetic client fixtures based on real-world enterprise benchmarks.

Produces for each benchmark enterprise:
1. assessment_responses.txt: Quantitative maturity survey responses (1-5 scale) for active towers only.
2. transcription_interview_session.docx: Deep technical interview dialogue (40-65 paragraphs per client) matching Molins operational density.
3. client_intelligence.json: Client intelligence dossier conforming to ClientDossierV3 with real financial telemetry.

Real Enterprise Benchmarks:
1. uk_fintech: Starling Bank Ltd (6 towers: T1, T3, T5, T6, T8, T10) | GBP (£) | en | banking | DORA / PRA / FCA
2. br_healthcare: Rede D'Or São Luiz S.A. (9 towers: T1-T9) | BRL (R$) | pt | healthcare | LGPD / ANS / ANVISA
3. fr_logistics: Geodis SA (10 towers: T1-T10) | EUR (€) | fr | critical_infrastructure | NIS2 / ANSSI / RGPD
4. mx_retail: Grupo Comercial Chedraui S.A.B. de C.V. (5 towers: T2, T3, T7, T9, T10) | MXN ($) | es | retail | PCI-DSS / SAT CFDI 4.0
5. us_saas: Datadog Inc. (4 towers: T1, T5, T6, T9) | USD ($) | en | technology | SOC 2 / FedRAMP / SEC
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import docx
from docx.shared import Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_ROOT = ROOT / "tests" / "test_data" / "synthetic_clients"


def load_tower_kpis(tower_id: str) -> list[str]:
    """Load ordered KPI IDs for a given tower from engine configuration."""
    def_file = ROOT / "engine_config" / "towers" / tower_id / f"tower_definition_{tower_id}.json"
    if not def_file.exists():
        return []
    data = json.loads(def_file.read_text(encoding="utf-8"))
    kpis = []
    for pillar in data.get("pillars", []):
        for kpi in pillar.get("kpis", []):
            kpis.append(kpi["kpi_id"])
    return kpis


def format_responses_text(scores: dict[str, float]) -> str:
    """Format dictionary of question_id -> score into standard survey response text."""
    lines = []
    current_tower = ""
    for q_id, score in scores.items():
        tower = q_id.split(".")[0]
        if tower != current_tower:
            if current_tower:
                lines.append("")
            current_tower = tower
        score_str = f"{int(score)}" if score.is_integer() else f"{score:.1f}".replace(".", ",")
        lines.append(f"{q_id}\t{score_str}")
    return "\n".join(lines) + "\n"


def create_docx_transcript(
    output_path: Path,
    title: str,
    meta_fields: list[tuple[str, str]],
    dialogue: list[tuple[str, str]],
) -> None:
    """Create a formatted .docx transcript with header metadata and turn-by-turn dialogue."""
    doc = docx.Document()

    # Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run(title)
    r_title.bold = True
    r_title.font.size = Pt(15)
    r_title.font.color.rgb = RGBColor(0, 114, 188)

    # Metadata
    p_meta = doc.add_paragraph()
    for label, val in meta_fields:
        p_meta.add_run(f"{label}: ").bold = True
        p_meta.add_run(f"{val}\n")

    doc.add_paragraph("=" * 80)

    # Dialogue turns
    for speaker, text in dialogue:
        p = doc.add_paragraph()
        run_spk = p.add_run(f"{speaker}: ")
        run_spk.bold = True
        run_spk.font.color.rgb = RGBColor(46, 64, 77)
        p.add_run(text)
        p.paragraph_format.space_after = Pt(6)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))


# ==============================================================================
# 1. UK FINTECH: Starling Bank Ltd (6 Towers - 54 Conversational Paragraphs)
# ==============================================================================
def build_uk_fintech() -> None:
    target_dir = SYNTHETIC_ROOT / "uk_fintech"
    target_dir.mkdir(parents=True, exist_ok=True)
    towers = ["T1", "T3", "T5", "T6", "T8", "T10"]

    scores: dict[str, float] = {}
    offsets = {"T1": 4.2, "T3": 4.5, "T5": 4.7, "T6": 4.7, "T8": 4.5, "T10": 4.6}
    for t in towers:
        kpis = load_tower_kpis(t)
        base = offsets[t]
        for idx, k in enumerate(kpis):
            val = min(5.0, round(base + (idx % 3 - 1) * 0.15, 1))
            scores[f"{k}.PR1"] = val

    (target_dir / "assessment_responses.txt").write_text(
        format_responses_text(scores), encoding="utf-8"
    )

    dialogue = [
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Good morning. This diagnostic session evaluates Starling Bank's technical architecture across six contracted domains: "
         "Physical Facilities & Clearing Ingress (Tower 1), Network & Connectivity (Tower 3), Continuous Resilience, Business Continuity "
         "& Cyber Recovery (Tower 5), Security & Identity Governance (Tower 6), Strategy, Governance & FinOps (Tower 8), and Core Payment "
         "Rails & Settlement Systems (Tower 10). Towers 2, 4, 7, and 9 are outside our contracted diagnostic scope. Steve, please outline "
         "Starling's commercial scale and architectural philosophy."),
        ("Steve Newson (Chief Technology Officer)",
         "Starling Bank is a fully authorised UK clearing bank dual-regulated by the Prudential Regulation Authority (PRA) and the Financial "
         "Conduct Authority (FCA). We hold over £10.6 billion in customer deposits across 4.2 million active accounts, generating annual operating "
         "revenue of approximately £665 million. We process over 95 million payment transactions per month across Faster Payments, BACS, CHAPS, "
         "and debit cards. Starling was built from day one as a 100% cloud-native bank on AWS across London (eu-west-2) and Dublin (eu-west-1). "
         "We operate zero mainframe hardware. However, to maintain direct settlement membership with Pay.UK and the Bank of England, we operate "
         "dedicated colocation footprints at Equinix LD4 in Slough and LD5."),

        # Tower 1: Physical Data Center & Ingress
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Let us start with Tower 1, Pillar 1: Electrical Continuity and Power Infrastructure at Equinix LD4. How is autonomy guaranteed?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "At LD4, our cryptographic Hardware Security Modules and border Arista switches receive true dual A/B utility feeds backed by rotary UPS "
         "banks. In the event of grid collapse, Cummins diesel generators kick in within 12 seconds with 72 hours of fuel on site. Power density "
         "per cabinet is maintained at 6.5 kVA, well inside LD4's 12 kVA design rating."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "And for Tower 1, Pillar 2: Climate Control and Environmental Monitoring in the caged suites?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "Equinix maintains hot-aisle containment with N+2 chillers. Temperature is strictly regulated between 19°C and 22°C with 45% relative "
         "humidity. Real-time SNMP feeds from cold-aisle sensors stream telemetry into our Datadog infrastructure dashboards."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Moving to Tower 1, Pillar 3: Physical Access Security and Audit Trail?"),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "Access to our caged suites requires three levels of physical validation: Equinix biometric iris scanning at the perimeter, biometric palm "
         "vein authentication at our cage gate, and dual-authorization escort for any vendor engineer. CCTV coverage is continuous with 365-day "
         "tamper-proof video archives complying with FCA and PCI-PIN requirements."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 1, Pillar 4: Fire Suppression and Environmental Hazard Protection?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "LD4 uses dual-action pre-action water mist alongside VESDA early smoke detection. If an anomaly is sensed, clean agent gas (Inergen) "
         "discharges in under 30 seconds without damaging the delicate cryptographic silicon inside our Thales units."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 1, Pillar 5: Facilities Operations and Maintenance Governance?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "We participate in Equinix's semi-annual ATS transfer and simulated black-building load bank drills. Our engineers shadow facility "
         "maintenance teams under strict Method Statements and Permits to Work. In four years of operation, we have experienced 100% uptime on feeds."),

        # Tower 3: Network & Connectivity
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Let us examine Tower 3, Pillar 1: Backbone Architecture and Core Redundancy between Slough and AWS."),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "We operate dual 10 Gbps AWS Direct Connect circuits from Equinix LD4 into AWS eu-west-2 (London) and diverse 10 Gbps circuits from LD5 "
         "into AWS eu-west-1 (Dublin). There is zero single point of failure. BGP failover triggers within 800 milliseconds via BFD sessions."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 3, Pillar 2: Corporate SD-WAN and Office Connectivity across London, Southampton, and Cardiff?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "All regional offices utilize dual diverse gigabit internet feeds terminated on Fortinet SD-WAN gateways. Traffic to cloud infrastructure "
         "is routed through encrypted WireGuard overlays with dynamic path selection, maintaining sub-15ms latency to AWS eu-west-2."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 3, Pillar 3: Direct Clearing Interconnects to Pay.UK and Vocalink?"),
        ("Steve Newson (Chief Technology Officer)",
         "We have dedicated DWDM optical cross-connects inside LD4 to the Vocalink Faster Payments clearing network and Mastercard clearing switches. "
         "Round-trip latency to the clearing gateways is measured at 1.8 milliseconds."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 3, Pillar 4: Cloud Ingress, Edge Security, and Open Banking APIs?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "Public endpoints, including our Open Banking PSD2 APIs and mobile banking gateway, terminate on Cloudflare Magic Transit and Cloudflare "
         "Enterprise WAF. We enforce mutual TLS (mTLS) for all banking partner API calls, with automated rate limiting and bot management."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 3, Pillar 5: Network Observability, NetDevOps, and CI/CD Automation?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "100% of our VPCs, subnets, route tables, and Transit Gateway attachments are managed via Terraform Cloud. We ingest all VPC Flow Logs "
         "into Datadog Network Performance Monitoring, allowing us to trace connection latency down to individual Kubernetes pods."),

        # Tower 5: Resilience, Business Continuity & Cyber Recovery
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Transitioning to Tower 5, Pillar 1: Business Impact Analysis and DORA Operational Resilience Framework."),
        ("Steve Newson (Chief Technology Officer)",
         "Under DORA and PRA SS1/21, our primary Important Business Service is core payment clearing. The board has established an impact "
         "tolerance ceiling of 15 minutes. In actual engineering drills, our RTO is under 4 minutes, and our database RPO is under 2 seconds."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 5, Pillar 2: Continuous Data Protection and Transactional Consistency?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "Our data tier is Amazon Aurora Global PostgreSQL. Transactional writes in London stream synchronously to three availability zones and "
         "replicate asynchronously to Dublin with typical lag of 140 milliseconds. We take continuous hourly snapshots with 35-day point-in-time recovery."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 5, Pillar 3: Disaster Recovery Execution and Automated Regional Failover?"),
        ("Steve Newson (Chief Technology Officer)",
         "We execute quarterly unannounced DR failovers. Using AWS Route 53 Application Recovery Controller, we shifted 100% of payment ingestion "
         "from London to Dublin in our September 2026 drill. Full API processing resumed in exactly 3 minutes and 25 seconds."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 5, Pillar 4: Cyber Recovery and Anti-Ransomware Vaulting?"),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "We maintain a decoupled 'Cyber Vault' AWS account in a separate AWS Organization. Ledger snapshots and Kafka offsets are replicated "
         "hourly using AWS KMS keys owned exclusively by the vault. S3 Object Lock is enforced in Compliance Mode with a 90-day retention lock."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 5, Pillar 5: Chaos Engineering and Systemic Shock Testing?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "We run continuous chaos experiments in production using Gremlin and Chaos Mesh. Every Tuesday, automated chaos pipelines terminate "
         "random Kubernetes worker nodes and inject 150ms synthetic latency across Aurora read replicas to verify automatic reconnection."),

        # Tower 6: Security & Identity Governance
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Let us assess Tower 6, Pillar 1: Identity and Access Management (IAM) under Zero Trust."),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "We enforce 100% MFA across all 3,200 employees via Okta integrated with FIDO2 WebAuthn hardware keys (YubiKeys). SMS, email OTP, "
         "and phone push notifications are barred for corporate or administrative access. Joiner-Mover-Leaver workflows sync via SCIM in real time."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 6, Pillar 2: Privileged Access Management (PAM) for Cloud Engineering?"),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "No engineer holds standing production AWS credentials or static SSH keys. All administrative access is brokered through Teleport PAM. "
         "Certificates expire after 60 minutes, require peer approval via Slack bots, and generate tamper-proof terminal session recordings."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 6, Pillar 3: Infrastructure Hardening and Secrets Governance?"),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "All microservices retrieve dynamic credentials from HashiCorp Vault Enterprise. Database credentials auto-rotate every 24 hours. "
         "Golden container images are built using minimal distroless base images hardened to CIS Level 2 benchmarks."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 6, Pillar 4: Vulnerability Management, AppSec, and Patching Cadence?"),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "Container images in Amazon ECR are scanned continuously via Trivy and Wiz. Critical CVEs must be patched within 48 hours. If upstream "
         "patches lag, we deploy virtual patches via Cloudflare WAF or Cilium network policies within 4 hours."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 6, Pillar 5: Security Operations, SIEM, and Threat Intelligence?"),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "Our 24/7 SOC ingests 14 terabytes of telemetry daily into Splunk Cloud. We undergo annual CBEST penetration testing mandated by the "
         "Bank of England and hold clean PCI-DSS v4.0 Level 1 and SOC 2 Type II accreditations with zero exceptions."),

        # Tower 8: Strategy, Governance & FinOps
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Moving to Tower 8, Pillar 1: Technology Alignment and Cloud Strategy Roadmap."),
        ("Steve Newson (Chief Technology Officer)",
         "Our technology strategy is aligned with Starling's 3-year European expansion plan. All engineering squads operate against quarterly OKRs. "
         "Our Architecture Review Board meets weekly to review Architectural Decision Records (ADRs) for any service exceeding £20k spend."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 8, Pillar 2: Engineering Delivery Governance and Velocity?"),
        ("Steve Newson (Chief Technology Officer)",
         "We operate autonomous cross-functional squads releasing to production an average of 18 times per day. Deployment success rate is 99.6%, "
         "and our change failure recovery time (MTTR) is under 12 minutes."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 8, Pillar 3: Technology Risk and Regulatory Compliance Governance?"),
        ("Sarah Jenkins (Chief Information Security Officer)",
         "Technology risk is monitored through our Enterprise Risk Management Framework aligned with FCA SYSC and PRA rules. Risk dashboards "
         "are presented monthly to the Board Audit & Risk Committee with quantitative residual risk tracking."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 8, Pillar 4: FinOps, Unit Economics, and Cloud Cost Allocation?"),
        ("Steve Newson (Chief Technology Officer)",
         "We track cloud costs per transaction in real time inside Datadog and Kubecost. Our current total technology cost per settlement "
         "transaction is £0.0019. Total monthly AWS expenditure is £380,000, representing less than 1.8% of gross revenues. We maintain 84% "
         "discount coverage via 3-year Compute Savings Plans and Karpenter Spot provisioning for non-critical queues."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 8, Pillar 5: Vendor Risk and Hyperscaler Concentration Governance?"),
        ("Steve Newson (Chief Technology Officer)",
         "Because we are heavily reliant on AWS, we conduct annual cloud exit strategy simulations mandated by the PRA. All core services are "
         "packaged in standard OCI containers orchestrated via vanilla Kubernetes manifests, ensuring portability if required."),

        # Tower 10: Core Payment Rails & Settlement Systems
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Finally, Tower 10, Pillar 1: Core Banking Engine Architecture and Standard Operating Procedures."),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "Our core banking engine, StarlingLedger, is built in Java 21 and Go. It implements an event-sourcing paradigm backed by Apache Kafka. "
         "All transactions are modeled as immutable double-entry journal entries with cryptographic hashing."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 10, Pillar 2: Core Rails CI/CD and Canary Release Pipeline?"),
        ("Steve Newson (Chief Technology Officer)",
         "We deploy core payment microservices using blue/green canary deployments on Amazon EKS via ArgoCD. Automated synthetic payment probes "
         "verify settlement integrity before shifting 100% of live clearing traffic."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 10, Pillar 3: High-Throughput Processing and Clearing House SLAs?"),
        ("Tariq Mansoor (Director of Platform Infrastructure)",
         "We process Faster Payments in under 38 milliseconds end to end. In stress tests, StarlingLedger sustained 6,200 TPS for four hours "
         "with P99 latency below 95ms, well above our record peak of 1,850 TPS on Black Friday."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 10, Pillar 4: Payment Messaging Interoperability and ISO 20022 Compliance?"),
        ("Steve Newson (Chief Technology Officer)",
         "Starling is fully compliant with ISO 20022 message standards across Faster Payments, CHAPS, and SEPA. Inbound XML messages are transformed "
         "into internal Protocol Buffers with automated schema validation against Pay.UK specifications."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Tower 10, Pillar 5: Platform Obsolescence and Continuous Modernization?"),
        ("Steve Newson (Chief Technology Officer)",
         "We maintain zero runtime technical debt. We run LTS versions of Java and Go, upgrading runtimes within six months of release. "
         "Our direct clearing membership with Pay.UK saves approximately £18 million annually compared to traditional bureau processing."),
        ("Dr. Alistair Vance (Lead Assessment Architect)",
         "Thank you Steve, Sarah, and Tariq. This granular testimony provides exhaustive evidential backing across all six domains."),
    ]

    create_docx_transcript(
        target_dir / "transcription_interview_session.docx",
        "TRANSCRIPTION: TECHNICAL ARCHITECTURE & RESILIENCE ASSESSMENT",
        [
            ("Client", "Starling Bank Ltd (UK Regulated Clearing Bank)"),
            ("Date", "14 October 2026"),
            ("Classification", "Confidential - PRA / FCA / DORA Regulatory Scope"),
            ("Currency", "GBP (£)"),
            ("Language", "English (UK)"),
            ("Format", "Full In-Depth Diagnostic Dialogue (54 Conversational Turns)"),
        ],
        dialogue,
    )

    intel = {
        "version": "3.0",
        "client_name": "Starling Bank",
        "metadata": {
            "dossier_id": "starling_bank_uk",
            "schema_version": "3.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lang": "en",
            "country": "United Kingdom",
            "currency": "GBP",
            "currency_symbol": "£",
        },
        "profile": {
            "industry": "banking",
            "sub_industry": "Digital Challenger Clearing Bank",
            "hierarchy": "UK Authorised Credit Institution",
            "headquarters": "London, United Kingdom",
            "operating_locations": ["London", "Southampton", "Cardiff", "Dublin"],
            "headcount": 3200,
            "financial_profile": {
                "currency": "GBP",
                "currency_symbol": "£",
                "annual_revenue": 665000000.0,
                "customer_deposits": 10600000000.0,
                "hourly_downtime_cost": 140000.0,
            },
        },
        "regulatory_context": [
            {"regulation": "DORA (Digital Operational Resilience Act)", "authority": "EBA", "status": "In Compliance Implementation"},
            {"regulation": "PRA SS1/21 (Operational Resilience)", "authority": "Bank of England", "status": "Audited & Supervised"},
            {"regulation": "FCA SYSC", "authority": "Financial Conduct Authority", "status": "Compliant"},
            {"regulation": "PCI-DSS v4.0 Level 1", "authority": "PCI SSC", "status": "Certified"},
        ],
        "business_context": {
            "ceo_agenda": {"summary": "Scale European clearing operations, expand SME banking franchise, and certify DORA compliance."},
            "transformation_horizon": {"stage": "H2", "label": "Operational Resilience & Scaled Clearing", "rationale": "High-maturity cloud native core expanding international payment rails."},
            "strategic_priorities": [
                {"name": "DORA & PRA SS1/21 Operational Resilience Certification"},
                {"name": "Multi-Region Cloud Failover and Exit Strategy Assurance"},
            ],
        },
        "technology_context": {
            "dominant_hyperscaler": "AWS",
            "footprint_summary": {"summary": "Cloud-native multi-region AWS topology with Equinix LD4/LD5 clearing colocation."},
            "group_level_stack": [
                {"category": "Cloud Hyperscaler", "name": "AWS (eu-west-2, eu-west-1)"},
                {"category": "Colocation", "name": "Equinix LD4 / LD5 (Slough)"},
                {"category": "Container Orchestration", "name": "Amazon EKS with Cilium eBPF"},
                {"category": "Database", "name": "Amazon Aurora Global PostgreSQL, DynamoDB"},
                {"category": "Identity & PAM", "name": "Okta, Teleport Enterprise, HashiCorp Vault"},
            ],
            "field_metrics": [
                {"metric": "Monthly Tx Volume", "value": "95,000,000 tx"},
                {"metric": "Unit Cost per Tx", "value": "£0.0019"},
                {"metric": "Tested RTO", "value": "3 min 25 sec"},
            ],
        },
        "tower_overrides": {t: {"target_maturity": 4.6, "status": "In Scope"} for t in towers},
        "epistemic_graph": {
            "topology": {"nodes": towers, "edges": [{"source": "T1", "target": "T3", "weight": 0.85}]},
            "audits": {"cascading_impact_index": 0.16},
        },
        "review": {"summary": "Starling Bank Benchmark Fixture", "status": "Certified"},
        "claims": [],
    }
    for t_out in ["T2", "T4", "T7", "T9"]:
        intel["tower_overrides"][t_out] = {"target_maturity": 0.0, "status": "Out of Scope"}

    (target_dir / "client_intelligence.json").write_text(
        json.dumps(intel, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Built: uk_fintech (Starling Bank - {len(dialogue)} paragraphs, 6 towers)")


# ==============================================================================
# 2. BRAZIL HEALTHCARE: Rede D'Or São Luiz S.A. (9 Towers - 56 Paragraphs)
# ==============================================================================
def build_br_healthcare() -> None:
    target_dir = SYNTHETIC_ROOT / "br_healthcare"
    target_dir.mkdir(parents=True, exist_ok=True)
    towers = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]

    scores: dict[str, float] = {}
    offsets = {"T1": 2.4, "T2": 2.0, "T3": 2.2, "T4": 1.8, "T5": 2.1, "T6": 1.7, "T7": 2.4, "T8": 2.0, "T9": 2.5}
    for t in towers:
        kpis = load_tower_kpis(t)
        base = offsets[t]
        for idx, k in enumerate(kpis):
            val = max(1.0, min(5.0, round(base + (idx % 3 - 1) * 0.2, 1)))
            scores[f"{k}.PR1"] = val

    (target_dir / "assessment_responses.txt").write_text(
        format_responses_text(scores), encoding="utf-8"
    )

    dialogue = [
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Bom dia. Iniciamos a sessão aprofundada de diagnóstico de maturidade técnica e resiliência hospitalar da Rede D'Or São Luiz. "
         "Nosso escopo abrange 9 torres: CPD Físico (T1), Computação (T2), Conectividade (T3), Armazenamento PACS (T4), Resiliência e "
         "Continuidade Clínica (T5), Cibersegurança LGPD (T6), ITSM e Suporte (T7), Governança e FinOps (T8) e Endpoints Beira-Leito (T9). "
         "A Torre 10 de Mainframe não se aplica ao setor de saúde e está formalmente excluída. Dr. Henrique, por favor apresente a operação."),
        ("Dr. Henrique Coutinho (Diretor Executivo de TI)",
         "A Rede D'Or São Luiz é a maior rede hospitalar privada da América Latina, operando 73 hospitais próprios, mais de 11.500 leitos "
         "e faturando R$ 47 bilhões ao ano com 75 mil colaboradores. Nossa operação assistencial não pode parar: qualquer indisponibilidade "
         "do prontuário eletrônico (Philips Tasy e MV Soul) ou dos exames radiológicos no centro cirúrgico compromete a segurança dos pacientes. "
         "Nosso custo de parada hospitalar é estimado em R$ 420.000 por hora."),

        # T1: CPD Físico
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Vamos avaliar a Torre 1, Pilar 1: Energia e Continuidade Elétrica nos datacenters hospitalares."),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "No Hospital São Luiz Itaim em São Paulo, temos geradores de 1.500 kVA e nobreaks rotativos redundantes. Contudo, em 22 hospitais "
         "regionais adquiridos no Nordeste, os nobreaks são estáticos com baterias que oferecem apenas 10 a 12 minutos de autonomia."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 1, Pilar 2: Climatização e Controle Térmico das salas de servidores?"),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Nos hospitais centrais usamos equipamentos de ar condicionado de precisão em configuração N+1. Mas em unidades periféricas, "
         "temos ar-condicionado de conforto comercial sem controle de umidade, gerando alertas frequentes de temperatura acima de 28°C no verão."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 1, Pilar 3: Segurança Física e Controle de Acesso aos racks?"),
        ("Carlos Eduardo Silveira (CISO)",
         "As salas de CPD principais usam biometria e eclusas com registro em CFTV. Nos hospitais regionais menores, o controle ainda é por chave "
         "física com a equipe de manutenção predial, sem rastreabilidade eletrônica de entrada e saída."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 1, Pilar 4 e 5: Combate a Incêndio e Monitoramento Predial?"),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Os datacenters principais têm gás FM-200 e detecção precoce de fumaça. As salas técnicas locais ainda dependem de extintores manuais "
         "de CO2 e não dispõem de sistema BMS integrado para envio de alarmes em tempo real para a central."),

        # T2: Computação e Virtualização
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Passando para a Torre 2, Pilar 1 e 2: Capacidade de Computação, Cisco UCS e VMware vSphere."),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Operamos 2.200 máquinas virtuais sobre Cisco UCS e Dell PowerEdge rodando VMware vSphere 7.0. O processamento do ERP Tasy exige bancos "
         "Oracle de grande porte. Em picos de internação matinais, a utilização de CPU dos hosts de banco atinge 88%."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 2, Pilar 3 e 4: Estratégia Híbrida e Nuvem Microsoft Azure?"),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Criamos uma zona de aterrissagem no Azure Brasil Sul conectada por ExpressRoute de 2 Gbps. Migramos portais de agendamento e aplicações "
         "secundárias, mas o núcleo clínico e os bancos relacionais de prontuário eletrônico permanecem 100% on-premises por latência."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 2, Pilar 5: Resiliência de Servidores e Manutenção Preventiva?"),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Cerca de 35% do parque de servidores em hospitais do interior atingiu o fim de garantia (EoL). A substituição de peças depende de contratos "
         "de terceiros que levam até 24 horas para atendimento em cidades forâneas."),

        # T3: Conectividade e Redes
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 3, Pilar 1: Arquitetura de Rede Core e Microssegmentação Hospitalar."),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Nosso core nos hospitais de ponta é baseado em switches Cisco Catalyst 9500. A grande fraqueza é que em 38 unidades não conseguimos "
         "microssegmentar a rede: computadores de triagem e bombas de infusão médica compartilham a mesma faixa de VLAN."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 3, Pilar 2 e 3: Conectividade WAN MPLS e Enlaces entre Hospitais?"),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "A rede entre os 73 hospitais utiliza MPLS da Embratel com links de 100 Mbps a 1 Gbps, com redundância por fibra da Vivo ou SD-WAN "
         "Fortinet. As quedas de link são raras nos grandes centros, mas comuns em cidades do interior durante tempestades."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 3, Pilar 4 e 5: Wi-Fi Médico Beira-Leito e Observabilidade de Rede?"),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Temos mais de 6.000 access points Cisco e Aruba. Em quartos de enfermaria com paredes de concreto espesso, há zonas de sombra que "
         "provocam desconexão dos carrinhos de medicação. Usamos o Cisco DNA Center para monitoramento nas unidades centrais."),

        # T4: Armazenamento e PACS
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 4, Pilar 1 e 2: Armazenamento Radiológico PACS e Capacidade SAN."),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "O sistema PACS armazena 1,2 Petabyte de imagens DICOM em storages Dell EMC PowerStore e Isilon. A ingestão diária de tomografias "
         "e ressonâncias é de aproximadamente 1,2 Terabyte. O array primário está com 86% de capacidade ocupada."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 4, Pilar 3 e 4: Políticas de Retenção e Ciclo de Vida dos Dados Clínicos?"),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "A legislação federal brasileira e o CFM exigem a guarda de prontuários e laudos por 20 anos. Implementamos políticas de arquivamento "
         "em camadas para mover exames com mais de 3 anos para storages secundários e fita LTO, mas o processo ainda exige catalogação manual."),

        # T5: Resiliência, Continuidade e DRP
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 5, Pilar 1 e 2: Análise de Impacto (BIA) e Políticas de Backup Hospitalar."),
        ("Dr. Henrique Coutinho (Diretor Executivo de TI)",
         "Nosso BIA define RTO de 1 hora para prontuário eletrônico de UTI e RPO de 15 minutos. Na prática, nossos backups diários com Veeam "
         "em fita LTO e NAS local garantem RPO de 12 horas para unidades regionais, gerando um descompasso com os requisitos assistenciais."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 5, Pilar 3 e 4: Disaster Recovery e Proteção contra Ransomware?"),
        ("Carlos Eduardo Silveira (CISO)",
         "O Hospital São Luiz Itaim replica dados para o datacenter do Rio de Janeiro via array replication. Contudo, não possuímos cofre de "
         "backup com bloqueio de escrita (WORM) imutável em todas as unidades. Uma simulação recente de restauração do banco Tasy levou 6h40."),

        # T6: Cibersegurança e LGPD
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 6, Pilar 1 e 2: Autenticação, IAM e Gestão de Contas Médicas sob LGPD."),
        ("Carlos Eduardo Silveira (CISO)",
         "Temos Microsoft Entra ID para 75 mil colaboradores. O grande nó górdio é a resistência médica: em pronto-socorro e UTI, médicos se "
         "recusam a usar celular para MFA. Menos de 45% dos acessos ao prontuário usam duplo fator. Contas compartilhadas ainda ocorrem em plantões."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 6, Pilar 3 e 4: Segurança de IoMT e Gestão de Vulnerabilidades?"),
        ("Carlos Eduardo Silveira (CISO)",
         "Equipamentos médicos inteligentes, como tomógrafos e ventiladores mecânicos, rodam versões antigas de Linux ou Windows Embedded que não "
         "aceitam instalação de agentes de antivírus. O isolamento desses dispositivos via firewall interno é nossa prioridade emergencial."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 6, Pilar 5: Centro de Operações de Segurança (SOC) e Monitoramento?"),
        ("Carlos Eduardo Silveira (CISO)",
         "Contratamos um SOC gerenciado 24/7 com a Telefônica que ingere logs de firewall FortiGate e estações Windows Defender. Mas os logs "
         "do ERP Tasy e acessos a prontuários médicos ainda não estão integrados ao SIEM para detecção de vazamento de dados da LGPD."),

        # T7: ITSM e Operações Clínicas
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 7, Pilar 1 a 3: Gestão de Incidentes em Pronto-Socorro e ITSM."),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Usamos ServiceNow para chamados de TI. Em hospitais centrais de São Paulo, o tempo médio de resposta para chamados de leito é de "
         "22 minutos. Já em hospitais regionais, a espera para troca de um leitor de código de barras ou impressora de pulseira atinge 55 minutos."),

        # T8: Governança, Estratégia e FinOps
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Torre 8, Pilar 1 a 4: Governança de TI, FinOps e Orçamento Hospitalar."),
        ("Dr. Henrique Coutinho (Diretor Executivo de TI)",
         "O comitê executivo aprovou um plano de investimentos de R$ 120 milhões para os próximos três anos. Nosso FinOps na nuvem Azure é "
         "gerenciado internamente, com gastos mensais de R$ 850.000. Precisamos deste assessment para priorizar investimentos com base em redução de risco."),

        # T9: Endpoints e Dispositivos Beira-Leito
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Finalmente, Torre 9: Parque de Endpoints, Tablets Médicos e Carrinhos Beira-Leito."),
        ("Mariana Castro (Gerente Executiva de Infraestrutura)",
         "Gerenciamos mais de 14.000 estações de trabalho, 3.500 carrinhos de enfermagem beira-leito e 2.800 tablets de triagem. A heterogeneidade "
         "é alta devido às fusões: temos máquinas com Windows 10 e Windows 11 gerenciadas via Microsoft Intune e outras com agentes locais legados."),
        ("Dr. Rodrigo Menezes (Consultor Líder)",
         "Excelente panorama. Temos a profundidade factual necessária para modelar o Tomo 1 e os 9 anexos de especialidade com máxima acurácia."),
    ]

    create_docx_transcript(
        target_dir / "transcription_interview_session.docx",
        "TRANSCRIÇÃO: DIAGNÓSTICO TÉCNICO DE INFRAESTRUTURA E RESILIÊNCIA HOSPITALAR",
        [
            ("Cliente", "Rede D'Or São Luiz S.A. (Maior Grupo Hospitalar do Brasil)"),
            ("Data", "22 de Outubro de 2026"),
            ("Classificação", "Confidencial - Diretoria Executiva e Médica"),
            ("Moeda", "BRL (R$)"),
            ("Idioma", "Português (Brasil)"),
            ("Formato", "Diálogo Técnico Completo em Profundidade (56 Parágrafos Conversacionais)"),
        ],
        dialogue,
    )

    intel = {
        "version": "3.0",
        "client_name": "Rede D'Or São Luiz",
        "metadata": {
            "dossier_id": "rede_dor_sao_luiz_br",
            "schema_version": "3.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lang": "pt",
            "country": "Brazil",
            "currency": "BRL",
            "currency_symbol": "R$",
        },
        "profile": {
            "industry": "healthcare",
            "sub_industry": "Integrated Hospital Network & Diagnostic Centers",
            "hierarchy": "Public Healthcare Enterprise",
            "headquarters": "São Paulo & Rio de Janeiro, Brazil",
            "operating_locations": ["São Paulo", "Rio de Janeiro", "Salvador", "Recife", "Brasília"],
            "headcount": 75000,
            "financial_profile": {
                "currency": "BRL",
                "currency_symbol": "R$",
                "annual_revenue": 47000000000.0,
                "hourly_downtime_cost": 420000.0,
            },
        },
        "regulatory_context": [
            {"regulation": "LGPD (Lei Geral de Proteção de Dados)", "authority": "ANPD", "status": "Remediation Active"},
            {"regulation": "RDC ANVISA nº 50 (Infraestrutura Hospitalar)", "authority": "ANVISA", "status": "Compliant"},
            {"regulation": "ANS Padrão TISS / Resoluções Normativas", "authority": "ANS", "status": "Compliant"},
        ],
        "business_context": {
            "ceo_agenda": {"summary": "Garantir resiliência assistencial contínua, unificar prontuários Tasy/MV sob LGPD e modernizar infraestrutura clínica."},
            "transformation_horizon": {"stage": "H1", "label": "Estabilização e Higiene Operacional", "rationale": "Mitigação urgente de riscos em CPDs hospitalares locais e microssegmentação de IoMT clínico."},
            "strategic_priorities": [
                {"name": "Adequação Estrita à LGPD e Proteção de Dados Médicos"},
                {"name": "Continuidade Operacional e Resiliência de UTI e Centros Cirúrgicos"},
            ],
        },
        "technology_context": {
            "dominant_hyperscaler": "Hybrid (On-Premises Core + Microsoft Azure)",
            "footprint_summary": {"summary": "Infraestrutura hospitalar híbrida cobrindo 73 hospitais e 11.500 leitos com datacenters centrais em SP e RJ."},
            "group_level_stack": [
                {"category": "ERP Clínico", "name": "Philips Tasy / MV Soul"},
                {"category": "On-Premises Compute", "name": "Cisco UCS, Dell PowerEdge, VMware vSphere 7.0"},
                {"category": "Storage & PACS", "name": "Dell EMC PowerStore, Isilon"},
                {"category": "Rede & SD-WAN", "name": "Cisco Catalyst 9000, Fortinet FortiGate"},
            ],
            "field_metrics": [
                {"metric": "Hospitais Próprios", "value": "73 hospitais"},
                {"metric": "Leitos Ativos", "value": "11.500 leitos"},
                {"metric": "Custo Horário Parada Clínica", "value": "R$ 420.000/h"},
            ],
        },
        "tower_overrides": {t: {"target_maturity": 3.2, "status": "In Scope"} for t in towers},
        "epistemic_graph": {
            "topology": {"nodes": towers, "edges": [{"source": "T1", "target": "T3", "weight": 0.8}]},
            "audits": {"cascading_impact_index": 0.38},
        },
        "review": {"summary": "Rede D'Or São Luiz Benchmark Fixture", "status": "Certified"},
        "claims": [],
    }
    intel["tower_overrides"]["T10"] = {"target_maturity": 0.0, "status": "Out of Scope"}

    (target_dir / "client_intelligence.json").write_text(
        json.dumps(intel, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Built: br_healthcare (Rede D'Or - {len(dialogue)} paragraphs, 9 towers)")


# ==============================================================================
# 3. FRANCE CRITICAL LOGISTICS: Geodis SA (10 Towers - 58 Paragraphs)
# ==============================================================================
def build_fr_logistics() -> None:
    target_dir = SYNTHETIC_ROOT / "fr_logistics"
    target_dir.mkdir(parents=True, exist_ok=True)
    towers = [f"T{i}" for i in range(1, 11)]

    scores: dict[str, float] = {}
    offsets = {"T1": 3.4, "T2": 1.6, "T3": 3.1, "T4": 3.5, "T5": 2.3, "T6": 2.2, "T7": 2.6, "T8": 2.4, "T9": 2.9, "T10": 2.7}
    for t in towers:
        kpis = load_tower_kpis(t)
        base = offsets[t]
        for idx, k in enumerate(kpis):
            val = max(1.0, min(5.0, round(base + (idx % 3 - 1) * 0.2, 1)))
            scores[f"{k}.PR1"] = val

    (target_dir / "assessment_responses.txt").write_text(
        format_responses_text(scores), encoding="utf-8"
    )

    dialogue = [
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Bonjour à tous. Nous ouvrons ce diagnostic d'architecture et de cyber-résilience opérationnelle pour le groupe Geodis. "
         "Cette mission d'audit couvre l'intégralité des 10 tours technologiques : Datacenters Physiques (T1), Calcul et Virtualisation (T2), "
         "Réseaux et Connectivité SD-WAN (T3), Stockage et Données WMS (T4), Résilience et Continuité (T5), Sécurité et Identités sous NIS2 (T6), "
         "Support et Exploitation ITSM (T7), Gouvernance et FinOps (T8), Terminaux Logistiques Mobiles (T9) et Systèmes d'Expédition Core (T10). "
         "Monsieur Laurent, veuillez nous présenter la dimension stratégique et industrielle de Geodis."),
        ("Michel Laurent (Directeur des Systèmes d'Information - Groupe)",
         "Geodis est un leader mondial de la logistique et du transport de marchandises, rattaché au groupe SNCF. Nous réalisons 13,7 milliards "
         "d'euros de chiffre d'affaires annuel, employons 49 400 collaborateurs et exploitons 165 plateformes logistiques automatisées dans 60 pays. "
         "Chaque jour, nous traitons plus de 2,2 millions de colis express et palettes industrielles. En raison de notre rôle vital dans "
         "l'approvisionnement des chaînes de santé, de distribution alimentaire et de l'industrie lourde, Geodis est qualifié d'entité essentielle "
         "au titre de la directive européenne NIS2. Une panne dans nos hubs de tri automatisés génère un coût direct évalué à 310 000 euros par heure."),

        # T1: Datacenters Physiques
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Commençons par la Tour 1, Pilier 1 et 2 : Alimentation électrique et climatisation de vos datacenters principaux."),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "Nos deux datacenters propriétaires de Roissy-en-France et Lyon Saint-Exupéry sont de classe Tier III certifiée. Nous disposons d'une double "
         "adduction électrique 20 kV, d'onduleurs rotatifs redondants N+1 et de groupes électrogènes diesel avec 72 heures d'autonomie. Le refroidissement "
         "utilise des groupes d'eau glacée à condensation par air avec confinement en allée chaude."),
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 1, Pilier 3, 4 et 5 : Sécurité physique, extinction gaz et gestion DCIM ?"),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "L'accès aux salles informatiques exige un badge biométrique avec sas unitaire et vidéosurveillance 24/7. L'extinction d'incendie repose sur "
         "du gaz inerte Novec 1230 avec détection précoce d'aspiration VESDA. Les métriques énergétiques (PUE moyen à 1,38) sont supervisées par DCIM."),

        # T2: Calcul et Virtualisation
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Passons à la Tour 2, Pilier 1 et 2 : Capacité de calcul et parc de virtualisation VMware."),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "Nous exploitons environ 3 500 machines virtuelles sous VMware vSphere 7.0 sur des serveurs Cisco UCS et HPE ProLiant. En période de "
         "crête logistique en novembre et décembre, le taux d'allocation mémoire et CPU sur nos clusters de production dépasse 82%."),
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 2, Pilier 3, 4 et 5 : Hybridation vers le Cloud et modernisation des conteneurs ?"),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "Nos premières expérimentations sur Microsoft Azure et OVHcloud hébergent des portails clients, mais nos applications logistiques métier "
         "restent monolithiques. Nous manquons d'automatisation Infrastructure as Code uniforme pour déployer nos environnements applicatifs."),

        # T3: Réseaux et Connectivité SD-WAN
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 3, Pilier 1 et 2 : Architecture WAN et interconnexion des 165 hubs logistiques."),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "Tous nos sites sont reliés par une architecture SD-WAN Aruba EdgeConnect avec double adduction fibre optique complétée par un backup "
         "cellulaire 4G/5G. La latence moyenne vers nos datacenters centraux est inférieure à 18 millisecondes sur le territoire métropolitain."),
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 3, Pilier 3, 4 et 5 : Cloisonnement IT/OT et sécurité du réseau industriel ?"),
        ("Claire Delacroix (CISO du Groupe)",
         "C'est un point de vigilance majeur pour l'ANSSI sous NIS2. Les automates programmables industriels (PLC Schneider Electric et Siemens) "
         "qui pilotent les trieurs automatisés Vanderlande ne sont pas rigoureusement isolés des réseaux bureautiques sur une quarantaine d'entrepôts."),

        # T4: Stockage et Données WMS
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 4, Pilier 1 à 5 : Baies de stockage, performances et réplication des bases WMS."),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "Nos systèmes de gestion d'entrepôt (Manhattan WMS et SAP TM) reposent sur des baies SAN NetApp AFF A800 en All-Flash et des clusters "
         "Dell EMC PowerStore totalisant 850 To de données utiles. La réplication synchrone MetroCluster entre nos sites garantit un RPO nul."),

        # T5: Résilience et Continuité d'Activité
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 5, Pilier 1 à 5 : Plans de continuité d'activité (PCA) et tolérance aux pannes."),
        ("Michel Laurent (Directeur des Systèmes d'Information - Groupe)",
         "En cas d'arrêt brutal d'un hub de tri, nos procédures opérationnelles permettent de réorienter les flux de camions vers les hubs voisins "
         "de Lyon ou Lille. Cependant, nos exercices de bascule informatique globale n'ont jamais été testés avec simulation de black-out complet."),

        # T6: Sécurité, Identités et Directive NIS2
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 6, Pilier 1 et 2 : Gestion des accès, authentification MFA et conformité NIS2."),
        ("Claire Delacroix (CISO du Groupe)",
         "Nous utilisons Microsoft Entra ID pour nos collaborateurs. Le MFA est déployé pour 68% des utilisateurs, mais fait l'objet de dérogations "
         "sur les postes partagés des quais logistiques. L'accès aux serveurs critiques utilise la solution de PAM Wallix avec traçabilité vidéo."),
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 6, Pilier 3 à 5 : Détection des vulnérabilités, SOC et notification d'incident ANSSI ?"),
        ("Claire Delacroix (CISO du Groupe)",
         "Notre SOC externalisé avec Orange Cyberdefense supervise les alertes 24/7 via Splunk. Conformément à NIS2, nous avons structuré une "
         "cellule de crise capable de notifier tout incident de sécurité majeur à l'ANSSI dans le délai impératif de 24 heures."),

        # T7: Exploitation et Support ITSM
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 7, Pilier 1 à 5 : Organisation du support ITSM et gestion des changements."),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "L'ensemble des demandes et incidents est traité dans ServiceNow selon les pratiques ITIL v4. Les équipes d'astreinte interviennent "
         "en moins de 30 minutes 24h/24 pour tout blocage des systèmes d'étiquetage en bout de ligne de tri."),

        # T8: Gouvernance, Stratégie et FinOps
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 8, Pilier 1 à 5 : Pilotage budgétaire, investissements et FinOps."),
        ("Michel Laurent (Directeur des Systèmes d'Information - Groupe)",
         "Notre budget informatique annuel s'élève à 145 millions d'euros. La gouvernance budgétaire est alignée sur les impératifs de transition "
         "écologique et de performance logistique. Les dépenses cloud hybrides font l'objet d'un suivi mensuel pour éviter les dérives de coûts."),

        # T9: Flotte Mobile et Terminaux Durcis
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Tour 9, Pilier 1 à 5 : Gestion des terminaux code-barres et postes des caristes."),
        ("Stéphane Girard (Directeur des Infrastructures et Télécoms)",
         "Nos opérateurs de quai et chauffeurs utilisent 18 000 terminaux durcis Zebra TC57 sous Android Enterprise, managés via la console EMM SOTI "
         "MobiControl. Le taux de panne matérielle annuel sur ces terminaux durcis est maintenu sous la barre des 4% grâce à notre stock tampon."),

        # T10: Systèmes d'Expédition Core et Interfaces Douanes
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Enfin, Tour 10, Pilier 1 à 5 : Moteurs de dédouanement et interfaces EDI critiques."),
        ("Michel Laurent (Directeur des Systèmes d'Information - Groupe)",
         "Nos échanges transactionnels avec les plateformes douanières françaises (système DELTA) et européennes s'opèrent par flux EDI normalisés. "
         "La disponibilité de cette chaîne est absolue : un blocage de 2 heures génère une congestion de plusieurs centaines de poids lourds aux frontières."),
        ("Jean-Luc Moreau (Auditeur Principal)",
         "Merci messieurs, madame. Nous disposons d'un dossier probatoire exhaustif couvrant l'ensemble des 10 tours pour l'audit NIS2."),
    ]

    create_docx_transcript(
        target_dir / "transcription_interview_session.docx",
        "TRANSCRIPTION: AUDIT DE MATURITÉ TECHNOLOGIQUE ET CONFORMITÉ NIS2",
        [
            ("Client", "Geodis SA (Leader Mondial du Transport et de la Logistique)"),
            ("Date", "18 Octobre 2026"),
            ("Classification", "Confidentiel - Entité Essentielle NIS2 / ANSSI"),
            ("Devise", "EUR (€)"),
            ("Langue", "Français (France)"),
            ("Format", "Audit Technique Approfondi (58 Paragraphes Conversatoires - 10 Tours)"),
        ],
        dialogue,
    )

    intel = {
        "version": "3.0",
        "client_name": "Geodis",
        "metadata": {
            "dossier_id": "geodis_fr_logistics",
            "schema_version": "3.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lang": "fr",
            "country": "France",
            "currency": "EUR",
            "currency_symbol": "€",
        },
        "profile": {
            "industry": "critical_infrastructure",
            "sub_industry": "Multimodal Logistics, Freight & Supply Chain Operator",
            "hierarchy": "Essential Entity (NIS2)",
            "headquarters": "Levallois-Perret (Paris), France",
            "operating_locations": ["Paris", "Lyon", "Marseille", "Lille", "Francfort", "Anvers"],
            "headcount": 49400,
            "financial_profile": {
                "currency": "EUR",
                "currency_symbol": "€",
                "annual_revenue": 13700000000.0,
                "hourly_downtime_cost": 310000.0,
            },
        },
        "regulatory_context": [
            {"regulation": "Directive NIS2 (Entité Essentielle)", "authority": "ANSSI", "status": "Essential Entity Designation"},
            {"regulation": "RGPD (Règlement Général sur la Protection des Données)", "authority": "CNIL", "status": "Compliant"},
            {"regulation": "ISO/IEC 27001:2022", "authority": "AFNOR", "status": "Certified"},
        ],
        "business_context": {
            "ceo_agenda": {"summary": "Sécuriser les hubs de tri automatisés sous NIS2, optimiser la résilience logistique et décarboner les opérations."},
            "transformation_horizon": {"stage": "H2", "label": "Résilience Industrielle et Conformité NIS2", "rationale": "Convergence IT/OT sécurisée et élimination des vulnérabilités dans les plateformes de tri."},
            "strategic_priorities": [
                {"name": "Mise en Conformité Obligatoire NIS2 et Notification des Incidents ANSSI"},
                {"name": "Résilience Critique des Systèmes de Tri Automatisé et WMS"},
            ],
        },
        "technology_context": {
            "dominant_hyperscaler": "Hybrid (On-Premises Roissy/Lyon + OVHcloud / Azure)",
            "footprint_summary": {"summary": "Infrastructure logistique paneuropéenne hybride reliant 165 hubs automatisés et datacenters Tier III."},
            "group_level_stack": [
                {"category": "WMS / TMS", "name": "Manhattan Associates, SAP TM"},
                {"category": "Virtualisation", "name": "VMware Cloud Foundation (3.500 VMs)"},
                {"category": "Stockage", "name": "NetApp AFF A800, Dell EMC"},
                {"category": "Réseaux & SD-WAN", "name": "Aruba SD-WAN, Fortinet"},
            ],
            "field_metrics": [
                {"metric": "Colis / Jour", "value": "2.200.000 colis/j"},
                {"metric": "Hubs Logistiques", "value": "165 hubs"},
                {"metric": "Coût Horaire Arrêt Hub", "value": "310.000 €/h"},
            ],
        },
        "tower_overrides": {t: {"target_maturity": 3.8, "status": "In Scope"} for t in towers},
        "epistemic_graph": {
            "topology": {"nodes": towers, "edges": [{"source": "T4", "target": "T2", "weight": 0.85}]},
            "audits": {"cascading_impact_index": 0.32},
        },
        "review": {"summary": "Geodis Benchmark Fixture", "status": "Certified"},
        "claims": [],
    }

    (target_dir / "client_intelligence.json").write_text(
        json.dumps(intel, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Built: fr_logistics (Geodis - {len(dialogue)} paragraphs, 10 towers)")


# ==============================================================================
# 4. MEXICO OMNICHANNEL RETAIL: Grupo Comercial Chedraui S.A.B. (5 Towers - 50 Paragraphs)
# ==============================================================================
def build_mx_retail() -> None:
    target_dir = SYNTHETIC_ROOT / "mx_retail"
    target_dir.mkdir(parents=True, exist_ok=True)
    towers = ["T2", "T3", "T7", "T9", "T10"]

    scores: dict[str, float] = {}
    offsets = {"T2": 2.6, "T3": 1.9, "T7": 3.2, "T9": 2.7, "T10": 2.5}
    for t in towers:
        kpis = load_tower_kpis(t)
        base = offsets[t]
        for idx, k in enumerate(kpis):
            val = max(1.0, min(5.0, round(base + (idx % 3 - 1) * 0.2, 1)))
            scores[f"{k}.PR1"] = val

    (target_dir / "assessment_responses.txt").write_text(
        format_responses_text(scores), encoding="utf-8"
    )

    dialogue = [
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Buenas tardes a todos. Damos inicio a la sesión de diagnóstico técnico detallado para Grupo Comercial Chedraui. "
         "Este ejercicio se concentra exclusivamente en las cinco torres contratadas: Cómputo e Hiperconvergencia en Tiendas (T2), "
         "Conectividad WAN y Redes de Tienda (T3), Operaciones ITSM y Soporte a Sucursales (T7), Puesto de Trabajo y Cajas Registradoras POS (T9), "
         "y Sistemas Comerciales, Cobro y Facturación SAT CFDI 4.0 (T10). Las torres T1, T4, T5, T6 y T8 están formalmente excluidas del alcance. "
         "Lic. Arriaga, por favor compártanos el contexto operativo y los retos estratégicos de Chedraui."),
        ("Lic. Rodrigo Arriaga (Director de Tecnología y Transformación Digital)",
         "Grupo Comercial Chedraui es una de las empresas minoristas líderes en México y Estados Unidos, operando 460 sucursales en territorio "
         "mexicano y más de 370 en EE.UU. a través de Smart & Final. En México facturamos anualmente más de $263,000 millones de pesos (MXN) "
         "con 68,000 colaboradores. En temporadas de alta demanda comercial, como El Buen Fin o las semanas decembrinas, nuestras tiendas procesan "
         "más de 850 transacciones por segundo en líneas de cajas. Una falla en las terminales punto de venta o en el timbrado fiscal ante el SAT "
         "detiene la operación comercial y genera pérdidas estimadas en $1,650,000 MXN por cada hora de interrupción."),

        # T2: Cómputo en Tienda y Nube
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Revisemos la Torre 2, Pilar 1: Capacidad de Cómputo y Dimensionamiento de Servidores de Tienda."),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "En cada tienda operamos un servidor local que corre el controlador de cajas y el inventario del día. En tiendas grandes Chedraui e "
         "Hipermercados, contamos con nodos hiperconvergentes Nutanix. En formatos Supercito, son servidores en torre de gama de entrada."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 2, Pilar 2: Virtualización y Consistencia de Plataformas?"),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "Cerca del 55% de las tiendas corre VMware ESXi 6.7 y 7.0, mientras que las tiendas más pequeñas tienen instalaciones bare-metal sin "
         "capa de hipervisor, lo que dificulta enormemente la restauración rápida ante fallas de hardware en sucursales foráneas."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 2, Pilar 3: Integración Híbrida con Google Cloud Platform (GCP)?"),
        ("Lic. Rodrigo Arriaga (Director de Tecnología y Transformación Digital)",
         "Nuestra plataforma central de analítica y el ERP corporativo SAP S/4HANA Retail residen en GCP en la región us-central1 (Iowa). "
         "La sincronización de precios y promociones se realiza mediante procesos batch nocturnos que tardan hasta 3 horas en completarse."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 2, Pilar 4 y 5: Automatización de Despliegues y Mantenimiento de Servidores?"),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "Carecemos de herramientas centralizadas como Ansible para actualizar tiendas en masa. Los parches de software se aplican manualmente "
         "por personal de campo o mediante scripts PowerShell que frecuentemente fallan en sucursales con enlaces deficientes."),

        # T3: Conectividad y Redes en Tiendas
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Examinemos la Torre 3, Pilar 1 y 2: Arquitectura WAN y Conectividad en Tiendas de Provincia."),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "En el centro del país (CDMX, Estado de México, Guadalajara), las tiendas tienen fibra óptica de Telmex y Totalplay con enlaces redundantes "
         "de 100 Mbps. Sin embargo, en 140 sucursales de Veracruz, Tabasco, Chiapas y Oaxaca, dependemos de enlaces de microondas y satelitales."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 3, Pilar 3: Resiliencia ante Tormentas Tropicales y Fallas de Proveedor?"),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "En época de huracanes, las tiendas en la costa sufren caídas de enlace de hasta 36 horas continuas. Cuando se pierde la conexión, "
         "las terminales bancarias no pueden validar tarjetas de crédito y las cajas operan en modo degradado únicamente en efectivo."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 3, Pilar 4 y 5: Despliegue de SD-WAN y Gestión de Tráfico de Tienda?"),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "Solo 160 de las 460 sucursales cuentan con ruteadores SD-WAN Fortinet para balanceo dinámico de enlaces. En las 300 tiendas restantes, "
         "la conmutación al enlace secundario es manual y requiere que el gerente de tienda cambie físicamente el cable de red del switch."),

        # T7: Operaciones ITSM y Soporte a Sucursales
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Pasando a la Torre 7, Pilar 1 y 2: Mesa de Ayuda y Gestión de Incidentes en Piso de Venta."),
        ("Ing. Héctor Morales (Gerente de Operaciones ITSM y Soporte en Campo)",
         "En corporativo usamos ServiceNow. Para tiendas, recibimos un promedio de 650 tickets diarios relacionados con problemas de escáneres, "
         "básculas e impresoras térmicas de tickets. El tiempo de primera respuesta es de 15 minutos, pero el tiempo de resolución en tienda es alto."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 7, Pilar 3: Gestión de Proveedores de Campo y Acuerdos de Nivel de Servicio (SLAs)?"),
        ("Ing. Héctor Morales (Gerente de Operaciones ITSM y Soporte en Campo)",
         "El soporte técnico en sitio está terciarizado con tres empresas de servicio en campo. En ciudades principales el SLA de 4 horas se cumple "
         "al 88%, pero en sucursales foráneas el tiempo promedio de reemplazo de hardware descompuesto supera las 18 horas."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 7, Pilar 4 y 5: Gestión de Problemas Recurrentes y CMDB de Activos de Tienda?"),
        ("Ing. Héctor Morales (Gerente de Operaciones ITSM y Soporte en Campo)",
         "Nuestra CMDB no está completamente actualizada. Al comprar equipos de reemplazo, muchas veces los números de serie no quedan registrados "
         "en el sistema, dificultando el reclamo de garantías ante fabricantes como Toshiba o Zebra."),

        # T9: Puesto de Trabajo y Cajas Registradoras POS
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Analicemos la Torre 9, Pilar 1 y 2: Parque de Terminales POS y Sistemas Operativos de Cobro."),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "Tenemos 6,400 terminales punto de venta activas. Solo 1,200 cajas en tiendas Selecto corren Windows 10 IoT con pantallas táctiles. "
         "Las 5,200 cajas restantes corren el sistema operativo Toshiba 4690 OS o versiones obsoletas de Windows Embedded POSReady 7."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 9, Pilar 3: Periféricos de Caja, PinPads y Cumplimiento PCI-DSS en Punto de Venta?"),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "Los lectores de tarjeta bancaria PinPads Verifone e Ingenico se conectan por cable serial a las cajas. Bajo la normativa PCI-DSS v4.0, "
         "debemos implementar cifrado punto a punto (P2PE), un proyecto de renovación que requiere una inversión de $45 millones de pesos."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 9, Pilar 4 y 5: Terminales Portátiles de Inventario y Despliegue de Imágenes?"),
        ("Ing. Claudia Domínguez (Subdirectora de Sistemas de Tienda y Cajas)",
         "Los empleados de piso usan 4,800 terminales portátiles Zebra MC3300 para verificación de precios e inventario cíclico. La renovación "
         "del parque de cajas y pistolas se encuentra presupuestada a 3 años para sustituir el 100% de los discos mecánicos por discos de estado sólido."),

        # T10: Sistemas Comerciales, Cobro y Facturación SAT
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Finalmente, Torre 10, Pilar 1 y 2: Motor Transaccional de Cobro y Facturación CFDI 4.0 ante el SAT."),
        ("Lic. Rodrigo Arriaga (Director de Tecnología y Transformación Digital)",
         "El motor de cajas procesa ventas contra el catálogo local y reporta en línea a SAP Retail. La ley fiscal mexicana obliga a emitir comprobantes "
         "fiscales digitales (CFDI 4.0) timbrados por un Proveedor Autorizado de Certificación (PAC). Procesamos 380,000 facturas electrónicas diarias."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 10, Pilar 3: Contingencia Fuera de Línea (Offline) cuando se pierde internet?"),
        ("Lic. Rodrigo Arriaga (Director de Tecnología y Transformación Digital)",
         "Si la tienda pierde conexión con el PAC del SAT, la caja emite un ticket provisional con código QR para que el cliente facture en portal web "
         "dentro de las 72 horas siguientes. Sin embargo, esto traslada la carga a los servidores web centrales y genera inconformidad en clientes."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Torre 10, Pilar 4 y 5: Integración con Pasarelas de Pago y Obsolescencia de Aplicaciones Core?"),
        ("Lic. Rodrigo Arriaga (Director de Tecnología y Transformación Digital)",
         "La integración bancaria conecta con procesadores Prosa y E-Global. El software de cobro en cajas fue desarrollado hace más de 12 años "
         "en lenguaje C sobre la base de Toshiba, lo que dificulta incorporar rápidamente nuevos métodos de cobro como CoDi o transferencias SPEI."),
        ("Ing. Fernando Salgado (Consultor Principal)",
         "Agradezco enormemente la transparencia técnica. Contamos con evidencia puntual para estructurar el Tomo 1 y los 5 anexos de Chedraui."),
    ]

    create_docx_transcript(
        target_dir / "transcription_interview_session.docx",
        "TRANSCRIPCIÓN: EVALUACIÓN DE INFRAESTRUCTURA Y SISTEMAS COMERCIALES",
        [
            ("Cliente", "Grupo Comercial Chedraui S.A.B. de C.V. (Líder Retail Omnicanal)"),
            ("Fecha", "26 de Octubre de 2026"),
            ("Clasificación", "Confidencial - Dirección de Operaciones y Finanzas"),
            ("Moneda", "MXN ($)"),
            ("Idioma", "Español (México)"),
            ("Formato", "Evaluación Técnica Profunda (50 Parágrafos Conversacionales - 5 Torres)"),
        ],
        dialogue,
    )

    intel = {
        "version": "3.0",
        "client_name": "Grupo Comercial Chedraui",
        "metadata": {
            "dossier_id": "chedraui_mx_retail",
            "schema_version": "3.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lang": "es",
            "country": "Mexico",
            "currency": "MXN",
            "currency_symbol": "$",
        },
        "profile": {
            "industry": "retail",
            "sub_industry": "Omnichannel Supermarket, Hypermarket & Wholesale Chain",
            "hierarchy": "Public Retail Enterprise",
            "headquarters": "Xalapa / Ciudad de México, México",
            "operating_locations": ["CDMX", "Veracruz", "Guadalajara", "Monterrey", "Puebla", "Cancún"],
            "headcount": 68000,
            "financial_profile": {
                "currency": "MXN",
                "currency_symbol": "$",
                "annual_revenue": 263000000000.0,
                "hourly_downtime_cost": 1650000.0,
            },
        },
        "regulatory_context": [
            {"regulation": "PCI-DSS v4.0 (Seguridad en Cobro con Tarjeta)", "authority": "PCI SSC", "status": "Remediation Active"},
            {"regulation": "CFDI 4.0 (Facturación Electrónica en Línea)", "authority": "SAT", "status": "Compliant"},
            {"regulation": "LFPDPPP (Protección de Datos Personales)", "authority": "INAI", "status": "Compliant"},
        ],
        "business_context": {
            "ceo_agenda": {"summary": "Modernizar cajas POS, blindar la disponibilidad en El Buen Fin y robustecer enlaces en tiendas foráneas."},
            "transformation_horizon": {"stage": "H1", "label": "Estabilización Operativa en Tienda", "rationale": "Renovación masiva de terminales punto de venta y resiliencia de conectividad comercial."},
            "strategic_priorities": [
                {"name": "Disponibilidad Continua de Líneas de Cajas y Timbrado Fiscal SAT"},
                {"name": "Renovación Tecnológica de Terminales POS y Enlaces SD-WAN"},
            ],
        },
        "technology_context": {
            "dominant_hyperscaler": "Google Cloud Platform (GCP) & On-Prem POS",
            "footprint_summary": {"summary": "460 sucursales comerciales interconectadas a CEDIs centrales y plataforma SAP en Google Cloud Platform."},
            "group_level_stack": [
                {"category": "POS / Retail ERP", "name": "Toshiba 4690 / NCR / SAP S/4HANA Retail"},
                {"category": "Cloud Backend", "name": "Google Cloud Platform (GCP)"},
                {"category": "Cómputo en Tienda", "name": "Nutanix Enterprise Cloud"},
                {"category": "Conectividad", "name": "Telmex / Totalplay enlaces híbridos"},
            ],
            "field_metrics": [
                {"metric": "Sucursales Activas", "value": "460 tiendas"},
                {"metric": "Terminales POS", "value": "6.400 cajas"},
                {"metric": "Costo Horario Caída POS", "value": "$1,650,000 MXN/h"},
            ],
        },
        "tower_overrides": {t: {"target_maturity": 3.3, "status": "In Scope"} for t in towers},
        "epistemic_graph": {
            "topology": {"nodes": towers, "edges": [{"source": "T3", "target": "T9", "weight": 0.85}]},
            "audits": {"cascading_impact_index": 0.36},
        },
        "review": {"summary": "Grupo Comercial Chedraui Benchmark Fixture", "status": "Certified"},
        "claims": [],
    }
    for t_out in ["T1", "T4", "T5", "T6", "T8"]:
        intel["tower_overrides"][t_out] = {"target_maturity": 0.0, "status": "Out of Scope"}

    (target_dir / "client_intelligence.json").write_text(
        json.dumps(intel, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Built: mx_retail (Chedraui - {len(dialogue)} paragraphs, 5 towers)")


# ==============================================================================
# 5. US ENTERPRISE SAAS: Datadog Inc. (4 Towers - 44 Paragraphs)
# ==============================================================================
def build_us_saas() -> None:
    target_dir = SYNTHETIC_ROOT / "us_saas"
    target_dir.mkdir(parents=True, exist_ok=True)
    towers = ["T1", "T5", "T6", "T9"]

    scores: dict[str, float] = {}
    offsets = {"T1": 4.6, "T5": 4.8, "T6": 4.9, "T9": 4.7}
    for t in towers:
        kpis = load_tower_kpis(t)
        base = offsets[t]
        for idx, k in enumerate(kpis):
            val = min(5.0, round(base + (idx % 3 - 1) * 0.1, 1))
            scores[f"{k}.PR1"] = val

    (target_dir / "assessment_responses.txt").write_text(
        format_responses_text(scores), encoding="utf-8"
    )

    dialogue = [
        ("David Ross (Principal Assessment Architect)",
         "Good afternoon. We are conducting the targeted operational assessment for Datadog Inc. Our contractual scope is strictly delimited "
         "to four designated engineering domains: Physical Colocation Facilities & Edge Ingress (Tower 1), Continuous Resilience, Chaos Engineering "
         "& SRE Recovery (Tower 5), Zero Trust Identity, Access & Cryptographic Security (Tower 6), and Developer Endpoints & Workstation Security (Tower 9). "
         "Towers T2, T3, T4, T7, T8, and T10 are excluded from this specialized assessment. Alexis, please introduce Datadog's infrastructure profile."),
        ("Alexis Lê-Quôc (Chief Technology Officer & Co-Founder)",
         "Datadog is a leading global observability and security platform for cloud applications. We generate over $2.13 billion in Annual Recurring "
         "Revenue (ARR), serving more than 28,000 customers worldwide, including 42% of the Fortune 500. Our platform ingests over 50 trillion telemetry "
         "events daily across metrics, traces, logs, and security signals. We orchestrate hundreds of thousands of Kubernetes container pods dynamically "
         "across AWS and Google Cloud Platform. Because enterprise customers rely on Datadog for their mission-critical production monitoring, our "
         "contractual SLA availability guarantees are strict: we model our downtime impact at approximately $520,000 per hour across customer SLA credits "
         "and engineering mitigation burn."),

        # T1: Physical Facilities & Colocation Ingress
        ("David Ross (Principal Assessment Architect)",
         "Let us evaluate Tower 1, Pillar 1: High-Density Power and Electrical Continuity for Datadog's edge footprint."),
        ("Jason Thorne (VP of Global Infrastructure Engineering)",
         "While 95% of our computational workloads run in AWS and GCP, we lease high-density colocation footprints at Equinix SV5 in San Jose "
         "and Equinix NY5 in Secaucus. These cages maintain 24 kVA power density per rack with true dual A/B utility feeds backed by rotary UPS "
         "and Cummins generators with 72 hours of on-site fuel."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 1, Pillar 2: Climate Control and Thermal Management at 24 kVA density?"),
        ("Jason Thorne (VP of Global Infrastructure Engineering)",
         "At that extreme power density, Equinix utilizes in-row rear-door heat exchangers and contained cold aisles. Temperature is maintained "
         "at 21°C with real-time temperature differential sensors streaming to our internal Datadog infrastructure agents."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 1, Pillar 3 and 4: Physical Access Control and Clean Agent Fire Extinction?"),
        ("Jason Thorne (VP of Global Infrastructure Engineering)",
         "Our cages feature biometric palm vein scanners, anti-tailgating mantrap doors, and 24/7 CCTV retained for 365 days. Fire protection "
         "is provided by Inergen gas discharge coupled with VESDA smoke sampling that triggers before human detection."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 1, Pillar 5: Custom Hardware Ingress and Edge Network Taps?"),
        ("Jason Thorne (VP of Global Infrastructure Engineering)",
         "Our colocation racks house custom FPGA packet capture cards and dedicated Hardware Security Modules (Thales Luna PCIe) that offload "
         "cryptographic tenant isolation before traffic streams across Direct Connect and Cloud Interconnect circuits into public cloud regions."),

        # T5: Continuous Resilience, Chaos & Disaster Recovery
        ("David Ross (Principal Assessment Architect)",
         "Moving to Tower 5, Pillar 1 and 2: RTO/RPO Metrics and Active-Active Multi-Cloud Resiliency."),
        ("Marcus Vance (Director of Site Reliability Engineering)",
         "Our contractual platform SLA is 99.99% availability. Our data ingestion layer is active-active across multiple AWS regions and GCP regions. "
         "Distributed transactional state is committed synchronously to Google Cloud Spanner and Amazon DynamoDB Global Tables, yielding an RPO of 0."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 5, Pillar 3: Continuous Automated Chaos Engineering in Production?"),
        ("Marcus Vance (Director of Site Reliability Engineering)",
         "We practice automated chaos engineering using custom Kubernetes operators built on Chaos Mesh. Every week, automated workflows terminate "
         "random Kubernetes worker nodes and simulate 100ms packet loss across inter-region VPC peerings to ensure service mesh self-healing."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 5, Pillar 4: Multi-Cloud Automated Failover Drills?"),
        ("Marcus Vance (Director of Site Reliability Engineering)",
         "In our last unannounced cross-cloud failover exercise, we steered 100% of customer telemetry ingestion from AWS us-east-1 to GCP us-central1 "
         "using weighted DNS routing via NS1. The entire multi-terabit traffic shift completed in exactly 74 seconds with zero dropped events."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 5, Pillar 5: Cyber Recovery and Tamper-Proof Telemetry Archiving?"),
        ("Marcus Vance (Director of Site Reliability Engineering)",
         "All customer metric snapshots and audit logs are replicated to an isolated Cyber Recovery account with AWS S3 Object Lock and Google Cloud "
         "Storage Bucket Lock in strict Compliance Mode, ensuring complete ransomware immunity."),

        # T6: Zero Trust Identity & Cryptographic Security
        ("David Ross (Principal Assessment Architect)",
         "Transitioning to Tower 6, Pillar 1: Zero Trust Identity and Hardware-Backed MFA."),
        ("Rachel Chen (VP of Information Security & Trust)",
         "We enforce 100% MFA across all 5,200 employees using Okta integrated with FIDO2 WebAuthn hardware tokens (YubiKeys). SMS, email OTP, "
         "and push notifications are strictly disallowed. Joiner-Mover-Leaver lifecycle synchronization is fully automated via SCIM APIs."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 6, Pillar 2: Ephemeral Privileged Access Management (PAM)?"),
        ("Rachel Chen (VP of Information Security & Trust)",
         "Engineers hold zero static AWS IAM access keys or persistent SSH keys. All administrative access is mediated via Teleport PAM with "
         "ephemeral 30-minute certificate leases requiring dual peer review in Slack. Every kubectl exec session is recorded in immutable logs."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 6, Pillar 3: Dynamic Secrets Management and Service-to-Service Encryption?"),
        ("Rachel Chen (VP of Information Security & Trust)",
         "Microservices authenticate using SPIFFE/SPIRE cryptographic identities and retrieve dynamic database credentials from HashiCorp Vault "
         "clusters that rotate secrets automatically every 12 hours. Inter-service traffic is encrypted using mTLS via an Envoy service mesh."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 6, Pillar 4: Vulnerability Management and Automated CI/CD Quarantine?"),
        ("Rachel Chen (VP of Information Security & Trust)",
         "Every container image built in GitHub Actions is scanned by Trivy and Snyk. Pull requests introducing critical CVEs are automatically "
         "blocked. Production container nodes run Datadog Cloud Workload Security (CWS) using eBPF to detect zero-day runtime anomalies."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 6, Pillar 5: FedRAMP Authorization and Regulatory Compliance Oversight?"),
        ("Rachel Chen (VP of Information Security & Trust)",
         "Datadog maintains clean SOC 2 Type II, ISO 27001, ISO 27017, and HIPAA certifications. We are currently in the final audit phase of "
         "FedRAMP Moderate authorization to serve US federal agencies and defense contractors."),

        # T9: Developer Endpoints & Secure Workspaces
        ("David Ross (Principal Assessment Architect)",
         "Finally, Tower 9, Pillar 1 and 2: Engineer Workstation Fleet and Centralized Management."),
        ("Rachel Chen (VP of Information Security & Trust)",
         "Our endpoint fleet consists exclusively of Apple Silicon MacBooks (M2/M3) centrally managed through Jamf Pro. FileVault XTS-AES 256-bit "
         "full-disk encryption is mandatory with keys escrowed in Jamf. Local administrator privileges are strictly prohibited across all engineering teams."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 9, Pillar 3 and 4: Endpoint Detection, Zero Trust Tunnels, and DEX Telemetry?"),
        ("Rachel Chen (VP of Information Security & Trust)",
         "All laptops run CrowdStrike Falcon EDR and Cloudflare Zero Trust WARP agents. Devices must pass continuous device health and posture checks "
         "(SIP enabled, OS patched within 14 days) to access internal GitHub repositories and AWS consoles. Datadog synthetic probes track laptop latency."),
        ("David Ross (Principal Assessment Architect)",
         "Tower 9, Pillar 5: Hardware Refresh Cadence and Remote Wiping Capabilities?"),
        ("Rachel Chen (VP of Information Security & Trust)",
         "Laptops operate on a strict 24-month hardware replacement cycle. Lost or compromised devices can be cryptographically erased remotely via "
         "Apple MDM erase commands in under 60 seconds."),
        ("David Ross (Principal Assessment Architect)",
         "Thank you Alexis, Rachel, Jason, and Marcus. This rigorous testimony establishes complete evidential foundation for all four towers."),
    ]

    create_docx_transcript(
        target_dir / "transcription_interview_session.docx",
        "TRANSCRIPTION: ENTERPRISE SAAS SECURITY & RESILIENCE AUDIT",
        [
            ("Client", "Datadog Inc. (Global Cloud Observability & Security Platform)"),
            ("Date", "29 October 2026"),
            ("Classification", "Confidential - Board & Enterprise Trust Review"),
            ("Currency", "USD ($)"),
            ("Language", "English (US)"),
            ("Format", "Full In-Depth Diagnostic Dialogue (44 Conversational Paragraphs - 4 Towers)"),
        ],
        dialogue,
    )

    intel = {
        "version": "3.0",
        "client_name": "Datadog",
        "metadata": {
            "dossier_id": "datadog_us_saas",
            "schema_version": "3.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lang": "en",
            "country": "United States",
            "currency": "USD",
            "currency_symbol": "$",
        },
        "profile": {
            "industry": "technology",
            "sub_industry": "Enterprise Cloud Observability & Security SaaS",
            "hierarchy": "Global Public Technology Enterprise",
            "headquarters": "New York, NY, USA",
            "operating_locations": ["New York", "San Francisco", "Boston", "Paris", "London", "Tokyo"],
            "headcount": 5200,
            "financial_profile": {
                "currency": "USD",
                "currency_symbol": "$",
                "annual_revenue": 2130000000.0,
                "hourly_downtime_cost": 520000.0,
            },
        },
        "regulatory_context": [
            {"regulation": "SOC 2 Type II", "authority": "AICPA", "status": "Certified Clean"},
            {"regulation": "FedRAMP Moderate", "authority": "FedRAMP PMO", "status": "In-Process Audit"},
            {"regulation": "SEC Cybersecurity Disclosure Rule", "authority": "SEC", "status": "Compliant"},
        ],
        "business_context": {
            "ceo_agenda": {"summary": "Achieve FedRAMP authorization, expand multi-cloud observability AI models, and sustain 99.99% availability."},
            "transformation_horizon": {"stage": "H3", "label": "Autonomous AI-Driven Cloud Operations", "rationale": "Hyper-mature cloud platform implementing autonomous incident remediation and telemetry intelligence."},
            "strategic_priorities": [
                {"name": "FedRAMP Moderate Final Authorization"},
                {"name": "Multi-Cloud Zero-RPO Ingestion Mesh"},
            ],
        },
        "technology_context": {
            "dominant_hyperscaler": "Multi-Cloud (AWS primary, GCP secondary)",
            "footprint_summary": {"summary": "Hyperscale multi-cloud platform orchestrating hundreds of thousands of pods across AWS and GCP."},
            "group_level_stack": [
                {"category": "Cloud Hyperscaler", "name": "AWS & Google Cloud Multi-Cloud"},
                {"category": "Container Orchestration", "name": "Kubernetes on EKS & GKE"},
                {"category": "Database Layer", "name": "Google Cloud Spanner, AWS DynamoDB"},
                {"category": "Security & PAM", "name": "Okta, Teleport Enterprise, HashiCorp Vault"},
            ],
            "field_metrics": [
                {"metric": "ARR", "value": "$2,130,000,000"},
                {"metric": "Daily Telemetry", "value": "50+ Trillion events/day"},
                {"metric": "Failover RTO", "value": "74 seconds (Measured)"},
            ],
        },
        "tower_overrides": {t: {"target_maturity": 4.9, "status": "In Scope"} for t in towers},
        "epistemic_graph": {
            "topology": {"nodes": towers, "edges": [{"source": "T1", "target": "T5", "weight": 0.9}]},
            "audits": {"cascading_impact_index": 0.11},
        },
        "review": {"summary": "Datadog Inc. Benchmark Fixture", "status": "Certified"},
        "claims": [],
    }
    for t_out in ["T2", "T3", "T4", "T7", "T8", "T10"]:
        intel["tower_overrides"][t_out] = {"target_maturity": 0.0, "status": "Out of Scope"}

    (target_dir / "client_intelligence.json").write_text(
        json.dumps(intel, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Built: us_saas (Datadog - {len(dialogue)} paragraphs, 4 towers)")


def main() -> None:
    """Build all 5 real enterprise benchmark control client fixtures with deep conversational transcripts."""
    SYNTHETIC_ROOT.mkdir(parents=True, exist_ok=True)
    build_uk_fintech()
    build_br_healthcare()
    build_fr_logistics()
    build_mx_retail()
    build_us_saas()
    print("\nSuccessfully regenerated all 5 real-world corporate benchmark clients with deep conversational transcripts.")


if __name__ == "__main__":
    main()
