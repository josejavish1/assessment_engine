---
status: Verified
owner: docs-governance
source_of_truth:
- docs/ai/documentation-governance.md
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
- src/
last_verified_against: 2026-11-12
applies_to:
- gemini
doc_type: operational
diataxis: how_to
verification_mode: editorial
---
# Gemini Adapter

This file acts as the **concise operational adapter for Gemini CLI**, not as canonical project documentation.

## Governance Inheritance (Strict)

As a Google AI agent, **YOU MUST read and unconditionally submit to the Sovereign Engineering Laws and the Change Discipline Checklist defined in [AGENTS.md](AGENTS.md)**. These quality laws are absolute and immutable across this codebase.

### Mandatory Language Decoupling Law
- **Immutable Rule:** Even if the human operator dialogues or prompts in Spanish, **NEVER** write source code, inline comments, docstrings, exceptions, logs, prompts, or tests in Spanish.
- **Every engineering artifact must be 100% Technical English.**
- Spanish or other localized languages exist solely as data in `engine_config/locales.json` to render client deliverables when explicitly parameterized.
- Hardcoding `locale="es"` or using `"es"` as a function signature default is strictly prohibited; the system default is always `"en"`.

## Reading Order

1. [README.md](README.md)
2. [docs/README.md](docs/README.md)
3. [docs/ai/documentation-governance.md](docs/ai/documentation-governance.md)
4. [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)
5. The canonical document closest to the target change

## Operational Rules

- Prepend every response with the deterministic sentinel: `[CANARY: V4 | MONISM: SSOT | LOCALE: EN]`.
- Do not use this file as a standalone single source of truth.
- Rely on verified source code, automated test suites, schemas, and real workflows.
- When a factual assertion cannot be verified, treat it as `Needs Review`.
- Do not accumulate historical architecture notes, roadmap discussions, or transient logs in this file.
- If a change impacts architecture, contracts, operations, or governance, update canonical documentation in `docs/`.

## Transition Note

Historical operational memory from previous iterations is superseded by the unified canonical documentation base under `docs/`.
