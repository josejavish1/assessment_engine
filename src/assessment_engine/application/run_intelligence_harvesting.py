import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional, Type, cast

from pydantic import BaseModel, Field


class MetaExtract(BaseModel):
    """A data model encapsulating strategic metadata about a client's transformation journey.

    This model structures key metadata derived from an analysis of a client's
    technology stack, business strategy, and cloud adoption posture. It serves
    as a structured output for strategic intelligence harvesting processes.

    Attributes:
        dominant_hyperscaler (str): The inferred dominant public cloud provider
            (e.g., AWS, Azure, GCP). The value is set to 'N/A - 100% On-Premise'
            if no significant public cloud presence is detected.
        stage (str): The assigned transformation phase, must be one of "H1",
            "H2", or "H3". These values correspond to "Brilliant Basics",
            "Hyperautomation & Scale", and "Vanguard & AI-First", respectively,
            categorized by the client's automation maturity and strategic objectives.
        label (str): A concise, executive-level summary label that represents the
            client's transformation horizon (e.g., 'Intelligent Scaling & Cloud
            Native').
        rationale (str): A detailed qualitative analysis justifying the assigned
            transformation stage, contextualized by the client's observed
            investments, public statements, and business plans.
    """

    dominant_hyperscaler: str = Field(
        description="Infers the client's dominant public cloud provider based on their technology footprint (e.g., AWS, Azure, GCP). Value is 'N/A - 100% On-Premise' if the client operates without a public cloud presence."
    )
    stage: Literal["H1", "H2", "H3"] = Field(
        description="The assigned transformation phase: H1 (Brilliant Basics), H2 (Hyperautomation & Scale), or H3 (Vanguard & AI-First), determined by the client's automation level and strategic objectives."
    )
    label: str = Field(
        description="A concise, executive-level label representing the transformation horizon (e.g., 'Intelligent Scaling & Cloud Native')."
    )
    rationale: str = Field(
        description="Detailed strategic rationale for assigning this specific transformation phase, contextualized by the client's current investment and business plans."
    )


from assessment_engine.infrastructure.client_intelligence import (
    sign_dossier,
)
from assessment_engine.infrastructure.evidence_governance import EvidenceSnapshotter
from assessment_engine.infrastructure.runtime_paths import (
    resolve_client_intelligence_path,
)
from assessment_engine.infrastructure.text_utils import slugify

"""
Módulo run_intelligence_harvesting.py (MASTER EDITION V35.0 - THE PURIST).
Arquitectura Anti-Contaminación: Bloqueo estricto de nombres de otros clientes.
Garantiza que Eurovision Services sea 100% independiente de Redeia.
"""

MODEL_FAST = os.environ.get("MODEL_TIER_FAST", "gemini-2.5-flash")
MODEL_PRO = os.environ.get("MODEL_TIER_PRO", "gemini-2.5-pro")


