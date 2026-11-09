"""Semantic Ingestion & Epistemic Graph Routing (RFC 084 Phase 1).

Replaces legacy keyword grep and line-slicing truncation with lossless
proposition-level chunking and multi-label semantic vector affinity routing
across the 10 canonical technology towers (T1 to T10).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

EpistemicState = Literal["OBSERVED_EXPLICIT", "UNOBSERVED_BLINDSPOT"]
PolarityType = Literal["POSITIVE", "NEGATIVE", "NEUTRAL"]

CANONICAL_TOWERS: tuple[str, ...] = (
    "T1",
    "T2",
    "T3",
    "T4",
    "T5",
    "T6",
    "T7",
    "T8",
    "T9",
    "T10",
)

DEFAULT_TAXONOMY_ANCHORS: dict[str, str] = {
    "T1": (
        "Data center facilities, colocation, rack space, cooling, HVAC, CRAC, UPS, "
        "generator, power distribution, PDU, physical security, environmental monitoring, "
        "cabling, hot aisle, cold aisle, PUE, tier certification, power redundancy."
    ),
    "T2": (
        "Compute, server hardware, virtualization, hypervisor, VMware, vSphere, ESXi, "
        "vMotion, Nutanix, KVM, blades, CPU, RAM, memory utilization, bare metal, "
        "operating systems, Linux, Windows Server, legacy operating systems, hypervisor host, "
        "clusters, capacity, compute nodes, provisioning, node failure."
    ),
    "T3": (
        "Network infrastructure, core routing, switches, BGP, OSPF, VLAN, WAN, SD-WAN, "
        "MPLS, dark fiber, firewall hardware, load balancers, DNS, DHCP, latency, "
        "bandwidth, throughput, Wi-Fi, wireless, Cisco, Juniper, Arista, redundancy, "
        "redundant power supplies, spine-leaf, topology, subnet."
    ),
    "T4": (
        "Data storage, SAN, NAS, object storage, synchronous replication, active-active, "
        "Pure Storage, EMC, Dell, block storage, backup, recovery, snapshot retention, "
        "asynchronous, immutable storage, archive, RAID, fibre channel, iSCSI, IOPS, "
        "terabytes, petabytes, disaster recovery, RPO, RTO, tape."
    ),
    "T5": (
        "Public cloud, hybrid cloud, AWS, Azure, Google Cloud, GCP, cloud native, "
        "Kubernetes, K8s, OpenShift, Docker, containers, serverless, microservice, "
        "IaC, Terraform, CloudFormation, landing zone, VPC, VNet, cloud migration, "
        "egress, ingress, autoscaling, PaaS, IaaS."
    ),
    "T6": (
        "Cybersecurity, information security, identity and access management, IAM, "
        "Active Directory, MFA, SSO, zero trust, vulnerability, CVE, unpatched, "
        "privilege escalation, encryption, TLS, SSL, certificate, expired, SIEM, SOC, "
        "EDR, XDR, firewall policy, DMZ, jumpbox, bastion, EoL, end of life, "
        "compliance, ISO27001, SOC2, penetration testing, threat, ransom."
    ),
    "T7": (
        "IT operations, observability, monitoring, APM, logging, Prometheus, Grafana, "
        "Datadog, Splunk, New Relic, ITSM, ServiceNow, incident management, change "
        "management, SLA, SLO, SLI, runbook, automation, Ansible, patching, CMDB, "
        "on-call, escalation, MTTR, MTBF, telemetry, alerting."
    ),
    "T8": (
        "IT governance, FinOps, financial management, licensing, vendor renewal, contract, "
        "vendor lock-in, budget, unbudgeted, liabilities, TCO, ROI, CapEx, OpEx, "
        "procurement, audit, regulatory risk, shadow IT, IT strategy, PMO, "
        "enterprise architecture, cost optimization, chargeback, vendor support."
    ),
    "T9": (
        "Digital workplace, end-user computing, EUC, VDI, Citrix, Horizon, laptop, "
        "desktop, MDM, Intune, Jamf, Microsoft 365, Office 365, Teams, Zoom, Slack, "
        "email, Exchange, SharePoint, service desk, helpdesk, employee onboarding, "
        "endpoint management, collaboration tools, BYOD."
    ),
    "T10": (
        "Enterprise applications, software engineering, ERP, SAP, Oracle, CRM, "
        "Salesforce, custom applications, legacy code, technical debt, CI/CD, GitLab, "
        "GitHub, Jenkins, DevOps, API gateway, middleware, database, SQL, NoSQL, "
        "PostgreSQL, MongoDB, data warehouse, BI, analytics, SDLC, refactoring."
    ),
}

_NEGATIVE_MARKERS: frozenset[str] = frozenset({
    "lack",
    "lacks",
    "none",
    "no",
    "unpatched",
    "expired",
    "impedes",
    "freeze",
    "liabilities",
    "unbudgeted",
    "critical",
    "vulnerability",
    "vulnerabilities",
    "concern",
    "legacy",
    "manual",
    "failure",
    "outage",
    "risk",
    "bottleneck",
    "missing",
    "unsupported",
    "deprecated",
    "eol",
    "cve",
    "cves",
    "single",
})

_POSITIVE_MARKERS: frozenset[str] = frozenset({
    "automated",
    "redundant",
    "immutable",
    "synchronous",
    "resilient",
    "optimized",
    "compliant",
    "patched",
    "encrypted",
    "validated",
    "certified",
    "ha",
})

_STOPWORDS: frozenset[str] = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can", "had",
    "her", "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
    "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "its",
    "let", "put", "say", "she", "too", "use", "that", "with", "have", "this",
    "will", "your", "from", "they", "know", "want", "been", "good", "much",
    "some", "time", "very", "when", "come", "here", "just", "like", "long",
    "make", "many", "more", "only", "over", "such", "take", "than", "them",
    "well", "were", "what", "about", "there", "their", "which", "would", "these",
    "other", "into", "while", "where", "after", "being", "under", "turn",
    "speaker", "reviewing", "standard", "weekly", "operational", "status",
    "routine", "cadence", "updates", "morning", "everyone", "start",
})

_WORD_TOKEN_REGEX = re.compile(r"[a-z0-9]+")

_SUFFIX_RULES: tuple[tuple[str, int, int], ...] = (
    ("s", 3, -1),
    ("es", 4, -2),
    ("ed", 4, -2),
    ("ing", 5, -3),
    ("tion", 6, -4),
)


@dataclass(frozen=True)
class SemanticProposition:
    """Represents an atomic, lossless statement extracted from an assessment transcript."""

    text: str
    turn_index: int
    speaker: str = "Unknown"
    polarity: PolarityType = "NEUTRAL"
    affinity_scores: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class EpistemicContextPacket:
    """Encapsulates routed semantic evidence and epistemic state for a canonical tower."""

    tower_code: str
    propositions: list[SemanticProposition]
    semantic_density_score: float
    epistemic_state: EpistemicState


def _extract_word_features(word: str) -> list[str]:
    """Extracts structural prefixes and suffix-stripped stems for a single token."""
    w_len = len(word)
    features = [word]
    if w_len > 4:
        features.extend((word[:4], word[:5]))
    for suffix, min_len, slice_idx in _SUFFIX_RULES:
        if w_len > min_len and word.endswith(suffix):
            features.append(word[:slice_idx])
    return features


def _tokenize_and_stem(text: str) -> list[str]:
    """Extracts normalized alphanumeric tokens and structural character n-grams."""
    raw_words = _WORD_TOKEN_REGEX.findall(text.lower())
    features: list[str] = []
    for word in raw_words:
        if len(word) > 1 and word not in _STOPWORDS:
            features.extend(_extract_word_features(word))
    return features


def _compute_tf_vector(
    tokens: list[str],
    sublinear: bool = False,
) -> dict[str, float]:
    """Computes L2-normalized term-frequency vector from token features."""
    if not tokens:
        return {}
    counts: dict[str, float] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0.0) + 1.0
    if sublinear:
        counts = {k: 1.0 + math.log(v) for k, v in counts.items()}
    norm = math.sqrt(sum(val * val for val in counts.values()))
    return {k: v / norm for k, v in counts.items()}


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Computes cosine similarity between two L2-normalized sparse vectors."""
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    dot = sum(val * vec_b.get(key, 0.0) for key, val in vec_a.items())
    return max(0.0, min(1.0, dot))


