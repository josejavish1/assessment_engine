---
status: Verified
owner: docs-governance
source_of_truth:
- business_command_center/package.json
- business_command_center/src/app/actions/assessment.ts
- infrastructure/docker/supabase/docker-compose.yml
- /etc/systemd/system/assessment-portal.service
- /etc/caddy/Caddyfile
last_verified_against: '2026-10-29'
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# Business Command Center: Tier-1 Commercial Portal

## 1. Overview & Architecture
The **Business Command Center** (`business_command_center/`) is the flagship Tier-1 frontend portal of the Assessment Engine. It provides a multi-tenant, enterprise-grade interface allowing corporate clients, evaluators, and system administrators to manage and inspect technical assessments.

The portal follows a **Zero-Entropy Composable SaaS** paradigm:
*   **Frontend Core:** Next.js 16 (Turbopack) with React 19 Server Components.
*   **Production Daemon:** Systemd managed service (`assessment-portal.service`) running on internal port `3001` with automated crash recovery.
*   **Public HTTPS Gateway:** Caddy reverse proxy serving `https://soverik.com` and `https://demo.soverik.com` with automated Let's Encrypt TLS (HTTP/2 and HTTP/3 enabled).
*   **Identity & BaaS Gateway:** **Supabase Self-Hosted** running via Docker Compose (`infrastructure/docker/supabase/`), securely proxied under `https://auth.soverik.com` with PostgreSQL 17.6, Row Level Security (RLS), GoTrue Auth, and PostgREST.
*   **Design System:** Tailwind CSS v4 + Radix Nova (Shadcn UI) + Lucide Icons + Framer Motion.
*   **Python Engine Coupling:** Bidirectional Server Actions (`src/app/actions/assessment.ts` and `src/app/actions/war_room.ts`) connecting web requests to the underlying Python runtime.

## 2. Executive Console Features (BidStrategy Pattern)
*   **Multinational Archetype Selector:** Real-time inspection of 4 global entities (`Nordic Grid Power GmbH`, `Global Nippon Financial Group`, `Meridian BioHealth Inc.`, `Iberia Retail Logistics S.A.`).
*   **Dynamic Actuarial Synchronization:** Direct reading of `fair_actuarial_model.json` and `approved_annex_payload.json`, supporting localized currencies (`EUR €`, `JPY ¥`, `USD $`) and Monte Carlo statistical distributions.
*   **Inline Multidimensional Radar Chart:** Vector-grade 10-axis radar visualizer served natively via `/api/download?view=inline`.
*   **Official Deliverable Downloads:** Direct binary download of 3 Word documents (Technical Annex, Commercial Proposal, Technical Blueprint) and 1 PNG radar chart.
*   **Tactical War Room (ADR Mutator):** Interactive dialog powered by `gemini-3.8-flash` with deterministic fallbacks to recalculate architectural vectors under newly introduced constraints.
*   **Knowledge Hub & Ingest Modal:** Client-side ZIP decompression using `jszip` and secure evidence upload into `source_docs/<client_slug>/`.

## 3. Verification & Diagnostic Oracles
The portal is verified by 4 deterministic diagnostic suites:
*   `tests/diagnostics/diag_verify_portal_and_supabase.py` (TCP 5432 + HTTP 200 checks).
*   `tests/diagnostics/diag_verify_full_ui_render.py` (Binary download headers and content verification).
*   `tests/diagnostics/diag_e2e_browser_validation.py` (Chromium headless DOM decode and zero console errors).
*   `tests/diagnostics/diag_run_full_user_journey.py` (Full simulated browser user journey).
*   Regression test suite: `293/293 tests passed`.
