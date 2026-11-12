"""Plain-Language Technical & Operational Narrative Formatter (Zero Jargon, 4-Step Causal Pattern)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


class PlainLanguageRiskNarrative:
    """Formats enterprise risk cards into an intuitive, 4-step plain-language operational narrative.

    Eradicates obscure actuarial jargon (Poisson, Euler copula, stochastic convolutions)
    and delivers an executive explanation in plain terms:
    1. ¿Qué falla realmente en los sistemas? (Technical root failure)
    2. ¿Qué se detiene en la operativa? (Business operational chain reaction by industry)
    3. ¿De dónde sale el coste económico? (Practical downtime hours + restoration costs)
    4. ¿Por qué tiene sentido la inversión? (Common sense business case ROI)
    """

    _INDUSTRY_DISRUPTIONS: Mapping[str, Mapping[str, str]] = {
        "manufacturing": {
            "T1": "Al fallar la alimentación eléctrica o refrigeración del CPD, se apagan los servidores que gestionan el pesaje y expedición. Se forman colas de camiones en las entradas de fábrica y se detiene la emisión de albaranes y salida de material durante {rto_h:.1f} horas.",
            "T2": "La caída de los servidores y máquinas virtuales paraliza las bases de datos y el ERP de planta, impidiendo programar órdenes de fabricación, consultar stocks y coordinar la logística.",
            "T3": "El corte de comunicaciones o fallo de enrutamiento aísla las fábricas y canteras satélite, impidiendo que las básculas transmitan los pesajes a las oficinas centrales.",
            "T4": "La saturación o bloqueo de cabinas de almacenamiento paraliza la escritura de las bases de datos transaccionales, congelando los aplicativos de planta.",
            "T5": "Ante una contingencia grave en el centro de datos principal, la falta de conmutación automatizada prolonga la parada operativa durante días por configuración manual.",
            "T6": "El uso de contraseñas compartidas o accesos sin proteger permite el secuestro o cifrado de los servidores de control por ransomware, obligando a apagar la infraestructura de producción.",
            "T7": "La falta de herramientas y procedimientos de soporte provoca que las incidencias de los sistemas fabriles se acumulen y tarden el triple de tiempo en resolverse.",
            "T8": "La inercia contractual y falta de revisión económica mantiene sobrecostes anuales en contratos duplicados que desvían fondos necesarios para modernizar la planta.",
            "T9": "La preparación manual de equipos informáticos y los fallos de puesto consumen cientos de horas de técnicos y operarios en tareas reactivas improductivas.",
            "T10": "La obsolescencia de software aplicativo (Oracle 10g/Forms) o pasarelas serie de báscula provoca paradas en la expedición por falta de repuestos y personal que conozca el código antiguo.",
            "default": "Interrupción de los aplicativos de fábrica, retraso en la expedición de pedidos a clientes y horas improductivas de personal técnico y de transporte.",
        },
        "healthcare": {
            "T1": "La caída de energía o clima del CPD hospitalario apaga los servidores de historia clínica (HIS) y diagnóstico por imagen (PACS), obligando al personal médico y enfermería a pasar a registro manual en papel.",
            "T2": "La indisponibilidad de clústeres de computación retrasa la validación de pruebas analíticas en laboratorio y la dispensación de medicación desde farmacia hospitalaria.",
            "T3": "El corte de red desconecta los puestos de triaje en urgencias y las terminales de enfermería en planta, ralentizando la atención a pacientes críticos.",
            "T4": "La falta de almacenamiento rápido o copias seguras impide recuperar radiografías y resonancias en tiempo real durante consultas y cirugías.",
            "T5": "La falta de un plan de contingencia probado obliga a suspender consultas externas y reprogramar cirugías ante cualquier fallo del centro principal.",
            "T6": "Una brecha de seguridad o malware en la red hospitalaria expone historiales médicos confidenciales y bloquea el acceso a equipos biomédicos monitorizados.",
            "T7": "La falta de un centro de soporte especializado demora la resolución de incidencias en puestos clínicos y terminales de quirófano.",
            "T8": "El descontrol presupuestario en software clínico y licencias desaprovechadas resta presupuesto asistencial para renovación de equipamiento médico.",
            "T9": "La lentitud en el arranque de ordenadores de consulta y problemas de acceso de los facultativos reduce el tiempo efectivo dedicado a la atención del paciente.",
            "T10": "Sistemas heredados de gestión hospitalaria sin soporte de fabricante generan caídas intermitentes en la citación de consultas y facturación a aseguradoras.",
            "default": "Afectación directa a la continuidad del flujo asistencial, retraso en diagnósticos y desvío de tiempo médico hacia contingencias administrativas.",
        },
        "banking": {
            "T1": "La caída del centro de procesamiento paraliza los motores de liquidación de pagos inmediatos y los enlaces con las cámaras de compensación interbancarias.",
            "T2": "La indisponibilidad de los servidores centrales detiene la operativa de banca digital, apps móviles y la autorización de compras con tarjeta en TPVs.",
            "T3": "El corte de comunicaciones aísla la red de oficinas bancarias y cajeros automáticos, impidiendo la atención presencial al público.",
            "T4": "La pérdida de consistencia en el almacenamiento transaccional bloquea el cierre contable diario y los balances de saldos de clientes.",
            "T5": "La lentitud en la conmutación al centro de respaldo en crisis expone a la entidad a sanciones millonarias de supervisores financieros bajo DORA.",
            "T6": "El compromiso de cuentas con privilegios de administración permite fraudes transaccionales masivos y exfiltración de datos financieros de clientes.",
            "T7": "La gestión reactiva de incidentes alarga el tiempo de caída de las plataformas de pagos, dañando la reputación de la entidad en el mercado.",
            "T8": "La falta de gobierno FinOps en arquitecturas cloud genera fugas millonarias de gasto en instancias de computación infrautilizadas.",
            "T9": "Puestos de trabajo bancarios con problemas de rendimiento ralentizan la operativa comercial en sucursales y la gestión de préstamos.",
            "T10": "El software bancario legacy (core cobol/mainframe) sin documentación ni talento joven eleva exponencialmente el coste de cualquier nuevo producto.",
            "default": "Bloqueo transaccional financiero, pérdida de operaciones comerciales en tiempo real y riesgo inmediato de sanciones regulatorias.",
        },
        "retail": {
            "T1": "La caída del CPD apaga las pasarelas de cobro centralizadas y la gestión logística de aprovisionamiento de tiendas y supermercados.",
            "T2": "La indisponibilidad de servidores paraliza la plataforma de e-commerce y los sistemas de picking en almacenes automatizados.",
            "T3": "La pérdida de red en puntos de venta impide el cobro con tarjeta en cajas, generando abandono de carritos y colas de clientes.",
            "T4": "La corrupción de datos en almacenamiento genera roturas de stock al desajustar el inventario físico frente al inventario digital.",
            "T5": "La falta de recuperación ante desastres en campañas punta (Black Friday / Navidades) genera pérdidas millonarias irrecuperables de facturación.",
            "T6": "El robo de credenciales de acceso a pasarelas de pago expone números de tarjeta de clientes a multas severas de PCI-DSS.",
            "T7": "Soporte técnico lento en tiendas que deja líneas de caja cerradas durante horas punta de afluencia de público.",
            "T8": "Sobrecostes no controlados en infraestructura de nube para picos de ventas que no se apagan tras finalizar la campaña comercial.",
            "T9": "Terminales de cobro (TPVs) y lectores de código de barras lentos o desactualizados que alargan el tiempo de espera de los clientes en caja.",
            "T10": "Sistemas de gestión de tienda antiguos sin integración en tiempo real que impiden conocer el stock real disponible para recogida en tienda.",
            "default": "Pérdida directa de ventas por parada de cajas, rotura de inventarios y abandono de clientes hacia la competencia.",
        },
    }

    @classmethod
    def format_plain_narrative(
        cls,
        tower_code: str,
        kpi_name: str,
        failure_desc: str,
        industry: str,
        sle: float,
        ale: float,
        rto_hours: float,
        hourly_rate: float,
        doc_lang: str = "es",
    ) -> str:
        """Constructs an intuitive 4-step plain-language narrative tailored to the client's industry."""
        normalized_tower = tower_code.strip().upper()
        norm_ind = industry.strip().lower()
        if "health" in norm_ind or "sanid" in norm_ind or "hospit" in norm_ind:
            ind_key = "healthcare"
        elif "bank" in norm_ind or "banc" in norm_ind or "financ" in norm_ind:
            ind_key = "banking"
        elif "retail" in norm_ind or "comerc" in norm_ind or "tiend" in norm_ind:
            ind_key = "retail"
        else:
            ind_key = "manufacturing"

        ind_dict = cls._INDUSTRY_DISRUPTIONS.get(ind_key, cls._INDUSTRY_DISRUPTIONS["manufacturing"])

        # Resolve finding-specific operational disruption to eliminate repetitive tower parrots with strict word boundaries
        f_lower = failure_desc.lower()
        import re
        if "85%" in f_lower or "memoria ram" in f_lower or "vsphere ha" in f_lower:
            op_disruption = (
                f"Ante la caída imprevista de un host físico de SimpliVity, la ocupación de RAM al 85% impide que el nodo superviviente "
                f"asuma la totalidad de máquinas virtuales sin degradación. Aunque vSphere HA reinicia las máquinas críticas en minutos, "
                f"la contención de memoria ralentiza las aplicaciones durante unas {max(0.5, rto_hours):.1f} horas hasta que el equipo de soporte restablece el host."
            )
        elif "fibra" in f_lower:
            op_disruption = (
                f"La rotura de la fibra óptica troncal interrumpe la replicación síncrona de almacenamiento entre CPD 1 y CPD 2, "
                f"forzando a los sistemas a operar en modo aislado y demorando la consolidación de pesajes durante las {max(0.5, rto_hours):.1f} horas que dura el empalme."
            )
        elif "batería" in f_lower or re.search(r"\bsai\b|\bups\b", f_lower) or "eléctric" in f_lower:
            op_disruption = (
                f"Un corte imprevisto de suministro donde los SAIs no mantengan la sala apaga los servidores en frío. "
                f"Durante las {max(0.5, rto_hours):.1f} horas de recuperación, las básculas deben operar de forma manual con albaranes en papel "
                f"hasta comprobar la integridad de las bases de datos y cabinas."
            )
        elif re.search(r"\bpam\b|\broot\b|privilegiad", f_lower):
            op_disruption = (
                f"El uso de credenciales privilegiadas compartidas permite a un intruso o ransomware sabotear los hipervisores y cabinas, "
                f"obligando a aislar la red de fábrica y detener temporalmente la expedición de camiones."
            )
        elif "switch" in f_lower or "core lan" in f_lower or re.search(r"\blan\b", f_lower):
            op_disruption = (
                f"La avería del switch troncal de planta aísla las oficinas y terminales de pesaje respecto al centro de datos, "
                f"retrasando la salida de camiones durante unas {max(0.5, rto_hours):.1f} horas hasta sustituir el equipo por repuesto en frío."
            )
        elif "wan" in f_lower or "cantera" in f_lower or "enlace" in f_lower:
            op_disruption = (
                f"La caída del enlace monofibra en canteras o plantas satélite deja sin comunicaciones a las básculas remotas, "
                f"obligando a registrar pesajes en local o en papel hasta el restablecimiento del servicio por la operadora."
            )
        elif "estanco" in f_lower or "polvo" in f_lower or "ip55" in f_lower:
            op_disruption = (
                f"La acumulación de polvo de cemento y temperatura en armarios no estancos provoca sobrecalentamiento y fallos de fuentes "
                f"en switches locales de planta, requiriendo intervenciones técnicas de sustitución de unas {max(0.5, rto_hours):.1f} horas."
            )
        else:
            op_disruption = ind_dict.get(normalized_tower, ind_dict["default"]).format(rto_h=max(0.5, rto_hours))

        # Common sense mitigation estimate (typically ~35% - 50% of annual risk)
        mitigation_est = max(1500.0, round(ale * 0.40, -2)) if ale > 2000.0 else max(1000.0, round(ale * 0.70, -2))

        # Distinguish between pure FinOps/efficiency waste vs physical/cyber operational outages
        f_lower = failure_desc.lower()
        is_finops = (
            sle <= 0
            or rto_hours <= 0
            or any(
                k in f_lower
                for k in [
                    "desmantelamiento",
                    "zombie",
                    "etiquetado",
                    "sobredimensionamiento",
                    "licencia",
                    "broadcom",
                    "nos",
                    "contrato",
                    "rightsizing",
                    "finops",
                    "desperdicio",
                    "aprovisionamiento restrictivo",
                    "manual de flota",
                    "autoevaluación",
                ]
            )
        )

        if ale > 0 and sle > 0:
            events_per_year = ale / sle
            if events_per_year >= 1.0:
                freq_str = f"unas {events_per_year:.1f} veces al año"
            else:
                years_between = round(1.0 / events_per_year, 1)
                freq_str = f"aproximadamente 1 vez cada {years_between:.1f} años"
        else:
            freq_str = "de forma continua en cada ejercicio presupuestario"

        if is_finops:
            op_text = (
                "Esta situación no provoca una parada de fábrica ni interrupción directa en las básculas de expedición. "
                "El impacto operativo consiste en una ineficiencia sostenida de la infraestructura, al mantener recursos de cómputo, "
                "almacenamiento SAN y licenciamiento asignados a entornos inactivos o contratos desalineados, reduciendo el margen de seguridad de la plataforma."
            )
            cost_text = (
                f"Se estima una ineficiencia económica anual de {ale:,.0f} €/año. Este importe representa el sobrecoste acumulado "
                f"por capacidad ociosa y compromisos contractuales evitables, sumado a las horas de ingeniería interna y soporte dedicadas "
                f"a tareas manuales de gestión y verificación que deberían estar automatizadas."
            )
        else:
            op_text = op_disruption
            cost_text = (
                f"Ante una contingencia imprevista, se estima una parada técnica de unas {max(0.5, rto_hours):.1f} horas con un impacto "
                f"por evento de {sle:,.0f} € (combinando horas de recuperación técnica y sobrecostes de operativa degradada en planta). "
                f"Al estimarse una recurrencia estadística de {freq_str}, la exposición anualizada se cuantifica en {ale:,.0f} €/año."
            )

        return f"• Impacto en la Operación:\n{op_text}\n\n• Justificación del Coste Económico:\n{cost_text}"
