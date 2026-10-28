import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import asyncio
import os
from pydantic import BaseModel, Field
from google import genai

logger = logging.getLogger(__name__)

class DynamicRiskCalibration(BaseModel):
    """Structured financial schema representing the calibrated loss magnitude limits."""
    annual_revenue_eur: float = Field(
        description="Factual consolidated annual revenue of the client organization in Euros, e.g., 4900000000.0."
    )
    hourly_downtime_cost_eur: float = Field(
        description="Estimated operational hourly downtime cost for the client's critical virtual platform, e.g., 150000.0."
    )
    reg_max_fine_eur: float = Field(
        description="Maximum legal regulatory fine applicable to the client's industry sector and geography (e.g., up to 10000000.0 for NIS2 in Spain)."
    )
    hourly_rate_sre_eur: float = Field(
        default=36.0,
        description="Average hourly rate of a senior DevOps / SRE consulting engineer in the client's country in Euros, e.g., 36.0 for Spain or 150.0 for Switzerland."
    )
    currency_code: str = Field(
        default="EUR",
        description="The ISO currency code preferred by the client for report presentation, e.g., 'EUR', 'USD', or 'GBP'."
    )
    currency_symbol: str = Field(
        default="€",
        description="The currency symbol corresponding to the currency code, e.g., '€', '$', or '£'."
    )
    exchange_rate: float = Field(
        default=1.0,
        description="The dynamic exchange rate from EUR to the target currency_code (e.g., 1.0925 for EUR to USD)."
    )
    currency_justification: str = Field(
        default="Cambio de divisa base en Euros sin conversión (tasa 1.0).",
        description="SME Elicitation Rationale citing the official exchange rate published by the European Central Bank (BCE) with dates."
    )
    calibration_justification: str = Field(
        description="SME Elicitation Rationale (SR 11-7 Model Validation Rationale) citing real financial annual reports or official gazettes from Google Search."
    )

