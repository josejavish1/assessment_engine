"""Inject polymorphic tier focus descriptions into locales.json across all 6 languages."""

import json
from pathlib import Path

p = Path("engine_config/locales.json")
data = json.loads(p.read_text(encoding="utf-8"))

POLYMORPHIC_TIER_STRINGS = {
    "es": {
        "ch4_tier1_focus_capital_inefficiency": "Pasivos inminentes en renovaciones de licencias, penalizaciones de auditoría y desvío acumulado en consumo cloud.",
        "ch4_tier2_focus_capital_inefficiency": "Sobredimensionamiento de capacidades de cómputo, recursos huérfanos y falta de asignación de costes (showback).",
        "ch4_tier3_focus_capital_inefficiency": "Dispersión de suscripciones SaaS descentralizadas e ineficiencias de facturación de bajo importe.",
        
        "ch4_tier1_focus_regulatory_and_breach": "Vulnerabilidades críticas explotables, ausencia de segmentación IT/OT y riesgo de sanciones regulatorias mayores.",
        "ch4_tier2_focus_regulatory_and_breach": "Carencias en monitorización de seguridad (SIEM/SOC), control de accesos privilegiados (PAM) y planes de respuesta.",
        "ch4_tier3_focus_regulatory_and_breach": "Desviaciones menores en concienciación y procedimientos documentales de gobierno de seguridad.",
        
        "ch4_tier1_focus_productivity_toil": "Bloqueos operacionales y fallos de herramientas que paralizan la entrega de servicios o bloquean masivamente a usuarios.",
        "ch4_tier2_focus_productivity_toil": "Toil de soporte manual recurrente, triaje ineficiente y ausencia de flujos automatizados de resolución.",
        "ch4_tier3_focus_productivity_toil": "Fricciones de autoservicio y tiempos de espera menores en solicitudes no críticas.",
        
        "ch4_tier1_focus_availability_outage": "Puntos únicos de fallo estructural que paralizan servicios esenciales o interrumpen la continuidad del negocio.",
        "ch4_tier2_focus_availability_outage": "Vulnerabilidades operativas o redundancias incompletas que degradan el rendimiento y elevan el tiempo de recuperación (MTTR).",
        "ch4_tier3_focus_availability_outage": "Fricciones técnicas y fallos de componentes no redundados con impacto acotado en la operativa global.",
    },
    "en": {
        "ch4_tier1_focus_capital_inefficiency": "Imminent software license true-up liabilities, contract renewals, and cumulative on-demand cloud budget drift.",
        "ch4_tier2_focus_capital_inefficiency": "Oversized compute allocations, orphaned cloud resources, and lack of business unit cost allocation (showback).",
        "ch4_tier3_focus_capital_inefficiency": "Decentralized SaaS sprawl and micro-subscription billing inefficiencies.",
        
        "ch4_tier1_focus_regulatory_and_breach": "Critical exploitable vulnerabilities, lack of IT/OT segmentation, and major regulatory penalty exposure.",
        "ch4_tier2_focus_regulatory_and_breach": "Gaps in continuous security monitoring (SIEM/SOC), privileged access management (PAM), and incident response.",
        "ch4_tier3_focus_regulatory_and_breach": "Procedural compliance gaps and minor documentation drift without direct technical exploitability.",
        
        "ch4_tier1_focus_productivity_toil": "Operational bottlenecks and tool failures that halt service delivery or broadly disrupt end users.",
        "ch4_tier2_focus_productivity_toil": "Repetitive manual support toil, inefficient triage workflows, and absence of automated remediation.",
        "ch4_tier3_focus_productivity_toil": "Self-service friction and localized fulfillment delays on non-critical tickets.",
        
        "ch4_tier1_focus_availability_outage": "Structural single points of failure capable of halting essential operations or business continuity.",
        "ch4_tier2_focus_availability_outage": "Operational vulnerabilities or incomplete redundancies that degrade performance and extend recovery duration (MTTR).",
        "ch4_tier3_focus_availability_outage": "Localized non-redundant component failures with bounded operational impact.",
    }
}

# Mirror to other languages with English fallbacks if needed
for lang in ("pt", "fr", "de", "ja"):
    POLYMORPHIC_TIER_STRINGS[lang] = POLYMORPHIC_TIER_STRINGS["en"]

for lang, strings in POLYMORPHIC_TIER_STRINGS.items():
    if lang in data:
        data[lang].update(strings)

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("✓ Injected polymorphic tier focus strings across all languages in locales.json.")
