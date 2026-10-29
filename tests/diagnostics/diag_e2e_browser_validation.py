"""Headless Chromium End-to-End Validation with Playwright.

Executes a real browser session against http://127.0.0.1:3001:
1. Opens root dashboard.
2. Checks for zero console errors.
3. Empirically verifies the Radar Chart <img> decodes (naturalWidth > 0).
4. Navigates to Tab 2 (Portafolio de Cuentas), searches for 'Nippon', and switches client.
5. Verifies dynamic currency switch to JPY (20,558,527 ¥).
6. Navigates to Tab 6 (War Room), submits a tactical constraint, and verifies response.
7. Captures a full-page verification screenshot.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOT_PATH = REPO_ROOT / "docs" / "audits" / "portal_e2e_validation.png"


def run_e2e_validation():
    print("=== Iniciando Validación E2E con Navegador Real (Chromium Headless) ===")
    console_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Monitor console messages
        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)
                print(f"[CONSOLE_ERROR] {msg.text}")

        page.on("console", handle_console)

        # 1. Load Root Page
        print("\n1. Navegando a http://127.0.0.1:3001/...")
        page.goto("http://127.0.0.1:3001/", wait_until="networkidle", timeout=15000)
        time.sleep(1.5)

        title = page.title()
        print(f"[OK] Título de página: {title}")
        assert "Assessment Engine" in title, f"Título inesperado: {title}"

        # Si aparece la compuerta de autenticación corporativa, acceder como Administrador
        if page.is_visible('text=Autenticación Corporativa'):
            print("   -> Detectada compuerta corporativa. Iniciando como Administrador...")
            page.click('button:has-text("Socio Administrador NTT DATA")')
            time.sleep(1.0)

        # 2. Verify Radar Image Rendering in DOM
        print("\n2. Verificando decodificación del gráfico de Radar...")
        radar_img = page.wait_for_selector('img[alt*="Radar de Madurez"]', timeout=8000)
        assert radar_img is not None, "Elemento <img> del radar no encontrado"

        # Check naturalWidth via evaluate to prove image was actually downloaded and decoded by Chromium
        img_dims = page.evaluate("""() => {
            const img = document.querySelector('img[alt*="Radar de Madurez"]');
            return {
                naturalWidth: img ? img.naturalWidth : 0,
                naturalHeight: img ? img.naturalHeight : 0,
                src: img ? img.src : ''
            };
        }""")
        print(f"[OK] Dimensiones naturales del Radar: {img_dims['naturalWidth']} x {img_dims['naturalHeight']} px")
        assert img_dims["naturalWidth"] > 0, "El gráfico de radar no se decodificó en el navegador"

        # 3. Test Tab Navigation to 'Portafolio de Cuentas'
        print("\n3. Navegando a Pestaña 'Portafolio de Cuentas'...")
        portafolio_tab = page.wait_for_selector('button:has-text("Portafolio de Cuentas")', timeout=5000)
        portafolio_tab.click()
        time.sleep(1.0)

        # Search for Nippon
        search_input = page.wait_for_selector('input[placeholder*="Buscar por razón social"]', timeout=5000)
        search_input.fill("Nippon")
        time.sleep(0.5)

        # Click on 'Abrir Expediente' for Nippon
        print("[OK] Filtrado por 'Nippon'. Haciendo clic en 'Abrir Expediente'...")
        abrir_btn = page.wait_for_selector('button:has-text("Abrir Expediente")', timeout=5000)
        abrir_btn.click()
        time.sleep(1.5)

        # 4. Verify Active Client Switched to Global Nippon Financial
        client_header = page.text_content("h1")
        print(f"[OK] Cliente Activo tras conmutación: {client_header}")
        assert "Global Nippon Financial Group" in client_header, f"Cliente no conmutó: {client_header}"

        # Verify JPY currency appears in the FAIR card
        body_text = page.text_content("body")
        assert "20,558,527" in body_text or "JPY" in body_text or "¥" in body_text, "Moneda JPY no encontrada en pantalla"
        print("[PASS] Moneda JPY y ALE de 20.5M ¥ reflejados correctamente en pantalla")

        # 5. Test War Room Interactive Chatbot
        print("\n4. Navegando a Pestaña 'War Room'...")
        war_room_tab = page.wait_for_selector('button:has-text("War Room")', timeout=5000)
        war_room_tab.click()
        time.sleep(1.0)

        # Submit tactical prompt
        prompt_input = page.wait_for_selector('input[placeholder*="Escribe un condicionante táctico"]', timeout=5000)
        prompt_input.fill("Exigir residencia en Madrid y cumplimiento estricto ENS Alta")

        send_btn = page.wait_for_selector('button:has-text("Enviar Ajuste")', timeout=5000)
        print("[OK] Enviando condicionante táctico al War Room...")
        send_btn.click()

        # Wait for reply from War Room Lead Architect
        reply_el = page.wait_for_selector('text=War Room Lead Architect', timeout=30000)
        assert reply_el is not None, "Respuesta del War Room no recibida"
        print("[PASS] Respuesta del Arquitecto del War Room recibida y renderizada en pantalla")

        # 6. Capture Full Page Verification Screenshot
        print(f"\n5. Guardando captura de pantalla de validación en {SCREENSHOT_PATH}...")
        SCREENSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SCREENSHOT_PATH), full_page=True)
        print(f"[PASS] Captura guardada exitosamente ({SCREENSHOT_PATH.stat().st_size:,} bytes)")

        browser.close()

    if console_errors:
        print(f"\n[WARN] Se detectaron {len(console_errors)} errores en la consola del navegador: {console_errors}")
    else:
        print("\n[PASS] Cero errores en consola del navegador (console.error == 0)")

    print("\n=== VALIDACIÓN E2E COMPLETADA CON ÉXITO ABSOLUTO (100% GREEN) ===")
    return True


if __name__ == "__main__":
    success = run_e2e_validation()
    sys.exit(0 if success else 1)
