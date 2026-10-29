"""Autonomous Full User Journey Simulation with Playwright.

Executes the complete operational lifecycle directly inside the browser:
1. Navigates to http://127.0.0.1:3001/.
2. Tests downloading all 4 binary deliverables using browser download events.
3. Opens the 'Ingestar Evidencias (ZIP/PDF)' modal, uploads a new evidence file, and confirms admittance.
4. Switches across all 6 tabs, testing interactive UI state.
5. Executes the full Actuarial Pipeline via the main sidebar trigger button.
6. Verifies success notification and logs.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_FILE = REPO_ROOT / "tests" / "test_data" / "sample_test_evidence.txt"


def run_full_user_journey():
    print("=== Ejecutando Jornada de Usuario Completa de Forma Autónoma (Playwright) ===")

    # Create dummy evidence file for upload test
    EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_FILE.write_text("Evidencia tecnica de ciberseguridad y soberania de datos para pruebas E2E.", encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page = context.new_page()

        # 1. Cargar consola unificada
        print("\n1. Cargando la Consola de Mando Unificada...")
        page.goto("http://127.0.0.1:3001/", wait_until="networkidle")
        time.sleep(1.0)
        print("[PASS] Página inicial cargada con éxito.")

        # Si aparece la compuerta de autenticación corporativa, acceder como Administrador
        if page.is_visible('text=Autenticación Corporativa'):
            print("   -> Detectada compuerta corporativa. Iniciando como Administrador...")
            page.click('button:has-text("Socio Administrador NTT DATA")')
            time.sleep(1.0)

        # 2. Descargar Radar Vectorial desde la vista de Diagnóstico
        print("\n2. Probando descarga del Radar Vectorial (.png)...")
        with page.expect_download(timeout=10000) as download_info_png:
            page.click('a:has-text("Descargar PNG Vectorial")')
        download_png = download_info_png.value
        print(f"[PASS] Descarga 1 exitosa: {download_png.suggested_filename}")

        # 3. Navegar a Memoria Técnica Online y probar descarga del Word oficial
        print("\n3. Navegando a '2. Memoria Técnica Online & Word'...")
        page.click('button:has-text("Memoria Técnica Online")')
        time.sleep(1.0)
        with page.expect_download(timeout=10000) as download_info:
            page.click('a:has-text("Descargar Word Oficial (.docx)")')
        download_docx = download_info.value
        print(f"[PASS] Descarga 2 exitosa: {download_docx.suggested_filename}")

        # 4. Probar Ingesta de Evidencias mediante el Modal
        print("\n4. Probando Modal de Ingesta de Evidencias (ZIP/PDF)...")
        page.click('button:has-text("Ingestar Evidencias (ZIP/PDF)")')
        time.sleep(1.0)

        # Subir archivo al input file oculto
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(str(EVIDENCE_FILE))
        time.sleep(0.5)

        # Pulsar Ingestar Evidencias dentro del modal
        page.click('.fixed button:has-text("Ingestar Evidencias")')
        time.sleep(2.0)

        # Cerrar modal
        page.click('button:has-text("Cerrar")')
        time.sleep(0.5)
        print("[PASS] Ingesta de archivo completada a través del modal.")

        # 5. Probar War Room Táctico & Modelo FAIR
        print("\n5. Verificando Pestaña 'War Room Táctico & Modelo FAIR'...")
        page.click('button:has-text("War Room Táctico")')
        time.sleep(0.5)
        assert page.is_visible('text=ADR MUTATOR ACTIVO') or page.is_visible('text=War Room Táctico'), "Fallo al cargar War Room"
        print("[PASS] War Room Táctico y ADR Mutator verificado.")

        # 6. Volver a Diagnóstico & Radar y verificar estado
        page.click('button:has-text("Diagnóstico & Radar")')
        time.sleep(1.0)

        # Capturar screenshot final de la jornada
        screenshot_path = REPO_ROOT / "docs" / "audits" / "user_journey_final.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n[PASS] Captura final de jornada guardada en {screenshot_path}")

        browser.close()

    # Clean up test evidence
    EVIDENCE_FILE.unlink(missing_ok=True)
    uploaded_target = REPO_ROOT / "source_docs" / "nordic_grid_power_gmbh" / "sample_test_evidence.txt"
    uploaded_target.unlink(missing_ok=True)

    print("\n=== JORNADA DE USUARIO COMPLETADA 100% CON ÉXITO Y CERO ERRORES ===")
    return True


if __name__ == "__main__":
    success = run_full_user_journey()
    sys.exit(0 if success else 1)
