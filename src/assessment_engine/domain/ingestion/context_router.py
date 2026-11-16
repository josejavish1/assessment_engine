"""
Epistemic Graph Router & Tower Context Builder.

Routes evidence fragments to their legitimate MECE domain tower,
preventing cross-tower context contamination and LLM attention dilution.
Enforces strict fail-closed boundary isolation and word-bounded token matching.
"""

from typing import Dict, List, Optional, Pattern, Set
import re
import logging

logger = logging.getLogger(__name__)


class EpistemicContextRouter:
    """Routes evidence fragments to their legitimate MECE domain tower."""

    # Universal, domain-agnostic capability keywords per tower (100% Technical English)
    TOWER_DOMAIN_KEYWORDS: Dict[str, Set[str]] = {
        "T1": {
            "datacenter", "data center", "facilities", "electrical", "power", "cooling",
            "chiller", "crac", "pdu", "rack", "fire suppression", "ups", "generator",
            "transformer", "technical room", "hvac", "environmental telemetry",
        },
        "T2": {
            "compute", "server", "hypervisor", "virtualization", "vm", "vms",
            "cpu", "ram", "memory", "kubernetes", "k8s", "container", "containers",
            "docker", "host", "cluster", "node", "infrastructure as code",
        },
        "T3": {
            "network", "networking", "switch", "switches", "router", "routers",
            "wan", "lan", "interconnect", "dark fiber", "fiber", "ipsec", "vpn",
            "dns", "dhcp", "firewall", "bgp", "vlan", "bandwidth", "telemetry link", "dci",
        },
        "T4": {
            "storage", "disk", "san", "nas", "storage array", "metrocluster", "iops",
            "throughput", "tiering", "nvme", "flash", "block storage", "object storage",
            "volume", "snapshot", "nfs", "iscsi", "s3", "data tier",
        },
        "T5": {
            "resilience", "backup", "backups", "contingency", "failover", "dr",
            "disaster recovery", "rpo", "rto", "business continuity", "power outage",
            "outage", "recovery", "bia", "crisis management", "high availability",
        },
        "T6": {
            "security", "cybersecurity", "iam", "pam", "mfa", "authentication",
            "identity", "directory services", "encryption", "vulnerability", "threat",
            "soc", "siem", "edr", "ransomware", "privileged access", "compliance", "zero trust",
        },
        "T7": {
            "itsm", "operations", "it operations", "monitoring", "observability", "telemetry",
            "alerting", "incident", "ticket", "sla", "slo", "sli", "change management",
            "cmdb", "sre", "on-call", "support desk", "service operations",
        },
        "T8": {
            "finops", "governance", "cost", "cloud spend", "budget", "capex", "opex",
            "licensing", "it governance", "steering committee", "strategy", "itil",
            "investment", "roi", "tco", "chargeback", "showback", "unit economics",
        },
        "T9": {
            "workplace", "digital workplace", "endpoint", "endpoints", "laptop", "desktop",
            "vdi", "operating system", "productivity suite", "collaboration",
            "service desk", "helpdesk", "peripheral", "printer", "mobility",
        },
        "T10": {
            "erp", "legacy", "operational technology", "scada", "plc", "modbus",
            "plant", "manufacturing", "weighbridge", "telemetry controller",
            "mainframe", "midrange", "industrial", "industrial production", "dispatch",
            "mes", "shop floor",
        },
    }

    _COMPILED_PATTERNS: Dict[str, List[Pattern[str]]] = {}

    @classmethod
    def _get_patterns_for_tower(
        cls, tower_id: str, custom_keywords: Optional[Set[str]] = None
    ) -> List[Pattern[str]]:
        """Compiles regex patterns with word boundaries to prevent substring matching defects."""
        if custom_keywords is not None:
            return [re.compile(rf"\b{re.escape(kw.lower())}\b") for kw in custom_keywords]
        if tower_id not in cls._COMPILED_PATTERNS:
            kws = cls.TOWER_DOMAIN_KEYWORDS.get(tower_id, set())
            cls._COMPILED_PATTERNS[tower_id] = [
                re.compile(rf"\b{re.escape(kw.lower())}\b") for kw in sorted(kws)
            ]
        return cls._COMPILED_PATTERNS[tower_id]

    @classmethod
    def filter_context_for_tower(
        cls,
        tower_id: str,
        raw_fragments: List[str],
        max_chars: int = 25000,
        custom_keywords: Optional[Set[str]] = None,
    ) -> str:
        """Filters a list of text fragments so that only fragments relevant to the tower are included.

        Enforces strict fail-closed MECE isolation using word-boundary lexical matching.
        """
        t_id = tower_id.upper()
        patterns = cls._get_patterns_for_tower(t_id, custom_keywords)
        if not patterns:
            logger.warning(
                "[EpistemicContextRouter] Unknown or unconfigured tower_id '%s'. Failing closed with empty context.",
                tower_id,
            )
            return ""

        relevant_frags = []

        for frag in raw_fragments:
            frag_lower = frag.lower()
            score = sum(1 for pat in patterns if pat.search(frag_lower))
            if score >= 1:
                relevant_frags.append(frag)

        if not relevant_frags:
            logger.info(
                "[EpistemicContextRouter] Zero domain-relevant fragments matched for %s. Failing closed.",
                tower_id,
            )
            return ""

        logger.info(
            "[EpistemicContextRouter] Filtered %d raw fragments down to %d domain-relevant fragments for %s",
            len(raw_fragments),
            len(relevant_frags),
            tower_id,
        )
        return "\n\n".join(relevant_frags)[:max_chars]
