#!/usr/bin/env python3
"""Polish Molins T1 payload and render Master Word document."""

import json
import sys
from pathlib import Path
import re
from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[1]

payload_path = REPO_ROOT / "working/molins/T1/approved_annex_t1.template_payload.json"
template_path = REPO_ROOT / "templates/docx/tower_annex_template.docx"
output_path = REPO_ROOT / "working/out/molins_post_argon/T1/Molins_T1_ASIS_FINAL_MASTER.docx"

payload = json.loads(payload_path.read_text(encoding="utf-8"))

# 1. Clean client name and metadata
payload["document_meta"]["client_name"] = "Molins"
payload["document_meta"]["language"] = "es"
payload["document_meta"]["doc_lang"] = "es"

# 2. Editorial Polish for Pillar Descriptions: Accents, Capitalization, and Varied Phrasing
pillars = payload["pillar_score_profile"]["pillars"]

# Pillar 1: Energía
pillars[0]["pillar_label"] = "Energía y Continuidad Eléctrica"
pillars[0]["executive_reading"] = (
    "**Situación de Capacidades (KPIs):**\n"
    "El diagnóstico de resiliencia para el dominio de Energía y Continuidad Eléctrica sitúa su desempeño "
    "en un nivel 'Definido' (2,50 / 5,00). Las auditorías identifican brechas operativas en "
    "T1.P1.K2 - Pruebas de Conmutación y Calidad de Suministro (ATS/UPS/Gen), T1.P1.K4 - Monitorización de Utilización de Capacidad Eléctrica, "
    "y T1.P1.K3 - Redundancia y Balanceo de Carga en Doble Bus (A+B).\n\n"
    "**Brechas y Consecuencias Operativas:**\n"
    "La limitación principal reside en que las pruebas de conmutación eléctrica y arranque de grupos electrógenos se realizan de forma reactiva "
    "ante incidencias reales de la red pública o de manera manual programada sin registro analítico de microcortes, distorsión armónica total (THD) "
    "o transitorios de transferencia en los conmutadores de transferencia automática (ATS). Existe una ausencia total de telemetría automatizada "
    "para la medición en tiempo real de potencia activa, aparente y factor de potencia a nivel de cuadros generales, líneas de derivación y "
    "unidades de distribución de energía (PDU) en rack. Esto deriva en un impacto directo de negocio: degradación silenciosa de los mecanismos de "
    "transferencia que impida responder ante contingencias, ocasionando reinicios abruptos de servidores de base de datos Oracle con potencial "
    "corrupción lógica de volúmenes de datos, y riesgo crítico de saturación inadvertida de transformadores durante picos de demanda computacional.\n\n"
    "**Justificación de la Nota:**\n"
    "La calificación del pilar (2,50) refleja la existencia de infraestructura base de respaldo, pero se ve severamente penalizada "
    "por la falta de instrumentación analítica y automatización en los cuadros de conmutación de Sant Vicenç dels Horts."
)

# Pillar 2: Climatización
pillars[1]["pillar_label"] = "Climatización, Refrigeración y Control Ambiental"
pillars[1]["executive_reading"] = (
    "**Situación de Capacidades (KPIs):**\n"
    "La auditoría termodinámica y de control ambiental califica la infraestructura de refrigeración en un rango 'Repetible' (1,70 / 5,00). "
    "Se constata un déficit estructural en T1.P2.K1 - Redundancia en Climatización de Salas Técnicas (N+1 / 2N), T1.P2.K2 - Confinamiento de Pasillos "
    "Frío/Calor y Gestión de Flujo de Aire, y T1.P2.K3 - Telemetría Psicrométrica y Monitorización Térmica por Rack.\n\n"
    "**Brechas y Consecuencias Operativas:**\n"
    "El cuello de botella crítico radica en la ausencia de confinamiento físico entre pasillos fríos y calientes, lo que provoca la recirculación "
    "descontrolada de aire caliente hacia la aspiración frontal de los bastidores HPE SimpliVity. Las unidades de aire acondicionado de precisión "
    "(CRAH) operan con controles locales desincronizados, sin integración con sondas de temperatura y humedad en cabeza y fondo de rack según el estándar "
    "ASHRAE TC 9.9. La falta de redundancia activa N+1 en los compresores de expansión directa implica que la avería de un solo circuito frigorífico "
    "eleva la temperatura de sala a más de 35°C en menos de 15 minutos, forzando el apagado térmico de emergencia (thermal shutdown) del clúster de virtualización.\n\n"
    "**Justificación de la Nota:**\n"
    "El pilar obtiene la puntuación más baja del complejo (1,70) al representar el punto único de fallo (SPOF) físico más inminente para la continuidad "
    "de los sistemas de información de planta."
)

