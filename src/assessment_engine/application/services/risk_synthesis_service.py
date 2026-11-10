"""Application service providing deterministic fallback risk synthesis for CI and offline pipelines."""

from __future__ import annotations

from typing import Any, Dict

from assessment_engine.domain.schemas.risk_synthesis import (
    IRiskSynthesizer,
    RiskSynthesisContext,
    SynthesizedRiskItem,
)
from assessment_engine.domain.taxonomy.archetype_registry import (
    LossArchetypeType,
    get_actuarial_archetype_registry,
)
from assessment_engine.infrastructure.localization import format_currency

# Bijective Pillar-Specific Failure Patterns to guarantee 0% title cloning
PILLAR_FAILURE_PATTERNS: dict[str, dict[str, str]] = {
    # Tower 8: Strategy, Governance & FinOps
    "T8.P1": {
        "title": "Target architecture misalignment and technical debt accumulation in {tech_name}",
        "mechanism": "Uncoordinated roadmap prioritization and deferred technical debt across {tech_name} lead to architectural divergence and elevated lifecycle maintenance overhead.",
        "remediation": "Establish formal Architecture Review Board (ARB) governance and technical debt retirement milestones for {tech_name}.",
    },
    "T8.P2": {
        "title": "Portfolio demand fragmentation and delayed business value realization in {tech_name}",
        "mechanism": "Lack of disciplined capacity allocation and un-tiered decision frameworks for {tech_name} induce budget variances and prolonged initiative delivery cycles.",
        "remediation": "Implement value-driven portfolio governance and stage-gate investment prioritization for {tech_name}.",
    },
    "T8.P3": {
        "title": "Unverified regulatory control attestation and vendor concentration risk in {tech_name}",
        "mechanism": "Inadequate continuous compliance auditing and unmitigated vendor concentration on {tech_name} expose the enterprise to regulatory sanctions and single-partner bottlenecks.",
        "remediation": "Automate risk register synchronization and continuous control attestation under applicable regulatory compliance frameworks for {tech_name}.",
    },
    "T8.P4": {
        "title": "Unreserved on-demand compute drift and unallocated cloud spend leakage in {tech_name}",
        "mechanism": "Absence of tag-based cost allocation and low commitment coverage on {tech_name} lead to continuous cloud budget overruns and EBITDA margin erosion.",
        "remediation": "Enforce automated FinOps cost-allocation tags and automated Savings Plans / Reserved Instance commitments for {tech_name}.",
    },
    "T8.P5": {
        "title": "Executive KPI visibility vacuum and unmeasured ROI on technology investments in {tech_name}",
        "mechanism": "Absence of unit-economics telemetry and structured post-implementation reviews on {tech_name} obscures business value attainment and continuous improvement.",
        "remediation": "Deploy unified executive value dashboards and operational OKR tracking for {tech_name}.",
    },
    # Tower 1: Physical Data Center & Facilities
    "T1.P1": {
        "title": "UPS autonomy degradation and switchgear single point of failure in {tech_name}",
        "mechanism": "Unverified battery discharge cycles and single-cord power paths on {tech_name} eliminate electrical redundancy during utility brownouts.",
        "remediation": "Deploy dual-feed ATS distribution circuits and certified automated load-bank testing for {tech_name}.",
    },
    "T1.P2": {
        "title": "Thermal hotspot accumulation and HVAC cooling redundancy deficit in {tech_name}",
        "mechanism": "Uncontained airflow mixing and lack of N+1 precision CRAC unit maintainability in {tech_name} cause localized thermal throttling under peak server loads.",
        "remediation": "Implement aisle containment and continuous ASHRAE TC 9.9 thermal telemetry probes for {tech_name}.",
    },
    "T1.P3": {
        "title": "Whitespace physical access auditing latency and permit-to-work gaps in {tech_name}",
        "mechanism": "Unsynchronized biometric logs and manual vendor escorts in {tech_name} suites compromise physical security compliance boundaries.",
        "remediation": "Integrate two-factor biometric access controls and immutable CCTV audit logging for {tech_name}.",
    },
    "T1.P4": {
        "title": "Aspirating smoke detection delay and clean-agent discharge compliance in {tech_name}",
        "mechanism": "Deferred room integrity testing and unmonitored gaseous suppression circuits in {tech_name} risk catastrophic environmental damage.",
        "remediation": "Conduct annual room enclosure integrity certification and continuous VESDA aspirating smoke telemetry for {tech_name}.",
    },
    "T1.P5": {
        "title": "DCIM telemetry fragmentation and facility lifecycle obsolescence in {tech_name}",
        "mechanism": "Fragmented building management alarms and manual capacity planning for {tech_name} delay detection of mechanical facility degradation.",
        "remediation": "Deploy unified DCIM infrastructure monitoring and predictive maintenance lifecycle schedules for {tech_name}.",
    },
}

