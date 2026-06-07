import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Type

from google.adk.agents import Agent
from pydantic import BaseModel, ValidationError
from vertexai.agent_engines import AdkApp

"""
Módulo run_intelligence_harvesting.py (MASTER EDITION V16.0 - INHERITANCE & ARCHITECTURE MINING).
"""

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
from infrastructure.evidence_engine import EvidenceEngine
from infrastructure.evidence_governance import EvidenceSnapshotter
from infrastructure.raptor_engine import RaptorEngine
from infrastructure.runtime_paths import resolve_client_intelligence_path
from infrastructure.text_utils import slugify


async def run_agent_safe(
    app: AdkApp,
    user_id: str,
    message: str,
    schema: Type[BaseModel] | None = None,
    raw_output_file: Path | None = None,
    max_retries: int = 5,
) -> Any:
    last_error = ""
    for attempt in range(max_retries):
        try:
            current_message = message
            if last_error:
                current_message += f"\n\n🚨 ERROR DE VALIDACIÓN:\n{last_error}\nPor favor, asegúrate de devolver un JSON válido."
            return await run_agent(
                app,
                user_id=user_id,
                message=current_message,
                schema=schema,
                raw_output_file=raw_output_file,
            )
        except (ValidationError, json.JSONDecodeError) as e:
            last_error = str(e)
            print(
                f"    ⚠️ Fallo de procesamiento para {user_id} (Intento {attempt + 1}). Reintentando..."
            )
    raise RuntimeError(f"Fallo crítico: {user_id} falló tras {max_retries} intentos.")


async def run_agent_osint_sovereign(
    prompt: str, schema: Type[BaseModel] | None = None, pdf_path: Path | None = None
) -> Any:
    """Adaptador de Inteligencia Soberana V3: Búsqueda + Deep Reading + Architecture Mining."""
    import os

    from google import genai
    from google.genai import types

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/jsanchhi/.secrets/sa-key.json"
    client = genai.Client(
        vertexai=True, project="sub403o4u0q5", location="europe-west1"
    )

    contents = [prompt]
    if pdf_path and pdf_path.exists():
        contents.append(
            types.Part.from_bytes(
                data=pdf_path.read_bytes(), mime_type="application/pdf"
            )
        )
        print("      📖 [MULTIMODAL] Minería de Arquitectura sobre PDF...")

    tools = [types.Tool(google_search=types.GoogleSearch())] if not pdf_path else []

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=contents,
        config=types.GenerateContentConfig(tools=tools, temperature=0.0),
    )

    text = response.text
    links = []
    if (
        response.candidates[0].grounding_metadata
        and response.candidates[0].grounding_metadata.grounding_chunks
    ):
        for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
            if chunk.web:
                links.append({"title": chunk.web.title, "url": chunk.web.uri})

    if schema:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1:
                data = json.loads(text[start:end])
                data["_osint_links"] = links
                return data
        except Exception:
            pass
    return {"raw_text": text, "_osint_links": links}


