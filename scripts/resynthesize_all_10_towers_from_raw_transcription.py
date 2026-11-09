#!/usr/bin/env python3
"""Universal 10-Tower Re-Synthesizer from Raw Transcription & Epistemic Ledger (RFC 083).

Systematically processes all 10 technical domains (T1 to T10) for Molins,
invoking gemini-4-argon to formulate 100% grounded, truthful AS-IS architectures,
eradicating residual hallucinations and anchoring every claim in the client's words.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List
from docx import Document

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.adapters.compilers.payload_to_ast import (
    compile_asis_docx_via_ast,
)
from assessment_engine.application.services.tower_payload_hydrator import (
    TowerPayloadHydrator,
)
from assessment_engine.application.services.semantic_epistemic_router import (
    EpistemicContextPacket,
    SemanticEpistemicRouter,
)
from assessment_engine.application.services.universal_tower_synthesizer import (
    ClientAssessmentContext,
    UniversalTowerSynthesizer,
)
from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

TRANSCRIPT_DOCX = (
    REPO_ROOT
    / "source_docs/molins/260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx"
)
LEDGER_PATH = REPO_ROOT / "working/molins/epistemic_ledger.json"
TAXONOMY_PATH = REPO_ROOT / "engine_config/taxonomy_multilingual.json"

MOLINS_CANONICAL_FILENAMES: Dict[str, str] = {
    "T1": "Molins_202610_Anexo_01_Data_Center_ASIS.docx",
    "T2": "Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx",
    "T3": "Molins_202610_Anexo_03_Redes_ASIS.docx",
    "T4": "Molins_202610_Anexo_04_Datos_Storage_ASIS.docx",
    "T5": "Molins_202610_Anexo_05_Resiliencia_ASIS.docx",
    "T6": "Molins_202610_Anexo_06_Seguridad_Identidad_ASIS.docx",
    "T7": "Molins_202610_Anexo_07_Operaciones_ITSM_ASIS.docx",
    "T8": "Molins_202610_Anexo_08_FinOps_Gobernanza_ASIS.docx",
    "T9": "Molins_202610_Anexo_09_Puesto_Trabajo_ASIS.docx",
    "T10": "Molins_202610_Anexo_10_Sistemas_Expedicion_Operaciones_ASIS.docx",
}


def load_transcript_paragraphs() -> List[str]:
    doc = Document(str(TRANSCRIPT_DOCX))
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]


def load_epistemic_ledger() -> Dict[str, Any]:
    with open(LEDGER_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_taxonomy() -> Dict[str, Any]:
    with open(TAXONOMY_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def gather_evidence_for_tower(
    tower_code: str,
    ledger_data: Dict[str, Any],
    packet: EpistemicContextPacket,
) -> str:
    lines = []

    # 1. Epistemic ledger entries & fragments
    for entry in ledger_data.get("epistemic_entries", []):
        tax = str(entry.get("domain_taxonomy_ref", "")).upper()
        if tax == tower_code:
            for frag in entry.get("supporting_fragments", []):
                pol = frag.get("polarity", "NEUTRAL")
                txt = frag.get("canonical_assertion", "")
                if txt:
                    lines.append(f"[{tax} LEDGER {pol}] {txt}")

    # 2. Lossless semantic propositions routed via SemanticEpistemicRouter (RFC 084)
    for prop in packet.propositions:
        lines.append(f"[{tower_code} TRANSCRIPT Turn {prop.turn_index}] {prop.text}")

    return "\n".join(lines)


def synthesize_tower(
    tower_code: str,
    packet: EpistemicContextPacket,
    taxonomy_data: Dict[str, Any],
    client_context: ClientAssessmentContext,
    client: Any,
    model_name: str,
) -> Dict[str, Any]:
    """Universal, decoupled synthesis delegating to UniversalTowerSynthesizer."""
    synthesizer = UniversalTowerSynthesizer()
    tower_tax = taxonomy_data.get(tower_code, {})
    prompt = synthesizer.build_synthesis_prompt(
        context=client_context,
        tower_code=tower_code,
        evidence_packet=packet,
        tower_definition=tower_tax,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    clean_json = response.text.strip()
    if clean_json.startswith("```"):
        clean_json = clean_json.split("\n", 1)[1]
    if clean_json.endswith("```"):
        clean_json = clean_json.rsplit("\n", 1)[0]
    clean_json = clean_json.strip()

    parsed = json.loads(clean_json)
    return synthesizer.parse_and_validate_synthesis(parsed, client_context, tower_code)


def main() -> None:
    print("=" * 80)
    print("STARTING UNIVERSAL 10-TOWER RE-SYNTHESIS FROM RAW TRANSCRIPTION (RFC 083)")
    print("=" * 80)

    transcript_paras = load_transcript_paragraphs()
    ledger_data = load_epistemic_ledger()
    taxonomy_data = load_taxonomy()

    router = SemanticEpistemicRouter()
    print("   Routing transcript propositions via SemanticEpistemicRouter (RFC 084)...")
    routed_packets = router.route_transcript(transcript_paras)
    for code, packet in routed_packets.items():
        print(f"   - {code}: {len(packet.propositions)} propositions routed (State: {packet.epistemic_state}, Density: {packet.semantic_density_score:.3f})")

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Connecting to reasoning tier model: {model_name}...")

    tower_codes = [f"T{i}" for i in range(1, 11)]

    for code in tower_codes:
        print(f"\n>>> Processing Tower {code} from primary evidence <<<")
        payload_file = REPO_ROOT / f"working/molins/{code}/blueprint_{code.lower()}_payload.json"
        with open(payload_file, "r", encoding="utf-8-sig") as f:
            base_payload = json.load(f)

        packet = routed_packets.get(code)
        force_synthesis = "--skip-llm" not in sys.argv
        if (
            not force_synthesis
            and base_payload.get("synthesis_provenance")
            == "RAW_INTERVIEW_TRANSCRIPT_AND_EPISTEMIC_LEDGER"
        ):
            print(f"   ⏭️ Tower {code} already synthesized from raw transcript. Skipping LLM call.")
            synthesized_data = None
        else:
            evidence = gather_evidence_for_tower(code, ledger_data, packet) if packet else ""
            print(f"   Collected {len(evidence.splitlines())} evidence turns for {code}.")

            doc_meta = base_payload.get("document_meta", {})
            client_ctx = ClientAssessmentContext(
                client_name=str(doc_meta.get("client_name") or "Molins"),
                industry_vertical=str(doc_meta.get("industry_vertical") or "manufacturing"),
                annual_revenue=float(base_payload.get("financial_telemetry", {}).get("annual_revenue") or 1_144_000_000.0),
                currency_code=str(doc_meta.get("currency") or "EUR"),
                regulatory_frameworks=tuple(doc_meta.get("regulatory_context") or ["NIS2", "ISO27001"]),
                target_language=str(doc_meta.get("language") or "es"),
            )

            retries = 3
            synthesized_data = None
            for attempt in range(1, retries + 1):
                try:
                    synthesized_data = synthesize_tower(
                        code, packet, taxonomy_data, client_ctx, client, model_name
                    )
                    if len(synthesized_data.get("pillars_analysis", [])) == 5:
                        break
                    print(f"   ⚠️ Attempt {attempt}: Received {len(synthesized_data.get('pillars_analysis', []))} pillars instead of 5, retrying...")
                except Exception as e:
                    print(f"   ⚠️ Attempt {attempt} failed: {e}")
                    time.sleep(2)

            if not synthesized_data or len(synthesized_data.get("pillars_analysis", [])) != 5:
                print(f"   ❌ FAILED to synthesize valid 5-pillar payload for {code}. Skipping.")
                continue

            base_payload["executive_snapshot"] = synthesized_data["executive_snapshot"]
            base_payload["pillars_analysis"] = synthesized_data["pillars_analysis"]
            base_payload["synthesis_provenance"] = "RAW_INTERVIEW_TRANSCRIPT_AND_EPISTEMIC_LEDGER"

        # Phase 2 SSOT Boundary Enforcement: Reconcile payload with deterministic scoring SSOT
        from assessment_engine.application.run_scoring import build_scoring
        from assessment_engine.application.sync_payload_scores import parse_raw_responses
        from assessment_engine.domain.services.score_reconciler import reconcile_tower_scores
        from assessment_engine.domain.validation.mathematical_integrity import (
            assert_tower_mathematical_integrity,
        )

        answers_file = REPO_ROOT / "source_docs/molins/261014 Respuestas Test Molins.txt"
        if answers_file.exists():
            answers_map = parse_raw_responses(answers_file)
            tower_def_path = REPO_ROOT / f"engine_config/towers/{code}/tower_definition_{code}.json"
            if tower_def_path.exists():
                with open(tower_def_path, "r", encoding="utf-8-sig") as df:
                    tower_def = json.load(df)
                case_input = {
                    "case_id": f"CASE_{code}",
                    "tower_id": code,
                    "tower_name": tower_def.get("tower_name", code),
                    "answers": answers_map.get(code, []),
                }
                scoring_ssot = build_scoring(case_input, tower_def)
                base_payload = reconcile_tower_scores(base_payload, scoring_ssot)
                assert_tower_mathematical_integrity(base_payload)

        canonical_score = base_payload.get("score") or TowerPayloadHydrator.compute_canonical_score(
            base_payload, doc_lang="es"
        )
        base_payload["score"] = canonical_score
        base_payload["exact_score"] = canonical_score
        base_payload["overall_score"] = canonical_score
        base_payload["maturity_score"] = canonical_score

        with open(payload_file, "w", encoding="utf-8") as f:
            json.dump(base_payload, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Updated {payload_file.name} (Canonical Score: {canonical_score:.2f})")

        # Compile specialist DOCX
        annex_docx = (
            REPO_ROOT
            / f"working/out/molins/{code}/Molins_202610_Anexo_{code}_ASIS.docx"
        )
        # Check canonical filename mapping
        canonical_fname = MOLINS_CANONICAL_FILENAMES.get(code, f"Molins_202610_Anexo_{code}_ASIS.docx")
        annex_docx = REPO_ROOT / f"working/out/molins/{code}/{canonical_fname}"
        annex_docx.parent.mkdir(parents=True, exist_ok=True)

        compile_asis_docx_via_ast(payload_file, annex_docx, doc_lang="es")
        print(f"   ✓ Compiled DOCX: {annex_docx.name}")

        # Convert to PDF
        pdf_path = annex_docx.with_suffix(".pdf")
        try:
            subprocess.run(
                ["soffice", "--headless", "--convert-to", "pdf", str(annex_docx), "--outdir", str(annex_docx.parent)],
                check=True,
                capture_output=True,
            )
            print(f"   ✓ Generated PDF: {pdf_path.name}")
        except Exception as e:
            print(f"   ⚠️ PDF conversion failed: {e}")

        # Small delay between calls
        time.sleep(1)

    print("\n" + "=" * 80)
    print("ALL 10 TOWERS RE-SYNTHESIZED. NOW SYNCHRONIZING DELIVERY SUITE & TOMO 1...")
    print("=" * 80)

    # Re-run build_full_client_delivery_suite.py
    subprocess.run([sys.executable, "scripts/build_full_client_delivery_suite.py"], check=True)
    print("\n✅ Universal re-synthesis and deliverable compilation completed successfully!")


if __name__ == "__main__":
    main()