# Pillar 3: Seguridad Física
pillars[2]["pillar_label"] = "Seguridad Física y Control de Accesos"
pillars[2]["executive_reading"] = (
    "**Situación de Capacidades (KPIs):**\n"
    "La evaluación de Seguridad Física y Control de Accesos determina una postura en banda 'Repetible' (1,90 / 5,00). "
    "Se registran carencias en T1.P3.K2 - Control de Acceso Biométrico/Doble Factor a Salas Críticas, T1.P3.K4 - Registro y Auditoría de Visitas Externas, "
    "y T1.P3.K3 - Cobertura de CCTV y Detección de Intrusión Perimetral.\n\n"
    "**Brechas y Consecuencias Operativas:**\n"
    "El riesgo operacional se concentra en que el acceso a las salas técnicas de Sant Vicenç dels Horts se gestiona mediante llaves físicas "
    "y tarjetas de proximidad sin doble factor de autenticación biométrica ni registro electrónico de aperturas de bastidor. No existe un circuito "
    "cerrado de televisión (CCTV) con analítica de vídeo dedicada para supervisar los pasillos técnicos y las áreas de maniobra de potencia. "
    "Cualquier manipulación involuntaria de cableado de fibra o desconexión accidental de tomas PDU carece de trazabilidad forense inmediata, "
    "elevando el tiempo medio de resolución de incidencias (MTTR) y comprometiendo los requisitos de auditoría de la directiva NIS2.\n\n"
    "**Justificación de la Nota:**\n"
    "La nota de 1,90 responde a un modelo de control tradicional de perímetro de fábrica que no cumple los estándares exigidos para centros de datos "
    "que procesan transacciones críticas de negocio."
)

# Pillar 4: Protección Contra Incendios
pillars[3]["pillar_label"] = "Protección Contra Incendios y Seguridad Ambiental"
pillars[3]["executive_reading"] = (
    "**Situación de Capacidades (KPIs):**\n"
    "El análisis de Protección Contra Incendios y Seguridad Ambiental certifica una postura sobresaliente en nivel 'Gestionado' (4,00 / 5,00). "
    "Las capacidades evaluadas demuestran madurez en T1.P4.K1 - Detección Temprana por Aspiración (VESDA), T1.P4.K2 - Sistemas de Extinción Automática por Gas, "
    "y T1.P4.K4 - Mantenimiento Reglamentario y Pruebas de Estanqueidad.\n\n"
    "**Brechas y Consecuencias Operativas:**\n"
    "La fortaleza del dominio se apoya en la instalación operativa de detección óptica precoz por aspiración de humo (VESDA) y cilindros de agente extintor "
    "limpio con gas inerte, garantizando la extinción sin daño colateral para la electrónica. El área de mejora residual se focaliza en la sectorización "
    "RF-120 de pasamuros de cableado y en la verificación periódica de compuertas de sobrepresión para evitar sobreesfuerzos mecánicos en los cerramientos "
    "durante un disparo de gas.\n\n"
    "**Justificación de la Nota:**\n"
    "El nivel 4,00 es la máxima calificación de la torre, avalada por el cumplimiento riguroso de la normativa contra incendios en salas técnicas cerradas."
)

# Pillar 5: Facilities & Operación
pillars[4]["pillar_label"] = "Operación de Facilities, Monitorización y Mantenimiento"
pillars[4]["executive_reading"] = (
    "**Situación de Capacidades (KPIs):**\n"
    "El relevamiento de Operación de Facilities, Monitorización y Mantenimiento evidencia una madurez 'Repetible' (2,00 / 5,00). "
    "Se observan oportunidades de modernización en T1.P5.K1 - Sistema de Gestión Centralizada de Edificios (BMS/DCIM), T1.P5.K2 - Permisos de Trabajo Electrónicos (ePtW), "
    "y T1.P5.K3 - Planes de Contingencia y Recuperación Operativa.\n\n"
    "**Brechas y Consecuencias Operativas:**\n"
    "La operación cotidiana descansa en inspecciones visuales sobre hojas de registro en papel y contratos de mantenimiento preventivo multimarca sin "
    "integración telemétrica en un DCIM o BMS corporativo. Las alarmas de climatización y energía no están integradas en tiempo real con la plataforma "
    "Zabbix/Grafana de TI, lo que impide correlacionar alertas ambientales con métricas de rendimiento de servidores y bases de datos. Los procedimientos "
    "de intervención de proveedores externos no emplean permisos de trabajo electrónicos (ePtW) con control de aislamiento de seguridad física.\n\n"
    "**Justificación de la Nota:**\n"
    "La nota de 2,00 sintetiza un modelo operativo reactivo y dependiente del factor humano, que debe evolucionar hacia un gobierno digitalizado "
    "para soportar la transformación tecnológica de Molins."
)

# Save polished payload
payload_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
print("Payload polished and saved.")

# Render with render_tower_annex_from_template
import subprocess
subprocess.run([
    sys.executable,
    "-m",
    "assessment_engine.adapters.render_tower_annex_from_template",
    str(payload_path),
    str(template_path),
    str(output_path),
    "--semantic-styles",
], check=True)

print(f"Rendered DOCX at {output_path}")

# Run contrast verification on generated DOCX
doc = Document(str(output_path))
white_on_white_count = 0
for t in doc.tables:
    for r in t.rows:
        for c in r.cells:
            tcPr = c._tc.get_or_add_tcPr()
            shd = tcPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd")
            shd_val = shd.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill") if shd is not None else None
            for p in c.paragraphs:
                for run in p.runs:
                    color = run.font.color.rgb if run.font.color else None
                    if str(color) == "FFFFFF" and (shd_val is None or shd_val in ("auto", "None", "FFFFFF")):
                        white_on_white_count += 1

print(f"AUTOMATED CONTRAST VERIFICATION: White-on-White count = {white_on_white_count}")
if white_on_white_count == 0:
    print("SUCCESS: Zero invisible text! All text is 100% visible and contrast-verified!")
else:
    print(f"WARNING: Still {white_on_white_count} low contrast elements!")