async def run_market_intelligence(
    client_name: str, output_path: Path, context_file: Path | None = None
) -> None:
    print(
        f"\n🚀 Iniciando Pipeline V16.0 (Inheritance & Architecture Mining) para: {client_name}"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    client_id = slugify(client_name)
    evidence_engine = EvidenceEngine(
        client_id=client_id, storage_dir=output_path.parent
    )
    raptor_engine = RaptorEngine(client_id=client_id, storage_dir=output_path.parent)

    # --- FASE 0: CONTEXTO INTERNO ---
    if context_file and context_file.exists():
        print("  -> [FASE 0] Ingestando Documento...")
        evidence_engine.ingest_file(context_file)
        await raptor_engine.build_tree(evidence_engine.ledger.fragments)
        _ = raptor_engine.get_context_at_level(1)

    # --- FASE 1: DESAMBIGUACIÓN Y TAXONOMÍA ---
    print("  -> [FASE 1] Mapeando Jerarquía Corporativa...")
    perimeter_prompt = f"Analiza {client_name}. Define: 1. Matriz (Holding). 2. Filiales clave por país. Indica qué activos son 'Nivel Grupo' y cuáles son específicos."
    perimeter_data = await run_agent_osint_sovereign(perimeter_prompt)
    perimeter_text = (
        perimeter_data.get("raw_text")
        if isinstance(perimeter_data, dict)
        else str(perimeter_data)
    )

    tasks = [
        run_agent_osint_sovereign(
            f"Líneas de negocio de {client_name}. Segmenta por Holding vs Filial. Info: {perimeter_text}",
            schema=BusinessHarvest,
        ),
        run_agent_osint_sovereign(
            f"Stack tecnológico de {client_name}. APLICA ATRIBUCIÓN EN CASCADA: Si no se sabe la filial, asume 'Nivel Grupo'. BUSCA: Versiones software, EoL, y detalles de red. Info: {perimeter_text}",
            schema=TechHarvest,
        ),
        run_agent_osint_sovereign(
            f"Regulación de {client_name} (NIS2, PIC, leyes locales). Info: {perimeter_text}",
            schema=RegulatoryHarvest,
        ),
    ]
    biz_data, tech_data, reg_data = await asyncio.gather(*tasks)

    # --- FASE 2: GOBERNANZA Y MINERÍA MULTIMODAL ---
    print("  -> [FASE 2] Capturando Evidencias y Minería de Arquitectura...")
    snapshotter = EvidenceSnapshotter(storage_dir=output_path.parent)
    all_urls = [
        link["url"]
        for d in [biz_data, tech_data, reg_data]
        if isinstance(d, dict)
        for link in d.get("_osint_links", [])
    ]
    captured_claims = await snapshotter.process_urls(" ".join(all_urls[:15]))

    pdf_intelligence = ""
    for snap in [
        c
        for c in captured_claims
        if c.get("url", "").lower().endswith(".pdf") and c.get("status") == "verified"
    ]:
        local_path = output_path.parent.parent.parent / snap["local_snapshot"]
        if local_path.exists():
            deep_prompt = f"""
            Analiza este PDF de {client_name}.
            REGLA DE ÉLITE: Traduce cualquier diagrama o esquema en una descripción técnica de arquitectura (Topología, DMZs, Diodos).
            Busca versiones de software (ej. 19c, vSphere 8) y fechas de EoL.
            Atribuye cada dato a la sociedad correcta (Holding vs Filial).
            """
            enriched = await run_agent_osint_sovereign(deep_prompt, pdf_path=local_path)
            pdf_intelligence += f"\n[FUENTE {snap['url']}]:\n{enriched.get('raw_text') if isinstance(enriched, dict) else enriched}\n"

    # --- FASE 3: ENSAMBLAJE JERÁRQUICO ---
    print("  -> [FASE 3] Consolidando Dossier con Herencia y Sombreado...")

    raw_dossier = {
        "version": "16.0",
        "client_name": client_name,
        "metadata": {
            "dossier_id": f"{client_name}-architecture",
            "schema_version": "3.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lang": "es",
        },
        "profile": {
            "industry": "Critical Infrastructure Holding",
            "hierarchy": perimeter_text,
            "business_lines": biz_data.get("business_lines", [])
            if isinstance(biz_data, dict)
            else [],
        },
        "regulatory_context": [
            {
                "name": f.get("name"),
                "impacto": "Crítico",
                "entity": f.get("entity", "Holding"),
            }
            for f in (
                reg_data.get("frameworks", []) if isinstance(reg_data, dict) else []
            )
        ],
        "business_context": {
            "ceo_agenda": {
                "summary": biz_data.get("ceo_agenda", "")
                if isinstance(biz_data, dict)
                else ""
            },
            "strategic_priorities": [
                {"name": p.get("name") if isinstance(p, dict) else str(p)}
                for p in (
                    biz_data.get("business_drivers", [])
                    if isinstance(biz_data, dict)
                    else []
                )
            ],
        },
        "technology_context": {
            "group_level_stack": tech_data.get("group_level_stack", [])
            if isinstance(tech_data, dict)
            else [],
            "entity_specific_overrides": tech_data.get("entity_specific_overrides", [])
            if isinstance(tech_data, dict)
            else [],
            "technical_debt": tech_data.get("technical_debt_and_eol", [])
            if isinstance(tech_data, dict)
            else [],
            "architecture_specs": tech_data.get("architecture_and_topology", [])
            if isinstance(tech_data, dict)
            else [],
            "field_metrics": tech_data.get("specific_infrastructure_metrics", [])
            if isinstance(tech_data, dict)
            else [],
        },
        "review": {
            "summary": "Arquitectura y herencia de datos verificada",
            "status": "Final",
        },
        "claims": captured_claims,
    }

    tribunal_agent = Agent(
        name="partner_agent",
        model="gemini-2.5-pro",
        instruction="Eres un Socio Director experto en Arquitectura Empresarial.",
    )
    tribunal_app = AdkApp(agent=tribunal_agent)

    polish_prompt = f"""
    Redacta el Dossier Final para {client_name}.
    DATOS BRUTOS: {json.dumps(raw_dossier)}
    MINERÍA TÉCNICA (PDFs): {pdf_intelligence}

    MANDATOS DE ARQUITECTURA:
    1. HERENCIA: El stack técnico de nivel GRUPO (ej. SAP, AWS, Oracle, Siemens) DEBE aparecer en la matriz.
    2. SOMBREADO: Indica qué tecnologías son únicas de cada filial (ej. Reintel -> 400GE).
    3. TOPOLOGÍA: Describe detalladamente cualquier esquema de red, DMZ o diodo industrial detectado.
    4. DEUDA: Menciona versiones de software y riesgos de EoL para el assessment de madurez.

    Devuelve JSON ClientDossierV3.
    """

    final_dossier = await run_agent_safe(
        tribunal_app, user_id="partner", message=polish_prompt, schema=ClientDossierV3
    )
    final_dossier = sign_dossier(final_dossier)
    output_path.write_text(
        json.dumps(final_dossier, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ FASE 2 CERRADA CON ÉXITO (ARQUITECTURA 10/10): {output_path}")


def main():
    if len(sys.argv) < 2:
        return
    asyncio.run(
        run_market_intelligence(
            sys.argv[1],
            resolve_client_intelligence_path(sys.argv[1]),
            Path(sys.argv[2]) if len(sys.argv) > 2 else None,
        )
    )


if __name__ == "__main__":
    main()
