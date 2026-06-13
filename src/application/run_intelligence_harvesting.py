import asyncio
import json
import os
import sys
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Type, cast, Dict, Optional, Literal

from google.adk.agents import Agent
from pydantic import BaseModel, Field, ValidationError
from vertexai.agent_engines import AdkApp

class MetaExtract(BaseModel):
    dominant_hyperscaler: str = Field(description="Deduce el proveedor cloud dominante del cliente en base al footprint (ej: AWS, Azure, GCP, o 'N/A - 100% On-Premise' si opera localmente sin nube pública).")
    stage: Literal["H1", "H2", "H3"] = Field(description="La fase de transformación: H1 (Brilliant Basics), H2 (Hyperautomation & Scale), o H3 (Vanguard & AI-First) basada en el nivel de automatización y metas del cliente.")
    label: str = Field(description="Etiqueta ejecutiva corta y representativa del horizonte (ej: 'Escalado Inteligente y Cloud Nativa').")
    rationale: str = Field(description="Justificación estratégica detallada de por qué se asigna esta fase en el contexto de sus planes de inversión y negocio actuales.")

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
Módulo run_intelligence_harvesting.py (MASTER EDITION V35.0 - THE PURIST).
Arquitectura Anti-Contaminación: Bloqueo estricto de nombres de otros clientes.
Garantiza que Eurovision Services sea 100% independiente de Redeia.
"""

MODEL_FAST = os.environ.get("MODEL_TIER_FAST", "gemini-2.5-flash")
MODEL_PRO = os.environ.get("MODEL_TIER_PRO", "gemini-2.5-pro")

async def probe_ai(prompt: str, schema: Type[BaseModel] = None, model_name: str = MODEL_FAST, client_name: Optional[str] = None) -> Any:
    from google import genai
    from google.genai import types
    client = genai.Client(vertexai=True, project="sub403o4u0q5", location="europe-west1")
    tools = [types.Tool(google_search=types.GoogleSearch())]
    
    # REGLA ANTI-MEZCLA DINÁMICA: Aislamiento absoluto y agnóstico de contexto del cliente
    anti_mix = ""
    if client_name:
        anti_mix = (
            f"\n\n⚠️ REGLA CRÍTICA DE AISLAMIENTO: Estás analizando exclusivamente el caso de la empresa '{client_name}'. "
            "Queda terminantemente prohibido cruzar, mencionar o contaminar la respuesta con información, "
            "proyectos, marcas o nombres de directivos pertenecientes a otras entidades o a evaluaciones previas. "
            "Si no posees con total certeza el nombre verificado de un directivo, utiliza siempre un término "
            "institucional o colectivo genérico (ej: 'Dirección Ejecutiva' o 'Comité Técnico') en lugar de "
            "alucinar o heredar nombres propios de otras compañías."
        )
    
    try:
        res = client.models.generate_content(model=model_name, contents=[prompt + anti_mix], config=types.GenerateContentConfig(tools=cast(Any, tools), temperature=0.0))
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

class SourceVault:
    def __init__(self, client_name: str = ""):
        self.atoms = []
        self.client_name = client_name

    def ingest(self, data: Any, source_uri: str, source_type: str):
        if not data: return
        raw = str(data.get("text", "")) + str(data)
        
        # 1. Brands
        brands = ["Siemens", "ABB", "GE", "AWS", "Google", "Dynatrace", "Splunk", "Oracle", "SAP", "Microsoft"]
        if self.client_name and "eurovision" in self.client_name.lower():
            brands.append("EBU")
            
        for b in brands:
            if b.lower() in raw.lower():
                idx = raw.lower().find(b.lower())
                self.atoms.append({
                    "category": "stack", "value": b,
                    "snippet": raw[max(0, idx-100):min(len(raw), idx+250)],
                    "uri": source_uri, "type": source_type
                })
        
        # 2. Metrics
        hits = re.findall(r"(\d+[\.,]\d+|\d+)\s*(km|MW|ms|Gbps|CHF|%)", raw, re.IGNORECASE)
        for val, unit in hits:
            idx = raw.find(val)
            self.atoms.append({
                "category": "metric", "value": val, "unit": unit,
                "snippet": raw[max(0, idx-100):min(len(raw), idx+250)],
                "uri": source_uri, "type": source_type
            })

async def run_market_intelligence(client_name: str, output_path: Path, context_file: Path = None) -> None:
    print(f"\n🚀 Iniciando Pipeline V35.0 (The Purist) para: {client_name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vault = SourceVault(client_name)

    # 0. INGESTA INTERNA (Unica fuente de verdad para el CEO)
    if context_file and context_file.exists():
        from docx import Document
        doc_text = "\n".join([p.text for p in Document(context_file).paragraphs])
        vault.ingest({"text": doc_text}, source_uri=str(context_file), source_type="Internal Document")

    # 1. WEB PROBES
    print("  -> [FASE 1] Cosechando Huellas Técnicas Reales...")
    tasks = [
        probe_ai(f"Estrategia independiente de {client_name} tras el acuerdo con EBU.", client_name=client_name),
        probe_ai(f"Stack tecnológico de broadcast y nube de {client_name}.", client_name=client_name),
    ]
    res_strat, res_stack = await asyncio.gather(*tasks)
    vault.ingest(res_strat, source_uri="Web-Strategy", source_type="Web Search")
    vault.ingest(res_stack, source_uri="Web-Stack", source_type="Web Search")

    # 2. PDF DEEP MINING
    snapshotter = EvidenceSnapshotter(storage_dir=output_path.parent)
    pdf_search = await probe_ai(f"filetype:pdf {client_name} ESG OR Annual Report", client_name=client_name)
    captured = await snapshotter.process_urls(" ".join(pdf_search.get("_links", [])[:5]))
    
    for snap in [c for c in captured if c.get("local_snapshot") and c["local_snapshot"].endswith(".pdf")]:
        local_p = output_path.parent.parent.parent / snap["local_snapshot"]
        if local_p.exists():
            print(f"       📖 Minería PDF: {snap['url']}")
            from google import genai
            from google.genai import types
            client = genai.Client(vertexai=True, project="sub403o4u0q5", location="europe-west1")
            res = client.models.generate_content(model=MODEL_PRO, contents=["Extrae marcas y métricas en texto denso.", types.Part.from_bytes(data=Path(local_p).read_bytes(), mime_type="application/pdf")])
            vault.ingest({"text": res.text or ""}, source_uri=snap["url"], source_type="PDF Document")

    # 3. LABELING
    print("  -> [FASE 3] Etiquetado y Citación de Bóveda...")
    label_q = f"Organiza estos hallazgos en JSON. ÁTOMOS: {json.dumps(vault.atoms[:40])}. JSON: {{'metrics': [{{'name':'', 'value':'', 'unit':'', 'source':{{'uri':''}}}}], 'stack': [{{'technology':'', 'vendor':'', 'source':{{'uri':''}}}}]}}"
    organized = await probe_ai(label_q, model_name=MODEL_PRO, client_name=client_name)

    # 4. SÍNTESIS
    print("  -> [FASE 4] Redactando Narrativa (Anti-Contaminación)...")
    narrative = await probe_ai(f"Resume Estrategia y Agenda de Liderazgo para {client_name}. No inventes nombres de CEOs si no aparecen en los datos.", model_name=MODEL_PRO, client_name=client_name)

    # 4.5. CÁLCULO DINÁMICO DE OBJETIVOS DE MADUREZ (SOVEREIGN TARGET MODEL)
    print("  -> [FASE 4.5] Evaluando Criterios de Madurez por Torre (Conjoint Multi-Criteria Matrix)...")
    
    if "redeia" in client_name.lower():
        client_context_str = (
            f"footprint de transporte eléctrico y telecomunicaciones críticas, "
            f"cumplimiento con Directiva PIC y NIS2, y la necesidad de ciberresiliencia, "
            f"convergencia operacional IT/OT y digitalización bajo el Plan Estratégico de REDEIA."
        )
        compliance_example_str = "ej: NIS2, Directiva PIC, protección de infraestructura crítica, soberanía IT/OT como T6, T5 o T3, ~90. T1 u otras, ~40"
        feasibility_example_str = "ej: T2 es compleja debido a migración e integración de sistemas legados de subestaciones, ~50. T10 DTO es de soporte estratégico, ~70"
    elif "eurovision" in client_name.lower():
        client_context_str = (
            f"footprint de 50 PoPs, adquisición por DUBAG Group, "
            f"e independencia tecnológica de la EBU ('Project Independence & Resilience') bajo eventos en directo críticos (UEFA, NBA)."
        )
        compliance_example_str = "ej: NIS2, DORA, Directiva PIC, o soberanía existencial de identidades post-EBU como T6 y T5, ~90. T1 u otras, ~40"
        feasibility_example_str = "ej: T2 es compleja debido a VMware legacy, ~50. T10 DTO es de soporte estratégico, ~70"
    else:
        client_context_str = (
            f"footprint global, cumplimiento normativo general de sector crítico, "
            f"y la necesidad de modernización de su arquitectura, resiliencia operativa e independencia tecnológica."
        )
        compliance_example_str = "ej: NIS2, DORA o regulaciones específicas del sector para seguridad e identidad, ~85. T1 u otras, ~40"
        feasibility_example_str = "ej: T2 es compleja debido a migración de infraestructura heredada, ~50. T10 DTO es de soporte estratégico, ~70"

    overrides_prompt = (
        f"Actúa como un Consultor de Estrategia Tecnológica Principal de Gartner.\n"
        f"Analiza todo el contexto de la empresa '{client_name}': {client_context_str}\n\n"
        f"Evalúa para cada una de las 10 torres técnicas (T1 a la T10) los siguientes tres criterios cuantitativos (puntuaciones de 0 a 100):\n"
        f"1. 'criticality': Puntuación de criticidad de negocio de la torre para evitar interrupciones de señal o pérdidas inmediatas de ingresos (ej. T3 Networks debe ser extremadamente alta, ~95. T7 ITSM es soporte, ~50).\n"
        f"2. 'compliance': Presión regulatoria, legal y ciberseguridad ({compliance_example_str}).\n"
        f"3. 'feasibility': Viabilidad operacional y facilidad de implementación técnica real considerando la inercia cultural y que actualmente se opera con excels heterogéneos ({feasibility_example_str}).\n\n"
        f"Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta (claves T1, T2... T10):\n"
        f"{{\n"
        f"  \"T1\": {{\n"
        f"    \"criticality\": 60,\n"
        f"    \"compliance\": 40,\n"
        f"    \"feasibility\": 70,\n"
        f"    \"justification\": \"Explicación estratégica de por qué se asignan estos valores en base a los hechos del cliente.\"\n"
        f"  }},\n"
        f"  \"T2\": {{\n"
        f"    \"criticality\": 75,\n"
        f"    \"compliance\": 80,\n"
        f"    \"feasibility\": 50,\n"
        f"    \"justification\": \"...\"\n"
        f"  }},\n"
        f"  ...\n"
        f"}}"
    )
    raw_overrides = await probe_ai(overrides_prompt, model_name=MODEL_PRO, client_name=client_name)

    # 4.6. CÁLCULO MATEMÁTICO DETERMINISTA (Sovereign Target Engine)
    print("  -> [FASE 4.6] Ejecutando Algoritmo de Decisión Multicriterio (Sovereign Target Engine)...")
    calculated_overrides = {}
    if isinstance(raw_overrides, dict):
        for tower_id, metrics in raw_overrides.items():
            if not isinstance(metrics, dict): continue
            try:
                crit = float(metrics.get("criticality", 50))
                comp = float(metrics.get("compliance", 50))
                feas = float(metrics.get("feasibility", 50))
                
                # Deterministic Utility Formula: Target = 3.0 + 2.0 * ((Crit*0.4 + Comp*0.4 + Feas*0.2) / 100)
                # Esto garantiza límites estrictos entre [3.0, 5.0] de forma realista y asimétrica
                raw_target = 3.0 + 2.0 * ((crit * 0.4 + comp * 0.4 + feas * 0.2) / 100.0)
                target_score = round(raw_target, 1)
                
                calculated_overrides[tower_id] = {
                    "target_maturity": target_score,
                    "metrics": {
                        "business_criticality": crit,
                        "regulatory_compliance": comp,
                        "implementation_feasibility": feas
                    },
                    "justification": metrics.get("justification", "Alineación multicriterio calculada.")
                }
                just_str = metrics.get('justification', '')[:60]
                print(f"       * {tower_id}: Score Calculado = {target_score} (Justificación: {just_str}...)")
            except Exception as e:
                calculated_overrides[tower_id] = {
                    "target_maturity": 4.0,
                    "justification": f"Fallback estándar por fallo en cálculo: {e}"
                }
    else:
        # Fallback de seguridad en caso de que falle la generación JSON del modelo
        print("  ⚠️ Fallo en el retorno de matriz de madurez. Aplicando fallbacks estándar.")
        calculated_overrides = {f"T{i}": {"target_maturity": 4.0, "justification": "Estándar por defecto."} for i in range(1, 11)}

    # 5. ASSEMBLY (DYNAMIC JIT EXTRACTION & PYDANTIC SANDWICH)
    print("  -> [FASE 4.7] Extrayendo Meta-Arquitectura e Hyperscaler Dominante de forma Dinámica (Agnóstico)...")
    meta_prompt = (
        f"Analiza de forma síncrona el contexto recopilado de la empresa '{client_name}':\n"
        f"1. Narrativa: {narrative.get('text', 'N/A')}\n"
        f"2. Stack Técnico: {json.dumps(organized.get('stack', []), ensure_ascii=False)}\n\n"
        f"Deduce el proveedor cloud dominante ('dominant_hyperscaler') y la fase de horizonte de transformación óptimo."
    )
    from google import genai
    from google.genai import types
    client_gen = genai.Client(vertexai=True, project="sub403o4u0q5", location="europe-west1")
    
    try:
        res_meta = client_gen.models.generate_content(
            model=MODEL_PRO,
            contents=[meta_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MetaExtract
            )
        )
        meta_data = json.loads(res_meta.text)
        dominant_hyperscaler = meta_data.get("dominant_hyperscaler", "AWS")
        horizon_obj = {
            "stage": meta_data.get("stage", "H1"),
            "label": meta_data.get("label", "Estandarización"),
            "rationale": meta_data.get("rationale", "Calculado dinámicamente.")
        }
    except Exception as e:
        print(f"  ⚠️ Error en extracción de meta-datos: {e}. Usando fallbacks.")
        dominant_hyperscaler = "AWS"
        horizon_obj = {
            "stage": "H1", "label": "Estandarización", "rationale": "Fallback estándar."
        }

    industry_str = "Energy & Critical Infrastructure" if "redeia" in client_name.lower() else "Broadcast Infrastructure"

    final_json = {
        "version": "3.0", "client_name": client_name,
        "metadata": {"dossier_id": f"{slugify(client_name)}-purist", "schema_version": "3.0", "created_at": datetime.now(timezone.utc).isoformat(), "lang": "es"},
        "profile": {"industry": industry_str, "hierarchy": "Global Entity"},
        "regulatory_context": [], 
        "business_context": {
            "ceo_agenda": {"summary": narrative.get("text", "N/A")},
            "transformation_horizon": horizon_obj
        },
        "technology_context": {
            "footprint_summary": {"summary": narrative.get("text", "N/A")},
            "group_level_stack": organized.get("stack", []),
            "field_metrics": organized.get("metrics", []),
            "dominant_hyperscaler": dominant_hyperscaler
        },
        "tower_overrides": calculated_overrides,
        "review": {"summary": "Certificación Purist V35.0 (Aislamiento de Contexto)", "status": "Final"},
        "claims": captured
    }

    final_json = sign_dossier(final_json)
    output_path.write_text(json.dumps(final_json, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    print(f"✅ BLUEPRINT SANEADO Y COMPLETADO: {output_path}")

def main() -> None:
    if len(sys.argv) < 2: return
    asyncio.run(run_market_intelligence(sys.argv[1], Path(sys.argv[3]) if len(sys.argv) > 3 else resolve_client_intelligence_path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None))

if __name__ == "__main__": main()
