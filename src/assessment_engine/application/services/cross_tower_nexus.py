"""Cross-Tower Nexus & Second-Order Cascade Engine (RFC 084 Phase 3).

Transforms the 10 technology towers from isolated analytical silos into a
Directed Acyclic Graph (DAG) capable of evaluating deterministic second-order
risk cascades and topological dependencies.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any


ALL_TOWERS: tuple[str, ...] = (
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

DEFAULT_NEXUS_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "CASCADE_T1_TO_T2_001",
        "source_tower": "T1",
        "source_pillar": "T1.P1",
        "target_tower": "T2",
        "target_pillar": "T2.P1",
        "trigger_keywords": ["power", "cooling", "ups", "generator", "thermal", "hvac"],
        "title": "Secondary Compute Risk: Thermal Throttling and Unplanned Host Outage",
        "causal_narrative": "Facility power or cooling instability directly threatens physical hypervisor uptime and hardware longevity.",
        "ale_multiplier": 0.45,
        "blast_radius_severity": "CRITICAL",
    },
    {
        "rule_id": "CASCADE_T1_TO_T3_001",
        "source_tower": "T1",
        "source_pillar": "T1.P1",
        "target_tower": "T3",
        "target_pillar": "T3.P1",
        "trigger_keywords": ["power", "cooling", "ups", "mdf", "idf", "telecom"],
        "title": "Secondary Network Risk: Telecom Closet Brownout and Core Switch Failure",
        "causal_narrative": "Facility power and cooling failures in distribution rooms induce core routing hardware damage and packet loss.",
        "ale_multiplier": 0.35,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T1_TO_T4_001",
        "source_tower": "T1",
        "source_pillar": "T1.P1",
        "target_tower": "T4",
        "target_pillar": "T4.P1",
        "trigger_keywords": ["power", "cooling", "ups", "generator", "facility"],
        "title": "Secondary Storage Risk: Unclean Array Shutdown and Write-Cache Loss",
        "causal_narrative": "Environmental power instability risks ungraceful SAN/NAS controller shutdown and storage metadata corruption.",
        "ale_multiplier": 0.40,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T2_TO_T5_001",
        "source_tower": "T2",
        "source_pillar": "T2.P1",
        "target_tower": "T5",
        "target_pillar": "T5.P1",
        "trigger_keywords": ["ram", "cpu", "saturated", "redundancy", "hypervisor", "cluster", "capacity"],
        "title": "Secondary Resilience Risk: Inability to Execute Failover and Snapshot Consolidation",
        "causal_narrative": "Compute and hypervisor resource exhaustion prevents snapshot stun recovery and compromises HA failover capacity.",
        "ale_multiplier": 0.50,
        "blast_radius_severity": "CRITICAL",
    },
    {
        "rule_id": "CASCADE_T2_TO_T6_001",
        "source_tower": "T2",
        "source_pillar": "T2.P1",
        "target_tower": "T6",
        "target_pillar": "T6.P1",
        "trigger_keywords": ["ram", "saturated", "hypervisor", "cluster", "redundancy", "ha", "eol", "capacity"],
        "title": "Secondary Security Risk: Impeded Kernel and Hypervisor Patching",
        "causal_narrative": "Exhaustion of hypervisor cluster RAM and lack of HA headroom prevent live workload evacuation required for emergency security patching.",
        "ale_multiplier": 0.40,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T2_TO_T8_001",
        "source_tower": "T2",
        "source_pillar": "T2.P2",
        "target_tower": "T8",
        "target_pillar": "T8.P1",
        "trigger_keywords": ["ram", "cpu", "saturated", "latency", "contention", "hypervisor", "licensing"],
        "title": "Secondary FinOps Risk: Unbudgeted Per-Core Licensing and Zombie VM Sprawl",
        "causal_narrative": "Uncontrolled monolithic virtual machine expansion inflates hypervisor socket licensing liabilities and unbudgeted CapEx.",
        "ale_multiplier": 0.35,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T3_TO_T6_001",
        "source_tower": "T3",
        "source_pillar": "T3.P1",
        "target_tower": "T6",
        "target_pillar": "T6.P1",
        "trigger_keywords": ["flat", "vlan", "segmentation", "routing", "firewall", "spanning", "switch"],
        "title": "Secondary Security Risk: Uninhibited Lateral Movement Blast Radius",
        "causal_narrative": "Deficient network segmentation and flat Layer-2 switching domains enable rapid lateral propagation of ransomware and unauthorized access.",
        "ale_multiplier": 0.55,
        "blast_radius_severity": "CRITICAL",
    },
    {
        "rule_id": "CASCADE_T3_TO_T9_001",
        "source_tower": "T3",
        "source_pillar": "T3.P1",
        "target_tower": "T9",
        "target_pillar": "T9.P1",
        "trigger_keywords": ["wifi", "wan", "bandwidth", "jitter", "latency", "packet", "bgp", "mpls"],
        "title": "Secondary Workplace Risk: VDI Session Drops and Collaboration Degradation",
        "causal_narrative": "Network transport jitter and WAN link saturation degrade remote workplace productivity and unified communications.",
        "ale_multiplier": 0.30,
        "blast_radius_severity": "MEDIUM",
    },
    {
        "rule_id": "CASCADE_T3_TO_T10_001",
        "source_tower": "T3",
        "source_pillar": "T3.P1",
        "target_tower": "T10",
        "target_pillar": "T10.P1",
        "trigger_keywords": ["switch", "wan", "latency", "packet", "scada", "telemetry", "link"],
        "title": "Secondary Plant Operations Risk: Industrial SCADA and Weighbridge Line Cuts",
        "causal_narrative": "Single-carrier WAN topology and unredundant plant switches trigger dispatch halting during carrier outages.",
        "ale_multiplier": 0.45,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T4_TO_T5_001",
        "source_tower": "T4",
        "source_pillar": "T4.P1",
        "target_tower": "T5",
        "target_pillar": "T5.P1",
        "trigger_keywords": ["iops", "latency", "storage", "san", "nas", "capacity", "disk", "throughput", "snapshot"],
        "title": "Secondary Resilience Risk: RTO Breach via Degraded Backup Throughput",
        "causal_narrative": "Primary storage I/O bottlenecks and capacity exhaustion severely elongate backup windows and violate recovery time objectives.",
        "ale_multiplier": 0.45,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T4_TO_T2_001",
        "source_tower": "T4",
        "source_pillar": "T4.P1",
        "target_tower": "T2",
        "target_pillar": "T2.P1",
        "trigger_keywords": ["storage", "san", "nas", "capacity", "volume", "iops", "disk", "exhaustion"],
        "title": "Secondary Compute Risk: VM Freeze Alarms from Volume Exhaustion",
        "causal_narrative": "Storage volume capacity exhaustion above 90% triggers automated hypervisor pause alarms across compute clusters.",
        "ale_multiplier": 0.50,
        "blast_radius_severity": "CRITICAL",
    },
    {
        "rule_id": "CASCADE_T5_TO_T10_001",
        "source_tower": "T5",
        "source_pillar": "T5.P1",
        "target_tower": "T10",
        "target_pillar": "T10.P1",
        "trigger_keywords": ["rpo", "rto", "backup", "dr", "replication", "immutable", "contingency"],
        "title": "Secondary Application Risk: Unrecoverable Business Logic and Data Loss",
        "causal_narrative": "Gaps in disaster recovery orchestration expose mission-critical enterprise applications to permanent data loss during catastrophic events.",
        "ale_multiplier": 0.50,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T6_TO_T9_001",
        "source_tower": "T6",
        "source_pillar": "T6.P1",
        "target_tower": "T9",
        "target_pillar": "T9.P1",
        "trigger_keywords": ["mfa", "identity", "edr", "patch", "endpoint", "privilege", "active", "directory"],
        "title": "Secondary Workplace Risk: Endpoint Compromise and Identity Takeover",
        "causal_narrative": "Weaknesses in identity governance and endpoint protection expose user workspaces to credential harvesting.",
        "ale_multiplier": 0.40,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T6_TO_T10_001",
        "source_tower": "T6",
        "source_pillar": "T6.P1",
        "target_tower": "T10",
        "target_pillar": "T10.P1",
        "trigger_keywords": ["privilege", "credentials", "access", "pam", "ad", "unauthorized"],
        "title": "Secondary Application Risk: Database Infiltration and Unauthorized Alteration",
        "causal_narrative": "Over-privileged service accounts expose core transactional databases and plant execution systems to tampering.",
        "ale_multiplier": 0.45,
        "blast_radius_severity": "HIGH",
    },
    {
        "rule_id": "CASCADE_T7_TO_T8_001",
        "source_tower": "T7",
        "source_pillar": "T7.P1",
        "target_tower": "T8",
        "target_pillar": "T8.P1",
        "trigger_keywords": ["monitoring", "ticket", "itsm", "cmdb", "sla", "observability", "incident"],
        "title": "Secondary Governance Risk: SLA Penalty Liabilities and Unmeasured MTTR",
        "causal_narrative": "Absence of automated ITSM telemetry exposes corporate leadership to unmeasured service delivery penalties and governance blindspots.",
        "ale_multiplier": 0.30,
        "blast_radius_severity": "MEDIUM",
    },
]


@dataclass(frozen=True)
class SecondOrderRiskAssertion:
    """Immutable value object representing a derived cross-tower risk cascade."""

    assertion_id: str
    source_tower: str
    source_pillar: str
    target_tower: str
    target_pillar: str
    title: str
    causal_narrative: str
    compounded_ale_impact: float
    blast_radius_severity: str


def _first_present(mapping: dict[str, Any], keys: tuple[str, ...], default: Any) -> Any:
    """Returns the first truthy value for the given keys in mapping, or default."""
    for key in keys:
        val = mapping.get(key)
        if val:
            return val
    return default


def _extract_raw_rule_list(raw_data: Any) -> list[Any]:
    """Extracts the list of raw rules from loaded JSON data."""
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        return _first_present(raw_data, ("rules", "nexus_rules", "cascades"), [])
    return []


def _extract_tower_id(val: Any) -> str:
    """Extracts canonical tower prefix (e.g., 'T2.P1' -> 'T2')."""
    raw = str(val or "").strip()
    return raw.split(".")[0].strip() if raw else ""


def _parse_single_rule(item: Any, idx: int) -> dict[str, Any] | None:
    """Validates and normalizes a single raw rule dictionary."""
    if not isinstance(item, dict):
        return None
    src = _extract_tower_id(
        _first_present(item, ("source_tower", "source_pillar", "source"), "")
    )
    tgt = _extract_tower_id(
        _first_present(item, ("target_tower", "target_pillar", "target"), "")
    )
    if not src or not tgt:
        return None
    return _build_canonical_rule(item, src, tgt, idx)


def _build_canonical_rule(
    item: dict[str, Any], src: str, tgt: str, idx: int
) -> dict[str, Any]:
    """Constructs a standardized rule dictionary with safe defaults."""
    default_id = f"CASCADE_{src}_TO_{tgt}_{idx:03d}"
    keywords = _first_present(item, ("trigger_keywords", "keywords"), [])
    multiplier = float(
        _first_present(
            item, ("ale_multiplier", "compounding_factor", "impact_multiplier"), 0.40
        )
    )
    default_title = f"Secondary Risk Cascade: {src} impact on {tgt}"
    default_narrative = (
        f"Critical finding in {src} induces downstream operational risk in {tgt}."
    )
    narrative = _first_present(
        item, ("causal_narrative", "narrative", "description"), default_narrative
    )
    severity = _first_present(item, ("blast_radius_severity", "severity"), "HIGH")

    return {
        "rule_id": str(_first_present(item, ("rule_id", "id"), default_id)),
        "source_tower": src,
        "source_pillar": str(_first_present(item, ("source_pillar",), f"{src}.P1")),
        "target_tower": tgt,
        "target_pillar": str(_first_present(item, ("target_pillar",), f"{tgt}.P1")),
        "trigger_keywords": [str(k).lower() for k in keywords],
        "title": str(_first_present(item, ("title",), default_title)),
        "causal_narrative": str(narrative),
        "ale_multiplier": multiplier,
        "blast_radius_severity": str(severity).upper(),
    }


def _tower_sort_key(tower_id: str) -> int:
    """Extracts numeric index from tower identifier (e.g. 'T10' -> 10) for stable sorting."""
    digits = "".join(ch for ch in tower_id if ch.isdigit())
    return int(digits) if digits else 999


def _build_dag_structures(
    rules: list[dict[str, Any]],
) -> tuple[dict[str, set[str]], dict[str, int]]:
    """Builds adjacency sets and in-degree counts for all towers."""
    adjacency: dict[str, set[str]] = {t: set() for t in ALL_TOWERS}
    in_degree: dict[str, int] = {t: 0 for t in ALL_TOWERS}
    for rule in rules:
        _add_dag_edge(
            adjacency,
            in_degree,
            rule.get("source_tower", ""),
            rule.get("target_tower", ""),
        )
    return adjacency, in_degree


def _add_dag_edge(
    adjacency: dict[str, set[str]],
    in_degree: dict[str, int],
    src: str,
    tgt: str,
) -> None:
    """Registers a directed edge if both nodes are valid towers and edge is new."""
    if src in adjacency and tgt in adjacency and tgt not in adjacency[src]:
        adjacency[src].add(tgt)
        in_degree[tgt] += 1


def _decrement_neighbors(
    neighbors: set[str], in_degree: dict[str, int], queue: deque[str]
) -> None:
    """Decrements in-degrees of neighbor towers and enqueues zero-degree nodes."""
    for neighbor in sorted(neighbors, key=_tower_sort_key):
        in_degree[neighbor] -= 1
        if in_degree[neighbor] == 0:
            queue.append(neighbor)


class CrossTowerNexusEngine:
    """Deterministic DAG engine for evaluating cross-tower causal risk cascades."""

    DEFAULT_POLICY_REL_PATH = Path("engine_config/policies/cross_domain_nexus_map.json")

    def __init__(self, policy_path: Path | str | None = None) -> None:
        self._policy_path = self._resolve_policy_path(policy_path)
        self._rules: list[dict[str, Any]] = self._load_rules(self._policy_path)
        self._topological_order: list[str] = self._compute_topological_order()

    @property
    def rules(self) -> list[dict[str, Any]]:
        """Returns a shallow copy of loaded declarative cross-domain rules."""
        return [dict(rule) for rule in self._rules]

    def get_topological_order(self) -> list[str]:
        """Returns the deterministic topological evaluation order of the 10 towers."""
        return list(self._topological_order)

    def evaluate_cascades(
        self, tower_payloads: dict[str, dict[str, Any]]
    ) -> list[SecondOrderRiskAssertion]:
        """Evaluates second-order risk cascades across the topological tower graph."""
        if not tower_payloads:
            return []

        assertions: list[SecondOrderRiskAssertion] = []
        seen_ids: set[str] = set()

        for tower_id in self._topological_order:
            payload = tower_payloads.get(tower_id)
            if payload:
                findings = self._extract_tower_findings(tower_id, payload)
                assertions.extend(
                    self._match_rules_for_tower(tower_id, findings, seen_ids)
                )

        return assertions

    def _resolve_policy_path(self, custom_path: Path | str | None) -> Path:
        """Resolves the path to cross_domain_nexus_map.json across working directories."""
        if custom_path is not None:
            return Path(custom_path)

        candidates = [Path.cwd()] + list(Path(__file__).resolve().parents)
        for base in candidates:
            candidate = base / self.DEFAULT_POLICY_REL_PATH
            if candidate.is_file():
                return candidate

        return Path.cwd() / self.DEFAULT_POLICY_REL_PATH

    def _load_rules(self, path: Path) -> list[dict[str, Any]]:
        """Loads declarative ontology rules from JSON or falls back to default catalog."""
        if not path.is_file():
            return [dict(r) for r in DEFAULT_NEXUS_RULES]

        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return [dict(r) for r in DEFAULT_NEXUS_RULES]

        extracted = self._normalize_raw_rules(raw_data)
        return extracted if extracted else [dict(r) for r in DEFAULT_NEXUS_RULES]

    def _normalize_raw_rules(self, raw_data: Any) -> list[dict[str, Any]]:
        """Normalizes raw JSON structures and merges baseline ontology rules."""
        raw_list = _extract_raw_rule_list(raw_data)
        parsed = [
            r
            for idx, item in enumerate(raw_list, 1)
            if (r := _parse_single_rule(item, idx)) is not None
        ]
        seen_pairs = {(r["source_tower"], r["target_tower"]) for r in parsed}
        for default_rule in DEFAULT_NEXUS_RULES:
            pair = (default_rule["source_tower"], default_rule["target_tower"])
            if pair not in seen_pairs:
                parsed.append(dict(default_rule))
        return parsed

    @staticmethod
    def _build_canonical_rule(
        item: dict[str, Any], src: str, tgt: str, idx: int
    ) -> dict[str, Any]:
        """Constructs a standardized rule dictionary with safe defaults."""
        return _build_canonical_rule(item, src, tgt, idx)

    def _compute_topological_order(self) -> list[str]:
        """Computes Kahn's topological sort across all 10 towers and verifies acyclicity."""
        adjacency, in_degree = _build_dag_structures(self._rules)
        zero_in = (t for t, deg in in_degree.items() if deg == 0)
        queue: deque[str] = deque(sorted(zero_in, key=_tower_sort_key))
        ordered: list[str] = []

        while queue:
            current = queue.popleft()
            ordered.append(current)
            _decrement_neighbors(adjacency[current], in_degree, queue)

        if len(ordered) != len(ALL_TOWERS):
            raise ValueError(
                "Cycle detected in Cross-Tower Nexus graph; DAG invariant violated."
            )

        return ordered

    @staticmethod
    def _tower_sort_key(tower_id: str) -> int:
        """Extracts numeric index from tower identifier (e.g. 'T10' -> 10) for stable sorting."""
        return _tower_sort_key(tower_id)

    def _extract_tower_findings(
        self, tower_id: str, payload: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extracts and normalizes health check findings from a tower payload."""
        pillars = payload.get("pillars_analysis")
        if not isinstance(pillars, list):
            return []

        extracted: list[dict[str, Any]] = []
        for pillar in pillars:
            if isinstance(pillar, dict):
                extracted.extend(self._extract_pillar_findings(tower_id, pillar))
        return extracted

    def _extract_pillar_findings(
        self, tower_id: str, pillar: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extracts normalized findings for a single pillar dictionary."""
        pillar_id = str(_first_present(pillar, ("pillar_id",), f"{tower_id}.P1"))
        checks = pillar.get("health_check_asis")
        if not isinstance(checks, list):
            return []
        return [
            self._normalize_finding(pillar_id, check)
            for check in checks
            if isinstance(check, dict)
        ]

    @staticmethod
    def _normalize_finding(pillar_id: str, check: dict[str, Any]) -> dict[str, Any]:
        """Normalizes a single health check finding dictionary."""
        finding_text = str(_first_present(check, ("finding",), ""))
        risk_text = str(_first_present(check, ("business_risk",), ""))
        severity = str(_first_present(check, ("severity",), "HIGH")).upper()
        raw_ale = check.get("fair_ale_score")
        ale_score = 150000.0
        if raw_ale is not None:
            try:
                parsed = float(str(raw_ale).replace(",", "").replace("$", "").replace("€", "").strip())
                if math.isfinite(parsed) and parsed > 0.0:
                    ale_score = parsed
            except (ValueError, TypeError):
                pass
        return {
            "pillar_id": pillar_id,
            "combined_text": f"{finding_text} {risk_text}".lower(),
            "severity": severity,
            "ale_score": max(ale_score, 1000.0),
        }

    def _match_rules_for_tower(
        self,
        tower_id: str,
        findings: list[dict[str, Any]],
        seen_ids: set[str],
    ) -> list[SecondOrderRiskAssertion]:
        """Matches extracted tower findings against declarative rules for that source tower."""
        tower_rules = [r for r in self._rules if r.get("source_tower") == tower_id]
        severe_findings = [
            f for f in findings if f["severity"] in ("CRITICAL", "HIGH")
        ]
        results: list[SecondOrderRiskAssertion] = []

        for finding in severe_findings:
            results.extend(
                self._evaluate_finding_against_rules(finding, tower_rules, seen_ids)
            )

        return results

    def _evaluate_finding_against_rules(
        self,
        finding: dict[str, Any],
        tower_rules: list[dict[str, Any]],
        seen_ids: set[str],
    ) -> list[SecondOrderRiskAssertion]:
        """Evaluates a single severe finding against applicable tower rules."""
        matched: list[SecondOrderRiskAssertion] = []
        for rule in tower_rules:
            if self._does_finding_trigger_rule(finding, rule):
                assertion = self._create_assertion(finding, rule, len(seen_ids) + 1)
                if assertion.assertion_id not in seen_ids:
                    seen_ids.add(assertion.assertion_id)
                    matched.append(assertion)
        return matched

    @staticmethod
    def _does_finding_trigger_rule(
        finding: dict[str, Any], rule: dict[str, Any]
    ) -> bool:
        """Determines whether a finding triggers a cascade rule via token-set or phrase match."""
        keywords: list[str] = rule.get("trigger_keywords") or []
        if not keywords:
            return finding.get("severity") in ("CRITICAL", "HIGH")
        combined_text = str(finding.get("combined_text", "")).lower()
        tokens = set(re.findall(r"[a-z0-9]+", combined_text))
        for kw in keywords:
            norm_kw = kw.strip().lower()
            if not norm_kw:
                continue
            if (" " in norm_kw or "-" in norm_kw) and norm_kw in combined_text:
                return True
            if norm_kw in tokens:
                return True
        return False

    @staticmethod
    def _create_assertion(
        finding: dict[str, Any], rule: dict[str, Any], sequence: int
    ) -> SecondOrderRiskAssertion:
        """Instantiates an immutable SecondOrderRiskAssertion from a matched rule and finding."""
        src = str(rule["source_tower"])
        tgt = str(rule["target_tower"])
        multiplier = float(_first_present(rule, ("ale_multiplier",), 0.40))
        compounded_ale = round(float(finding["ale_score"]) * multiplier, 2)
        default_id = f"CASCADE_{src}_TO_{tgt}_{sequence:03d}"
        rule_id = str(_first_present(rule, ("rule_id",), default_id))
        src_pillar = _first_present(
            finding,
            ("pillar_id",),
            _first_present(rule, ("source_pillar",), f"{src}.P1"),
        )
        tgt_pillar = _first_present(rule, ("target_pillar",), f"{tgt}.P1")
        severity = _first_present(rule, ("blast_radius_severity",), "HIGH")

        return SecondOrderRiskAssertion(
            assertion_id=rule_id,
            source_tower=src,
            source_pillar=str(src_pillar),
            target_tower=tgt,
            target_pillar=str(tgt_pillar),
            title=str(rule["title"]),
            causal_narrative=str(rule["causal_narrative"]),
            compounded_ale_impact=compounded_ale,
            blast_radius_severity=str(severity),
        )
