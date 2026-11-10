#!/usr/bin/env python3
"""Run multi-tenant forensic E2E audit across 3 global enterprise archetypes:
1. Cementos Molins (Spain, Heavy Manufacturing, EUR, es-ES)
2. Starling Bank (UK, FinTech, GBP, en-GB)
3. Rede D'Or São Luiz (Brazil, Healthcare, BRL, pt-BR)
"""

import json
import os
import sys
import time
from pathlib import Path
from zipfile import ZipFile

import requests
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8000"


def audit_tenant_flow():
    audit_results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # TENANT 1: Cementos Molins (Spain · Manufacturing · EUR · es)
        # -------------------------------------------------------------
        print("\n=======================================================")
        print("AUDITING TENANT 1: Cementos Molins (cto@molins.com)")
        print("=======================================================")
        page1 = browser.new_page(viewport={"width": 1920, "height": 1080})
        page1.goto(BASE_URL)
        page1.wait_for_timeout(1000)

        # Login
        if page1.locator('input[type="email"]').count() > 0:
            page1.fill('input[type="email"]', "cto@molins.com")
            page1.fill('input[type="password"]', "Password123!")
            page1.click('button[type="submit"]')
            page1.wait_for_timeout(2000)

        page1.select_option("header select", "es")
        page1.wait_for_timeout(1000)

        # Navigate to Tab 2
        page1.click('main button')
        page1.wait_for_timeout(2000)

        # Viewport check
        s_h1 = page1.evaluate("() => document.documentElement.scrollHeight")
        c_h1 = page1.evaluate("() => document.documentElement.clientHeight")
        print(f"  Viewport 1080p: scrollHeight={s_h1}, clientHeight={c_h1}")

        # Text readouts
        content1 = page1.content()
        has_dora_molins = "DORA" in page1.locator('text=Directiva NIS2').locator("..").inner_text()
        has_nis2 = "Directiva NIS2" in content1
        has_spain = "España" in content1
        has_mfg = "Materiales de Construcción e Industria" in content1

        page1.screenshot(path="e2e_molins_tab2_audit.png")
        print("  Screenshot saved: e2e_molins_tab2_audit.png")
        page1.close()

        # Ingest real Molins context transcript (.docx) via API
        molins_token = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "cto@molins.com", "password": "Password123!"}).json()["access_token"]
        molins_headers = {"Authorization": f"Bearer {molins_token}"}
        docx_path = REPO_ROOT / "source_docs" / "molins" / "260721 Transcripción sesion de contexto de molins (Fairfly) 1.docx"

        ingest_doc_ok = False
        frags_count = 0
        if docx_path.is_file():
            with open(docx_path, "rb") as f:
                res_ingest = requests.post(
                    f"{BASE_URL}/api/workspace/cementos-molins/ingest/context-document",
                    files={"file": (docx_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                    headers=molins_headers,
                )
            if res_ingest.status_code == 200:
                ingest_doc_ok = True
                frags_count = res_ingest.json().get("total_fragments", 0)
                print(f"  ✓ Ingested real context transcript: {frags_count} evidence fragments extracted into evidence_vault.json")

        # Ingest real Molins matrix (.xlsx) via API
        xlsx_path = REPO_ROOT / "source_docs" / "molins" / "Preguntas Fast Assessment Molins contestadas cliente.xlsx"
        ingest_matrix_ok = False
        towers_ingested = 0
        if xlsx_path.is_file():
            with open(xlsx_path, "rb") as f:
                res_matrix = requests.post(
                    f"{BASE_URL}/api/workspace/cementos-molins/ingest/assessment-matrix",
                    files={"file": (xlsx_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    headers=molins_headers,
                )
            if res_matrix.status_code == 200:
                ingest_matrix_ok = True
                towers_ingested = res_matrix.json().get("towers_ingested", 0)
                print(f"  ✓ Ingested real Excel assessment matrix: {towers_ingested} towers calibrated into digital_twin_state.json")

        # Trigger real compilation
        res_compile = requests.post(f"{BASE_URL}/api/workspace/cementos-molins/compile?lang=es", headers=molins_headers)
        compile_job_ok = res_compile.status_code == 200
        compile_finished_ok = False
        completed_docx_files = []

        if compile_job_ok:
            for _ in range(40):
                time.sleep(1)
                st_res = requests.get(f"{BASE_URL}/api/workspace/cementos-molins/compile/status", headers=molins_headers)
                if st_res.status_code == 200:
                    st_data = st_res.json()
                    if st_data.get("status") == "COMPLETED":
                        compile_finished_ok = True
                        completed_docx_files = st_data.get("completed_files", [])
                        break
                    elif st_data.get("status") == "FAILED":
                        print(f"  ✗ Compilation failed: {st_data.get('error_detail')}")
                        break

        print(f"  ✓ Real Compilation Status: {'COMPLETED' if compile_finished_ok else 'FAILED'} (Files: {completed_docx_files})")

        audit_results["molins"] = {
            "viewport_clean": s_h1 == 1080,
            "has_dora_leak": has_dora_molins,
            "has_nis2": has_nis2,
            "has_spain_localized": has_spain,
            "has_industry_localized": has_mfg,
            "transcript_ingested": ingest_doc_ok,
            "evidence_fragments_count": frags_count,
            "matrix_ingested": ingest_matrix_ok,
            "towers_ingested_count": towers_ingested,
            "compilation_success": compile_finished_ok,
            "compiled_files_count": len(completed_docx_files),
        }

        # -------------------------------------------------------------
        # TENANT 2: Starling Bank (UK · FinTech · GBP · en)
        # -------------------------------------------------------------
        print("\n=======================================================")
        print("AUDITING TENANT 2: Starling Bank (head.infrastructure@starlingbank.co.uk)")
        print("=======================================================")
        page2 = browser.new_page(viewport={"width": 1920, "height": 1080})
        page2.goto(BASE_URL)
        page2.wait_for_timeout(1000)

        if page2.locator('button:has-text("Cerrar sesión")').count() > 0:
            page2.click('button:has-text("Cerrar sesión")')
            page2.wait_for_timeout(1000)
        if page2.locator('button:has-text("Sign out")').count() > 0:
            page2.click('button:has-text("Sign out")')
            page2.wait_for_timeout(1000)

        if page2.locator('input[type="email"]').count() > 0:
            page2.fill('input[type="email"]', "head.infrastructure@starlingbank.co.uk")
            page2.fill('input[type="password"]', "Password123!")
            page2.click('button[type="submit"]')
            page2.wait_for_timeout(2000)

        page2.select_option("header select", "en")
        page2.wait_for_timeout(1000)
        page2.click('main button')
        page2.wait_for_timeout(2000)

        s_h2 = page2.evaluate("() => document.documentElement.scrollHeight")
        c_h2 = page2.evaluate("() => document.documentElement.clientHeight")
        content2 = page2.content()

        has_pra = "PRA Operational Resilience" in content2
        has_gbp = "GBP (£)" in content2
        has_bfsi = "Banking" in content2 and "Financial Services" in content2 and "BFSI" in content2
        has_uk = "United Kingdom" in content2

        page2.screenshot(path="e2e_starling_tab2_audit.png")
        print("  Screenshot saved: e2e_starling_tab2_audit.png")
        page2.close()

        audit_results["starling"] = {
            "viewport_clean": s_h2 == 1080,
            "has_pra_resilience": has_pra,
            "has_gbp_currency": has_gbp,
            "has_bfsi_industry": has_bfsi,
            "has_uk_country": has_uk,
        }

        # -------------------------------------------------------------
        # TENANT 3: Rede D'Or São Luiz (Brazil · Healthcare · BRL · pt)
        # -------------------------------------------------------------
        print("\n=======================================================")
        print("AUDITING TENANT 3: Rede D'Or São Luiz (diretor.ti@rededor.com.br)")
        print("=======================================================")
        page3 = browser.new_page(viewport={"width": 1920, "height": 1080})
        page3.goto(BASE_URL)
        page3.wait_for_timeout(1000)

        if page3.locator('button:has-text("Sign out")').count() > 0:
            page3.click('button:has-text("Sign out")')
            page3.wait_for_timeout(1000)

        if page3.locator('input[type="email"]').count() > 0:
            page3.fill('input[type="email"]', "diretor.ti@rededor.com.br")
            page3.fill('input[type="password"]', "Password123!")
            page3.click('button[type="submit"]')
            page3.wait_for_timeout(2000)

        page3.select_option("header select", "pt")
        page3.wait_for_timeout(1000)
        page3.click('main button')
        page3.wait_for_timeout(2000)

        s_h3 = page3.evaluate("() => document.documentElement.scrollHeight")
        c_h3 = page3.evaluate("() => document.documentElement.clientHeight")
        content3 = page3.content()

        has_anvisa = "ANVISA" in content3
        has_dora_leak_br = "DORA" in content3
        has_brl = "BRL (R$)" in content3
        has_health_pt = "Saúde e Redes Hospitalares" in content3
        has_brasil = "Brasil" in content3

        page3.screenshot(path="e2e_rededor_tab2_audit.png")
        print("  Screenshot saved: e2e_rededor_tab2_audit.png")
        page3.close()

        audit_results["rededor"] = {
            "viewport_clean": s_h3 == 1080,
            "has_anvisa_framework": has_anvisa,
            "has_dora_leak": has_dora_leak_br,
            "has_brl_currency": has_brl,
            "has_healthcare_pt": has_health_pt,
            "has_brasil_country": has_brasil,
        }

        browser.close()

    out_file = REPO_ROOT / "docs" / "audits" / "MULTI_TENANT_E2E_FORENSIC_EVALUATION.json"
    out_file.write_text(json.dumps(audit_results, indent=2), encoding="utf-8")
    print(f"\nFinal Forensic Audit Report written to: {out_file}")
    print(json.dumps(audit_results, indent=2))


if __name__ == "__main__":
    audit_tenant_flow()