DOMAIN_FAILURE_PATTERNS: dict[str, dict[str, str]] = {
    "T1": {
        "title": "Electromechanical power instability and cooling threshold breach in {tech_name}",
        "mechanism": "Uncontained thermal fluctuations and UPS battery degradation within {tech_name} risk ungraceful facility brownouts. Without dual-feed power paths and automated environmental telemetry, facility disruptions trigger cascading hardware halts across dependent compute infrastructure.",
        "remediation": "Deploy redundant N+1 precision cooling units and dual ATS power distribution paths for {tech_name}, enforcing ASHRAE thermal compliance.",
    },
    "T2": {
        "title": "Hypervisor compute saturation and unreserved memory contention in {tech_name}",
        "mechanism": "Unconstrained CPU/RAM overcommitment and co-located mixed workloads on {tech_name} eliminate hypervisor failover headroom. Under sudden burst demand, hypervisor kernel contention induces host ballooning, noisy-neighbor starvation, and ungraceful workload termination.",
        "remediation": "Enforce strict resource pools, CPU/RAM reservations, and automated DRS affinity rules across {tech_name} clusters.",
    },
    "T3": {
        "title": "Network transit chokepoint and perimeter routing convergence latency in {tech_name}",
        "mechanism": "Asymmetric routing paths and buffer exhaustion on core distribution switches within {tech_name} induce packet loss under peak transaction volume. The lack of dynamic multi-path mesh routing creates single-interface failure bottlenecks.",
        "remediation": "Implement active-active ECMP multi-chassis link aggregation and BGP route dampening across core {tech_name} fabrics.",
    },
    "T4": {
        "title": "Storage array IOPS throttling and asynchronous write-cache exhaustion in {tech_name}",
        "mechanism": "Storage controller saturation and unsegmented I/O queues on {tech_name} cause write-cache de-staging delays during peak operational load, leading to storage timeouts, volume disconnects, and transactional lockups.",
        "remediation": "Provision tiered NVMe caching, isolate high-I/O volumes via dedicated storage QoS policies, and configure automated snapshot consolidation on {tech_name}.",
    },
    "T5": {
        "title": "Unverified DRP failover runbooks and recovery time expansion in {tech_name}",
        "mechanism": "Disaster recovery workflows and secondary site failover mechanisms for {tech_name} lack automated non-disruptive validation. In a disaster event, uncoordinated service dependencies and manual DNS/IP redirection drastically exceed business RTO limits.",
        "remediation": "Automate orchestrated application failover and conduct scheduled non-disruptive DR simulation drills for {tech_name} under ISO 22301 standards.",
    },
    "T6": {
        "title": "Privilege sprawl and uncontained lateral movement pathways in {tech_name}",
        "mechanism": "Overly permissive access rights, shared administrative accounts, and lack of mandatory MFA across {tech_name} enable unconstrained lateral traversal. Credential compromise of a single privileged account exposes core tenant boundaries.",
        "remediation": "Deploy Zero Trust identity segmentation, ephemeral JIT administrative access, and mandatory FIDO2 hardware MFA across all {tech_name} administrative endpoints.",
    },
    "T7": {
        "title": "ITSM incident escalation bottleneck and un-triaged alert fatigue in {tech_name}",
        "mechanism": "Unfiltered telemetry floods and manual triage workflows in {tech_name} delay detection of high-severity outages. The absence of automated event correlation and bidirectional incident handoffs prolongs Mean Time to Resolution (MTTR).",
        "remediation": "Implement AIOps event correlation and automated tier-1 triage runbooks for {tech_name}, establishing strict SLA-bound escalation matrices.",
    },
    "T8": {
        "title": "Unbudgeted licensing liability and cloud infrastructure cost drift in {tech_name}",
        "mechanism": "Unmonitored resource provisioning and unaligned commercial agreements for {tech_name} create unexpected financial liability during contractual renewals. The absence of tag-based cost allocation obscures organizational unit accountability.",
        "remediation": "Establish automated FinOps cost allocation tags, continuous reservation optimization, and license usage tracking for {tech_name}.",
    },
    "T9": {
        "title": "Unmanaged endpoint attack surface and client operating system patch drift in {tech_name}",
        "mechanism": "Fragmented device compliance and delayed endpoint security patching on {tech_name} leave client workstations vulnerable to local privilege escalation and uncontained remote malware execution.",
        "remediation": "Enforce unified endpoint management (UEM), automated patch compliance baselines, and EDR isolation policies across all {tech_name} client fleets.",
    },
    "T10": {
        "title": "Transactional lock escalation and legacy message queue latency in {tech_name}",
        "mechanism": "Monolithic database lock contention and legacy state management within {tech_name} halt transaction processing during batch reconciliation. Deadlocks and schema bottlenecks delay customer-facing processing loops.",
        "remediation": "Decouple monolithic transaction pipelines, introduce distributed event streaming buffers, and optimize database indexing schemas for {tech_name}.",
    },
}

