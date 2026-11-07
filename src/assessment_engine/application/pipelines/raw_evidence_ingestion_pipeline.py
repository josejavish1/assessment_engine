"""Raw Evidence Ingestion Pipeline Orchestrator (RFC 082).

Integrates raw transcript parsing, dynamic phonetic normalization, empirical data parsing,
and epistemic truth synthesis into an immutable Ground Truth ledger.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from assessment_engine.application.services.epistemic_synthesizer import (
    EpistemicSynthesizer,
)
from assessment_engine.domain.contracts.ingestion_ports import (
    IEmpiricalDataParserPort,
    IEpistemicSynthesizerPort,
    IPhoneticResolverPort,
    ITranscriptParserPort,
)
from assessment_engine.domain.schemas.epistemic_ledger import (
    EpistemicLedger,
    RawUtterance,
)
from assessment_engine.infrastructure.normalization.phonetic_entity_resolver import (
    PhoneticEntityResolver,
)
from assessment_engine.infrastructure.parsers.empirical_response_parser import (
    EmpiricalResponseParser,
)
from assessment_engine.infrastructure.parsers.raw_transcript_parser import (
    RawTranscriptParser,
)
from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)


class RawEvidenceIngestionPipeline:
    """End-to-end orchestrator for raw evidence extraction and epistemic synthesis."""

    def __init__(
        self,
        client_id: str,
        output_dir: Optional[Path] = None,
        ontology_path: Optional[Path] = None,
        transcript_parser: Optional[ITranscriptParserPort] = None,
        empirical_parser: Optional[IEmpiricalDataParserPort] = None,
        phonetic_resolver: Optional[IPhoneticResolverPort] = None,
        epistemic_synthesizer: Optional[IEpistemicSynthesizerPort] = None,
    ) -> None:
        self.client_id = client_id
        self.output_dir = output_dir or (ROOT / "working" / client_id)
        self.ontology_path = ontology_path or (
            ROOT / "engine_config" / "ontologies" / "global_tech_ontology.yaml"
        )

        self.transcript_parser: ITranscriptParserPort = (
            transcript_parser or RawTranscriptParser(ontology_path=self.ontology_path)
        )
        self.empirical_parser: IEmpiricalDataParserPort = (
            empirical_parser or EmpiricalResponseParser()
        )
        self.phonetic_resolver: IPhoneticResolverPort = (
            phonetic_resolver or PhoneticEntityResolver(ontology_path=self.ontology_path)
        )
        self.epistemic_synthesizer: IEpistemicSynthesizerPort = (
            epistemic_synthesizer or self._build_synthesizer_from_ontology()
        )

    def _build_synthesizer_from_ontology(self) -> EpistemicSynthesizer:
        if not self.ontology_path.exists():
            return EpistemicSynthesizer()
        with open(self.ontology_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        raw_tax = data.get("domain_taxonomy_rules", {})
        domain_taxonomy: Optional[Dict[str, List[str]]] = None
        if isinstance(raw_tax, dict) and raw_tax:
            domain_taxonomy = {
                dom_id: rule.get("keywords", [])
                for dom_id, rule in raw_tax.items()
                if isinstance(rule, dict) and rule.get("keywords")
            }

        polarity_cfg = data.get("polarity_cues", {})
        neg_cues = polarity_cfg.get("negative") if isinstance(polarity_cfg, dict) else None
        pos_cues = polarity_cfg.get("positive") if isinstance(polarity_cfg, dict) else None

        return EpistemicSynthesizer(
            domain_taxonomy=domain_taxonomy,
            negative_cues=neg_cues,
            positive_cues=pos_cues,
        )

    def run(
        self,
        transcript_files: List[Path],
        empirical_files: List[Path],
        runtime_context: Optional[Dict[str, Any]] = None,
        persist: bool = True,
    ) -> EpistemicLedger:
        """Executes full raw ingestion and optionally persists verified epistemic_ledger.json."""
        logger.info("Starting raw evidence ingestion for client '%s'...", self.client_id)

        # 1. Parse raw transcripts into monotonically sequenced utterances
        all_raw_utterances: List[RawUtterance] = []
        global_seq = 1
        for tf in transcript_files:
            if tf.exists():
                logger.info("Parsing transcript: %s", tf.name)
                parsed = self.transcript_parser.parse_transcript(tf)
                for u in parsed:
                    all_raw_utterances.append(
                        u.model_copy(
                            update={
                                "sequence_index": global_seq,
                                "source_file": tf.name,
                            }
                        )
                    )
                    global_seq += 1
            else:
                logger.warning("Transcript file not found: %s", tf)

        # 2. Normalize STT corruptions using dynamic ontology
        logger.info("Normalizing %d raw utterances...", len(all_raw_utterances))
        normalized_utterances = self.phonetic_resolver.normalize_batch(
            all_raw_utterances, runtime_context=runtime_context
        )

        # 3. Parse empirical data files (.xlsx, .txt, .csv)
        all_empirical_fragments = []
        for ef in empirical_files:
            if ef.exists():
                logger.info("Parsing empirical file: %s", ef.name)
                all_empirical_fragments.extend(
                    self.empirical_parser.parse_empirical_file(ef)
                )
            else:
                logger.warning("Empirical file not found: %s", ef)

        # 4. Synthesize multi-source ground truth ledger
        logger.info("Synthesizing multi-modal epistemic ledger...")
        ledger = self.epistemic_synthesizer.synthesize_ledger(
            client_id=self.client_id,
            normalized_utterances=normalized_utterances,
            empirical_fragments=all_empirical_fragments,
            runtime_context=runtime_context,
        )

        # 5. Persist to working directory if enabled
        if persist:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            ledger_path = self.output_dir / "epistemic_ledger.json"
            ledger_path.write_text(
                ledger.model_dump_json(indent=2),
                encoding="utf-8",
            )
            logger.info("Epistemic ledger persisted at: %s", ledger_path)

        return ledger
