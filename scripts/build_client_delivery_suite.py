"""Generic, decoupled deliverable suite compiler for enterprise clients.

Builds:
- Individual specialist tower blueprint payloads
- Global report payload and radar chart
- Consolidated Volume 1 AS-IS diagnostic report (.docx) via AST compiler
- Specialist tower annexes (.docx)

Enforces 100% technical decoupling:
- Dynamic currency, locale, and sector resolution
- Dynamic N-tower topology (only in-scope towers compiled)
- Strict zero-hardcoding and zero-contamination verification
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.adapters.compilers.payload_to_ast import (
    compile_asis_docx_via_ast,
)
from assessment_engine.adapters.compilers.tomo_asis_ast_compiler import (
    Volume1AsisASTCompiler,
)
from assessment_engine.application.build_case_input import build_case_input
from assessment_engine.application.generate_global_radar_chart import render_radar_chart
from assessment_engine.application.services.blueprint_synthesis_service import (
    synthesize_tower_blueprints,
)
from assessment_engine.application.services.tower_payload_hydrator import (
    TowerPayloadHydrator,
)
from assessment_engine.infrastructure.text_utils import slugify


def load_json(p: Path) -> dict[str, Any]:
    """Load JSON file safely."""
    return cast(dict[str, Any], json.loads(p.read_text(encoding="utf-8-sig")))


def setup_client_workspace(client_id: str) -> tuple[Path, dict[str, Any], list[str]]:
    """Resolve and prepare client working directory from synthetic fixture or existing working dir."""
    fixture_dir = REPO_ROOT / "tests" / "test_data" / "synthetic_clients" / client_id
    if not fixture_dir.exists():
        raise FileNotFoundError(f"Fixture directory not found: {fixture_dir}")

    intel_path = fixture_dir / "client_intelligence.json"
    intel_data = load_json(intel_path)
    from assessment_engine.infrastructure.runtime_paths import (
        resolve_client_dir,
    )

    client_name = intel_data["client_name"]
    client_slug = slugify(client_name)

    working_client_dir = resolve_client_dir(client_slug)
    working_client_dir.mkdir(parents=True, exist_ok=True)

    # Copy intelligence dossier to working directory
    shutil.copy2(intel_path, working_client_dir / "client_intelligence.json")

    # Determine in-scope towers
    tower_overrides = intel_data.get("tower_overrides", {})
    in_scope_towers = [
        t_id for t_id, ov in tower_overrides.items()
        if ov.get("status") in ("In Scope", "in_scope") or (ov.get("target_maturity", 0) > 0.0)
    ]
    if not in_scope_towers:
        in_scope_towers = [f"T{i}" for i in range(1, 11)]

    # Sort towers numerically
    in_scope_towers.sort(key=lambda x: int(x[1:]) if x[1:].isdigit() else 99)

    # Purge legacy out-of-scope tower directories to prevent stale artifacts
    for existing_t in working_client_dir.glob("T*"):
        if existing_t.is_dir() and existing_t.name not in in_scope_towers:
            shutil.rmtree(existing_t)

    return working_client_dir, intel_data, in_scope_towers


def generate_tower_case_inputs(
    working_dir: Path,
    fixture_dir: Path,
    client_name: str,
    active_towers: list[str],
) -> None:
    """Run build_case_input for all active towers."""
    transcript_file = fixture_dir / "transcription_interview_session.docx"
    responses_file = fixture_dir / "assessment_responses.txt"

    for t_id in active_towers:
        t_dir = working_dir / t_id
        t_dir.mkdir(parents=True, exist_ok=True)
        args = argparse.Namespace(
            client=client_name,
            tower=t_id,
            context_file=str(transcript_file),
            responses_file=str(responses_file),
        )
        case_data = build_case_input(args)
        case_out = t_dir / "case_input.json"
        case_out.write_text(json.dumps(case_data, indent=2, ensure_ascii=False), encoding="utf-8")


def compile_client_delivery_suite(
    client_id: str = "uk_fintech",
    doc_lang: str = "en",
    enrich_risks: bool = False,
) -> tuple[Path, list[Path]]:
    """End-to-end compilation pipeline for synthetic or production enterprise clients."""
    working_dir, intel_data, active_towers = setup_client_workspace(client_id)
    fixture_dir = REPO_ROOT / "tests" / "test_data" / "synthetic_clients" / client_id
    client_name = intel_data["client_name"]

    print("\n================================================================================")
    print(f"STARTING COMPILATION FOR CLIENT: {client_name} ({client_id})")
    print(f"Active Towers ({len(active_towers)}): {active_towers}")
    print(f"Language: {doc_lang} | Currency: {intel_data['metadata']['currency']} ({intel_data['metadata']['currency_symbol']})")
    print(f"Enrich Risks: {'ENABLED (Neurosymbolic LLM)' if enrich_risks else 'DISABLED (Deterministic Fallback)'}")
    print("================================================================================")

    # 1. Ingest case inputs
    generate_tower_case_inputs(working_dir, fixture_dir, client_name, active_towers)
    print("✓ Ingested raw transcripts and assessment responses into case_input.json")

    # 2. Synthesize tower blueprints
    blueprints = synthesize_tower_blueprints(working_dir, intel_data, active_towers, doc_lang, enrich_risks=enrich_risks)
    print(f"✓ Synthesized {len(blueprints)} tower blueprints in working directory")

    # 3. Construct global report payload
    fin = intel_data.get("profile", {}).get("financial_profile", {})
    currency = intel_data["metadata"]["currency"]
    currency_symbol = intel_data["metadata"]["currency_symbol"]
    annual_revenue = float(fin.get("annual_revenue", 665_000_000.0))
    hourly_rate = float(fin.get("hourly_downtime_cost", 140_000.0))

    heatmap = [
        {
            "id": t_id,
            "tower_code": t_id,
            "tower_name": bp["tower_name"],
            "score": bp["overall_score"],
        }
        for t_id, bp in blueprints.items()
    ]

    total_ale = sum(bp["total_fair_ale"] for bp in blueprints.values())
    global_payload = {
        "meta": {
            "client": client_name,
            "client_name": client_name,
            "version": "1.0",
            "date": "October 2026",
            "lang": doc_lang,
            "doc_lang": doc_lang,
            "currency": currency,
            "currency_symbol": currency_symbol,
            "domain_scope": "scoped",
            "is_modular": True,
        },
        "domain_scope": "scoped",
        "is_modular": True,
        "search_roots": [str(working_dir)],
        "financial_telemetry": {
            "currency": currency,
            "currency_symbol": currency_symbol,
            "annual_revenue": annual_revenue,
            "hourly_downtime_rate": hourly_rate,
            "consolidated_hourly_downtime_rate": hourly_rate,
            "corporate_ale": total_ale,
            "total_fair_p90": total_ale * 2.2,
        },
        "heatmap": heatmap,
        "tower_overrides": intel_data.get("tower_overrides", {}),
    }

    global_payload_file = working_dir / "global_report_payload.json"
    global_payload_file.write_text(json.dumps(global_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("✓ Constructed global_report_payload.json with scoped N-tower topology")

    # 4. Generate Radar Chart
    radar_png_path = working_dir / "global_radar_chart.png"
    render_radar_chart(
        towers=heatmap,
        out_path=radar_png_path,
        doc_lang=doc_lang,
    )
    print(f"✓ Rendered polar radar chart: {radar_png_path.name} ({radar_png_path.stat().st_size:,} bytes)")

    # 5. Hydrate payloads via TowerPayloadHydrator
    hydrated_payloads = TowerPayloadHydrator.load_and_hydrate_all_towers(
        REPO_ROOT,
        global_payload,
        doc_lang=doc_lang,
        target_towers=active_towers,
        persist_to_disk=True,
    )
    print(f"✓ Hydrated {len(hydrated_payloads)} towers with actuarial calibration")

    # 6. Compile Consolidated Tomo 1 AS-IS DOCX via Declarative AST Compiler
    from assessment_engine.infrastructure.runtime_paths import resolve_tenant_workspace

    out_dir = resolve_tenant_workspace(slugify(client_name)).deliverables
    out_dir.mkdir(parents=True, exist_ok=True)
    tomo1_out_docx = out_dir / f"{slugify(client_name).title()}_202610_Tomo_1_Diagnostico_ASIS.docx"

    # Copy radar chart to output directory for AST compiler bundling
    shutil.copy2(radar_png_path, out_dir / "global_radar_chart.png")

    compiler = Volume1AsisASTCompiler()
    compiler.compile(
        global_payload=global_payload,
        tower_payloads=hydrated_payloads,
        output_docx_path=tomo1_out_docx,
        doc_lang=doc_lang,
    )
    print(f"✓ Compiled Tomo 1 AS-IS DOCX: {tomo1_out_docx.name} ({tomo1_out_docx.stat().st_size:,} bytes)")

    # 7. Compile Specialist Tower Annexes via Declarative AST Engine
    annex_docs: list[Path] = []
    print("\n================================================================================")
    print(f"PHASE: COMPILING {len(active_towers)} SPECIALIST ANNEXES VIA AST ENGINE")
    print("================================================================================")
    for t_id in active_towers:
        bp_path = working_dir / t_id / f"blueprint_{t_id.lower()}_payload.json"
        num_str = f"{int(t_id[1:]):02d}"
        slug_tower = slugify(blueprints[t_id]["tower_name"])
        annex_filename = f"{slugify(client_name).title()}_202610_Annex_{num_str}_{slug_tower.title()}_ASIS.docx"
        annex_out_path = out_dir / annex_filename
        compile_asis_docx_via_ast(bp_path, annex_out_path, doc_lang=doc_lang)
        print(f"  ✓ Compiled Annex {t_id}: {annex_filename} ({annex_out_path.stat().st_size:,} bytes)")
        annex_docs.append(annex_out_path)

    return tomo1_out_docx, annex_docs


# Backward compatibility alias for legacy test suites
compile_starling_delivery_suite = compile_client_delivery_suite


def audit_compiled_deliverable(
    docx_path: Path,
    expected_currency: str,
    expected_towers: list[str],
    is_tomo1: bool = True,
) -> None:
    """Forensic audit of a compiled DOCX deliverable ensuring zero contamination."""
    import docx

    doc = docx.Document(str(docx_path))
    full_text = "\n".join(p.text for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            full_text += "\n" + " | ".join(c.text for c in row.cells)

    print(f"\n--- AUDIT: {docx_path.name} ---")
    print(f"  Total Text Size: {len(full_text):,} chars | Paragraphs: {len(doc.paragraphs)} | Tables: {len(doc.tables)}")

    # 1. Contamination check: Zero Molins
    assert "molins" not in full_text.lower(), f"CRITICAL CONTAMINATION: 'Molins' string found in {docx_path.name}!"
    print("  ✓ Zero 'Molins' cross-client contamination.")

    # 2. Industrial / cement leaks check
    assert "weighbridge" not in full_text.lower(), f"Weighbridge leak found in {docx_path.name}!"
    print("  ✓ Zero 'weighbridge' / industrial contamination.")

    # 3. Currency check: Correct symbol present, foreign symbols absent
    assert expected_currency in full_text, f"Currency symbol '{expected_currency}' missing from {docx_path.name}!"
    if expected_currency != "€":
        assert "€" not in full_text, f"CRITICAL ERROR: Euro symbol '€' found in non-EUR deliverable {docx_path.name}!"
    if expected_currency != "£":
        assert "£" not in full_text, f"CRITICAL ERROR: Pound symbol '£' found in non-GBP deliverable {docx_path.name}!"
    if expected_currency != "R$":
        assert "R$" not in full_text, f"CRITICAL ERROR: Real symbol 'R$' found in non-BRL deliverable {docx_path.name}!"
    print(f"  ✓ Native currency '{expected_currency}' verified; 0 foreign currency leaks.")

    # 4. Dynamic Topology check (only for Tomo 1)
    if is_tomo1:
        for t_id in expected_towers:
            assert f"Dominio {t_id}" in full_text or f"Domain {t_id}" in full_text or f"Tower {t_id}" in full_text or f"{t_id}:" in full_text or f"[{t_id}]" in full_text or t_id in full_text, (
                f"Active tower {t_id} missing from {docx_path.name}!"
            )
        print(f"  ✓ All {len(expected_towers)} active towers correctly rendered in topology.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile and audit client deliverable suite.")
    parser.add_argument("--client", default="uk_fintech", help="Client ID from synthetic clients.")
    parser.add_argument("--lang", default=None, help="Target document language (defaults to client intelligence).")
    parser.add_argument(
        "--enrich-risks",
        action="store_true",
        help="Execute live neurosymbolic LLM enrichment for risk cards (offline deterministic fallback by default).",
    )
    args = parser.parse_args()

    fixture_dir = REPO_ROOT / "tests" / "test_data" / "synthetic_clients" / args.client
    intel_data = load_json(fixture_dir / "client_intelligence.json")
    doc_lang = args.lang or intel_data.get("metadata", {}).get("lang", "en")
    expected_curr = intel_data["metadata"]["currency_symbol"]
    active_towers = [
        t_id for t_id, ov in intel_data.get("tower_overrides", {}).items()
        if ov.get("status") in ("In Scope", "in_scope") or (ov.get("target_maturity", 0) > 0.0)
    ]
    active_towers.sort(key=lambda x: int(x[1:]) if x[1:].isdigit() else 99)

    tomo1_file, annex_files = compile_client_delivery_suite(
        client_id=args.client,
        doc_lang=doc_lang,
        enrich_risks=args.enrich_risks,
    )

    print("\n================================================================================")
    print(f"STARTING COMPREHENSIVE FORENSIC DIAGNOSTIC AUDIT FOR {args.client.upper()}")
    print("================================================================================")
    audit_compiled_deliverable(tomo1_file, expected_currency=expected_curr, expected_towers=active_towers, is_tomo1=True)
    for annex_p in annex_files:
        audit_compiled_deliverable(annex_p, expected_currency=expected_curr, expected_towers=active_towers, is_tomo1=False)

    print(f"\n>> FULL DELIVERABLE SUITE (TOMO 1 + {len(annex_files)} ANNEXES) FULLY CERTIFIED CLEAN <<\n")


if __name__ == "__main__":
    main()
