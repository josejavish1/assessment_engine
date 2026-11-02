#!/usr/bin/env python3
"""Argon-4 Master Consultation: RFC 049 Dynamic Domain Modernization Focus & Tower Differentiation.

Addresses the user's critique:
"por cierto este párrafo parece exactamente igual en los 2 documentos:
'La plataforma actual sostiene con solvencia la operativa diaria... No obstante, se identifican áreas clave de modernización para dotar a las instalaciones de mayor redundancia física...'
¿es un antipatrón? ¿no podríamos aportar más valor?"
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)


def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)

    prompt = """
Role: Chief Enterprise Architect & Executive Editorial Fellow (McKinsey Senior Partner / Gartner VP / Google Core Infrastructure).

USER CRITIQUE & SYSTEMIC ANTIPATTERN DIAGNOSIS:
The user noticed:
"por cierto este párrafo parece exactamente igual en los 2 documentos:
'La plataforma actual sostiene con solvencia la operativa diaria de cargas de misión crítica de producción, expedición en planta y servicios corporativos centralizados gracias a la dedicación continua del equipo técnico. No obstante, se identifican áreas clave de modernización para dotar a las instalaciones de mayor redundancia física y tolerancia a fallos ante el incremento en la exigencia operativa del negocio.'
¿es un antipatrón? ¿no podríamos aportar más valor?"

ARCHITECTURAL EVALUATION:
1. The Antipattern:
   - Reusing identical boilerplate text across all 10 capability towers is a severe consulting and engineering antipattern.
   - Furthermore, asserting "dotar a las instalaciones de mayor redundancia física" in Tower 2 (Hybrid Compute), Tower 3 (Storage), Tower 4 (Network), Tower 6 (Cybersecurity), or Tower 10 (FinOps) is factually incorrect and amateurish because those domains deal with compute capacity, virtualization, storage IOPS, network paths, IAM, and cloud governance—not physical building facilities ("instalaciones").

2. The High-Value Architecture (RFC 049):
   - In `engine_config/locales.json`, under `tower_domain_semantics`, add `posture_modernization_focus` for each of the 10 capability towers (T1 through T10 + DEFAULT) in both Spanish (`es`) and English (`en`).
   - For example:
     * T1 (Physical Data Center): "reforzar la redundancia electromecánica y la climatización de precisión para blindar la alimentación de los equipos de planta" / "reinforcing electromechanical redundancy and precision cooling to safeguard continuous power to plant systems"
     * T2 (Hybrid Compute & Platforms): "ampliar la capacidad de memoria en los clústeres y asegurar la conmutación automática de máquinas virtuales sin degradación" / "expanding cluster memory capacity and ensuring automated virtual machine failover without performance degradation"
     * T3 (Storage): "garantizar la inmutabilidad de las copias de seguridad y eliminar cuellos de botella de I/O en las bases de datos transaccionales" / "guaranteeing backup immutability and eliminating I/O latency bottlenecks across transactional databases"
     * T4 (Network): "incorporar redundancia activa en las rutas de comunicaciones y segmentar el tráfico entre entornos corporativos e industriales" / "embedding active path redundancy across transit links and segmenting corporate from industrial OT traffic"
     * T5 (OT/Industrial): "reforzar la segregación de redes y la supervisión de controladores de planta para proteger las líneas de fabricación continua" / "strengthening network zoning and plant controller supervision to protect continuous manufacturing lines"
     * T6 (Cybersecurity): "elevar el control sobre cuentas privilegiadas e implantar monitorización continua para la detección temprana de amenazas" / "elevating privileged access governance and deploying continuous telemetry for early threat detection"
     * T7 (Business Applications): "estandarizar las integraciones y modernizar los desarrollos a medida para agilizar los procesos operativos y comerciales" / "standardizing core integrations and modernizing custom workflows to accelerate operational and commercial throughput"
     * T8 (Data & Analytics): "unificar los repositorios de información y mejorar la calidad del dato para acelerar la toma de decisiones directivas" / "unifying enterprise data repositories and improving data quality to accelerate executive decision-making"
     * T9 (Workplace): "homogeneizar los terminales de usuario y automatizar el despliegue de parches para reducir incidencias y costes de soporte" / "standardizing endpoint device configurations and automating patch distribution to reduce recurring support friction"
     * T10 (Cloud Governance & FinOps): "establecer guardrails automatizados de control de gasto y asegurar el cumplimiento continuo de estándares de arquitectura" / "enforcing automated cloud expenditure guardrails and ensuring continuous compliance with architectural standards"
     * DEFAULT: "reforzar los controles operativos y modernizar los componentes clave del dominio para maximizar la resiliencia" / "reinforcing operational controls and modernizing key domain components to maximize resilience"

3. Updated Paragraph 1 Template:
   - Spanish: "La evaluación técnica de la infraestructura de **{tower_name}** en {client_name} ({operational_mission}) sitúa su nivel de madurez estimado en **{maturity_score} sobre 5,0 ({maturity_tier_label})**. La plataforma actual sostiene con solvencia la operativa diaria de {primary_workloads_summary} gracias a la dedicación continua del equipo técnico. No obstante, se identifican oportunidades claras de modernización para **{posture_modernization_focus}** ante el incremento en la exigencia operativa del negocio."
   - English: "The technical assessment of the **{tower_name}** domain at {client_name} ({operational_mission}) establishes an estimated architectural maturity score of **{maturity_score} out of 5.0 ({maturity_tier_label})**. The current platform reliably supports daily operations across {primary_workloads_summary} through the ongoing stewardship of the engineering staff. However, key modernization opportunities exist to **{posture_modernization_focus}** as enterprise operational demands continue to scale."

NON-NEGOTIABLE LAWS:
1. Zero bugs, zero antipatterns.
2. Zero hardcoding (scales across any tenant, vertical, currency, or locale).
3. 100% Technical English codebase (zero Spanish words in Python code).
4. Split-brain eradication across all 10 capability towers.
5. OpenXML layout determinism.

YOUR TASK:
Synthesize an authoritative Architectural Blueprint (RFC 049) in Markdown:
1. Review and ratify the bilingual catalog additions for all 10 towers.
2. Review the Python implementation in `ExecutiveNarrativeSynthesizer.synthesize_chapter_one_paragraphs`.
3. Deliver a definitive VERDICT: PASS.
"""

    print(f"Requesting RFC 049 from {model_name}...")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    out_file = REPO_ROOT / "docs/architecture/RFC_049_DYNAMIC_DOMAIN_MODERNIZATION_FOCUS_ARGON.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(response.text, encoding="utf-8")

    print("\n" + "=" * 80)
    print("GEMINI-4-ARGON: RFC 049 DYNAMIC DOMAIN MODERNIZATION FOCUS")
    print("=" * 80)
    print(response.text)
    print("=" * 80)
    print(f"\nSaved to: {out_file.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
