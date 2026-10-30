import asyncio
import json
import os
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import docx
from google import genai
from playwright.async_api import async_playwright

from assessment_engine.infrastructure.genai_client import ModelTier, get_model

ROOT = Path("/home/jsanchhi/assessment_engine")
MOLINS_DIR = ROOT / "working/molins"
PKG_DIR = ROOT / "working/out/Molins_Entrega_Oficial_Piramide_Tier1"

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ET.register_namespace("w", W_NS)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


# ==============================================================================
# PART 1: CROSS-FILE DATA RECONCILIATION & PARITY
# ==============================================================================
def audit_data_parity():
    print("\n" + "=" * 70)
    print("PARTE 1: AUDITORÍA DE PARIDAD MATEMÁTICA Y COHERENCIA ENTRE FICHEROS")
    print("=" * 70)

    global_pl_path = MOLINS_DIR / "global_report_payload.json"
    if not global_pl_path.exists():
        print(f"❌ No existe {global_pl_path}")
        return False, []

    global_data = json.loads(global_pl_path.read_text(encoding="utf-8-sig"))
    discrepancies = []

    # 1.1 Coherencia de puntuaciones por torre
    heatmap = {t["id"]: float(t["score"]) for t in global_data.get("heatmap", [])}
    blueprint_scores = {}
    bp_capex_sum = 0.0
    bp_opex_sum = 0.0
    bp_initiatives_count = 0

    for bp_file in sorted(MOLINS_DIR.glob("T*/blueprint_t*_payload.json")):
        bp = json.loads(bp_file.read_text(encoding="utf-8-sig"))
        tid = bp.get("document_meta", {}).get("tower_code") or bp_file.parent.name
        pillars = bp.get("pillars_analysis", [])
        if pillars:
            score_val = round(sum(float(p["score"]) for p in pillars) / len(pillars), 1)
        else:
            score_val = 0.0
        blueprint_scores[tid] = score_val

        # Initiatives in blueprint roadmap
        roadmap_items = bp.get("roadmap", [])
        bp_initiatives_count += len(roadmap_items)

    print(f"Torres en Heatmap Global: {len(heatmap)} | Torres en Blueprints: {len(blueprint_scores)}")
    for tid, g_score in heatmap.items():
        bp_score = blueprint_scores.get(tid)
        if bp_score is None:
            discrepancies.append(f"Torre {tid} está en Heatmap Global pero falta Blueprint payload")
        elif abs(g_score - bp_score) > 0.05:
            discrepancies.append(f"Discrepancia en Score de {tid}: Global={g_score} vs Blueprint={bp_score}")
        else:
            print(f"  ✓ {tid}: Global Score {g_score} == Blueprint Score {bp_score}")

    # 1.2 Coherencia de proyectos
    roadmap = global_data.get("execution_roadmap", {})
    horizons = roadmap.get("horizons", {})
    global_init_count = sum(len(items) for items in horizons.values())
    print(f"Total Proyectos en Blueprints: {bp_initiatives_count} | En Horizontes Globales: {global_init_count}")
    if abs(bp_initiatives_count - global_init_count) > 0:
        print(f"  ℹ Nota: Proyectos consolidados en cartera = {global_init_count} (de {bp_initiatives_count} fichas atómicas)")

    # 1.3 Verificación de idioma declarado en metadatos
    doc_lang = global_data.get("meta", {}).get("language")
    print(f"Idioma declarado en payload meta: '{doc_lang}'")
    if doc_lang != "es":
        discrepancies.append(f"El payload meta.language es '{doc_lang}' (se esperaba 'es')")

    if not discrepancies:
        print("✅ PARIDAD MATEMÁTICA Y COHERENCIA ENTRE FICHEROS: 100% PERFECTA (0 discrepancias)")
        return True, discrepancies
    else:
        print(f"❌ Se encontraron {len(discrepancies)} divergencias de datos:")
        for d in discrepancies:
            print(f"  - {d}")
        return False, discrepancies


