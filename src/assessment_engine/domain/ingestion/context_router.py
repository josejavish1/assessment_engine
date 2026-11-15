"""
Epistemic Graph Router & Tower Context Builder.

Routes evidence fragments to their legitimate MECE domain tower,
preventing cross-tower context contamination and LLM attention dilution.
"""

from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)


class EpistemicContextRouter:
    """Routes evidence fragments to their legitimate MECE domain tower."""

    # Domain-specific keyword tokens per tower (100% Technical English)
    TOWER_DOMAIN_KEYWORDS: Dict[str, Set[str]] = {
        "T1": {
            "datacenter", "data center", "cpd", "facilities", "electrical", "power", "cooling",
            "chiller", "crac", "pdu", "rack", "fire suppression", "ups", "generator",
            "transformer", "technical room",
        },
        "T2": {
            "compute", "server", "vmware", "vsphere", "hypervisor", "simplivity",
            "proxmox", "cpu", "ram", "memory", "virtualization", "vm", "vms",
            "kubernetes", "k8s", "container", "docker", "broadcom", "host", "cluster",
        },
        "T3": {
            "network", "networking", "switch", "router", "wan", "lan", "huawei",
            "equinix", "interconnect", "dark fiber", "fiber", "ipsec", "vpn",
            "dns", "dhcp", "firewall", "bgp", "vlan", "bandwidth", "10 gbps", "dci",
        },
        "T4": {
            "storage", "disk", "san", "nas", "netapp", "metrocluster", "iops",
            "throughput", "tiering", "ontap", "nvme", "flash", "cohesity", "cbt",
            "volume", "snapshot", "nfs", "iscsi", "s3",
        },
        "T5": {
            "resilience", "backup", "contingency", "failover", "dr", "disaster recovery",
            "rpo", "rto", "business continuity", "power outage", "outage",
            "recovery", "bia", "crisis",
        },
        "T6": {
            "security", "cybersecurity", "iam", "pam", "mfa", "authentication",
            "identity", "active directory", "encryption", "vulnerability", "threat",
            "soc", "siem", "edr", "ransomware", "privileged access", "nis2", "compliance",
        },
        "T7": {
            "itsm", "operations", "it operations", "zabbix", "nagstamon", "prometheus",
            "grafana", "loki", "incident", "ticket", "sla", "slo", "sli",
            "change management", "cmdb", "sre", "on-call", "support",
        },
        "T8": {
            "finops", "governance", "cost", "cloud spend", "budget", "capex", "opex",
            "licensing", "broadcom", "it governance", "steering committee", "strategy",
            "itil", "investment", "roi", "tco",
        },
        "T9": {
            "workplace", "digital workplace", "endpoint", "laptop", "desktop", "vdi",
            "windows", "office", "teams", "collaboration", "service desk",
            "helpdesk", "peripheral", "printer", "mobility",
        },
        "T10": {
            "core", "legacy", "ot", "scada", "prenet", "plant", "manufacturing",
            "scale", "weighing", "oracle", "forms", "reports", "iseries", "as400",
            "industrial", "industrial production", "dispatch",
        },
    }

    @classmethod
    def filter_context_for_tower(
        cls,
        tower_id: str,
        raw_fragments: List[str],
        max_chars: int = 25000,
    ) -> str:
        """Filters a list of text fragments so that only fragments relevant to the tower are included.

        Excludes out-of-scope fragments, preventing cross-tower context contamination.
        """
        t_id = tower_id.upper()
        keywords = cls.TOWER_DOMAIN_KEYWORDS.get(t_id, set())
        if not keywords:
            return "\n\n".join(raw_fragments)[:max_chars]

        relevant_frags = []
        general_frags = []

        for frag in raw_fragments:
            frag_lower = frag.lower()
            score = sum(1 for kw in keywords if kw in frag_lower)
            if score >= 1:
                relevant_frags.append(frag)
            elif "molins" in frag_lower and len(frag) < 400:
                # Brief corporate context
                general_frags.append(frag)

        combined = relevant_frags + general_frags[:2]
        if not combined:
            return "\n\n".join(raw_fragments[:5])[:max_chars]

        logger.info(
            "[EpistemicContextRouter] Filtered %d raw fragments down to %d domain-relevant fragments for %s",
            len(raw_fragments),
            len(combined),
            tower_id,
        )
        return "\n\n".join(combined)[:max_chars]
