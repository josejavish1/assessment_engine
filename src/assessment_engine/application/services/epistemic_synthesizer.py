"""Epistemic Synthesizer Application Service (RFC 082).

Decomposes normalized utterances into atomic facts, triangulates oral testimony
with empirical questionnaire fragments, resolves multi-source ground truth,
and detects epistemic dissonance events using externalized taxonomy rules.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional, Pattern
from uuid import uuid4

from assessment_engine.domain.contracts.ingestion_ports import IEpistemicSynthesizerPort
from assessment_engine.domain.schemas.epistemic_ledger import (
    AuthorityRole,
    EpistemicFragment,
    EpistemicLedger,
    EpistemicState,
    EvidenceEntry,
    NormalizedUtterance,
    Polarity,
    TruthStatus,
)

logger = logging.getLogger(__name__)


def _normalize_unicode(text: str) -> str:
    """Normalizes Unicode text via NFKC casefolding while preserving all international scripts."""
    return unicodedata.normalize("NFKC", text).casefold().strip()


_DEFAULT_DOMAIN_TAXONOMY: Dict[str, List[str]] = {
    "T1": ["datacenter", "data center", "ups", "hvac", "cooling", "generator", "facilities", "power", "rack"],
    "T2": ["virtualization", "vmware", "vsphere", "simplivity", "proxmox", "compute", "cluster", "esxi", "vcenter", "hyper-v", "nutanix", "kubernetes"],
    "T3": ["storage", "netapp", "vnx", "san", "nas", "backup", "cohesity", "veeam", "s3", "metrocluster", "recovery", "replication"],
    "T4": ["network", "switch", "routing", "lan", "wan", "sd-wan", "huawei", "firewall", "fortinet", "fortigate", "vpn", "equinix", "fiber"],
    "T5": ["edge", "industrial", "ot", "scada", "plc", "iot", "telemetry", "plant", "manufacturing", "hivision"],
    "T6": ["identity", "active directory", "entra", "iam", "pam", "mfa", "rbac", "privileged", "cyberark", "credential", "sso"],
    "T7": ["cloud", "gcp", "azure", "oci", "aws", "sap", "s/4hana", "erp", "iaas", "paas", "saas"],
    "T8": ["cybersecurity", "security", "edr", "xdr", "soc", "siem", "vulnerability", "patching", "ransomware", "antivirus", "netskope", "ztna"],
    "T9": ["workplace", "endpoint", "laptop", "desktop", "vdi", "m365", "teams", "helpdesk", "service desk", "ticketing"],
    "T10": ["modernization", "legacy", "technical debt", "iseries", "as400", "mainframe", "oracle forms", "architecture", "middleware", "wso2", "integration"],
}

_DEFAULT_NEGATIVE_CUES: List[str] = [
    "bottleneck", "outage", "failure", "fail", "risk", "strained", "strain",
    "legacy", "limitation", "limit", "lack", "saturated", "severe", "degraded",
    "debt", "deficit", "vulnerability",
]

_DEFAULT_POSITIVE_CUES: List[str] = [
    "robust", "healthy", "automated", "redundant", "high availability",
    "optimal", "compliant", "resilient", "stable",
]


class EpistemicSynthesizer(IEpistemicSynthesizerPort):
    """Reconciles oral transcript evidence and empirical survey scores into an audit-grade EpistemicLedger."""

    def __init__(
        self,
        domain_taxonomy: Optional[Dict[str, List[str]]] = None,
        negative_cues: Optional[List[str]] = None,
        positive_cues: Optional[List[str]] = None,
    ) -> None:
        self._domain_taxonomy = domain_taxonomy or dict(_DEFAULT_DOMAIN_TAXONOMY)
        self._negative_cues = [_normalize_unicode(c) for c in (negative_cues or _DEFAULT_NEGATIVE_CUES)]
        self._positive_cues = [_normalize_unicode(c) for c in (positive_cues or _DEFAULT_POSITIVE_CUES)]
        self._compiled_taxonomy: Dict[str, List[Pattern[str]]] = self._compile_taxonomy(
            self._domain_taxonomy
        )

    @staticmethod
    def _compile_taxonomy(
        taxonomy: Dict[str, List[str]]
    ) -> Dict[str, List[Pattern[str]]]:
        compiled: Dict[str, List[Pattern[str]]] = {}
        for domain_id, keywords in taxonomy.items():
            patterns: List[Pattern[str]] = []
            for kw in keywords:
                norm_kw = _normalize_unicode(kw)
                if norm_kw:
                    patterns.append(re.compile(rf"(?<!\w){re.escape(norm_kw)}", re.UNICODE))
            compiled[domain_id] = patterns
        return compiled

    def _classify_domain_for_text(
        self,
        text: str,
        compiled_taxonomy: Dict[str, List[Pattern[str]]],
    ) -> str:
        normalized = _normalize_unicode(text)
        if not normalized or not compiled_taxonomy:
            return ""
        scores: Dict[str, int] = {k: 0 for k in compiled_taxonomy}
        for domain_id, patterns in compiled_taxonomy.items():
            for pat in patterns:
                if pat.search(normalized):
                    scores[domain_id] += 1
        best_domain = max(scores, key=lambda k: scores[k])
        return best_domain if scores[best_domain] > 0 else ""

    def synthesize_ledger(
        self,
        client_id: str,
        normalized_utterances: List[NormalizedUtterance],
        empirical_fragments: List[EpistemicFragment],
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> EpistemicLedger:
        """Synthesize normalized epistemic ledger from empirical client observations."""
        entries: List[EvidenceEntry] = []
        entry_seq = 1

        # Allow runtime_context overrides for tenant-specific domain taxonomies and polarity cues
        compiled_tax = self._compiled_taxonomy
        if runtime_context and "domain_taxonomy" in runtime_context:
            compiled_tax = self._compile_taxonomy(runtime_context["domain_taxonomy"])

        neg_cues = (
            [_normalize_unicode(c) for c in runtime_context["negative_cues"]]
            if runtime_context and "negative_cues" in runtime_context
            else self._negative_cues
        )
        pos_cues = (
            [_normalize_unicode(c) for c in runtime_context["positive_cues"]]
            if runtime_context and "positive_cues" in runtime_context
            else self._positive_cues
        )

        # 1. Group empirical fragments by top-level taxonomy domain
        empirical_by_domain: Dict[str, List[EpistemicFragment]] = {}
        for ef in empirical_fragments:
            t_key = (
                ef.domain_taxonomy_ref.split(".")[0]
                if "." in ef.domain_taxonomy_ref
                else ef.domain_taxonomy_ref
            )
            if t_key:
                empirical_by_domain.setdefault(t_key, []).append(ef)

        # 2. Extract epistemic fragments from SME and Executive utterances
        transcript_by_domain: Dict[str, List[EpistemicFragment]] = {}
        for u in normalized_utterances:
            if u.speaker_role == AuthorityRole.INTERVIEWER:
                continue

            domain_ref = self._classify_domain_for_text(u.normalized_text, compiled_tax)
            if not domain_ref:
                continue

            weight = 0.85 if u.speaker_role == AuthorityRole.SME_TECHNICAL else 0.70

            polarity = Polarity.NEUTRAL
            normalized_turn = _normalize_unicode(u.normalized_text)
            if any(w in normalized_turn for w in neg_cues):
                polarity = Polarity.NEGATIVE
            elif any(w in normalized_turn for w in pos_cues):
                polarity = Polarity.POSITIVE

            frag = EpistemicFragment(
                fragment_id=uuid4(),
                utterance_id=u.utterance_id,
                source_type="RAW_TRANSCRIPT",
                source_file=u.source_file,
                location_reference=f"Seq {u.sequence_index}",
                domain_taxonomy_ref=domain_ref,
                canonical_assertion=u.normalized_text,
                epistemic_weight=weight,
                polarity=polarity,
                state=EpistemicState.CURRENT,
                metadata={
                    "speaker": u.speaker_identifier,
                    "role": u.speaker_role.value,
                    "resolved_entities": [e.model_dump() for e in u.resolved_entities],
                },
            )
            transcript_by_domain.setdefault(domain_ref, []).append(frag)

        # 3. Triangulate and reconcile entries per domain
        all_domains = sorted(
            set(list(empirical_by_domain.keys()) + list(transcript_by_domain.keys()))
        )

        for dom in all_domains:
            dom_emp = empirical_by_domain.get(dom, [])
            dom_trans = transcript_by_domain.get(dom, [])

            if dom_trans and dom_emp:
                has_emp_high = any(f.polarity == Polarity.POSITIVE for f in dom_emp)
                has_trans_neg = any(f.polarity == Polarity.NEGATIVE for f in dom_trans)

                is_dissonant = has_emp_high and has_trans_neg
                status = (
                    TruthStatus.VERIFIED_DISSONANT
                    if is_dissonant
                    else TruthStatus.VERIFIED_CONSISTENT
                )
                dissonance_text = (
                    f"Operational reality gap detected in {dom}: Self-reported questionnaire scores indicate robust controls, "
                    f"whereas SME technical interview confirms operational frictions or architectural deficits."
                    if is_dissonant
                    else None
                )

                top_trans = dom_trans[0].canonical_assertion
                summary_assertion = (
                    f"{dom}: {top_trans[:180]}..."
                    if len(top_trans) > 180
                    else f"{dom}: {top_trans}"
                )

                entries.append(
                    EvidenceEntry(
                        entry_id=f"EVD-{entry_seq:04d}",
                        domain_taxonomy_ref=dom,
                        canonical_assertion=summary_assertion,
                        truth_status=status,
                        composite_confidence=0.92,
                        dissonance_flag=is_dissonant,
                        dissonance_analysis=dissonance_text,
                        supporting_fragments=(dom_trans[:4] + dom_emp[:4]),
                    )
                )
                entry_seq += 1

            elif dom_trans:
                top_trans = dom_trans[0].canonical_assertion
                summary_assertion = (
                    f"{dom}: {top_trans[:180]}..."
                    if len(top_trans) > 180
                    else f"{dom}: {top_trans}"
                )
                entries.append(
                    EvidenceEntry(
                        entry_id=f"EVD-{entry_seq:04d}",
                        domain_taxonomy_ref=dom,
                        canonical_assertion=summary_assertion,
                        truth_status=TruthStatus.SINGLE_SOURCE_UNVERIFIED,
                        composite_confidence=0.75,
                        dissonance_flag=False,
                        supporting_fragments=dom_trans[:4],
                    )
                )
                entry_seq += 1

            elif dom_emp:
                summary_assertion = (
                    f"{dom}: Structured questionnaire telemetry recorded across {len(dom_emp)} questions."
                )
                entries.append(
                    EvidenceEntry(
                        entry_id=f"EVD-{entry_seq:04d}",
                        domain_taxonomy_ref=dom,
                        canonical_assertion=summary_assertion,
                        truth_status=TruthStatus.SINGLE_SOURCE_UNVERIFIED,
                        composite_confidence=0.80,
                        dissonance_flag=False,
                        supporting_fragments=dom_emp[:4],
                    )
                )
                entry_seq += 1

        return EpistemicLedger(
            client_id=client_id,
            epistemic_entries=entries,
            metadata={
                "total_utterances_processed": len(normalized_utterances),
                "total_empirical_fragments": len(empirical_fragments),
                "total_domains_covered": len(all_domains),
            },
        )