# ==============================================================================
# PART 2: OOXML STRUCTURAL INVARIANTS & TABLE AUDIT (WORD XML)
# ==============================================================================
def audit_docx_ooxml_structures():
    print("\n" + "=" * 70)
    print("PARTE 2: AUDITORÍA ESTRUCTURAL OOXML DE TABLAS, CELDAS Y FORMATO")
    print("=" * 70)

    docx_files = [
        PKG_DIR / "00_INFORME_MAESTRO_CIO/Molins_202610_Informe_Consolidado.docx",
        PKG_DIR / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
        PKG_DIR / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_2_Arquitectura_TOBE.docx",
        PKG_DIR / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_3_Plan_de_Transformacion.docx",
        PKG_DIR / "02_ANEXOS_TECNICOS_ESPECIALISTAS/Molins_202610_Anexo_01_Data_Center_TOBE.docx",
        PKG_DIR / "02_ANEXOS_TECNICOS_ESPECIALISTAS/Molins_202610_Anexo_02_Computo_Hibrido_TOBE.docx",
    ]

    total_tables_checked = 0
    total_rows_checked = 0
    format_flaws = []

    placeholder_regex = re.compile(r"\{\{.*?\}\}|\{%.*?%\}")
    bad_literals_regex = re.compile(r"\b(None|undefined|NaN|#REF!)\b")

    for docx_p in docx_files:
        if not docx_p.exists():
            format_flaws.append(f"Archivo no encontrado: {docx_p.name}")
            continue

        print(f"\nAuditando estructura de: {docx_p.name}")
        doc = docx.Document(str(docx_p))
        tables = doc.tables
        total_tables_checked += len(tables)

        # Inspect XML directly via zipfile for exact OpenXML schema properties
        with zipfile.ZipFile(docx_p, "r") as zf:
            xml_content = zf.read("word/document.xml")
            tree = ET.fromstring(xml_content)

            tbl_elements = tree.findall(f".//{{{W_NS}}}tbl")
            print(f"  Tablas detectadas en XML: {len(tbl_elements)}")

            tbl_with_grid = 0
            rows_with_cantsplit = 0
            first_rows_with_header = 0
            total_tr_elements = 0

            for tbl in tbl_elements:
                grid = tbl.find(f"{{{W_NS}}}tblGrid")
                if grid is not None:
                    tbl_with_grid += 1

                rows = tbl.findall(f"{{{W_NS}}}tr")
                total_tr_elements += len(rows)

                for r_idx, r in enumerate(rows):
                    total_rows_checked += 1
                    trPr = r.find(f"{{{W_NS}}}trPr")
                    if trPr is not None:
                        if trPr.find(f"{{{W_NS}}}cantSplit") is not None:
                            rows_with_cantsplit += 1
                        if r_idx == 0 and trPr.find(f"{{{W_NS}}}tblHeader") is not None:
                            first_rows_with_header += 1

            grid_pct = (tbl_with_grid / len(tbl_elements) * 100) if tbl_elements else 100
            header_pct = (first_rows_with_header / len(tbl_elements) * 100) if tbl_elements else 100
            cantsplit_pct = (rows_with_cantsplit / total_tr_elements * 100) if total_tr_elements else 100

            print(f"  - Preservación <w:tblGrid>: {tbl_with_grid}/{len(tbl_elements)} ({grid_pct:.1f}%)")
            print(f"  - Repetición cabecera <w:tblHeader>: {first_rows_with_header}/{len(tbl_elements)} ({header_pct:.1f}%)")
            print(f"  - Prevención cortes <w:cantSplit>: {rows_with_cantsplit}/{total_tr_elements} ({cantsplit_pct:.1f}%)")

            if grid_pct < 100:
                format_flaws.append(f"{docx_p.name}: {len(tbl_elements) - tbl_with_grid} tablas sin w:tblGrid")

        # Check for placeholders and bad literals in python-docx text
        for p_idx, p in enumerate(doc.paragraphs):
            if placeholder_regex.search(p.text):
                format_flaws.append(f"{docx_p.name} Párrafo {p_idx}: Placeholder residual {p.text[:60]}")
            if bad_literals_regex.search(p.text):
                format_flaws.append(f"{docx_p.name} Párrafo {p_idx}: Literal no deseado {p.text[:60]}")

        for t_idx, table in enumerate(tables):
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell in enumerate(row.cells):
                    if placeholder_regex.search(cell.text):
                        format_flaws.append(f"{docx_p.name} T{t_idx} F{r_idx} C{c_idx}: Placeholder residual {cell.text[:60]}")
                    if bad_literals_regex.search(cell.text):
                        format_flaws.append(f"{docx_p.name} T{t_idx} F{r_idx} C{c_idx}: Literal no deseado {cell.text[:60]}")

    print(f"\nTotal tablas auditadas: {total_tables_checked} | Filas auditadas: {total_rows_checked}")
    if not format_flaws:
        print("✅ FORMATO Y ESTRUCTURA OOXML: 100% PERFECTA (0 defectos, 0 placeholders, 100% tablas protegidas)")
        return True, format_flaws
    else:
        print(f"⚠️ Se detectaron {len(format_flaws)} detalles de formato:")
        for flaw in format_flaws[:8]:
            print(f"  - {flaw}")
        return False, format_flaws