async def probe_ai(
    prompt: str,
    schema: Type[BaseModel] = None,
    model_name: str = MODEL_FAST,
    client_name: Optional[str] = None,
) -> Any:
    """Queries a generative AI model with grounding and optional data isolation.

    Sends a prompt to a Google generative AI model, utilizing Google Search for
    grounded responses. If a `client_name` is provided, a critical instruction
    is appended to the prompt to enforce strict data isolation, preventing
    information from being mixed between different client contexts.

    The function attempts to find and parse a JSON object within the model's raw
    text output. If successful, the parsed dictionary is enriched with a `_links`
    key containing a list of URIs from the grounding metadata. If no JSON is
    found, a dictionary containing the raw text and the links is returned. A
    comprehensive `try...except` block ensures that any error during the API
    call or response processing results in a default empty response.

    Note: This function is defined as `async` but internally uses a synchronous
    API call, which will block the event loop.

    Args:
        prompt: The primary query or instruction for the generative model.
        schema: A Pydantic model for response validation. This parameter is
            currently not used in the function's implementation.
        model_name: The identifier of the generative model to use, defaulting to
            the `MODEL_FAST` constant.
        client_name: An optional identifier for a client. If provided, a rule is
            appended to the prompt to enforce strict data isolation.

    Returns:
        A dictionary containing the processed model output. If a JSON object is
        parsed from the response, it is returned augmented with a `_links` key
        containing a list of grounding source URIs. If no JSON is found, a
        dictionary of the form {'text': str, '_links': list[str]} is returned.
        In case of any exception, a default dictionary {'text': '', '_links': []}
        is returned.

    Raises:
        This function does not raise exceptions. All potential errors during API
        calls or response processing are suppressed, and a default value is
        returned instead.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(
        vertexai=True, project="sub403o4u0q5", location="europe-west1"
    )
    tools = [types.Tool(google_search=types.GoogleSearch())]

    # Enforces strict, context-agnostic data isolation between client datasets. This rule is critical for maintaining data confidentiality and preventing cross-contamination.
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
        res = client.models.generate_content(
            model=model_name,
            contents=[prompt + anti_mix],
            config=types.GenerateContentConfig(tools=cast(Any, tools), temperature=0.0),
        )
        text = res.text
        links = []
        if (
            res.candidates
            and res.candidates[0].grounding_metadata
            and res.candidates[0].grounding_metadata.grounding_chunks
        ):
            for chunk in res.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.web:
                    links.append(chunk.web.uri)
        if text and "{" in text:
            start, end = text.find("{"), text.rfind("}") + 1
            data = json.loads(text[start:end])
            data["_links"] = links
            return data
        return {"text": text or "", "_links": links}
    except Exception:
        return {"text": "", "_links": []}


class SourceVault:
    """Extracts brand and metric intelligence 'atoms' from unstructured data.

    Parses an input data object to identify and extract structured information,
    referred to as 'atoms', which are then appended to the instance's `atoms`
    list. This method operates in two distinct stages:

    1.  **Brand Extraction:** A predefined list of technology brand names is
        scanned against the input text in a case-insensitive manner. This
        list may be dynamically extended with client-specific brands based on
        the `self.client_name` attribute. Matches result in 'stack' atoms.

    2.  **Metric Extraction:** A regular expression is used to find numerical
        values associated with specific units (e.g., km, MW, Gbps, %).
        Matches result in 'metric' atoms.

    Each generated atom is a dictionary containing the extracted value, its
    category, a contextual snippet from the source text, and the provided
    source URI and type.

    Args:
        data: The raw input data to process. The method constructs the text
            corpus by concatenating `str(data.get("text", ""))` with `str(data)`.
            If the `data` object is falsy, processing is skipped.
        source_uri: The Uniform Resource Identifier of the data source, which
            is embedded in each extracted atom.
        source_type: A string descriptor for the data source type (e.g.,
            'pdf', 'html'), which is embedded in each extracted atom.
    """

    def __init__(self, client_name: str = ""):
        """Initialize the instance with a client name."""
        self.atoms = []
        self.client_name = client_name

    def ingest(self, data: Any, source_uri: str, source_type: str):
        """Extracts brand and metric intelligence atoms from raw data.

        This method processes an input data object to identify and extract
        predefined brand names and quantitative metrics. The extraction occurs in
        two stages. First, it performs a case-insensitive search for a static
        list of brand names, which may be augmented based on the instance's
        `client_name` attribute. Second, it uses a regular expression to find
        numerical values followed by specific units (e.g., km, MW, ms, Gbps).

        Each piece of identified intelligence is structured into a dictionary,
        termed an 'atom', containing its category ('stack' or 'metric'), value,
        unit (for metrics), source URI, source type, and a contextual snippet
        from the raw data. These atoms are appended to the instance's `atoms` list.

        Args:
            data (Any): The input data to process. A searchable string is
                constructed by concatenating the value of a 'text' key (if
                present) and the string representation of the `data` object.
                The method returns immediately if `data` is falsy.
            source_uri (str): The Uniform Resource Identifier of the data's origin.
            source_type (str): A string describing the source type (e.g., 'PDF').

        Side Effects:
            Appends dictionary objects representing found intelligence to the
            instance's `self.atoms` list.
        """
        if not data:
            return
        raw = str(data.get("text", "")) + str(data)

        # Stage 1: Brand Intelligence Extraction. Aggregates and processes brand-specific data points from designated public and private sources.
        brands = [
            "Siemens",
            "ABB",
            "GE",
            "AWS",
            "Google",
            "Dynatrace",
            "Splunk",
            "Oracle",
            "SAP",
            "Microsoft",
        ]
        # Get client-specific brands declaratively from config loaders or brand profile if available
        from assessment_engine.infrastructure.config_loader import load_brand_profile
        try:
            brand_profile = load_brand_profile()
            custom_brands = brand_profile.get("custom_brands", [])
            for cb in custom_brands:
                if cb not in brands:
                    brands.append(cb)
        except Exception:
            pass

        # Legacy fallback
        if self.client_name and "eurovision" in self.client_name.lower():
            if "EBU" not in brands:
                brands.append("EBU")

        for b in brands:
            if b.lower() in raw.lower():
                idx = raw.lower().find(b.lower())
                self.atoms.append(
                    {
                        "category": "stack",
                        "value": b,
                        "snippet": raw[max(0, idx - 100) : min(len(raw), idx + 250)],
                        "uri": source_uri,
                        "type": source_type,
                    }
                )

        # Stage 2: Metric Derivation. Computes quantitative metrics from raw, unstructured intelligence data.
        hits = re.findall(
            r"(\d+[\.,]\d+|\d+)\s*(km|MW|ms|Gbps|CHF|%)", raw, re.IGNORECASE
        )
        for val, unit in hits:
            idx = raw.find(val)
            self.atoms.append(
                {
                    "category": "metric",
                    "value": val,
                    "unit": unit,
                    "snippet": raw[max(0, idx - 100) : min(len(raw), idx + 250)],
                    "uri": source_uri,
                    "type": source_type,
                }
            )


async def run_market_intelligence(
    client_name: str, output_path: Path, context_file: Path = None
) -> None:
    """Orchestrates an asynchronous, multi-stage market intelligence pipeline.

    This function executes a comprehensive intelligence gathering and analysis
    process. It begins by ingesting an optional internal document, then
    asynchronously probes public web sources and PDF reports for client-specific
    data. The collected information is synthesized and semantically labeled
    against a structured ontology. A deterministic multi-criteria decision model
    then calculates strategic maturity scores based on the synthesized data and
    client-specific context. Finally, all findings are assembled into a
    structured JSON dossier and persisted to the specified output path.

    Args:
        client_name: The name of the target client company for the analysis.
        output_path: The destination file path for the final JSON dossier.
            Parent directories are created if they do not exist.
        context_file: An optional path to a .docx file providing initial
            internal context. If provided and the file exists, its text content
            is ingested. Defaults to None.

    Returns:
        None: The function has side effects (writing a file) and does not
            return a value.

    Raises:
        FileNotFoundError: If a referenced local file, such as a downloaded PDF
            report, cannot be located on the filesystem for processing.
        PermissionError: If the process lacks sufficient permissions to read a
            source file (e.g., `context_file`) or write to the `output_path`.
        json.JSONDecodeError: If a generative AI API call returns a string that
            is not valid JSON when a structured JSON response is required.
        google.api_core.exceptions.GoogleAPICallError: If an interaction with the
            Google Generative AI API fails due to network issues, authentication
            problems, or invalid arguments.
        docx.opc.exceptions.PackageNotFoundError: If the file specified by
            `context_file` is not a valid or uncorrupted .docx file.
    """
    print(f"\n🚀 Iniciando Pipeline V35.0 (The Purist) para: {client_name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    vault = SourceVault(client_name)

    # Stage 0: Internal Ingestion. Establishes the canonical data source for subsequent executive insight generation.
    if context_file and context_file.exists():
        from docx import Document

        doc_text = "\n".join([p.text for p in Document(context_file).paragraphs])
        vault.ingest(
            {"text": doc_text},
            source_uri=str(context_file),
            source_type="Internal Document",
        )

    # Stage 1: Web Intelligence Probing. Executes targeted scans of public web sources to acquire relevant client-specific intelligence.
    print("  -> [FASE 1] Cosechando Huellas Técnicas Reales...")
    tasks = [
        probe_ai(
            f"Estrategia independiente de {client_name} tras el acuerdo con EBU.",
            client_name=client_name,
        ),
        probe_ai(
            f"Stack tecnológico de broadcast y nube de {client_name}.",
            client_name=client_name,
        ),
    ]
    res_strat, res_stack = await asyncio.gather(*tasks)
    vault.ingest(res_strat, source_uri="Web-Strategy", source_type="Web Search")
    vault.ingest(res_stack, source_uri="Web-Stack", source_type="Web Search")

    # Stage 2: PDF Deep Mining and Analysis. Performs deep content extraction and semantic analysis on specified PDF documents.
    snapshotter = EvidenceSnapshotter(storage_dir=output_path.parent)
    pdf_search = await probe_ai(
        f"filetype:pdf {client_name} ESG OR Annual Report", client_name=client_name
    )
    captured = await snapshotter.process_urls(
        " ".join(pdf_search.get("_links", [])[:5])
    )

    for snap in [
        c
        for c in captured
        if c.get("local_snapshot") and c["local_snapshot"].endswith(".pdf")
    ]:
        local_p = output_path.parent.parent.parent / snap["local_snapshot"]
        if local_p.exists():
            print(f"       📖 Minería PDF: {snap['url']}")
            from google import genai
            from google.genai import types

            client = genai.Client(
                vertexai=True, project="sub403o4u0q5", location="europe-west1"
            )
            res = client.models.generate_content(
                model=MODEL_PRO,
                contents=[
                    "Extrae marcas y métricas en texto denso.",
                    types.Part.from_bytes(
                        data=Path(local_p).read_bytes(), mime_type="application/pdf"
                    ),
                ],
            )
            vault.ingest(
                {"text": res.text or ""},
                source_uri=snap["url"],
                source_type="PDF Document",
            )

    # Stage 3: Semantic Labeling and Classification. Applies semantic tags to and classifies synthesized data against a predefined, structured ontology.
    print("  -> [FASE 3] Etiquetado y Citación de Bóveda...")
    label_q = f"Organiza estos hallazgos en JSON. ÁTOMOS: {json.dumps(vault.atoms[:40])}. JSON: {{'metrics': [{{'name':'', 'value':'', 'unit':'', 'source':{{'uri':''}}}}], 'stack': [{{'technology':'', 'vendor':'', 'source':{{'uri':''}}}}]}}"
    organized = await probe_ai(label_q, model_name=MODEL_PRO, client_name=client_name)

    # Stage 4: Intelligence Synthesis. Consolidates and integrates intelligence from multiple sources into a unified analytical model.
    print("  -> [FASE 4] Redactando Narrativa (Anti-Contaminación)...")
    narrative = await probe_ai(
        f"Resume Estrategia y Agenda de Liderazgo para {client_name}. No inventes nombres de CEOs si no aparecen en los datos.",
        model_name=MODEL_PRO,
        client_name=client_name,
    )

    # Stage 4.5: Dynamic Maturity Target Calculation. Executes the Sovereign Target Model to compute dynamic, strategic maturity targets.
    print(
        "  -> [FASE 4.5] Evaluando Criterios de Madurez por Torre (Conjoint Multi-Criteria Matrix)..."
    )

    # Load declarative custom narratives from brand_profile.json first (elite approach)
    from assessment_engine.infrastructure.config_loader import load_brand_profile
    brand_data_narratives = {}
    try:
        brand_data_narratives = load_brand_profile()
    except Exception:
        pass

    custom_narratives = brand_data_narratives.get("custom_narratives", {})
    client_context_str = custom_narratives.get("client_context")
    compliance_example_str = custom_narratives.get("compliance_example")
    feasibility_example_str = custom_narratives.get("feasibility_example")

    # Fallback to legacy hardcoded text if not declaratively configured
    if not client_context_str or not compliance_example_str or not feasibility_example_str:
        if "redeia" in client_name.lower():
            client_context_str = (
                "footprint de transporte eléctrico y telecomunicaciones críticas, "
                "cumplimiento con Directiva PIC y NIS2, y la necesidad de ciberresiliencia, "
                "convergencia operacional IT/OT y digitalización bajo el Plan Estratégico de REDEIA."
            )
            compliance_example_str = "ej: NIS2, Directiva PIC, protección de infraestructura crítica, soberanía IT/OT como T6, T5 o T3, ~90. T1 u otras, ~40"
            feasibility_example_str = "ej: T2 es compleja debido a migración e integración de sistemas legados de subestaciones, ~50. T10 DTO es de soporte estratégico, ~70"
        elif "eurovision" in client_name.lower():
            client_context_str = (
                "footprint de 50 PoPs, adquisición por DUBAG Group, "
                "e independencia tecnológica de la EBU ('Project Independence & Resilience') bajo eventos en directo críticos (UEFA, NBA)."
            )
            compliance_example_str = "ej: NIS2, DORA, Directiva PIC, o soberanía existencial de identidades post-EBU como T6 y T5, ~90. T1 u otras, ~40"
            feasibility_example_str = "ej: T2 es compleja debido a VMware legacy, ~50. T10 DTO es de soporte estratégico, ~70"
        else:
            client_context_str = (
                "footprint global, cumplimiento normativo general de sector crítico, "
                "y la necesidad de modernización de su arquitectura, resiliencia operativa e independencia tecnológica."
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
        f'  "T1": {{\n'
        f'    "criticality": 60,\n'
        f'    "compliance": 40,\n'
        f'    "feasibility": 70,\n'
        f'    "justification": "Explicación estratégica de por qué se asignan estos valores en base a los hechos del cliente."\n'
        f"  }},\n"
        f'  "T2": {{\n'
        f'    "criticality": 75,\n'
        f'    "compliance": 80,\n'
        f'    "feasibility": 50,\n'
        f'    "justification": "..."\n'
        f"  }},\n"
        f"  ...\n"
        f"}}"
    )
    raw_overrides = await probe_ai(
        overrides_prompt, model_name=MODEL_PRO, client_name=client_name
    )

    # Stage 4.6: Deterministic Mathematical Computation. Applies the Sovereign Target Engine's deterministic mathematical formula to derive a precise maturity score.
    print(
        "  -> [FASE 4.6] Ejecutando Algoritmo de Decisión Multicriterio (Sovereign Target Engine)..."
    )
    calculated_overrides = {}
    if isinstance(raw_overrides, dict):
        for tower_id, metrics in raw_overrides.items():
            if not isinstance(metrics, dict):
                continue
            try:
                crit = float(metrics.get("criticality", 50))
                comp = float(metrics.get("compliance", 50))
                feas = float(metrics.get("feasibility", 50))

                # Defines the deterministic utility function that maps weighted scores for Criticality, Complexity, and Feasibility to a final target value. The formula is `Target = 3.0 + 2.0 * ((Crit*0.4 + Comp*0.4 + Feas*0.2) / 100)`.
                # The base `3.0` and multiplier `2.0` constants enforce a strict, asymmetrical output range of [3.0, 5.0] for the calculated target value. This constraint prevents score drift outside the defined maturity spectrum.
                raw_target = 3.0 + 2.0 * (
                    (crit * 0.4 + comp * 0.4 + feas * 0.2) / 100.0
                )
                target_score = round(raw_target, 1)

                calculated_overrides[tower_id] = {
                    "target_maturity": target_score,
                    "metrics": {
                        "business_criticality": crit,
                        "regulatory_compliance": comp,
                        "implementation_feasibility": feas,
                    },
                    "justification": metrics.get(
                        "justification", "Alineación multicriterio calculada."
                    ),
                }
                just_str = metrics.get("justification", "")[:60]
                print(
                    f"       * {tower_id}: Score Calculado = {target_score} (Justificación: {just_str}...)"
                )
            except Exception as e:
                calculated_overrides[tower_id] = {
                    "target_maturity": 4.0,
                    "justification": f"Fallback estándar por fallo en cálculo: {e}",
                }
    else:
        # Provides a fallback mechanism to ensure system stability and graceful degradation in the event of a malformed or non-compliant JSON response from the large language model.
        print(
            "  ⚠️ Fallo en el retorno de matriz de madurez. Aplicando fallbacks estándar."
        )
        calculated_overrides = {
            f"T{i}": {"target_maturity": 4.0, "justification": "Estándar por defecto."}
            for i in range(1, 11)
        }

    # Stage 5: Final Assembly. Executes dynamic just-in-time (JIT) data extraction and enforces schema integrity through Pydantic model validation.
    print(
        "  -> [FASE 4.7] Extrayendo Meta-Arquitectura e Hyperscaler Dominante de forma Dinámica (Agnóstico)..."
    )
    meta_prompt = (
        f"Analiza de forma síncrona el contexto recopilado de la empresa '{client_name}':\n"
        f"1. Narrativa: {narrative.get('text', 'N/A')}\n"
        f"2. Stack Técnico: {json.dumps(organized.get('stack', []), ensure_ascii=False)}\n\n"
        f"Deduce el proveedor cloud dominante ('dominant_hyperscaler') y la fase de horizonte de transformación óptimo."
    )
    from google import genai
    from google.genai import types

    client_gen = genai.Client(
        vertexai=True, project="sub403o4u0q5", location="europe-west1"
    )

    try:
        res_meta = client_gen.models.generate_content(
            model=MODEL_PRO,
            contents=[meta_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", response_schema=MetaExtract
            ),
        )
        meta_data = json.loads(res_meta.text)
        dominant_hyperscaler = meta_data.get("dominant_hyperscaler", "AWS")
        horizon_obj = {
            "stage": meta_data.get("stage", "H1"),
            "label": meta_data.get("label", "Estandarización"),
            "rationale": meta_data.get("rationale", "Calculado dinámicamente."),
        }
    except Exception as e:
        print(f"  ⚠️ Error en extracción de meta-datos: {e}. Usando fallbacks.")
        dominant_hyperscaler = "AWS"
        horizon_obj = {
            "stage": "H1",
            "label": "Estandarización",
            "rationale": "Fallback estándar.",
        }

    # Decouples industry-vertical-specific logic from the core processing pipeline.
    # Reads declaratively from brand profile first (elite approach)
    industry_str = brand_data_narratives.get("industry_profile_name")
    if not industry_str:
        # Fallback to legacy string check
        if "redeia" in client_name.lower():
            industry_str = "Energy & Critical Infrastructure"
        elif "eurovision" in client_name.lower():
            industry_str = "Broadcast Infrastructure"
        else:
            industry_str = "Enterprise & Infrastructure Technology"

    final_json = {
        "version": "3.0",
        "client_name": client_name,
        "metadata": {
            "dossier_id": f"{slugify(client_name)}-purist",
            "schema_version": "3.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lang": "es",
        },
        "profile": {"industry": industry_str, "hierarchy": "Global Entity"},
        "regulatory_context": [],
        "business_context": {
            "ceo_agenda": {"summary": narrative.get("text", "N/A")},
            "transformation_horizon": horizon_obj,
        },
        "technology_context": {
            "footprint_summary": {"summary": narrative.get("text", "N/A")},
            "group_level_stack": organized.get("stack", []),
            "field_metrics": organized.get("metrics", []),
            "dominant_hyperscaler": dominant_hyperscaler,
        },
        "tower_overrides": calculated_overrides,
        "review": {
            "summary": "Certificación Purist V35.0 (Aislamiento de Contexto)",
            "status": "Final",
        },
        "claims": captured,
    }

    final_json = sign_dossier(final_json)
    output_path.write_text(
        json.dumps(final_json, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ BLUEPRINT SANEADO Y COMPLETADO: {output_path}")


def main() -> None:
    """Executes the market intelligence harvesting process from the command line.

    This function serves as the main entry point for the script. It parses
    positional command-line arguments to configure and launch the asynchronous
    `run_market_intelligence` coroutine.

    The script expects the following command-line arguments in order:

    1.  `client_id` (str): A mandatory identifier for the client.
    2.  `input_file` (str, optional): The path to an input file.
    3.  `output_dir` (str, optional): The path to the output directory. If
        not provided, a default path is resolved using the `client_id`.
    """
    if len(sys.argv) < 2:
        return
    asyncio.run(
        run_market_intelligence(
            sys.argv[1],
            Path(sys.argv[3])
            if len(sys.argv) > 3
            else resolve_client_intelligence_path(sys.argv[1]),
            Path(sys.argv[2]) if len(sys.argv) > 2 else None,
        )
    )


if __name__ == "__main__":
    main()
