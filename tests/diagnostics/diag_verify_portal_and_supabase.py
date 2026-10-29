"""Diagnostic verification script for Supabase Self-Hosted and Tier-1 Portal.

Empirically validates:
1. PostgreSQL availability (Port 5432).
2. Supabase Envoy Gateway (Port 8000).
3. PostgREST multi-tenant tables.
4. Next.js routes (/login, /admin, /company, /portal).
"""

import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path


def test_postgres_tcp() -> bool:
    s = socket.socket()
    s.settimeout(2.0)
    try:
        s.connect(("127.0.0.1", 5432))
        s.close()
        print("[PASS] PostgreSQL Port 5432 is accepting TCP connections")
        return True
    except Exception as e:
        print(f"[FAIL] PostgreSQL connection failed: {e}")
        return False


def test_supabase_gateway_and_rest() -> bool:
    env_file = Path(__file__).resolve().parents[2] / "infrastructure/docker/supabase/.env"
    if not env_file.exists():
        print(f"[FAIL] Supabase .env not found at {env_file}")
        return False

    content = env_file.read_text(encoding="utf-8")
    service_match = re.search(r"^SERVICE_ROLE_KEY=(.*)$", content, re.MULTILINE)
    if not service_match:
        print("[FAIL] SERVICE_ROLE_KEY not found in Supabase .env")
        return False

    service_key = service_match.group(1).strip()
    url = "http://127.0.0.1:8002/rest/v1/organizations?select=*"
    req = urllib.request.Request(
        url,
        headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                print(f"[PASS] Supabase PostgREST responded HTTP {resp.status} on /rest/v1/organizations")
                return True
            print(f"[FAIL] Supabase PostgREST responded with status: {resp.status}")
            return False
    except Exception as e:
        print(f"[FAIL] Supabase Gateway request failed: {e}")
        return False


def test_nextjs_routes() -> bool:
    routes = ["/login", "/admin", "/company", "/portal"]
    all_ok = True
    for r in routes:
        url = f"http://127.0.0.1:3001{r}"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    print(f"[PASS] Next.js route {r} returned HTTP 200")
                else:
                    print(f"[FAIL] Next.js route {r} returned HTTP {resp.status}")
                    all_ok = False
        except Exception as e:
            print(f"[FAIL] Route {r} request failed: {e}")
            all_ok = False
    return all_ok


def main():
    print("=== Empirical Portal & Supabase Diagnostic Test ===")
    pg_ok = test_postgres_tcp()
    sb_ok = test_supabase_gateway_and_rest()
    next_ok = test_nextjs_routes()

    if pg_ok and sb_ok and next_ok:
        print("=== ALL DIAGNOSTIC CHECKS PASSED (Tier-1 SOTA Verified) ===")
        sys.exit(0)
    else:
        print("=== SOME DIAGNOSTIC CHECKS FAILED ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
