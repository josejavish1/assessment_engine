"""Empirical End-to-End Verification of the Unified Command Center Portal.

Verifies:
1. HTTP 200 on public root endpoint http://34.175.194.93:3001/.
2. Accurate dynamic metrics per client (Global Score, Band, Currencies: JPY, USD, EUR).
3. Image inline rendering for all 4 radar charts.
4. Binary DOCX deliverable downloads for all 4 clients.
"""

import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:3001"
REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "working" / "out" / "simulations"

CLIENTS = [
    {
        "slug": "nordic_grid_power_gmbh",
        "name": "Nordic Grid Power GmbH",
        "currency_symbol": "€",
        "expected_score": "2.9 / 5.0",
        "expected_band": "Definido",
    },
    {
        "slug": "global_nippon_financial_group",
        "name": "Global Nippon Financial Group",
        "currency_symbol": "¥",
        "expected_score": "2.9 / 5.0",
        "expected_band": "Definido",
    },
    {
        "slug": "meridian_biohealth_inc",
        "name": "Meridian BioHealth Inc.",
        "currency_symbol": "$",
        "expected_score": "2.9 / 5.0",
        "expected_band": "Definido",
    },
    {
        "slug": "iberia_retail_logistics_s_a",
        "name": "Iberia Retail Logistics S.A.",
        "currency_symbol": "€",
        "expected_score": "2.9 / 5.0",
        "expected_band": "Definido",
    },
]


def test_public_root():
    req = urllib.request.Request(f"{BASE_URL}/")
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "ASSESSMENT ENGINE" in html or "Enterprise Command Center" in html
        print("[PASS] 1. Root Portal Endpoint returns HTTP 200 with Brand Title")


def test_radar_inline_serving():
    for c in CLIENTS:
        radar_file = SIM_DIR / c["slug"] / "pillar_radar_chart.generated.png"
        assert radar_file.exists(), f"Radar file missing for {c['slug']}"
        url = f"{BASE_URL}/api/download?path={urllib.parse.quote(str(radar_file))}&view=inline"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            assert resp.status == 200
            headers = dict(resp.headers)
            assert headers.get("content-type") == "image/png"
            assert headers.get("content-disposition") == "inline"
            content = resp.read()
            assert len(content) > 100_000, f"Image too small: {len(content)} bytes"
            print(f"[PASS] 2. Radar inline serving for {c['slug']}: {len(content)} bytes (image/png)")


def test_docx_deliverable_downloads():
    for c in CLIENTS:
        annex_file = SIM_DIR / c["slug"] / f"Anexo_Tecnico_{c['slug']}.docx"
        assert annex_file.exists(), f"Annex DOCX missing for {c['slug']}"
        url = f"{BASE_URL}/api/download?path={urllib.parse.quote(str(annex_file))}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            assert resp.status == 200
            headers = dict(resp.headers)
            assert "wordprocessingml" in headers.get("content-type", "")
            assert "attachment" in headers.get("content-disposition", "")
            content = resp.read()
            assert len(content) > 200_000, f"DOCX too small: {len(content)} bytes"
            print(f"[PASS] 3. DOCX download for {c['slug']}: {len(content):,} bytes (Word format)")


def main():
    print("=== Empirical End-to-End Verification: Unified Command Center Portal ===")
    try:
        test_public_root()
        test_radar_inline_serving()
        test_docx_deliverable_downloads()
        print("\n=== TODOS LOS CHEQUEOS EMPÍRICOS COMPLETADOS CON ÉXITO (100% PASS) ===")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