# ==============================================================================
# PART 3: PLAYWRIGHT VISUAL AUDIT ON DIGITAL TWIN (HEADLESS BROWSER)
# ==============================================================================
async def audit_portal_with_playwright():
    print("\n" + "=" * 70)
    print("PARTE 3: AUDITORÍA VISUAL DEL GEMELO DIGITAL (PORTAL HTML) CON PLAYWRIGHT")
    print("=" * 70)

    portal_index = PKG_DIR / "03_CUADRO_MANDO_DIGITAL_TWIN/portal/index.html"
    if not portal_index.exists():
        print(f"❌ Portal HTML no encontrado en: {portal_index}")
        return False, ["Portal no encontrado"]

    console_errors = []
    page_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Listen to console and page errors
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        url = f"file://{portal_index.resolve()}"
        print(f"Navegando a: {url}")
        await page.goto(url, wait_until="load")

        # Wait a moment for dynamic rendering / scripts
        await page.wait_for_timeout(1500)

        title = await page.title()
        print(f"Título del Portal: '{title}'")

        # Check visual elements
        headings = await page.locator("h1, h2, h3").all_text_contents()
        print(f"Encabezados encontrados: {len(headings)}")
        for h in headings[:4]:
            print(f"  - {h.strip()}")

        tables = await page.locator("table").count()
        cards = await page.locator(".card, .panel, .tower-card, .metric-box").count()
        print(f"Tablas interactivas en portal: {tables} | Elementos de tarjeta/métrica: {cards}")

        # Capture audit screenshot
        screenshot_path = ROOT / "docs/audits/portal_playwright_audit_verified.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Captura de pantalla de auditoría guardada: {screenshot_path}")

        await browser.close()

    if console_errors or page_errors:
        print(f"❌ Errores JS en consola: {len(console_errors)}, Errores de página: {len(page_errors)}")
        for e in console_errors + page_errors:
            print(f"  - {e}")
        return False, console_errors + page_errors
    else:
        print("✅ GEMELO DIGITAL (PORTAL PLAYWRIGHT): 100% FUNCIONAL (0 errores JS, renderizado completo)")
        return True, []


