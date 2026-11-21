---
status: Verified
owner: docs-governance
source_of_truth:
- business_command_center/package.json
- business_command_center/src/app/actions/assessment.ts
- docs/architecture/business-command-center-portal.md
last_verified_against: '2026-11-21'
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# Business Command Center (BCC)

The **Business Command Center** is the Tier-1 commercial web portal and executive war room for `assessment-engine`. Built as a zero-entropy composable SaaS application, it provides an enterprise-grade multi-tenant console enabling corporate clients, lead evaluators, and system administrators to manage assessments, inspect actuarial models, and steer architectural trade-offs in real time.

---

## 1. Core Architecture & Tech Stack

The portal integrates directly with the underlying Python actuarial runtime via Next.js Server Actions and JSON state contracts:

- **Frontend Core:** Next.js 16 (Turbopack engine) with React 19 Server Components.
- **Enterprise CRUD & State:** [Refine](https://refine.dev/) (`@refinedev/core`, `@refinedev/nextjs-router`) backed by TanStack React Query.
- **Design System & Primitives:** Tailwind CSS v4, Radix Nova UI primitives, Lucide Icons, and Framer Motion.
- **Type-Safe Validation:** React Hook Form coupled with strict Zod schemas (`src/features/clients/schema.ts`).
- **Sovereign Local Authentication:** Multi-tenant cryptographic session verification with PBKDF2-SHA512 password hashing (`engine_config/users.json`) and OTP verification (`engine_config/otp_store.json`), fully air-gapped from third-party identity SaaS.
- **Python Engine Interop:** Asynchronous Server Actions (`src/app/actions/assessment.ts`, `src/app/actions/war_room.ts`, `src/app/actions/governance.ts`) dispatching pipeline runs and streaming execution progress.

---

## 2. Directory Layout

```
business_command_center/
├── src/
│   ├── app/                           # Next.js App Router routes and layouts
│   │   ├── (admin)/admin/             # System administrator console
│   │   ├── (company)/company/         # Evaluator client management
│   │   ├── (user)/portal/             # Client tenant assessment dashboard
│   │   ├── actions/                   # Server Actions bridging Next.js to Python backend
│   │   ├── api/                       # Streaming SSE and binary download endpoints
│   │   └── login/                     # Sovereign PBKDF2 authentication views
│   ├── components/                    # Reusable UI primitives and layout containers
│   ├── features/                      # Domain features (clients, reports, war-room)
│   ├── lib/                           # Utility helpers and auth cookies
│   └── middleware.ts                  # Edge route protection and session verification
├── public/                            # Static SVG assets and brand vectors
├── next.config.ts                     # Next.js runtime configuration
├── package.json                       # Node.js dependencies and script definitions
└── tsconfig.json                      # Strict TypeScript compiler options
```

---

## 3. Local Development & Operational Commands

### Development Server
```bash
# Navigate to the frontend workspace
cd business_command_center

# Install Node dependencies (pinned via package-lock.json)
npm install

# Start development server on all interfaces (port 3000 by default)
npm run dev
```

### Production Build & Launch
```bash
# Compile production bundle with Turbopack and TypeScript verification
npm run build

# Start production server
npm run start
```

### Code Quality & Static Analysis
```bash
# Run Next.js ESLint validation
npm run lint
```

---

## 4. Production Daemon & Reverse Proxy

In production environments, the portal runs as an isolated systemd daemon:
- **Systemd Service:** `assessment-portal.service` running on internal port `3001` with auto-restart on failure.
- **Gateway Proxy:** Caddy reverse proxy routing traffic for `https://soverik.com` and `https://demo.soverik.com` with automated TLS termination (HTTP/2 and HTTP/3 QUIC).

---

## 5. Governance & Verification Oracles

All frontend code must adhere to the sovereign engineering standards defined in the root `AGENTS.md`:
- **Language Decoupling:** 100% Technical English for all identifiers, comments, logs, and user-facing copy. Multilingual localizations exist exclusively in declarative schemas (`engine_config/locales_ui.json`).
- **Accessibility:** WCAG 2.2 AA compliance certified via Chromium headless automation (`tests/diagnostics/diag_e2e_browser_validation.py`).
- **E2E Oracles:** Verified by `tests/diagnostics/diag_run_full_user_journey.py` and `tests/diagnostics/diag_verify_full_ui_render.py`.
