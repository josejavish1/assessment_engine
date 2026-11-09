"""Application service providing deterministic fallback risk synthesis for CI and offline pipelines."""

from __future__ import annotations

from typing import Any

from assessment_engine.domain.schemas.risk_synthesis import (
    IRiskSynthesizer,
    RiskSynthesisContext,
    SynthesizedRiskItem,
)
from assessment_engine.infrastructure.localization import format_currency

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

        # Lookup domain-native failure pattern by tower code
        tower_key = str(ctx.tower_code).upper()
        pattern = DOMAIN_FAILURE_PATTERNS.get(tower_key, DEFAULT_FAILURE_PATTERN)

        title = pattern["title"].format(tech_name=tech_name, pillar_name=ctx.pillar_name)
        mechanism = pattern["mechanism"].format(tech_name=tech_name, pillar_name=ctx.pillar_name)
        remediation = pattern["remediation"].format(tech_name=tech_name, pillar_name=ctx.pillar_name)

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
