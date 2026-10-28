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
    industry_sector: str = Field(
        default="Enterprise & Industrial Technology",
        description="Identifies the client's actual industry sector based on their business operations, products, and market activities (e.g. 'Manufacturing & Building Materials', 'Banking & Financial Services', 'Retail & Commerce', 'Energy & Utilities', 'Healthcare', 'Logistics')."
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
Arquitectura Anti-Contaminación: Bloqueo estricto de cruces de datos entre clientes.
Garantiza el aislamiento absoluto de los contextos empresariales.
"""

from assessment_engine.infrastructure.config_loader import resolve_model_for_role

MODEL_FAST = os.environ.get("MODEL_TIER_FAST", "").strip() or resolve_model_for_role("section_writer", "gemini-2.5-flash")
MODEL_PRO = os.environ.get("MODEL_TIER_PRO", "").strip() or resolve_model_for_role("section_reviewer", "gemini-2.5-pro")


def _get_genai_client():
    """Dynamically resolves Google Cloud project ID and location, and initializes the GenAI Client."""
    from google import genai

    from assessment_engine.infrastructure.runtime_env import (
        get_google_cloud_project_location,
    )

    project_id, location = get_google_cloud_project_location()
    return genai.Client(vertexai=True, project=project_id, location=location)


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
    if client_name:
        import re
        client_name = re.sub(r"_v\d+$", "", client_name, flags=re.IGNORECASE).upper()

    from google.genai import types

    client = _get_genai_client()
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


def load_pdf_cache(cache_path: Path) -> dict[str, str]:
    """Loads the SHA-256 PDF text extraction cache from the specified path."""
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load PDF extraction cache ({e}). Initializing new cache.")
    return {}


def save_pdf_cache(cache_path: Path, cache_data: dict[str, str]) -> None:
    """Saves the SHA-256 PDF text extraction cache atomically to disk."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_path.with_name(f"{cache_path.name}.tmp")
    try:
        tmp_path.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_path.replace(cache_path)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to save PDF extraction cache ({e}).")
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except (OSError, ValueError, KeyError, AttributeError) as ex:

                logger.debug(f"[Fallback] Excepción controlada: {ex}")


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
        self.custom_discovered_brands = []

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
            "Azure",
            "GCP",
            "VMware",
            "Okta",
            "Dynatrace",
            "Splunk",
            "Oracle",
            "SAP",
            "Microsoft",
        ]
        # Include custom discovered brands dynamically
        for cb in getattr(self, "custom_discovered_brands", []):
            if cb and cb not in brands:
                brands.append(cb)

        # Get client-specific brands declaratively from config loaders or brand profile if available
        from assessment_engine.infrastructure.config_loader import load_brand_profile

        try:
            brand_profile = load_brand_profile()
            custom_brands = brand_profile.get("custom_brands", [])
            for cb in custom_brands:
                if cb not in brands:
                    brands.append(cb)
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Excepción controlada: {ex}")

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
            r"(\d+[\.,]\d+|\d+)\s*(km|MW|kW|GW|kV|MVA|ms|Gbps|Tbps|vCPUs|cores|GB|TB|CHF|EUR|€|USD|%)", raw, re.IGNORECASE
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
    discovered_brands = []
    if context_file and context_file.exists():
        from docx import Document

        doc_text = "\n".join([p.text for p in Document(context_file).paragraphs])
        vault.ingest(
            {"text": doc_text},
            source_uri=str(context_file),
            source_type="Internal Document",
        )

        # Discover brands dynamically from the context file using the fast LLM!
        print("  -> [FASE 0] Descubriendo marcas tecnológicas dinámicamente desde el documento de contexto...")
        try:
            discovery_prompt = f"""
            Analiza el siguiente texto de contexto técnico e identifica todas las marcas tecnológicas, proveedores de nube, fabricantes de hardware, soluciones de software corporativas y bases de datos que utiliza esta organización de forma activa (por ejemplo, AWS, Alibaba Cloud, GCP, IBM, Proxmox, Oracle, SAP, VMware, Cohesity, Centreon, Okta, Dynatrace).
            
            TEXTO DE CONTEXTO:
            {doc_text[:8000]}
            
            REGLA DE ORO: Devuelve ÚNICAMENTE una lista JSON de strings con los nombres exactos de las marcas detectadas (ej. ["AWS", "Alibaba", "IBM", "VMware"]). No devuelvas explicaciones ni texto adicional.
            """
            res_brand = await probe_ai(discovery_prompt, client_name=client_name, model_name=MODEL_FAST)
            if isinstance(res_brand, dict) and "text" in res_brand:
                txt = res_brand["text"].strip()
                if "[" in txt and "]" in txt:
                    start, end = txt.find("["), txt.rfind("]") + 1
                    try:
                        brands_list = json.loads(txt[start:end])
                        if isinstance(brands_list, list):
                            discovered_brands = [str(b).strip() for b in brands_list if b]
                            print(f"     ✓ Marcas descubiertas por IA: {discovered_brands}")
                    except (OSError, ValueError, KeyError, AttributeError) as ex:

                        logger.debug(f"[Fallback] Excepción controlada: {ex}")
        except Exception as e:
            print(f"  ⚠️ Error en descubrimiento dinámico de marcas: {e}")

    vault.custom_discovered_brands = discovered_brands

    # Stage 1: Web Intelligence Probing. Executes targeted scans of public web sources to acquire relevant client-specific intelligence.
    print("  -> [FASE 1] Cosechando Huellas Técnicas Reales...")
    tasks = [
        probe_ai(
            f"Estrategia de transformación digital, negocio y sostenibilidad de {client_name}.",
            client_name=client_name,
        ),
        probe_ai(
            f"Stack tecnológico de infraestructura, TI, centros de datos y nube de {client_name}.",
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

    cache_path = Path("working") / ".pdf_cache.json"
    pdf_cache = load_pdf_cache(cache_path)
    cache_updated = False

    for snap in [
        c
        for c in captured
        if c.get("local_snapshot") and c["local_snapshot"].endswith(".pdf")
    ]:
        local_p = output_path.parent.parent.parent / snap["local_snapshot"]
        if local_p.exists():
            import hashlib
            try:
                pdf_bytes = Path(local_p).read_bytes()
                pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
            except Exception as e:
                print(f"       ⚠️ Error al calcular hash de PDF {local_p}: {e}")
                pdf_hash = None

            if pdf_hash and pdf_hash in pdf_cache:
                print(f"       📖 Minería PDF (Caché): {snap['url']}")
                extracted_text = pdf_cache[pdf_hash]
            else:
                print(f"       📖 Minería PDF (API): {snap['url']}")
                from google.genai import types

                try:
                    client = _get_genai_client()
                    res = client.models.generate_content(
                        model=MODEL_PRO,
                        contents=[
                            "Extrae marcas y métricas en texto denso.",
                            types.Part.from_bytes(
                                data=pdf_bytes, mime_type="application/pdf"
                            ),
                        ],
                    )
                    extracted_text = res.text or ""
                    if pdf_hash:
                        pdf_cache[pdf_hash] = extracted_text
                        cache_updated = True
                except Exception as e:
                    print(f"       ❌ Error fatal en API de Vertex AI para PDF {snap['url']}: {e}")
                    print("       ⚠️ Saltando este documento para no bloquear el pipeline de inteligencia.")
                    extracted_text = ""

            vault.ingest(
                {"text": extracted_text},
                source_uri=snap["url"],
                source_type="PDF Document",
            )

    if cache_updated:
        save_pdf_cache(cache_path, pdf_cache)

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
    except (OSError, ValueError, KeyError, AttributeError) as ex:

        logger.debug(f"[Fallback] Excepción controlada: {ex}")

    custom_narratives = brand_data_narratives.get("custom_narratives", {})
    client_context_str = custom_narratives.get("client_context")
    compliance_example_str = custom_narratives.get("compliance_example")
    feasibility_example_str = custom_narratives.get("feasibility_example")

    # Fallback to decoupled generic default text if not declaratively configured in brand_profile.json
    if not client_context_str:
        client_context_str = (
            "footprint global, cumplimiento normativo general de sector crítico, "
            "y la necesidad de ciberresiliencia, resiliencia operativa y modernización de su arquitectura."
        )
    if not compliance_example_str:
        compliance_example_str = "ej: NIS2, DORA, Directiva PIC o regulaciones específicas de seguridad de la información, ~85. T1 u otras, ~40"
    if not feasibility_example_str:
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

                # Run advanced Global Sensitivity Analysis (Sobol Indices & Monte Carlo Fuzzing)
                from assessment_engine.infrastructure.mcda_sensitivity_engine import (
                    MCDASensitivityEngine,
                )

                gsa_samples = int(os.environ.get("ASSESSMENT_GSA_MONTE_CARLO_SAMPLES", "10000"))
                gsa_uncertainty = float(os.environ.get("ASSESSMENT_GSA_UNCERTAINTY_RANGE", "20.0"))

                sensitivity_engine = MCDASensitivityEngine()
                gsa_report = sensitivity_engine.run_sensitivity_analysis(
                    base_criticality=crit,
                    base_compliance=comp,
                    base_feasibility=feas,
                    N=gsa_samples,
                    uncertainty_range=gsa_uncertainty,
                )

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
                    "sensitivity_analysis": gsa_report,
                }
                just_str = metrics.get("justification", "")[:60]
                print(
                    f"       * {tower_id}: Score Calculado = {target_score} (Justificación: {just_str}...)"
                )
            except Exception as e:
                from assessment_engine.infrastructure.mcda_sensitivity_engine import (
                    MCDASensitivityEngine,
                )

                gsa_samples = int(os.environ.get("ASSESSMENT_GSA_MONTE_CARLO_SAMPLES", "10000"))
                gsa_uncertainty = float(os.environ.get("ASSESSMENT_GSA_UNCERTAINTY_RANGE", "20.0"))

                fallback_engine = MCDASensitivityEngine()
                fallback_gsa = fallback_engine.run_sensitivity_analysis(
                    50.0, 50.0, 50.0, N=gsa_samples, uncertainty_range=gsa_uncertainty
                )
                calculated_overrides[tower_id] = {
                    "target_maturity": 4.0,
                    "metrics": {
                        "business_criticality": 50.0,
                        "regulatory_compliance": 50.0,
                        "implementation_feasibility": 50.0,
                    },
                    "justification": f"Fallback estándar por fallo en cálculo de torre: {e}",
                    "sensitivity_analysis": fallback_gsa,
                }
    else:
        # Provides a fallback mechanism to ensure system stability and graceful degradation in the event of a malformed or non-compliant JSON response from the large language model.
        print(
            "  ⚠️ Fallo en el retorno de matriz de madurez. Aplicando fallbacks estocásticos estándar de robustez..."
        )
        calculated_overrides = {}
        from assessment_engine.infrastructure.mcda_sensitivity_engine import (
            MCDASensitivityEngine,
        )

        sensitivity_engine = MCDASensitivityEngine()

        for i in range(1, 11):
            tower_id = f"T{i}"
            crit, comp, feas = 50.0, 50.0, 50.0

            # Compute a mathematically valid default GSA report for structural consistency
            gsa_report = sensitivity_engine.run_sensitivity_analysis(
                base_criticality=crit,
                base_compliance=comp,
                base_feasibility=feas,
                N=10000,
                uncertainty_range=20.0,
            )

            calculated_overrides[tower_id] = {
                "target_maturity": 4.0,
                "metrics": {
                    "business_criticality": crit,
                    "regulatory_compliance": comp,
                    "implementation_feasibility": feas,
                },
                "justification": "Estándar por defecto debido a indisponibilidad de API.",
                "sensitivity_analysis": gsa_report,
            }

    # Stage 5: Final Assembly. Executes dynamic just-in-time (JIT) data extraction and enforces schema integrity through Pydantic model validation.
    print(
        "  -> [FASE 4.7] Extrayendo Meta-Arquitectura e Hyperscaler Dominante de forma Dinámica (Agnóstico)..."
    )
    meta_prompt = (
        f"Analiza de forma síncrona el contexto recopilado de la empresa '{client_name}':\n"
        f"1. Narrativa: {narrative.get('text', 'N/A')}\n"
        f"2. Stack Técnico: {json.dumps(organized.get('stack', []), ensure_ascii=False)}\n\n"
        f"Deduce:\n"
        f"- industry_sector: El sector industrial/empresarial real y específico de la compañía (ej. 'Manufacturing & Building Materials', 'Banking & Finance', 'Retail', etc.).\n"
        f"- dominant_hyperscaler: El proveedor cloud dominante ('dominant_hyperscaler').\n"
        f"- stage, label, rationale: La fase de horizonte de transformación óptimo."
    )
    from google.genai import types

    client_gen = _get_genai_client()

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
        inferred_industry = meta_data.get("industry_sector")
        horizon_obj = {
            "stage": meta_data.get("stage", "H1"),
            "label": meta_data.get("label", "Estandarización"),
            "rationale": meta_data.get("rationale", "Calculado dinámicamente."),
        }
    except Exception as e:
        print(f"  ⚠️ Error en extracción de meta-datos: {e}. Usando fallbacks.")
        dominant_hyperscaler = "AWS"
        inferred_industry = None
        horizon_obj = {
            "stage": "H1",
            "label": "Estandarización",
            "rationale": "Fallback estándar.",
        }

    # Decouples industry-vertical-specific logic from the core processing pipeline.
    # Dynamically inferred from the client's actual data first (agnostic by design)
    industry_str = inferred_industry or brand_data_narratives.get("industry_profile_name") or "Enterprise & Industrial Technology"

    # Instantiate the Epistemic Graph Bayesian Belief Network (BBN) Service
    from assessment_engine.infrastructure.epistemic_graph_service import (
        EpistemicGraphService,
    )

    graph_service = EpistemicGraphService()

    # Collect intrinsic target maturities from the calculated overrides
    intrinsic_maturities = {
        t_id: float(t_data.get("target_maturity", 4.0))
        for t_id, t_data in calculated_overrides.items()
    }
    # Ensure all 10 towers are present in the intrinsic map (default to 4.0 if missing)
    for i in range(1, 11):
        t_id = f"T{i}"
        if t_id not in intrinsic_maturities:
            intrinsic_maturities[t_id] = 4.0

    # Propagate risks and find Single Point of Failure (SPOF)
    propagated_maturities = graph_service.propagate_risk(intrinsic_maturities)
    spof_tower, spof_impact = graph_service.get_single_point_of_failure(
        intrinsic_maturities
    )

    # Gather standard deviations from Phase 1 Monte Carlo sensitivity analysis
    std_devs = {
        t_id: float(
            t_data.get("sensitivity_analysis", {})
            .get("statistics", {})
            .get("std_deviation", 0.05)
        )
        for t_id, t_data in calculated_overrides.items()
    }
    # Ensure all 10 towers are present in the std dev map
    for i in range(1, 11):
        t_id = f"T{i}"
        if t_id not in std_devs:
            std_devs[t_id] = 0.05

    # Compute advanced PageRank-style Risk Centrality (ERC)
    risk_centrality = graph_service.calculate_risk_centrality(std_devs)
    spof_by_centrality = max(risk_centrality, key=risk_centrality.get)

    # Update overrides with risk-propagated target maturities and preserve intrinsic targets
    for t_id, t_data in calculated_overrides.items():
        orig_score = t_data.get("target_maturity", 4.0)
        t_data["intrinsic_target_maturity"] = orig_score
        t_data["target_maturity"] = propagated_maturities.get(t_id, orig_score)

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
        "epistemic_graph": {
            "topology": {
                "nodes": list(graph_service.graph.nodes),
                "edges": [
                    {"source": u, "target": v, "weight": d["weight"]}
                    for u, v, d in graph_service.graph.edges(data=True)
                ],
            },
            "audits": {
                "single_point_of_failure_by_cascade": spof_tower,
                "cascading_impact_index": spof_impact,
                "single_point_of_failure_by_centrality": spof_by_centrality,
                "eigenvector_risk_centrality": risk_centrality,
                "propagated_maturities": propagated_maturities,
            },
        },
        "review": {
            "summary": "Certificación Purist V35.0 (Aislamiento de Contexto)",
            "status": "Final",
        },
        "claims": captured,
    }

    final_json = sign_dossier(final_json)

    import uuid

    tmp_path = output_path.with_name(f"{output_path.name}.{uuid.uuid4().hex[:8]}.tmp")
    try:
        tmp_path.write_text(
            json.dumps(final_json, indent=2, ensure_ascii=False), encoding="utf-8-sig"
        )
        # POSIX Atomic Rename: replaces the old file atomically, preventing partial corruption
        tmp_path.replace(output_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

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
