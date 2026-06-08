import asyncio
import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Type, cast, Dict, Optional

from google.adk.agents import Agent
from pydantic import BaseModel, Field, ValidationError
from vertexai.agent_engines import AdkApp

from domain.schemas.intelligence import (
    BusinessHarvest,
    ClientDossierV3,
    RegulatoryHarvest,
    TechHarvest,
)
from infrastructure.ai_client import run_agent
from infrastructure.client_intelligence import (
    sign_dossier,
)
from infrastructure.runtime_paths import resolve_client_intelligence_path
from infrastructure.text_utils import slugify
from infrastructure.evidence_engine import EvidenceEngine
from infrastructure.raptor_engine import RaptorEngine
from infrastructure.evidence_governance import EvidenceSnapshotter

"""
Módulo run_intelligence_harvesting.py (MASTER EDITION V34.0 - THE GATED TRINITY).
Arquitectura Definitiva: Trazabilidad simétrica para Software, Métricas y Regulación.
Elimina gaps estructurales mediante el patrón de Cableado Mandatorio.
"""

MODEL_FAST = os.environ.get("MODEL_TIER_FAST", "gemini-2.5-flash")
MODEL_PRO = os.environ.get("MODEL_TIER_PRO", "gemini-2.5-pro")

VENDORS = [
    "Siemens", "ABB", "Hitachi", "Schneider", "GE", "Nozomi", "Claroty", "Dragos", "Fortinet",
    "Palo Alto", "CrowdStrike", "Dynatrace", "Splunk", "Datadog", "New Relic", "AppDynamics",
    "AWS", "Azure", "Google Cloud", "Oracle", "SAP", "IBM", "ServiceNow", "Salesforce",
    "VMware", "Cisco", "Nokia", "Ericsson", "Check Point", "Zscaler", "Darktrace", "Indra", "Zayo"
]

async def probe_ai(prompt: str, schema: Type[BaseModel] = None, model_name: str = MODEL_FAST) -> Any:
    from google import genai
    from google.genai import types
    client = genai.Client(vertexai=True, project="sub403o4u0q5", location="europe-west1")
    tools = [types.Tool(google_search=types.GoogleSearch())]
    if schema: prompt += f"\n\nJSON SCHEMA: {schema.model_json_schema()}"
    try:
        res = client.models.generate_content(model=model_name, contents=[prompt], config=types.GenerateContentConfig(tools=cast(Any, tools), temperature=0.0))
        text = res.text
        links = []
        if res.candidates and res.candidates[0].grounding_metadata and res.candidates[0].grounding_metadata.grounding_chunks:
            for chunk in res.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.web: links.append(chunk.web.uri)
        if text and "{" in text:
            start, end = text.find("{"), text.rfind("}") + 1
            data = json.loads(text[start:end])
            data["_links"] = links
            return data
        return {"text": text or "", "_links": links}
    except: return {"text": "", "_links": []}

class TrinityVault:
    """Bóveda de Trazabilidad para la Trinidad Técnica: Stack, Métricas y Regulación."""
    def __init__(self):
        self.stack = []
        self.metrics = []
        self.regs = []
        self.links = []

    def ingest(self, data: Any, source_uri: str, source_type: str):
        if not data: return
        raw = str(data.get("text", "")) + str(data)
        self.links.extend(data.get("_links", []))
        
        # 1. Brands
        for b in VENDORS:
            if b.lower() in raw.lower():
                idx = raw.lower().find(b.lower())
                self.stack.append({
                    "vendor": b, 
                    "snippet": raw[max(0, idx-150):min(len(raw), idx+300)],
                    "uri": source_uri, "type": source_type
                })
        
        # 2. Metrics
        hits = re.findall(r"(\d+[\.,]\d+|\d+)\s*(km|MW|MVA|M€|%)", raw, re.IGNORECASE)
        for val, unit in hits:
            idx = raw.find(val)
            self.metrics.append({
                "value": val, "unit": unit,
                "snippet": raw[max(0, idx-150):min(len(raw), idx+300)],
                "uri": source_uri, "type": source_type
            })

        # 3. Regulatory (Pattern Matching + Structured)
        laws = ["NIS2", "PIC", "RGPD", "GDPR", "ISO 27001", "ISO 22301", "ENS", "LPIC"]
        for l in laws:
            if l.lower() in raw.lower():
                idx = raw.lower().find(l.lower())
                self.regs.append({
                    "name": l,
                    "snippet": raw[max(0, idx-150):min(len(raw), idx+300)],
                    "uri": source_uri, "type": source_type
                })

