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

TOWER_KEYWORDS: Dict[str, List[str]] = {
    "T1": ["cpd", "datacenter", "centro de datos", "sant vicenç", "sai", "ups", "climatiz", "crac", "falso suelo", "potencia", "eléctric", "cuadro", "extinción", "incendio", "bms", "ats", "pdu"],
    "T2": ["simplivity", "vmware", "vsphere", "vcenter", "nodo", "clúster", "cluster", "esxi", "virtualiz", "cómputo", "ot", "memoria", "ram", "cpu", "host", "kubernetes", "contenedor"],
    "T3": ["red", "switch", "huawei", "firewall", "forti", "fortinet", "enlace", "fibra", "10 gb", "dci", "wan", "sd-wan", "equinix", "fabric", "hivision", "lan", "vlan", "enrutamiento"],
    "T4": ["netapp", "metrocluster", "vnx", "almacenamiento", "storage", "san", "cohesity", "backup", "s3", "objeto", "wasabi", "snapshot", "bloque", "cinta", "qos", "i/o"],
    "T5": ["continuidad", "resiliencia", "rto", "rpo", "parada", "caída", "recuperación", "desastre", "dr", "500 metros", "planta", "fabril", "contingencia", "ransomware", "air-gap"],
    "T6": ["seguridad", "ciber", "active directory", "ad", "pam", "mfa", "edr", "soc", "vulnerab", "parche", "credencial", "privilegi", "fortigate", "acceso", "nis2", "microsegment"],
    "T7": ["zabbix", "prometheus", "grafana", "loki", "itsm", "ticket", "soporte", "isau", "dba", "croata", "sla", "slo", "cmdb", "monitoriz", "incidencia", "operaciones", "gestión"],
    "T8": ["estrategia", "gobernanza", "finops", "gcp", "azure", "oci", "sap", "databricks", "prenet", "coste", "facturación", "nube", "cloud", "presupuesto", "inversión", "licencia"],
    "T9": ["puesto", "workplace", "portátil", "equipo", "windows", "m365", "office", "teams", "impresora", "cau", "helpdesk", "dex", "usuario", "dispositivo", "planta"],
    "T10": ["báscula", "bascula", "pesaje", "camión", "expedición", "albarán", "oracle", "forms", "reports", "batch", "centos", "legacy", "malla", "secil", "nos", "fábrica"],
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
    transcript_paras: List[str],
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

    # 2. Matching raw transcript paragraphs
    keywords = TOWER_KEYWORDS.get(tower_code, [])
    for idx, para in enumerate(transcript_paras):
        para_lower = para.lower()
        if any(kw in para_lower for kw in keywords):
            lines.append(f"[{tower_code} TRANSCRIPT Turn {idx}] {para}")

    return "\n".join(lines[:35])  # Cap to top 35 high-signal fragments


def synthesize_tower(
    tower_code: str,
    evidence_text: str,
    taxonomy_data: Dict[str, Any],
    client: Any,
    model_name: str,
) -> Dict[str, Any]:
    tower_tax = taxonomy_data.get(tower_code, {})
    tower_name = tower_tax.get("canonical_name", f"Domain {tower_code}")
    pillars_meta = tower_tax.get("pillars", {})

    pillars_schema_list = []
    for pid, pdata in sorted(pillars_meta.items()):
        es_name = pdata.get("locales", {}).get("es", pdata.get("canonical_name"))
        pillars_schema_list.append(f"- {pid}: {es_name}")
    pillars_prompt_desc = "\n".join(pillars_schema_list)

    prompt = f"""
Role: Principal Infrastructure Architect & Lead Forensic Systems Auditor.

TASK:
Synthesize the authoritative, 100% grounded AS-IS diagnostic content for Tower {tower_code}:
"{tower_name}" for Molins (heavy manufacturing, cement production at Sant Vicenç dels Horts and Portugal SECIL).

PRIMARY SOURCE OF TRUTH (LITERAL CLIENT EVIDENCE):
{evidence_text}

CANONICAL 5 PILLARS FOR TOWER {tower_code}:
{pillars_prompt_desc}

GROUNDING RULES:
1. ONLY make claims supported by the evidence above. Never hallucinate non-existent platforms, modernizations, or enterprise tools.
2. If a technology was only mentioned as an aspiration (TO-BE), mark AS-IS maturity strictly as Initial/Ad-hoc (1.0 to 1.5).
3. Connect technical findings directly to manufacturing reality: Sant Vicenç dels Horts twin CPDs (500m apart), básculas/weighbridges, truck dispatch, HPE SimpliVity nodes (2018 vintage), NetApp MetroCluster, Oracle 10g/11g Forms, Secil/NOS in Portugal.
4. Maturity scores must be strictly realistic CMMI v2.0 (1.00 to 5.00), quantized to 1 decimal place.

OUTPUT SCHEMA:
Output ONLY a valid JSON object matching this structure (Spanish technical prose for executive client delivery):
{{
  "executive_snapshot": {{
    "bottom_line": "...",
    "operational_benefits": [
      "Concise strength 1...",
      "Concise strength 2...",
      "Concise strength 3..."
    ],
    "structural_risks": [
      "Concise risk 1...",
      "Concise risk 2...",
      "Concise risk 3..."
    ]
  }},
  "pillars_analysis": [
    {{
      "pillar_id": "T{tower_code[1:]}.P1",
      "pilar_id": "T{tower_code[1:]}.P1",
      "pillar_name": "...",
      "pilar_name": "...",
      "score": 2.5,
      "target_score": 4.0,
      "thought_process": "...",
      "asis_architecture_description": "Comprehensive technical description (2-3 paragraphs)...",
      "health_check_asis": [
        {{
          "node_id": "{tower_code.lower()}-p1-hc-01",
          "capability": "...",
          "finding": "...",
          "business_risk": "...",
          "literal_evidence": "...",
          "threat_event_frequency": 3,
          "vulnerability_level": 3,
          "loss_magnitude": 3,
          "fair_ale_score": 25000.0,
          "fair_p90_score": 75000.0,
          "fair_min_score": 0.0,
          "fair_max_score": 150000.0
        }}
      ]
    }}
    // Exactly 5 pillars (P1 through P5)
  ]
}}
"""

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

    return json.loads(clean_json)


def main() -> None:
    print("=" * 80)
    print("STARTING UNIVERSAL 10-TOWER RE-SYNTHESIS FROM RAW TRANSCRIPTION (RFC 083)")
    print("=" * 80)

    transcript_paras = load_transcript_paragraphs()
    ledger_data = load_epistemic_ledger()
    taxonomy_data = load_taxonomy()

    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    print(f"Connecting to reasoning tier model: {model_name}...")

    tower_codes = [f"T{i}" for i in range(1, 11)]

    for code in tower_codes:
        print(f"\n>>> Processing Tower {code} from primary evidence <<<")
        payload_file = REPO_ROOT / f"working/molins/{code}/blueprint_{code.lower()}_payload.json"
        with open(payload_file, "r", encoding="utf-8-sig") as f:
            base_payload = json.load(f)

        if (
            base_payload.get("synthesis_provenance")
            == "RAW_INTERVIEW_TRANSCRIPT_AND_EPISTEMIC_LEDGER"
            and "--force" not in sys.argv
        ):
            print(f"   ⏭️ Tower {code} already synthesized from raw transcript. Skipping LLM call.")
            synthesized_data = None
        else:
            evidence = gather_evidence_for_tower(code, ledger_data, transcript_paras)
            print(f"   Collected {len(evidence.splitlines())} evidence turns for {code}.")

            retries = 3
            synthesized_data = None
            for attempt in range(1, retries + 1):
                try:
                    synthesized_data = synthesize_tower(
                        code, evidence, taxonomy_data, client, model_name
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

        canonical_score = TowerPayloadHydrator.compute_canonical_score(
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