def _infer_polarity(text: str) -> PolarityType:
    """Determines epistemic polarity of a statement based on risk/resilience markers."""
    words = set(_WORD_TOKEN_REGEX.findall(text.lower()))
    neg_hits = len(words.intersection(_NEGATIVE_MARKERS))
    pos_hits = len(words.intersection(_POSITIVE_MARKERS))
    if neg_hits > pos_hits:
        return "NEGATIVE"
    if pos_hits > neg_hits:
        return "POSITIVE"
    return "NEUTRAL"


def _parse_speaker_and_body(raw_line: str) -> tuple[str, str]:
    """Splits a transcript utterance into speaker label and proposition text without ReDoS."""
    stripped = raw_line.strip()
    if ":" in stripped:
        prefix, rest = stripped.split(":", 1)
        clean_prefix = prefix.strip()
        clean_rest = rest.strip()
        if (
            1 <= len(clean_prefix) <= 40
            and clean_rest
            and all(c.isalnum() or c in "_- " for c in clean_prefix)
        ):
            return clean_prefix, clean_rest
    return "Participant", stripped


def _extract_strings_recursive(obj: Any) -> list[str]:
    """Recursively collects string values from a nested JSON structure."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, list):
        result: list[str] = []
        for item in obj:
            result.extend(_extract_strings_recursive(item))
        return result
    if isinstance(obj, dict):
        result = []
        for val in obj.values():
            result.extend(_extract_strings_recursive(val))
        return result
    return []


class EpistemicGraphRouter:
    """Lossless proposition chunker and multi-label semantic vector router (RFC 084)."""

    def __init__(
        self,
        taxonomy_path: str | Path | None = None,
        affinity_threshold: float = 0.055,
    ) -> None:
        self._affinity_threshold = affinity_threshold
        self._tower_corpuses: dict[str, str] = dict(DEFAULT_TAXONOMY_ANCHORS)
        self._load_external_taxonomy(taxonomy_path)
        self._tower_vectors: dict[str, dict[str, float]] = self._build_tower_vectors()

    def _load_external_taxonomy(self, taxonomy_path: str | Path | None) -> None:
        """Dynamically enriches tower semantic anchors from taxonomy_multilingual.json."""
        candidate_paths = self._resolve_taxonomy_paths(taxonomy_path)
        for path in candidate_paths:
            if path.is_file():
                self._merge_json_taxonomy(path)
                break

    @staticmethod
    def _resolve_taxonomy_paths(custom_path: str | Path | None) -> list[Path]:
        if custom_path is not None:
            return [Path(custom_path)]
        return [
            Path("engine_config/taxonomy_multilingual.json"),
            Path(__file__).resolve().parents[4] / "engine_config" / "taxonomy_multilingual.json",
        ]

    def _merge_json_taxonomy(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        towers_node = data.get("towers", data)
        if not isinstance(towers_node, dict):
            return
        for code in CANONICAL_TOWERS:
            if code in towers_node:
                extracted = " ".join(_extract_strings_recursive(towers_node[code]))
                self._tower_corpuses[code] = f"{self._tower_corpuses[code]} {extracted}"

    def _build_tower_vectors(self) -> dict[str, dict[str, float]]:
        vectors: dict[str, dict[str, float]] = {}
        for code in CANONICAL_TOWERS:
            base_tokens = _tokenize_and_stem(DEFAULT_TAXONOMY_ANCHORS[code])
            ext_tokens = _tokenize_and_stem(self._tower_corpuses[code])
            combined_tokens = (base_tokens * 3) + ext_tokens
            vectors[code] = _compute_tf_vector(combined_tokens, sublinear=True)
        return vectors

    def chunk_transcript(self, raw_lines: list[str]) -> list[SemanticProposition]:
        """Performs 100% lossless proposition-level chunking without array truncation."""
        propositions: list[SemanticProposition] = []
        for idx, line in enumerate(raw_lines):
            if not line or not line.strip():
                continue
            speaker, body_text = _parse_speaker_and_body(line)
            polarity = _infer_polarity(body_text)
            affinities = self._compute_body_affinities(body_text)
            propositions.append(
                SemanticProposition(
                    text=line.strip(),
                    turn_index=idx,
                    speaker=speaker,
                    polarity=polarity,
                    affinity_scores=affinities,
                )
            )
        return propositions

    def _compute_body_affinities(self, body: str) -> dict[str, float]:
        """Calculates multi-label cosine affinity directly from normalized body text."""
        prop_tokens = _tokenize_and_stem(body)
        prop_vec = _compute_tf_vector(prop_tokens)
        if not prop_vec:
            return {code: 0.0 for code in CANONICAL_TOWERS}

        scores: dict[str, float] = {}
        for code in CANONICAL_TOWERS:
            sim = _cosine_similarity(prop_vec, self._tower_vectors[code])
            scores[code] = round(sim, 4)
        return scores

    def compute_affinities(self, text: str) -> dict[str, float]:
        """Calculates multi-label cosine affinity scores across all 10 canonical towers."""
        _, body = _parse_speaker_and_body(text)
        return self._compute_body_affinities(body)

    def route_transcript(
        self, raw_lines: list[str]
    ) -> dict[str, EpistemicContextPacket]:
        """Routes transcript propositions across T1..T10 and resolves epistemic states."""
        propositions = self.chunk_transcript(raw_lines)
        routed_buckets: dict[str, list[SemanticProposition]] = {
            code: [] for code in CANONICAL_TOWERS
        }

        for prop in propositions:
            self._assign_proposition_to_towers(prop, routed_buckets)

        return {
            code: self._build_context_packet(code, routed_buckets[code])
            for code in CANONICAL_TOWERS
        }

    def _assign_proposition_to_towers(
        self,
        prop: SemanticProposition,
        buckets: dict[str, list[SemanticProposition]],
    ) -> None:
        scores = prop.affinity_scores or self.compute_affinities(prop.text)
        for code, score in scores.items():
            if score >= self._affinity_threshold:
                buckets[code].append(prop)

    def _build_context_packet(
        self,
        tower_code: str,
        props: list[SemanticProposition],
    ) -> EpistemicContextPacket:
        if not props:
            return EpistemicContextPacket(
                tower_code=tower_code,
                propositions=[],
                semantic_density_score=0.0,
                epistemic_state="UNOBSERVED_BLINDSPOT",
            )

        avg_affinity = sum(
            p.affinity_scores.get(tower_code, 0.1) for p in props
        ) / len(props)
        scaled_density = min(1.0, round(avg_affinity * 3.5, 4))
        density = max(0.01, scaled_density)

        return EpistemicContextPacket(
            tower_code=tower_code,
            propositions=props,
            semantic_density_score=density,
            epistemic_state="OBSERVED_EXPLICIT",
        )


SemanticEpistemicRouter = EpistemicGraphRouter

__all__ = [
    "CANONICAL_TOWERS",
    "EpistemicContextPacket",
    "EpistemicGraphRouter",
    "EpistemicState",
    "PolarityType",
    "SemanticEpistemicRouter",
    "SemanticProposition",
]