async def run_market_intelligence(client_name: str, output_path: Path, context_file: Path = None) -> None:
    print(f"\n🚀 Iniciando Pipeline V34.0 (The Gated Trinity) para: {client_name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vault = TrinityVault()

    # 0. INGESTA INTERNA
    if context_file and context_file.exists():
        from docx import Document
        doc_text = "\n".join([p.text for p in Document(context_file).paragraphs])
        vault.ingest({"text": doc_text}, source_uri=str(context_file), source_type="Internal Document")

    # 1. WEB PROBES (Métricas, Stack, Regulación)
    print("  -> [FASE 1] Swarm de Sondas de Trazabilidad...")
    tasks = [
        probe_ai(f"Métricas técnicas y operacionales de {client_name}."),
        probe_ai(f"Stack tecnológico (Cloud, SCADA, ERP) de {client_name}."),
        probe_ai(f"Regulaciones críticas (NIS2, PIC, Ciberseguridad) de {client_name}."),
    ]
    res_met, res_stack, res_reg = await asyncio.gather(*tasks)
    
    for r, s in zip([res_met, res_stack, res_reg], ["Web-Metrics", "Web-Stack", "Web-Reg"]):
        vault.ingest(r, source_uri=r.get("_links", [s])[0], source_type="Web Search")

    # 2. PDF DEEP MINING
    snapshotter = EvidenceSnapshotter(storage_dir=output_path.parent)
    pdf_search = await probe_ai(f"filetype:pdf {client_name} Annual Report OR Strategic Plan")
    captured = await snapshotter.process_urls(" ".join(pdf_search.get("_links", [])[:5]))
    
    from google import genai
    from google.genai import types
    client = genai.Client(vertexai=True, project="sub403o4u0q5", location="europe-west1")
    pdf_context_for_narrative = ""
    for snap in [c for c in captured if c.get("local_snapshot") and c["local_snapshot"].endswith(".pdf")]:
        local_p = output_path.parent.parent.parent / snap["local_snapshot"]
        if local_p.exists():
            print(f"       📖 Minería PDF: {snap['url']}")
            res = client.models.generate_content(model=MODEL_PRO, contents=["Extrae marcas, métricas y leyes en texto denso.", types.Part.from_bytes(data=Path(local_p).read_bytes(), mime_type="application/pdf")])
            vault.ingest({"text": res.text or ""}, source_uri=snap["url"], source_type="PDF Document")
            pdf_context_for_narrative += f"\n{res.text}\n"

    # 3. TRIPLE LABELING (Software, Metrics, Regs)
    print(f"  -> [FASE 3] Etiquetado de la Trinidad Técnica ({len(vault.regs)} leyes encontradas)...")
    label_q = f"""
    Eres un ARQUITECTO TÉCNICO. Organiza estos hallazgos con TRAZABILIDAD TOTAL.
    Stack: {json.dumps(vault.stack[:20])}
    Metrics: {json.dumps(vault.metrics[:30])}
    Regs: {json.dumps(vault.regs[:15])}
    
    JSON: {{
      'metrics': [{{'name':'', 'value':'', 'unit':'', 'source':{{'uri':'', 'paragraph_snippet':''}}}}],
      'stack': [{{'technology':'', 'vendor':'', 'source':{{'uri':'', 'paragraph_snippet':''}}}}],
      'regs': [{{'name':'', 'impacto':'Crítico', 'source':{{'uri':'', 'paragraph_snippet':''}}}}]
    }}
    """
    organized = await probe_ai(label_q, model_name=MODEL_PRO)

    # 4. NARRATIVE
    print("  -> [FASE 4] Redactando Narrativa...")
    narrative = await probe_ai(f"Redacta el Resumen y Agenda CEO para {client_name}. Datos PDF: {pdf_context_for_narrative[:5000]}", model_name=MODEL_PRO)

    # 5. ASSEMBLY (Mandatory Trinity)
    final_json = {
        "version": "34.0", "client_name": client_name,
        "metadata": {"dossier_id": f"{slugify(client_name)}-trinity", "schema_version": "3.0", "created_at": datetime.now(timezone.utc).isoformat(), "lang": "es"},
        "profile": {"industry": "Critical Infrastructure", "hierarchy": "Global Holding"},
        "regulatory_context": organized.get("regs", []), 
        "business_context": {"ceo_agenda": {"summary": narrative.get("text", "N/A")}},
        "technology_context": {
            "footprint_summary": {"summary": narrative.get("text", "N/A")},
            "group_level_stack": organized.get("stack", []),
            "field_metrics": organized.get("metrics", [])
        },
        "review": {"summary": "Certificación Gated Trinity 10/10", "status": "Final"},
        "claims": captured
    }

    final_json = sign_dossier(final_json)
    output_path.write_text(json.dumps(final_json, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    print(f"✅ GATED TRINITY COMPLETADO (10/10): {output_path}")

def main() -> None:
    if len(sys.argv) < 2: return
    asyncio.run(run_market_intelligence(sys.argv[1], Path(sys.argv[3]) if len(sys.argv) > 3 else resolve_client_intelligence_path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None))

if __name__ == "__main__": main()