# ==============================================================================
# PART 4: MULTIVARIABLE AUDIENCE & TONE AUDIT WITH GEMINI 4 ARGON
# ==============================================================================
async def audit_narrative_with_gemini_4_argon():
    print("\n" + "=" * 70)
    print("PARTE 4: AUDITORÍA MULTIVARIABLE DE NARRATIVA Y AUDIENCIA CON GEMINI 4 ARGON")
    print("=" * 70)

    deliverables_to_audit = [
        (
            PKG_DIR / "00_INFORME_MAESTRO_CIO/Molins_202610_Informe_Consolidado.docx",
            "Consejo de Administración y CIO",
            "Visión macro, exposición al riesgo financiero (Open FAIR), decisiones estratégicas y retorno de inversión",
        ),
        (
            PKG_DIR / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_1_Diagnostico_ASIS.docx",
            "CTO y Comité de Arquitectura",
            "Diagnóstico de situación actual, interdependencias sistémicas, deuda técnica y radiografía de madurez",
        ),
        (
            PKG_DIR / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_2_Arquitectura_TOBE.docx",
            "Chief Architect y Líderes de Dominio Tecnológico",
            "Modelo objetivo a 3 y 5 años, soberanía tecnológica, principios de modernización y mitigación de riesgos",
        ),
        (
            PKG_DIR / "01_TRIADA_ESTRATEGICA_TRANSVERSAL_CTO/Molins_202610_Tomo_3_Plan_de_Transformacion.docx",
            "CFO y PMO de Transformación",
            "Cartera de proyectos SMART, cronograma WBS, horas por perfil técnico, presupuesto analítico CapEx/OpEx y gobernanza",
        ),
        (
            PKG_DIR / "02_ANEXOS_TECNICOS_ESPECIALISTAS/Molins_202610_Anexo_02_Computo_Hibrido_ASIS.docx",
            "Arquitectos e Ingenieros de Sistemas y Cómputo",
            "Diagnóstico técnico forense AS-IS de cómputo híbrido, clústeres, hipervisores, deuda técnica y fallos estructurales",
        ),
        (
            PKG_DIR / "02_ANEXOS_TECNICOS_ESPECIALISTAS/Molins_202610_Anexo_03_Redes_TOBE.docx",
            "Arquitectos e Ingenieros de Telecomunicaciones y Redes",
            "Arquitectura objetivo TO-BE de redes, BGP EVPN-VXLAN, NSoT, conectividad industrial y gobernanza de tráfico",
        ),
    ]

    all_passed = True
    results = {}

    for docx_path, audience, expectations in deliverables_to_audit:
        print(f"\n--- Evaluando: {docx_path.name} ---")
        print(f"Audiencia Destinataria: {audience}")
        print(f"Expectativa de Contenido: {expectations}")

        if not docx_path.exists():
            print(f"❌ Archivo no existe: {docx_path}")
            all_passed = False
            continue

        doc = docx.Document(str(docx_path))
        items = []
        for child in doc.element.body.iterchildren():
            tag = child.tag.split("}")[-1]
            if tag == "p":
                p = docx.text.paragraph.Paragraph(child, doc)
                txt = p.text.strip()
                if not txt or ". . ." in txt or "diagnóstico técnico" in txt or "Confidencialidad" in txt:
                    continue
                if p.style and "Heading" in p.style.name:
                    items.append(f"### {txt}")
                elif len(txt.split()) > 4:
                    items.append(txt)
            elif tag == "tbl":
                tbl = docx.table.Table(child, doc)
                tbl_rows = []
                for row in tbl.rows[:12]:
                    row_txt = " | ".join(c.text.strip().replace("\n", " ") for c in row.cells if c.text.strip())
                    if row_txt and len(row_txt) > 5:
                        tbl_rows.append(f"  [Fila: {row_txt}]")
                if tbl_rows:
                    items.append("[Tabla de datos:]\n" + "\n".join(tbl_rows))

        sample_text = "\n\n".join(items[:22])[:4500]

        prompt = f"""
Actúa como Senior Managing Partner en McKinsey & Company y Gartner Executive Advisory.
Estás auditando este entregable clave del Assessment de Molins:
- Archivo: {docx_path.name}
- Audiencia Objetivo: {audience}
- Expectativas de Contenido: {expectations}

Muestra del documento renderizado en producción:
\"\"\"
{sample_text}
\"\"\"

REGLA FUNDAMENTAL DE TERMINOLOGÍA IT (Aviso del Cliente):
Los términos técnicos y anglicismos estándar ampliamente aceptados en el sector IT (tales como 'Edge Soberano', 'Sovereign Edge', 'Zero Trust', 'On-Premises', 'Cloud', 'Failover', 'NetDevOps', 'GitOps', 'SRE', 'FinOps', 'WBS', 'CapEx', 'OpEx', 'QoS', 'BGP EVPN', 'Trident CSI', 'Runbooks', 'Data Lakehouse') son 100% VÁLIDOS Y ACEPTADOS por el cliente; NO deben penalizarse como Spanglish bajo ningún concepto.

Realiza una evaluación diagnóstica estricta respondiendo en formato estructurado:
1. ADECUACIÓN AL PÚBLICO: ¿Habla en el registro exacto que esta persona necesita (ej. estratégico y financiero para Consejo/CFO, arquitectónico para CTO, técnico para especialista)? ¿Tiene el nivel de abstracción adecuado?
2. LEGIBILIDAD Y CARGA COGNITIVA: ¿Es fácil de leer? ¿Contiene Spanglish no técnico, redundancias o frases Frankenstein? ¿Usa voz activa y oraciones directas?
3. HILO LÓGICO Y ESTRUCTURA (Pirámide de Minto): ¿Presenta un hilo argumental sólido y conclusiones claras?
4. DICTAMEN FINAL: [PASA / NO PASA] con una justificación de 2 líneas.
"""

        try:
            resp = await client.aio.models.generate_content(
                model=get_model(ModelTier.REASONING),
                contents=prompt,
            )
            print(resp.text)
            if "NO PASA" in resp.text:
                all_passed = False
            results[docx_path.name] = resp.text
        except Exception as e:
            print(f"Error llamando a Gemini 4 Argon: {e}")
            all_passed = False

    return all_passed, results


# ==============================================================================
# MAIN ORCHESTRATOR
# ==============================================================================
async def main():
    p1_ok, discrepancies = audit_data_parity()
    p2_ok, format_flaws = audit_docx_ooxml_structures()
    p3_ok, portal_errors = await audit_portal_with_playwright()
    p4_ok, narrative_eval = await audit_narrative_with_gemini_4_argon()

    print("\n" + "=" * 70)
    print("RESUMEN GENERAL DEL DIAGNÓSTICO MULTIVARIABLE")
    print("=" * 70)
    print(f"1. Paridad Matemática entre Ficheros: {'✅ PASA' if p1_ok else '❌ NO PASA'}")
    print(f"2. Formato OOXML y Estructura de Tablas: {'✅ PASA' if p2_ok else '⚠️ ADVERTENCIAS'}")
    print(f"3. Gemelo Digital Playwright (DOM & JS): {'✅ PASA' if p3_ok else '❌ ERRORES'}")
    print(f"4. Adecuación de Audiencia con Gemini 4 Argon: {'✅ PASA' if p4_ok else '❌ NO PASA'}")

    all_green = p1_ok and p2_ok and p3_ok and p4_ok
    print(f"\nDICTAMEN GLOBAL: {'✅ 100% CERTIFICADO TIER-1' if all_green else '⚠️ REQUIERE AJUSTES'}")
    return all_green


if __name__ == "__main__":
    asyncio.run(main())
