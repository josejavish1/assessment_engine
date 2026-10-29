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
        description="Maximum legal regulatory fine applicable to the client's industry sector and geography (e.g., 2% of annual turnover or applicable legal cap)."
    )
    hourly_rate_sre_eur: float = Field(
        default=36.0,
        description="Average hourly rate of a senior DevOps / SRE consulting engineer in the client's country and economic region in Euros."
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
        from assessment_engine.infrastructure.genai_client import (
            ModelTier,
            get_model,
        )

        self.client = genai.Client()
        self.model_name = get_model(ModelTier.FAST)
        self.env = env

    async def calibrate_client_scale(self, client_id: str, tower_id: str, raw_industry: str) -> Optional[DynamicRiskCalibration]:
        """Runs the Two-Step Decoupled Elicitation to generate custom_risk_profile.json."""
        client_name = client_id.split('_')[0].capitalize()
        case_dir = Path(f"working/{client_id}/{tower_id}")
        case_dir.mkdir(parents=True, exist_ok=True)
        output_path = case_dir / "custom_risk_profile.json"

        # Try to resolve client preferred country and currency from intelligence dossier
        target_currency = "EUR"
        target_symbol = "€"
        client_country = "Internacional"

        intel_path = Path(f"working/{client_id}/client_intelligence.json")
        if not intel_path.exists():
            client_base = client_id.split("_")[0]
            intel_path = Path(f"working/{client_id}/{client_base}/client_intelligence.json")

        if intel_path.exists():
            try:
                with open(intel_path, "r", encoding="utf-8-sig") as inf:
                    intel_json = json.load(inf)
                    intel_meta = intel_json.get("profile", {})
                    country = intel_meta.get("country") or intel_json.get("country")
                    if country:
                        client_country = country
                    currency = intel_meta.get("currency") or intel_json.get("currency")
                    if currency:
                        target_currency = currency.upper()
                        target_symbol = {
                            "USD": "$",
                            "GBP": "£",
                            "CHF": "CHF",
                            "BRL": "R$",
                            "MXN": "$",
                            "EUR": "€",
                        }.get(target_currency, target_currency)
            except (OSError, json.JSONDecodeError, KeyError, AttributeError) as ex:
                logger.debug(f"[Calibrator] Error leyendo client_intelligence opcional: {ex}")

        cid_tokens = client_id.lower().replace("-", "_").split("_")
        if "usd" in cid_tokens or "usa" in cid_tokens:
            target_currency = "USD"
            target_symbol = "$"
            client_country = "Estados Unidos"
        elif "gbp" in cid_tokens or "uk" in cid_tokens or "gbr" in cid_tokens:
            target_currency = "GBP"
            target_symbol = "£"
            client_country = "Reino Unido"
        elif "chf" in cid_tokens or "che" in cid_tokens or "switzerland" in cid_tokens:
            target_currency = "CHF"
            target_symbol = "CHF"
            client_country = "Suiza"

        try:
            logger.info(f"🌐 [Financial Calibrator] Iniciando Elicitación en Dos Pasos para sortear limitación de API de Google...")
            loop = asyncio.get_running_loop()

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
                                except (OSError, ValueError, KeyError, AttributeError) as ex:

                                    logger.debug(f"[Fallback] Excepción controlada: {ex}")
                    if scores_list:
                        if ha_score == 3.0:
                            ha_score = round(sum(scores_list[:max(1, len(scores_list)//2)]) / max(1, len(scores_list)//2), 1)
                        if ops_score == 3.0:
                            ops_score = round(sum(scores_list[len(scores_list)//2:]) / max(1, len(scores_list) - len(scores_list)//2), 1)
                except Exception as ex:
                    logger.warning(f"Error crawling local case input for resilience and scores: {ex}")
            
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
            
            - hourly_downtime_cost_eur: El coste estimado por hora de inactividad de la infraestructura digital y operaciones del cliente. 
              Para calibrar esta cifra con rigor actuarial y credibilidad directiva según el estándar mundial ITIC / Gartner:
              1. CRUCE POR SECTOR DE ACTIVIDAD:
                 - Sector Financiero, Banca, Seguros y Pasarelas de Pago: 0.003% a 0.006% de la facturación anual consolidada por hora (alta dependencia transaccional en tiempo real).
                 - Comercio Masivo, E-Commerce, Retail y Telecomunicaciones: 0.0015% a 0.0035% de la facturación anual consolidada por hora (canales continuos de venta y logística).
                 - Industria Pesada, Manufactura, Construcción y Energía: 0.0008% a 0.0018% de la facturación anual consolidada por hora (buffers operativos y sistemas de control local OT/SCADA).
                 - Servicios Profesionales, Sanidad y Sector Público: 0.0005% a 0.0015% de la facturación anual consolidada por hora.
              2. CRUCE CON MADUREZ TÉCNICA AUDITADA:
                 - Si la madurez de Resiliencia es >= 3.0 (clustering distribuido, failover geográfico, redundancia) y/o Monitorización >= 3.0, sitúa el coste efectivo en el tercio inferior del rango sectorial correspondiente.
                 - Si la madurez es baja (< 3.0), sitúa el coste en el tercio superior del rango sectorial.
              IMPORTANTE: Mantén siempre la proporcionalidad matemática con la facturación real del cliente sin inflar artificialmente el coste.
            
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
            
            # Hourly downtime cost is realistically bounded relative to annual turnover.
            company_hourly_revenue = max(1.0, calibration.annual_revenue_eur / 8760.0)
            max_realistic_hourly = company_hourly_revenue * 1.0  # Max 100% of hourly revenue
            min_realistic_hourly = max(1.0, company_hourly_revenue * 0.005)  # Min 0.5% of hourly revenue
            if calibration.hourly_downtime_cost_eur > max_realistic_hourly:
                logger.warning(
                    f"⚠️ [Financial Calibrator] Clamping disproportionate hourly downtime cost ({calibration.hourly_downtime_cost_eur:,.2f} €) "
                    f"to revenue ceiling ({max_realistic_hourly:,.2f} €)."
                )
                calibration.hourly_downtime_cost_eur = max_realistic_hourly
            elif calibration.hourly_downtime_cost_eur < min_realistic_hourly:
                calibration.hourly_downtime_cost_eur = min_realistic_hourly

            # Save the custom profile physically in the case folder
            with open(output_path, "w", encoding="utf-8-sig") as out_f:
                json.dump(calibration.model_dump(), out_f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ [Financial Calibrator] Perfil dinámico de riesgos de Internet guardado con ÉXITO en: {output_path}")
            return calibration

        except Exception as e:
            logger.warning(f"⚠️ [Financial Calibrator] Track 1 (Internet Grounding) falló o no tiene red: {e}. Activando Track 2 (Dossier Fallback)...")
            
            fallback_calibration = self._run_local_fallback(client_name, raw_industry, target_currency, target_symbol)
            
            # Write fallback to disk
            with open(output_path, "w", encoding="utf-8-sig") as out_f:
                json.dump(fallback_calibration.model_dump(), out_f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ [Financial Calibrator] Perfil dinámico de riesgos guardado bajo Fallback de Autocuración en: {output_path}")
            return fallback_calibration

    def _run_local_fallback(self, client_name: str, raw_industry: str, target_currency: str = "EUR", target_symbol: str = "€") -> DynamicRiskCalibration:
        """Saves a resilient, fail-safe estimation based on declarative scale tiers (FAIR-MAM)."""
        # Load dynamic financial fallbacks from config catalog (FAIR-MAM)
        fallbacks_path = Path(__file__).resolve().parents[4] / "engine_config" / "policies" / "financial_fallbacks.json"
        rates = {}
        sre_rates = {}
        scale_tiers = {}

        if fallbacks_path.exists():
            try:
                with open(fallbacks_path, "r", encoding="utf-8-sig") as cf:
                    fallbacks_data = json.load(cf).get("financial_fallbacks", {})
                    rates = fallbacks_data.get("exchange_rates", rates)
                    sre_rates = fallbacks_data.get("sre_hourly_rates", sre_rates)
                    scale_tiers = fallbacks_data.get("scale_tiers", scale_tiers)
            except Exception as e:
                logger.warning(f"Error loading financial fallbacks config: {e}")

        # Resolve tier dynamically from environment or declarative fallback
        detected_tier = os.environ.get("ASSESSMENT_COMPANY_SCALE", "").upper()
        if detected_tier not in scale_tiers:
            # Map default tier: Mid-Market as conservative enterprise standard
            detected_tier = "MID_MARKET"

        tier_cfg = scale_tiers.get(detected_tier, scale_tiers.get("MID_MARKET", {}))
        revenue = float(tier_cfg.get("annual_revenue_eur", 50000000.0))
        dependency = float(tier_cfg.get("digital_dependency_factor", 0.5))
        hourly_cost = (revenue * dependency) / 8760.0
        fine_ratio = float(tier_cfg.get("statutory_fine_cap_ratio", 0.03))
        max_fine = revenue * fine_ratio

        rate_val = rates.get(target_currency, 1.0)
        
        # Determine base rate for SRE from rate_card or fallback to 36.0 if not found
        sre_rate_val = sre_rates.get(target_currency, 36.0)

        justification_msg = (
            f"Tipo de cambio del BCE consolidado de resiliencia (tasa {rate_val} {target_currency}/EUR)."
            if target_currency != "EUR"
            else "Divisa base en Euros sin conversión."
        )

        return DynamicRiskCalibration(
            annual_revenue_eur=revenue,
            hourly_downtime_cost_eur=hourly_cost,
            reg_max_fine_eur=max_fine,
            hourly_rate_sre_eur=sre_rate_val,
            currency_code=target_currency,
            currency_symbol=target_symbol,
            exchange_rate=rate_val,
            currency_justification=justification_msg,
            calibration_justification=f"Calibración paramétrica de resiliencia fallback: Perfil de escala {detected_tier} derivado de configuración declarativa.",
        )