DEFAULT_FAILURE_PATTERN: dict[str, str] = {
    "title": "State synchronization lag and failover latency across {tech_name} risking operational disruption in {pillar_name}",
    "mechanism": "Under operational stress or transit failover conditions, asynchronous state drift across {tech_name} disrupts execution within {pillar_name}, requiring manual engineering triage before service restoration.",
    "remediation": "Deploy automated health-check probes and continuous state checkpoints for {tech_name}, establishing deterministic recovery procedures.",
}


class DeterministicFallbackSynthesizer(IRiskSynthesizer):
    """Zero-network, sub-millisecond fallback risk synthesizer for CI/CD and offline execution."""

    def synthesize_risk(self, ctx: RiskSynthesisContext) -> SynthesizedRiskItem:
        """Synthesizes risk item with 100% technical English contracts and domain-native failure mechanics."""
        ctx_hash = ctx.compute_context_hash()
        tech_name = ctx.verified_tech_stack[0] if ctx.verified_tech_stack else ctx.pillar_name

        ale_str = format_currency(ctx.calibrated_ale, currency_symbol=ctx.currency_symbol, locale=ctx.doc_lang, decimals=0)
        sle_str = format_currency(ctx.total_sle, currency_symbol=ctx.currency_symbol, locale=ctx.doc_lang, decimals=0)
        stoppage_str = format_currency(ctx.stoppage_loss, currency_symbol=ctx.currency_symbol, locale=ctx.doc_lang, decimals=0)
        recovery_str = format_currency(ctx.recovery_burn, currency_symbol=ctx.currency_symbol, locale=ctx.doc_lang, decimals=0)
        penalty_str = format_currency(ctx.penalty_loss, currency_symbol=ctx.currency_symbol, locale=ctx.doc_lang, decimals=0)
        hourly_str = format_currency(ctx.hourly_rate, currency_symbol=ctx.currency_symbol, locale=ctx.doc_lang, decimals=0)

        # Lookup pillar-specific failure pattern first to prevent 100% title duplication
        tower_key = str(ctx.tower_code).upper()
        pillar_key = f"{tower_key}.{ctx.pillar_id}" if not str(ctx.pillar_id).startswith("T") else str(ctx.pillar_id)
        
        pattern = (
            PILLAR_FAILURE_PATTERNS.get(pillar_key)
            or DOMAIN_FAILURE_PATTERNS.get(tower_key)
            or DEFAULT_FAILURE_PATTERN
        )

        title = pattern["title"].format(tech_name=tech_name, pillar_name=ctx.pillar_name)
        mechanism = pattern["mechanism"].format(tech_name=tech_name, pillar_name=ctx.pillar_name)
        remediation = pattern["remediation"].format(tech_name=tech_name, pillar_name=ctx.pillar_name)

        # Actuarial justification decoupled by loss archetype
        try:
            arch_mapping = get_actuarial_archetype_registry().get_mapping_for_tower(tower_key)
            primary_arch = arch_mapping.primary_archetype
        except (KeyError, ValueError):
            primary_arch = LossArchetypeType.AVAILABILITY_OUTAGE

        if primary_arch == LossArchetypeType.CAPITAL_INEFFICIENCY:
            justification = (
                f"Under the Open FAIR taxonomy, this economic risk models an Annualized Loss Expectancy (ALE) of {ale_str}/year "
                f"with a single loss exposure benchmark of {sle_str}. "
                f"Across annual cloud infrastructure and software asset expenditures, this capital exposure decomposes into: "
                f"{stoppage_str} in direct unbudgeted on-demand compute drift; "
                f"{recovery_str} in engineering remediation labor and tagging governance overhead; and "
                f"{penalty_str} in retroactive vendor licensing true-up variances and unoptimized commitment penalties."
            )
        elif primary_arch == LossArchetypeType.PRODUCTIVITY_TOIL:
            justification = (
                f"Under the Open FAIR taxonomy, this operational toil risk models an Annualized Loss Expectancy (ALE) of {ale_str}/year. "
                f"Across aggregate workforce capacity, this cognitive friction decomposes into: "
                f"{stoppage_str} in lost productive employee hours against fully-burdened payroll rates; "
                f"{recovery_str} in tier-2/tier-3 escalation and manual ticket triage labor; and "
                f"{penalty_str} in delayed feature delivery velocity and project schedule slippage."
            )
        elif primary_arch == LossArchetypeType.REGULATORY_AND_BREACH:
            justification = (
                f"Under the Open FAIR taxonomy, this security compliance risk models an Annualized Loss Expectancy (ALE) of {ale_str}/year. "
                f"In the event of a significant security compromise, this liability decomposes into: "
                f"{stoppage_str} in potential statutory enforcement sanctions under regulatory frameworks (DORA/GDPR); "
                f"{recovery_str} in third-party forensic investigation and audit attestation costs; and "
                f"{penalty_str} in customer notification protocols and mandatory regulatory disclosures."
            )
        else:
            justification = (
                f"Under the Open FAIR taxonomy, this operational risk models an Annualized Loss Expectancy (ALE) of {ale_str}/year. "
                f"A single occurrence ({sle_str} SLE across a {ctx.downtime_minutes}-minute recovery window) decomposes into: "
                f"{stoppage_str} in direct operational stoppage against the baseline hourly burn rate of {hourly_str}/hr; "
                f"{recovery_str} in emergency SRE and engineering recovery labor; and "
                f"{penalty_str} in contractual SLA breach penalties and audit attestation overhead."
            )

        return SynthesizedRiskItem(
            risk_id=f"RSK-{ctx.kpi_id}",
            causal_risk_title=title,
            technical_failure_mechanism=mechanism,
            actuarial_justification=justification,
            remediation_architecture=remediation,
            context_hash=ctx_hash,
        )
