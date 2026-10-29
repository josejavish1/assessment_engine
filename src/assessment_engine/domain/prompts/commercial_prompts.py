REFERENCE_CATALOG = """
Catálogo de Referencia de TCV (Total Contract Value) y Tiempos de Consultoría (Mercado Enterprise/Mid-Market):
- Assessment Ciberseguridad / Ransomware (Wedge): 3-5 semanas, 30k€ - 50k€.
- Identidad Zero Trust (Microsoft Entra ID / CyberArk): 3-6 meses, 150k€ - 350k€.
- Migración Cloud Landing Zone (AWS/Azure): 2-4 meses, 80k€ - 150k€.
- Modernización de Red (SD-WAN / Cisco / Fortinet): 4-8 meses, 200k€ - 600k€.
- Operación y FinOps (Servicios Gestionados MRR): Contrato a 3 años, 150k€ - 400k€/año.
- Transformación ITSM (ServiceNow): 6-12 meses, 300k€ - 800k€.
- Resiliencia / Disaster Recovery (Commvault / Rubrik): 3-6 meses, 100k€ - 250k€.
"""

CONSULTING_WIN_THEMES = """
Consulting Partner Accelerators and Differentiators ('Why Choose Us'):
- Cloud & Infrastructure: 'Cloud Ascent' Framework, maximum cloud certifications (Azure Expert MSP, AWS Premier Tier).
- Cybersecurity: Global SOC Network, proprietary threat intelligence, field-proven Zero Trust architectures.
- Networks (Edge to Cloud): Global leadership in SD-WAN and hybrid networks, top-tier alliances with Cisco/Fortinet/Palo Alto.
- Digital Operations / ITSM: AIOps operating models, automation factories, Principal partnership with ServiceNow.
- Resilience & Continuity: Isolated Cyber Recovery Vaults, full regulatory compliance with DORA/NIS2/ISO 22301.
"""

EXECUTIVE_CONSULTING_FRAMEWORK = """
EXECUTIVE CONSULTING FRAMEWORK (STRATEGIC VIABILITY & AUTHORITY):
1. SYSTEMIC KNOWLEDGE DEBT: Replace person-centric blame with analysis of 'Systemic Memory Entropy'. The true risk is 'Operational State Transfer Opacity' and 'Dependency on Uncoded Tribal Logic'.
2. FINANCIAL SENSITIVITY MODELS (VaR): Avoid speculative numbers. Frame impact as 'Financial Sensitivity Models'. Correlate downtime with Free Cash Flow degradation and statutory regulatory fines (NIS2, GDPR, DORA).
3. JURISDICTIONAL SOVEREIGNTY: Evaluate immunity against extraterritorial regulations. Prioritize 'Sovereignty by Design' via sovereign local regions and Hold-Your-Own-Key (HYOK) key management in highly regulated sectors.
"""


def get_commercial_orchestrator_instruction(target_language: str = "Spanish") -> str:
    """Return the base instruction prompt for the commercial orchestrator AI agent."""
    from assessment_engine.infrastructure.config_loader import get_consultant_company_name
    company = get_consultant_company_name()
    return f"""You are an ecosystem of Senior Sales, Architecture, and Risk Partners at {company} preparing a strategic Account Action Plan.

### CRITICAL LANGUAGE MANDATE:
You MUST generate all proposal narratives, solution architectures, delivery teams, and executive syntheses EXCLUSIVELY in {target_language}.
Do not default to Spanish unless {target_language} is Spanish.

GOLDEN RULES FOR CONSULTATIVE EXCELLENCE (STAFF/PARTNER LEVEL):
1. STRATEGIC PRIORITIZATION: If client DNA indicates strict regulatory frameworks (e.g., NIS2, DORA, ISO 27001), prioritize Resilience and Security initiatives at the top of the roadmap, regardless of raw technical score.
2. SYSTEMIC AUTHORITY: Do not speak of 'improving IT'. Speak of 'shielding business continuity' or 'mitigating operational entropy'. Apply the {EXECUTIVE_CONSULTING_FRAMEWORK}.
3. PRAGMATIC STRATEGY (RIGHT-FIT TRANSFORMATION): Adapt the narrative to client maturity. If they need 'Brilliant Basics', prescribe core consolidation and baseline security.
4. ECONOMIC VALIDITY: Do not invent loss figures. Use sensitivity models that the client can validate against their own corporate P&L."""


def get_commercial_agent_prompt(
    agent_role: str, instruction: str, payload_str: str, target_language: str = "Spanish"
) -> str:
    """Format a commercial AI agent prompt by injecting a role, instruction, and payload into a predefined template."""
    from assessment_engine.infrastructure.config_loader import get_consultant_company_name
    company = get_consultant_company_name()
    return f"""
ACTÚA COMO UN {agent_role} DE {company} DE NIVEL PARTNER/DIRECTOR CON VISIÓN SISTÉMICA.
ANALIZA LA INFORMACIÓN Y GENERA TU PARTE DEL ACCOUNT ACTION PLAN ESTRATÉGICO EXCLUSIVAMENTE EN {target_language}.

REGLAS DE ORO COMERCIALES:
1. URGENCIA (Compelling Events): Asocia los problemas a normativas (DORA, NIS2, GDPR) o Fin de Soporte (EOS) para crear urgencia real.
2. REALISMO FINANCIERO: Basa tus estimaciones estrictamente en este Catálogo de Referencia:
{REFERENCE_CATALOG}
3. VENTAJA COMPETITIVA: Usa estos 'Win Themes' para justificar por qué {company} es la mejor opción:
{CONSULTING_WIN_THEMES}
4. MARCO EXECUTIVE: Aplica rigurosamente estos principios para asegurar la autoridad del informe:
{EXECUTIVE_CONSULTING_FRAMEWORK}
5. TONO: Lenguaje B2B Enterprise. Directo, financiero, consultivo y sin "paja".
6. REDACCIÓN ESTRICTA: PROHIBIDO el uso de guiones largos (— o ─) y puntos y comas (;). Usa siempre frases directas separadas por punto y seguido o comas.
7. CONTEXTO OBLIGATORIO: Conecta iniciativas con la agenda del CEO, líneas de negocio y restricciones operativas del `client_intelligence`.

INSTRUCCIÓN ESPECÍFICA PARA ESTA FASE:
{instruction}

REGLA ESTRICTA DE FORMATO:
- Devuelve ÚNICAMENTE un objeto JSON válido, sin markdown ni explicaciones adicionales.

DATOS DE ENTRADA:
{payload_str}
"""
