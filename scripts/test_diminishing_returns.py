import os
from pathlib import Path
from assessment_engine.infrastructure.genai_client import get_model, ModelTier, create_genai_client

client = create_genai_client()
model = get_model(ModelTier.REASONING)

prompt = """Role: Principal Systems Architect & Chief Software Auditor (Google Tier-1 / Anthropic Infrastructure).
Language Mandate: All engineering analysis, architectural critiques, code citations, and target designs MUST be in 100% formal Technical English. Zero Spanish allowed.

Context:
In our first two passes, we identified and documented 15 critical architectural flaws:
- 5 Split-Brains in Deliverable Compilation (AST vs Imperative vs XML vs Procedural; Monte Carlo vs 2.5x naive multipliers; Brand Profile vs 100+ RGBColor calls; Dynamic i18n vs hardcoded "Spanish" prompt defaults; In-memory SSOT vs asis_modules/*.md disk leaks).
- 10 Deep Antipatterns (Surjective country mapping of IEC 62443/NIS2 to Germany; Fake numerology in confidence scores; Impure domain I/O in taxonomy_resolver; Source-tree mutation in jurisdictions_dynamic; Incomplete Eurocentric linguistic guardrails; Fail-open silent exception swallowing in governance registries; 3-state sovereignty enum; Unbounded in-memory caches; Stringly-typed frameworks; Blocking synchronous I/O in async paths).

Task:
Conduct an uncompromising second-pass forensic inspection over the REMAINING subsystems:
1. `mcp_server.py`:
   - Spawning Python subprocesses (`sys.executable, -m, module_name`) for core operations (`build_tower_payload`, `render_tower_docx`) rather than in-process typed invocation.
   - Managing asynchronous background jobs in module-level dictionaries without persistent state machines.
2. `infrastructure/epistemic_graph.py`:
   - Hardcoded relative path `working/{client_id}/epistemic_ledger.jsonl` causing CWD sensitivity.
   - Silent event corruption swallowing during ledger replay (`logger.debug("Evento corrupto en ledger ignorado: ...")`).
   - SQLite in-memory `:memory:` connection instantiated per object, rebuilding from scratch on every invocation.
3. `application/run_scoring.py`:
   - Passing raw untyped dictionaries (`case_input: dict`, `tower_definition: dict`) without Pydantic validation.
   - Flat arithmetic averaging (`sum(values)/len(values)`) without weighting or outlier mitigation.
4. Concurrency & Daemon boundaries (`infrastructure/streaming_sentinel.py`, `infrastructure/raptor_engine.py`).

Answer with ruthless technical objectivity:
1. Are there genuine P0/P1 architectural failure modes among these remaining areas? Or is the analysis entering diminishing returns (secondary refactorings / stylistic hygiene)?
2. Detailed Technical Breakdown: For any genuine critical defect found, provide exact file citations, code snippets, failure modes under Fortune 500 load, and SOTA remediation.
3. The Diminishing Returns Verdict: Where is the exact boundary between architectural integrity (essential for an enterprise "work of art") and speculative over-engineering?
4. Final Codebase Maturity Scorecard: Quantify the current technical debt and the exact distance to 100% Tier-1 perfection.

Structure the output as a formal Markdown document. Start directly with the title `# ARCHITECTURAL AUDIT SECOND PASS: DIMINISHING RETURNS VERIFICATION`.
"""

resp = client.models.generate_content(model=model, contents=prompt)
out_path = Path("docs/architecture/second_pass_diminishing_returns_audit.md")
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(resp.text, encoding="utf-8")
print(f"Successfully wrote {len(resp.text)} characters to {out_path}")