class FinancialScaleCalibrator:
    """
    Automated risk calibrator that queries Gemini with Google Search (Internet Grounding)
    to dynamically research the client's annual revenue, regulatory exposure, live exchange rates,
    and average DevOps/SRE hourly rates, applying a Two-Step Decoupled Elicitation
    to bypass Google API constraints, backed by a local fallback track.
    """
    def __init__(self, env=None):
        self.client = genai.Client()
        self.model_name = "gemini-2.5-pro"
        self.env = env

    async def calibrate_client_scale(self, client_id: str, tower_id: str, raw_industry: str) -> Optional[DynamicRiskCalibration]:
        """Runs the Two-Step Decoupled Elicitation to generate custom_risk_profile.json."""
        client_name = client_id.split('_')[0].capitalize()
        case_dir = Path(f"working/{client_id}/{tower_id}")
        case_dir.mkdir(parents=True, exist_ok=True)
        output_path = case_dir / "custom_risk_profile.json"

        # Try to resolve client preferred currency from context
        target_currency = "EUR"
        target_symbol = "€"
        client_country = "España"
        if "usd" in client_id.lower() or "us" in client_id.lower() or "global" in raw_industry.lower():
            target_currency = "USD"
            target_symbol = "$"
            client_country = "Estados Unidos"
        elif "gbp" in client_id.lower() or "uk" in client_id.lower():
            target_currency = "GBP"
            target_symbol = "£"
            client_country = "Reino Unido"
        elif "chf" in client_id.lower() or "switzerland" in client_id.lower():
            target_currency = "CHF"
            target_symbol = "CHF"
            client_country = "Suiza"

        try:
            logger.info(f"🌐 [Financial Calibrator] Iniciando Elicitación en Dos Pasos para sortear limitación de API de Google...")
            loop = asyncio.get_running_loop()

            # --- STEP 0.8: Crawl Local Private Architecture Context from Case Input ---
            local_context_str = ""
            ha_score = 3.0       # Default standard
            ops_score = 3.0      # Default standard
            
            case_input_file = case_dir / "case_input.json"
            if case_input_file.exists():
                try:
                    with open(case_input_file, "r", encoding="utf-8-sig") as jf:
                        case_data = json.load(jf)
                    
                    found_snippets = []
                    context_summary = case_data.get("context_summary", "")
                    if context_summary:
                        found_snippets.append(f"Contexto general: {context_summary[:1000]}")
                    
                    def extract_resilience_hints(obj, matches):
                        if isinstance(obj, dict):
                            for k, v in obj.items():
                                if isinstance(v, (dict, list)):
                                    extract_resilience_hints(v, matches)
                                elif isinstance(v, str):
                                    if any(x in v.lower() for x in ["cpd", "backup", "redundancia", "replica", "contingencia", "recuperacion"]):
                                        matches.append(v[:400])
                        elif isinstance(obj, list):
                            for item in obj:
                                extract_resilience_hints(item, matches)
                    
                    hints = []
                    extract_resilience_hints(case_data, hints)
                    if hints:
                        found_snippets.append("Pistas de Arquitectura Privada encontradas:\n" + "\n- ".join(set(hints[:5])))
                    
                    local_context_str = "\n\n".join(found_snippets)[:2500]

                    # Extract specific structured questions (Maturity Matrix scores)
                    questions_list = []
                    if isinstance(case_data, dict):
                        for k, v in case_data.items():
                            if isinstance(v, list):
                                questions_list.extend(v)
                    scores_list = []
                    for q in questions_list:
                        if isinstance(q, dict):
                            q_id = str(q.get("question_id", ""))
                            val = q.get("value")
                            if val is not None:
                                try:
                                    score_val = float(val)
                                    scores_list.append(score_val)
                                    if f"{tower_id}.P1" in q_id or "K1" in q_id or "K4" in q_id:
                                        ha_score = score_val
                                    if f"{tower_id}.P5" in q_id or f"{tower_id}.P2" in q_id:
                                        ops_score = score_val
                                except Exception:
                                    pass
                    if scores_list:
                        if ha_score == 3.0:
                            ha_score = round(sum(scores_list[:max(1, len(scores_list)//2)]) / max(1, len(scores_list)//2), 1)
                        if ops_score == 3.0:
                            ops_score = round(sum(scores_list[len(scores_list)//2:]) / max(1, len(scores_list) - len(scores_list)//2), 1)
                except Exception as ex:
                    logger.warning(f"Error crawling local case input for resilience and scores: {ex}")
            
            # --- STEP 1: Quantitative Research via Google Search (No structured output constraints) ---
            research_prompt = f"""
            Investiga con internet (Google Search) de forma rigurosa los siguientes datos financieros y de costes laborales para la empresa "{client_name}" (sector: "{raw_industry}") en {client_country}:
            1. Su facturación anual consolidada más reciente (en Euros).
            2. El coste por hora estimado de inactividad de su plataforma corporativa de TI, centros de datos y operaciones digitales (el cual debe ser proporcional al tamaño e ingresos de la organización y reflejar el coste de parada operativa de sus servidores y servicios informáticos y de negocio internos).
            3. El límite máximo de multa reguladora aplicable bajo la directiva NIS2 (el cual ronda hasta 10.000.000 € o el 2% de su facturación global, lo que sea mayor).
            4. El tipo de cambio oficial del Euro (EUR) a la divisa preferida "{target_currency}" publicado por el Banco Central Europeo (BCE) al día de hoy, detallando su justificación citada con fecha.
            5. La tarifa horaria promedio en Euros de un consultor senior de DevOps / SRE en {client_country} en 2026.
            
            Devuelve un resumen detallado con todas las cifras reales encontradas y cita minuciosamente tus fuentes oficiales (informes financieros, boletines gubernamentales, comunicados oficiales del BCE, etc.).
            """
            
            logger.info(f"🌐 [Financial Calibrator] [Paso 1: Investigación] Consultando Google Search para {client_name} en {client_country}...")
            research_result = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model_name,
                    contents=research_prompt,
                    config=genai.types.GenerateContentConfig(
                        tools=[{"google_search": {}}],  # Google Search Grounding active
                        temperature=0.1
                    )
                )
            )
            raw_text = research_result.text
            
            # --- STEP 2: Extraction and Structuring into Pydantic Schema (No search tool constraints) ---
            struct_prompt = f"""
            Eres un validador financiero senior y experto en gestión de riesgos (SR 11-7 standard). Tu tarea es extraer y estructurar las cifras de investigación del texto proporcionado y formatearlas estrictamente en el JSON pedido bajo el esquema DynamicRiskCalibration.
            
            Texto de Investigación de Internet (OSINT):
            \"\"\"{raw_text}\"\"\"
            
            Contexto de Arquitectura Técnica Interna Privada del Cliente (Auditoría Local):
            \"\"\"{local_context_str}\"\"\"
            
            Métricas de Madurez Técnica Auditadas en Local para este Cliente:
            - Nivel de Resiliencia / Continuidad ({tower_id}): {ha_score}/5.0
            - Nivel de Operaciones / Monitorización ({tower_id}): {ops_score}/5.0
            
            Extrae de forma exacta y calcula:
            - annual_revenue_eur: La facturación consolidada de {client_name} en Euros.
            - reg_max_fine_eur: El límite máximo de multa reguladora aplicable bajo la directiva NIS2.
            - hourly_rate_sre_eur: La tarifa horaria de consultoría senior de DevOps / SRE para {client_country} en Euros.
            
            - hourly_downtime_cost_eur: El coste por hora de inactividad de su plataforma de TI, centros de datos y operaciones. 
              Para calibrar esta cifra de forma realista, realiza un razonamiento cruzado:
              1. Toma como límite de escala general proporcional una fracción de entre el 0.001% y el 0.01% de su facturación anual consolidada.
              2. CRUCE CON MADUREZ TÉCNICA LOCAL: Analiza las 'Métricas de Madurez Técnica' y el 'Contexto de Arquitectura' del cliente:
                 - Si la madurez de Resiliencia es >= 3.0 (clustering distribuido, failover geográfico, redundancia) y/o el nivel de Monitorización es >= 3.0, significa que cuentan con alta tolerancia a fallos. Sitúa el coste de inactividad efectiva en el extremo inferior del rango proporcional (ej. hacia el 0.001% de su facturación anual).
                 - Si la madurez es baja (< 3.0), significa que sufren de puntos únicos de fallo (SPOF) o falta de monitorización. Sitúa el coste en el extremo superior (ej. hacia el 0.01% de su facturación anual).
            
            Establece obligatoriamente de forma constante:
            - currency_code: "{target_currency}"
            - currency_symbol: "{target_symbol}"
            - exchange_rate: El tipo de cambio oficial de EUR a {target_currency} extraído del texto de investigación (por ejemplo, 1.0925).
            - currency_justification: Una justificación formal citando la tasa y la fuente del BCE del texto de investigación.
            - calibration_justification: La justificación de validación citando los ingresos del ejercicio, las fuentes de internet, y el análisis cruzado de resiliencia (basado en las respuestas reales de madurez del cuestionario local de la torre {tower_id} de este cliente) de la arquitectura privada del cliente.
            """
            
            logger.info(f"🌐 [Financial Calibrator] [Paso 2: Estructurado] Parseando datos de investigación en el esquema Pydantic...")
            struct_result = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model_name,
                    contents=struct_prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=DynamicRiskCalibration,
                        temperature=0.1
                    )
                )
            )
            
            # Validate and parse response
            calibration = DynamicRiskCalibration.model_validate_json(struct_result.text)
            
            # --- SOTA RISK GUARDRAIL (Anti-Hallucination Clamp) ---
            # An hourly downtime cost of e.g. 187M EUR/hour is a severe scale hallucination.
            # Even for critical infrastructure, hourly downtime cost should be bounded relative to annual revenue.
            # We calculate the company's total hourly revenue rate (Revenue / 8760).
            # We set the maximum realistic downtime cost to 5x the hourly revenue rate, or a hard cap of 500,000 EUR/hour.
            company_hourly_revenue = calibration.annual_revenue_eur / 8760.0
            max_realistic_hourly = max(50000.0, min(500000.0, company_hourly_revenue * 5.0))
            if calibration.hourly_downtime_cost_eur > max_realistic_hourly:
                logger.warning(
                    f"⚠️ [Financial Calibrator] Clamping disproportionate hourly downtime cost ({calibration.hourly_downtime_cost_eur:,.2f} €) "
                    f"to realistic guardrail ({max_realistic_hourly:,.2f} €)."
                )
                calibration.hourly_downtime_cost_eur = max_realistic_hourly

            # Save the custom profile physically in the case folder
            with open(output_path, "w", encoding="utf-8-sig") as out_f:
                json.dump(calibration.model_dump(), out_f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ [Financial Calibrator] Perfil dinámico de riesgos de Internet guardado con ÉXITO en: {output_path}")
            return calibration

        except Exception as e:
            logger.warning(f"⚠️ [Financial Calibrator] Track 1 (Internet Grounding) falló o no tiene red: {e}. Activando Track 2 (Dossier Fallback)...")
            
            # --- TRACK 2: Local Dossier Fallback ---
            fallback_calibration = self._run_local_fallback(client_name, raw_industry, target_currency, target_symbol)
            
            # Write fallback to disk
            with open(output_path, "w", encoding="utf-8-sig") as out_f:
                json.dump(fallback_calibration.model_dump(), out_f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ [Financial Calibrator] Perfil dinámico de riesgos guardado bajo Fallback de Autocuración en: {output_path}")
            return fallback_calibration

    def _run_local_fallback(self, client_name: str, raw_industry: str, target_currency: str = "EUR", target_symbol: str = "€") -> DynamicRiskCalibration:
        """Saves a resilient, fail-safe estimation based on client sector metadata."""
        is_large_critical = any(
            k in raw_industry.lower() or k in client_name.lower()
            for k in ["critical", "energy", "infraestructura", "banca", "finance"]
        )

        # Load dynamic financial fallbacks from config catalog (FAIR-MAM)
        fallbacks_path = Path(__file__).resolve().parents[4] / "engine_config" / "policies" / "financial_fallbacks.json"
        rates = {"EUR": 1.0, "USD": 1.09, "GBP": 0.84, "CHF": 0.96}
        sre_rates = {"EUR": 36.0, "USD": 110.0, "GBP": 95.0, "CHF": 140.0}
        
        if fallbacks_path.exists():
            try:
                with open(fallbacks_path, "r", encoding="utf-8-sig") as cf:
                    fallbacks_data = json.load(cf).get("financial_fallbacks", {})
                    rates = fallbacks_data.get("exchange_rates", rates)
                    sre_rates = fallbacks_data.get("sre_hourly_rates", sre_rates)
            except Exception as e:
                logger.warning(f"Error loading financial fallbacks config: {e}")

        rate_val = rates.get(target_currency, 1.0)
        sre_rate_val = sre_rates.get(target_currency, 36.0)
        
        justification_msg = f"Tipo de cambio del BCE consolidado de resiliencia (tasa {rate_val} {target_currency}/EUR)." if target_currency != "EUR" else "Divisa base en Euros sin conversión."

        if is_large_critical:
            # High-end default corporate baseline values
            return DynamicRiskCalibration(
                annual_revenue_eur=4900000000.0,  # High-end default corporate baseline value (4.9B EUR standard)
                hourly_downtime_cost_eur=150000.0,
                reg_max_fine_eur=10000000.0,
                hourly_rate_sre_eur=sre_rate_val,
                currency_code=target_currency,
                currency_symbol=target_symbol,
                exchange_rate=rate_val,
                currency_justification=justification_msg,
                calibration_justification="Calibración de resiliencia fallback: Estimación conservadora basada en el sector esencial y tamaño crítico del operador nacional."
            )
        else:
            # Medium business default baseline values
            return DynamicRiskCalibration(
                annual_revenue_eur=50000000.0,
                hourly_downtime_cost_eur=5000.0,
                reg_max_fine_eur=2000000.0,
                hourly_rate_sre_eur=sre_rate_val,
                currency_code=target_currency,
                currency_symbol=target_symbol,
                exchange_rate=rate_val,
                currency_justification=justification_msg,
                calibration_justification="Calibración de resiliencia fallback: Estimación de perfil estándar adecuada para corporaciones de volumen medio."
            )
