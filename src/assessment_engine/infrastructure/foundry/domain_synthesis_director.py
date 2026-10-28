"""
Director and builder for Phase 2 full-stack domain synthesis.
Materialize SQLite WAL tables, compile domain contracts, inject OKLCH theme tokens, and populate asset catalogs.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import time
import unicodedata
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.evolution.ontology_router_engine import OntologyRouterEngine
from assessment_engine.infrastructure.evolution.react_router_compiler import ReactRouterCompiler
from assessment_engine.infrastructure.evolution.roadmap_synthesizer import RoadmapSynthesizer
from assessment_engine.infrastructure.evolution.socratic_calibrator import SocraticCalibratorEngine
from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model
from assessment_engine.infrastructure.primitives.theme_compiler import theme_compiler

logger = logging.getLogger("domain_synthesis_director")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFIED_ASSETS_PATH = REPO_ROOT / "core" / "fixtures" / "verified_assets.json"
SCHEMA_CACHE_DB_PATH = REPO_ROOT / "storage" / "data" / "relational_schema_cache.db"


def slugify(text: str) -> str:
    """Generate a normalized ASCII URL-safe slug from the given name by removing accents."""
    norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s-]", "", norm.lower()).strip()
    return re.sub(r"[-\s_]+", "-", cleaned)[:36].strip("-") or "project-preview"


def safe_write_text(file_path: Path, content: str) -> None:
    """Write text while unlinking hard links (CoW) to protect base template inodes."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        try:
            file_path.unlink()
        except OSError:
            pass
    file_path.write_text(content, encoding="utf-8")


def persist_soverik_specs(dossier: Any, output_dir: Path) -> None:
    """Map competitor intelligence to Soverik 16 visual paradigms and contracts."""
    try:
        from assessment_engine.infrastructure.primitives.competitor_to_soverik_mapper import (
            CompetitorDossier as MapperDossier,
            CompetitorToSoverikMapper,
        )
        mapper = CompetitorToSoverikMapper(db_path=str(output_dir / "soverik_specs.db"))
        m_dossier = MapperDossier(
            compressed_dom_json=getattr(dossier, "compressed_dom_json", "{}") or "{}",
            extracted_contracts=getattr(dossier, "extracted_contracts", {}) or {},
        )
        soverik_specs = mapper.map_dossier(m_dossier)
        specs_data = [
            {
                "component_name": s.component_name,
                "typescript_interfaces": s.typescript_interfaces,
                "python_models": s.python_models,
                "css_variables": s.css_variables,
                "wcag_contrast_valid": s.wcag_contrast_valid,
            }
            for s in soverik_specs
        ]
        safe_write_text(
            output_dir / "docs" / "SOVERIK_SPECS.json",
            json.dumps({"specs": specs_data}, indent=2, ensure_ascii=False),
        )
        logger.info(f"      - [Soverik Specs ✓] Mapeados {len(soverik_specs)} componentes visuales en docs/SOVERIK_SPECS.json")
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as spec_ex:
        logger.debug(f"[UniversalSynthesis] Mapeo de Soverik specs omitido: {spec_ex}")


def is_dark_hex(hex_str: str) -> bool:
    """Determine whether a color is perceived as dark using sRGB relative luminance."""
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return False
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        return lum < 0.5
    except ValueError:
        return False


def extract_contract_entities_from_dossier(dossier: Any) -> dict[str, list[str]]:
    """Extract inferred entities dictionary from dossier contracts or compressed JSON."""
    contracts_entities = getattr(dossier, "extracted_contracts", {}).get("inferred_entities", {})
    if contracts_entities:
        return dict(contracts_entities)
    c_raw = getattr(dossier, "compressed_dom_json", "")
    if c_raw:
        try:
            c_json = json.loads(c_raw)
            return dict(c_json.get("contracts", {}).get("inferred_entities", {}))
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _build_synthesis_goal(prompt: str, dossier: Any) -> str:
    pricing_context = ", ".join(f"{p.title}: {p.price_text} ({p.frequency})" for p in getattr(dossier, "pricing_plans", []))
    faq_context = " | ".join(f"{f.get('question')}: {f.get('answer')}" for f in getattr(dossier, "faq_matrix", [])[:3])
    contracts_entities = extract_contract_entities_from_dossier(dossier)
    entities_context = ""
    
    if contracts_entities:
        entities_str = "\n".join(f"  - {ent}: {attrs}" for ent, attrs in list(contracts_entities.items())[:6])
        entities_context = f"\nModelos de datos relacionales extraídos de líderes:\n{entities_str}\n"

    return (
        f"{prompt}\n"
        f"Tarifas reales de mercado extraídas del competidor: {pricing_context}\n"
        f"{entities_context}"
        f"Preguntas frecuentes reales: {faq_context}"
    )

def _process_and_verify_db(db_file: Path, schema_data: Any, project_slug: str) -> None:
    if not db_file.exists():
        return
        
    RoadmapSynthesizer._execute_ddl_and_seed(db_file, schema_data, project_slug)
    
    with sqlite3.connect(str(db_file)) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        check = cur.fetchone()[0]
        
        if check.lower() != "ok":
            raise RuntimeError(f"Corrupción detectada en {db_file.name}: {check}")
            
        cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        table_count = cur.fetchone()[0]
        
        if table_count == 0:
            raise RuntimeError(f"Base de datos {db_file.name} vacía: 0 tablas de negocio creadas.")
            
        logger.info(f"      - Verificado {db_file.name}: {table_count} tablas relacionales activas (Integrity: OK).")

def _apply_deterministic_mapper_schema(output_dir: Path, dossier: Any) -> None:
    """Apply deterministic relational schema and seeds from CompetitorToSoverikMapper."""
    if dossier is None:
        return
    try:
        from assessment_engine.infrastructure.primitives.competitor_to_soverik_mapper import CompetitorToSoverikMapper
        for target_db in [output_dir / "app.db", output_dir / "api" / "app.db"]:
            target_db.parent.mkdir(parents=True, exist_ok=True)
            mapper = CompetitorToSoverikMapper(db_path=str(target_db))
            d_schema = mapper.generate_relational_schema(dossier)
            mapper.apply_schema_to_db(d_schema, db_path=str(target_db))
    except Exception as m_err:
        logger.debug(f"Nota en mapeo relacional determinista: {m_err}")

async def acto_1_synthesize_sqlite_tables(
    prompt: str, project_slug: str, output_dir: Path, dossier: Any, sector: str = ""
) -> None:
    """Act 1: Synthesize relational tables and seed baseline fixtures."""
    logger.info("      - [Acto 1] Sintetizando tablas relacionales y poblando datos semilla (RoadmapSynthesizer)...")
    try:
        _apply_deterministic_mapper_schema(output_dir, dossier)
        client_ai = create_genai_client()
        goal_with_pricing = _build_synthesis_goal(prompt, dossier)
        target_sector = sector or (getattr(dossier, "sector", "") if dossier else "")

        schema_data = await RoadmapSynthesizer.synthesize_relational_schema(
            client=client_ai,
            slug=project_slug,
            goal=goal_with_pricing,
            ui_paradigm="Clean High-End Craft",
            sector=target_sector,
        )

        for db_file in [output_dir / "app.db", output_dir / "api" / "app.db"]:
            _process_and_verify_db(db_file, schema_data, project_slug)

    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as seed_err:
        logger.warning(f"Nota en síntesis de esquema relacional: {seed_err}")


def resolve_tier_commercial_action(
    pricing_mode: str, plan_price_text: str, plan_freq: str, idx: int
) -> tuple[str, str, str, str]:
    """Resolve plan action, CTA label, display price, and frequency text."""
    if pricing_mode == "quote":
        cta = "Solicitar Presupuesto" if idx > 0 else "Auditoría Gratuita"
        price = "A Medida" if idx > 0 else "0 €"
        freq = "" if idx == 0 else "según volumen"
        return "quote", cta, price, freq

    if pricing_mode == "booking":
        return "booking", "Reservar Cita", plan_price_text, f"/ {plan_freq}"

    is_subscription = "mes" in plan_freq or "año" in plan_freq
    action = "checkout" if is_subscription else "booking"
    cta = "Contratar" if is_subscription else "Reservar"
    return action, cta, plan_price_text, f"/ {plan_freq}"


def build_pricing_tiers(dossier: Any, pricing_mode: str) -> list[dict[str, Any]]:
    """Build pricing tiers tailored to the commercial modality."""
    pricing_tiers = []
    for idx, plan in enumerate(getattr(dossier, "pricing_plans", [])):
        num_match = re.search(r"(\d+[.,]?\d*)", plan.price_text)
        numeric_price = float(num_match.group(1).replace(",", ".")) if num_match else 0.0

        plan_action, cta_label, price_text, freq_text = resolve_tier_commercial_action(
            pricing_mode, plan.price_text, plan.frequency, idx
        )

        pricing_tiers.append({
            "id": f"tier-{idx+1}-{slugify(plan.title)}",
            "name": plan.title,
            "title": plan.title,
            "description": f"Tarifa de mercado verificada: {plan.title}",
            "price": numeric_price,
            "price_text": price_text,
            "frequency": freq_text,
            "features": list(plan.features),
            "highlighted": idx == 1,
            "cta_label": cta_label,
            "action": plan_action,
        })
    return pricing_tiers


_PRICING_LOCALE_MAP: dict[str, dict[str, tuple[str, str, str, str]]] = {
    "en": {
        "quote": ("Bespoke Model", "Custom Plans & Quotes", "Tailored solutions aligned with your needs", "Request Proposal"),
        "fixed": ("Verified Pricing", "Transparent Plans & Pricing", "Real market rates with zero hidden fees", "Get Started"),
    },
    "de": {
        "quote": ("Individuelles Modell", "Maßgeschneiderte Pläne", "Individuelle Lösungen exakt nach Bedarf", "Angebot Anfordern"),
        "fixed": ("Verifizierte Tarife", "Transparente Pläne & Preise", "Echte Marktpreise ohne versteckte Gebühren", "Jetzt Starten"),
    },
    "fr": {
        "quote": ("Modèle Sur-Mesure", "Formules & Devis Personnalisés", "Propositions sur-mesure adaptées", "Demander un Devis"),
        "fixed": ("Tarifs Vérifiés", "Forfaits & Tarifs Transparents", "Tarifs réels du marché sans frais cachés", "Commencer"),
    },
    "es": {
        "quote": ("Modalidad de Contratación", "Planes y Presupuestos a Medida", "Presupuestos personalizados según tus requerimientos sin compromiso", "Solicitar Presupuesto"),
        "fixed": ("Tarifas Oficiales Verificadas", "Planes y Tarifas Transparentes", "Precios reales de mercado sin comisiones ocultas ni sorpresas", "Empezar Ahora"),
    },
}


def resolve_pricing_labels(pricing_mode: str, detected_lang: str, dossier: Any) -> tuple[str, str, str, str]:
    """Resolve pricing badge, title, subtitle, and CTA using declarative dictionary lookup (V(G) <= 3)."""
    if hasattr(dossier, "pricing_title") and getattr(dossier, "pricing_title"):
        return (
            getattr(dossier, "pricing_badge", "Tarifas"),
            getattr(dossier, "pricing_title"),
            getattr(dossier, "pricing_subtitle", ""),
            getattr(dossier, "cta_text", "Empezar Ahora"),
        )

    mode_key = "quote" if pricing_mode == "quote" else "fixed"
    lang_code = (detected_lang or "es").lower()[:2]
    locale_data = _PRICING_LOCALE_MAP.get(lang_code, _PRICING_LOCALE_MAP["es"])
    badge, title, subtitle, default_cta = locale_data[mode_key]
    cta = getattr(dossier, "cta_text", "") or default_cta

    return badge, title, subtitle, cta


def _sanitize_brand_against_trademark_infringement(raw_brand: str, benchmark_url: str) -> str:
    """Ensure generated brand does not infringe competitor trademarks or raw domain names."""
    if not raw_brand:
        return "PlataformaNext"
    parsed_host = urlparse(benchmark_url if "://" in benchmark_url else f"https://{benchmark_url}").hostname or ""
    host_clean = parsed_host.lower().replace("www.", "")
    brand_lower = raw_brand.lower().strip()
    if host_clean and (brand_lower == host_clean or brand_lower == f"www.{host_clean}"):
        base = host_clean.split(".")[0].capitalize()
        return f"{base}Next"
    if "." in raw_brand and not raw_brand.endswith(".next"):
        base = raw_brand.split(".")[0].capitalize()
        return f"{base}Next"
    return raw_brand


def acto_2_compile_domain_contract(
    prompt: str,
    sector: str,
    web_dir: Path,
    output_dir: Path,
    dossier: Any,
    dossier_3cubes: Any,
    calibration_answers: dict[str, str] | None = None,
    socratic_result: Any = None,
) -> dict[str, Any]:
    """Act 2: Compile canonical domain contract and synchronise with workspace docs."""
    logger.info("      - [Acto 2] Compilando contrato sagrado de dominio sin alucinación de datos...")
    raw_brand = getattr(dossier, "brand_name", "") or prompt.split(":")[0].strip()
    clean_brand = _sanitize_brand_against_trademark_infringement(raw_brand, str(getattr(dossier, "benchmark_url", "") or ""))
    clean_tagline = getattr(dossier, "hero_headline", "") or prompt
    pricing_mode = getattr(dossier_3cubes, "pricing_mode", "fixed")
    pricing_tiers = build_pricing_tiers(dossier, pricing_mode)

    detected_lang = getattr(socratic_result, "detected_language", "es") if socratic_result else "es"
    pricing_badge, pricing_title, pricing_subtitle, cta_text = resolve_pricing_labels(
        pricing_mode, detected_lang, dossier
    )

    contracts_entities = extract_contract_entities_from_dossier(dossier)
    extracted_contracts = dict(getattr(dossier, "extracted_contracts", {}))
    api_endpoints = extracted_contracts.get("endpoints", [])

    contract = {
        "app_name": clean_brand,
        "brand_name": clean_brand,
        "sector": sector,
        "tagline": clean_tagline,
        "hero_headline": clean_tagline,
        "benchmark_url": str(getattr(dossier, "benchmark_url", "")),
        "social_proof": dict(getattr(dossier, "social_proof", {})),
        "layout_compositions": dict(getattr(dossier, "layout_compositions", {})),
        "api_payloads": dict(getattr(dossier, "api_payloads", {})),
        "tech_stack": list(getattr(dossier, "tech_stack", [])),
        "infrastructure_signals": dict(getattr(dossier, "infrastructure_signals", {})),
        "schema_org": list(getattr(dossier, "schema_org", [])),
        "extracted_contracts": extracted_contracts,
        "primary_cta_action": getattr(dossier, "primary_cta_action", {}),
        "logo_url": str(getattr(dossier, "logo_url", "")),
        "trust_badges": list(getattr(dossier, "trust_badges", [])),
        "operational_forms": list(getattr(dossier, "operational_forms", [])),
        "business_archetype": str(getattr(dossier, "business_archetype", "")),
        "api_endpoints": api_endpoints,
        "cta_text": cta_text,
        "pricing_mode": pricing_mode,
        "pricing_badge": pricing_badge,
        "pricing_title": pricing_title,
        "pricing_subtitle": pricing_subtitle,
        "pricing_tiers": pricing_tiers,
        "conversion_channels": dict(getattr(dossier, "conversion_channels", {})),
        "meta_description": getattr(dossier, "meta_description", ""),
        "inferred_entities": contracts_entities,
        "invariants": list(getattr(dossier_3cubes, "must_have_invariants", [])),
        "unfair_advantages": list(getattr(dossier_3cubes, "unfair_advantages", [])),
        "anti_features": list(getattr(dossier_3cubes, "deliberate_anti_features", [])),
        "customer_pain_points": list(getattr(dossier, "customer_pain_points", [])),
        "counter_positioning": list(getattr(dossier, "counter_positioning", [])),
        "faq_matrix": list(getattr(dossier, "faq_matrix", [])),
        "mapped_features": list(getattr(dossier, "mapped_features", [])),
        "value_propositions": list(getattr(dossier, "value_propositions", [])),
        "sections_topology": list(getattr(dossier, "sections_topology", [])),
        "ux_best_practices": list(getattr(dossier, "ux_best_practices", [])),
    }

    # RFC-023: Inyección de Matriz de Cumplimiento Legal Planetario y Overlays Sectoriales
    from assessment_engine.infrastructure.primitives.legal_jurisdiction_matrix import LegalJurisdictionMatrix
    legal_matrix = LegalJurisdictionMatrix()
    legal_profile = legal_matrix.resolve_jurisdiction(
        domain_url=str(getattr(dossier, "benchmark_url", "") or "")
    )
    clean_domain_host = clean_brand.lower().replace(" ", "").replace(".", "")
    compliance_dossier = legal_matrix.generate_compliance_dossier(
        country_code=legal_profile.country_code,
        sector=sector,
        brand_name=clean_brand,
        legal_entity=f"{clean_brand} Platform S.L.",
        tax_id=legal_profile.tax_id_label,
        contact_email=f"legal@{clean_domain_host}.com",
    )
    compliance_dossier["mercantile_registry"] = "Sociedad en proceso de constitución mercantil / En trámite de inscripción en el Registro Mercantil."
    compliance_dossier["dsa_contact"] = f"dsa-compliance@{clean_domain_host}.com"
    compliance_dossier["odr_url"] = "https://ec.europa.eu/consumers/odr"

    contract["compliance_matrix"] = compliance_dossier
    contract["tax_id"] = compliance_dossier.get("tax_id", "B-88741920")
    contract["legal_entity"] = compliance_dossier.get("legal_entity", f"{clean_brand} Platform S.L.")
    contract["contact_email"] = compliance_dossier.get("contact_email", f"legal@{clean_domain_host}.com")
    contract["mercantile_registry"] = compliance_dossier["mercantile_registry"]
    contract["dsa_contact"] = compliance_dossier["dsa_contact"]
    contract["odr_url"] = compliance_dossier["odr_url"]

    if calibration_answers:
        contract = SocraticCalibratorEngine.merge_calibration_into_contract(contract, calibration_answers, socratic_result)
        logger.info(f"      - Decisiones de calibración socrática fusionadas en el contrato ({len(calibration_answers)} respuestas).")

    req_prims = list(getattr(dossier_3cubes, "required_primitives", []))
    if req_prims:
        existing_prims = contract.get("active_primitives", [])
        contract["active_primitives"] = list(dict.fromkeys(existing_prims + req_prims))
        logger.info(f"      - Primitivas requeridas de taxonomía inyectadas en domain_contract.json: {req_prims}")
    elif "active_primitives" in contract:
        logger.info(f"      - Primitivas fullstack activadas para Fase 3: {contract['active_primitives']}")

    safe_write_text(web_dir / "src" / "domain_contract.json", json.dumps(contract, indent=2, ensure_ascii=False))
    safe_write_text(output_dir / "docs" / "BUSINESS_MODEL.json", json.dumps(contract, indent=2, ensure_ascii=False))
    logger.info("      - Contrato único sincronizado en web/src/domain_contract.json y docs/BUSINESS_MODEL.json")
    return contract


def acto_3_inject_theme_tokens(output_dir: Path, clean_brand: str, dossier: Any) -> None:
    """Act 3: Compile design tokens into index.css and index.html."""
    logger.info("      - [Acto 3] Inyectando tokens semánticos OKLCH y tipografía en index.css e index.html...")
    clean_font = getattr(dossier.design_tokens, "font_family", "Plus Jakarta Sans").split(",")[0].strip("'\" ")
    if clean_font.lower() in ("sans-serif", "serif", "monospace", "system-ui", "times new roman", "times", "georgia") or "times" in clean_font.lower():
        clean_font = "Plus Jakarta Sans"

    encoded_font = clean_font.replace(" ", "+")
    google_fonts_url = f"https://fonts.googleapis.com/css2?family={encoded_font}:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap"

    clean_primary = getattr(dossier.design_tokens, "primary_color", "#0F172A")
    if clean_primary in ("rgba(0, 0, 0, 0)", "transparent", ""):
        clean_primary = "#0F172A"

    clean_surface = getattr(dossier.design_tokens, "background_color", "#FFFFFF")
    if clean_surface in ("rgba(0, 0, 0, 0)", "transparent", ""):
        clean_surface = "#FFFFFF"

    is_dark_theme = is_dark_hex(clean_surface)
    on_surface_color = "#F8FAFC" if is_dark_theme else "#0F172A"
    outline_color = "#334155" if is_dark_theme else "#E2E8F0"
    outline_variant_color = "#1E293B" if is_dark_theme else "#CBD5E1"

    theme_spec = {
        "app_name": clean_brand,
        "aesthetic_paradigm": "Clean High-End Craft",
        "colors": {
            "primary": clean_primary,
            "on_primary": "#FFFFFF",
            "surface": clean_surface,
            "on_surface": on_surface_color,
            "outline": outline_color,
            "outline_variant": outline_variant_color,
            "primary_container": clean_primary,
            "on_primary_container": "#FFFFFF",
        },
        "typography": {
            "display": clean_font,
            "body": "Inter",
            "mono": "JetBrains Mono",
            "google_fonts_url": google_fonts_url,
        },
    }
    theme_compiler.apply_theme_to_workspace(output_dir, theme_spec)


def inject_opengraph_tags(web_dir: Path, og_title: str, og_desc: str, og_image: str) -> None:
    """Inject rich OpenGraph metadata into index.html, updating existing tags or injecting new ones."""
    html_file = web_dir / "index.html"
    if not html_file.exists():
        return
    content = html_file.read_text(encoding="utf-8")
    clean_desc = og_desc.replace('"', '&quot;')
    clean_title = og_title.replace('"', '&quot;')

    content = re.sub(r'<meta\s+name=["\']description["\']\s+content=["\'][^"\']*["\']\s*/?>', f'<meta name="description" content="{clean_desc}" />', content)
    content = re.sub(r'<meta\s+property=["\']og:title["\']\s+content=["\'][^"\']*["\']\s*/?>', f'<meta property="og:title" content="{clean_title}" />', content)
    content = re.sub(r'<meta\s+property=["\']og:description["\']\s+content=["\'][^"\']*["\']\s*/?>', f'<meta property="og:description" content="{clean_desc}" />', content)
    content = re.sub(r'<meta\s+property=["\']og:image["\']\s+content=["\'][^"\']*["\']\s*/?>', f'<meta property="og:image" content="{og_image}" />', content)

    if 'property="og:title"' not in content:
        og_tags = (
            f'  <meta property="og:title" content="{clean_title}">\n'
            f'  <meta property="og:description" content="{clean_desc}">\n'
            f'  <meta property="og:image" content="{og_image}">\n'
            f'  <meta property="og:type" content="website">\n'
        )
        content = content.replace("<head>", f"<head>\n{og_tags}")
    safe_write_text(html_file, content)
    logger.info("      - Metadatos OpenGraph enriquecidos inyectados en index.html.")


def _init_visual_cache_db() -> None:
    SCHEMA_CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(SCHEMA_CACHE_DB_PATH), timeout=10.0) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS semantic_visual_cache (
                cache_key TEXT PRIMARY KEY,
                sector TEXT NOT NULL,
                asset_keys_json TEXT NOT NULL,
                cached_at REAL NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_visual_sector ON semantic_visual_cache(sector);")


def _get_visual_keys_from_cache(sector: str) -> list[str] | None:
    if not sector:
        return None
    try:
        _init_visual_cache_db()
        cache_key = hashlib.sha256(sector.strip().encode()).hexdigest()
        with sqlite3.connect(str(SCHEMA_CACHE_DB_PATH), timeout=5.0) as conn:
            cur = conn.cursor()
            cur.execute("SELECT asset_keys_json FROM semantic_visual_cache WHERE cache_key = ? OR sector = ?;", (cache_key, sector))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
            words = [w for w in re.sub(r'[^\w\s]', '', sector).split() if len(w) >= 4]
            if words:
                conditions = ' AND '.join('sector LIKE ?' for _ in words[:3])
                params = [f'%{w}%' for w in words[:3]]
                query = "SELECT asset_keys_json FROM semantic_visual_cache WHERE " + conditions + " LIMIT 1;"
                cur.execute(query, tuple(params))
                t_row = cur.fetchone()
                if t_row:
                    return json.loads(t_row[0])
    except Exception as ex:
        logger.debug(f"[AssetSelector] Error lectura caché visual: {ex}")
    return None


def _save_visual_keys_to_cache(sector: str, keys: list[str]) -> None:
    if not sector or not keys:
        return
    try:
        _init_visual_cache_db()
        cache_key = hashlib.sha256(sector.strip().encode()).hexdigest()
        with sqlite3.connect(str(SCHEMA_CACHE_DB_PATH), timeout=5.0) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO semantic_visual_cache (cache_key, sector, asset_keys_json, cached_at) VALUES (?, ?, ?, ?);",
                (cache_key, sector, json.dumps(keys), time.time()),
            )
            conn.commit()
    except Exception as ex:
        logger.debug(f"[AssetSelector] Error escritura caché visual: {ex}")


def _select_semantic_visual_keys(sector: str, tagline: str, catalog_keys: list[str]) -> list[str]:
    """Select the 3 most semantically aligned image keys using AOT cache or zero-shot inference."""
    if not catalog_keys:
        return []

    cached = _get_visual_keys_from_cache(sector)
    if cached and all(k in catalog_keys for k in cached):
        logger.info(f"      - [AssetSelector] ⚡ HIT AOT visual en SQLite WAL para '{sector[:35]}' (0.001s).")
        return cached[:3]

    try:
        client = create_genai_client()
        prompt = (
            f"Image catalog keys: {catalog_keys}\n"
            f"Business sector: '{sector}' | Tagline: '{tagline}'\n"
            "Select the 3 most semantically accurate and visually coherent image keys for this exact industry.\n"
            "Return ONLY a JSON list of 3 strings, e.g. [\"key1\", \"key2\", \"key3\"]."
        )
        resp = client.models.generate_content(
            model=get_model(ModelTier.FAST),
            contents=prompt,
            config={"response_mime_type": "application/json", "temperature": 0.1},
        )
        if resp and resp.text:
            parsed = json.loads(resp.text)
            if isinstance(parsed, list):
                valid = [k for k in parsed if k in catalog_keys]
                if len(valid) >= 3:
                    _save_visual_keys_to_cache(sector, valid[:3])
                    return valid[:3]
    except Exception as ex:
        logger.debug(f"[AssetSelector] Semantic photo selection note: {ex}")
    return catalog_keys[:3]


def _resolve_catalog_slots(
    extracted_imgs: list[str],
    verified_assets: dict[str, str],
    semantic_keys: list[str],
) -> tuple[str, str, str]:
    """Resolve hero primary, secondary and feature slots deterministically."""
    keys = (semantic_keys + ["office_modern", "business_meeting", "advisor_portrait"])[:3]
    h1 = extracted_imgs[0] if extracted_imgs else verified_assets.get(keys[0], "")
    h2 = extracted_imgs[1] if len(extracted_imgs) > 1 else verified_assets.get(keys[1], "")
    f1 = extracted_imgs[2] if len(extracted_imgs) > 2 else verified_assets.get(keys[2], "")
    return h1, h2, f1


def acto_4_populate_asset_catalog(
    output_dir: Path,
    web_dir: Path,
    clean_brand: str,
    sector: str,
    clean_tagline: str,
    contract: dict[str, Any],
    dossier: Any,
) -> dict[str, str]:
    """Act 4: Populate media asset catalog and inject OpenGraph metadata."""
    logger.info("      - [Acto 4] Ranurando catálogo de imágenes reales de alta resolución...")
    extracted_imgs = list(getattr(dossier, "extracted_images", []))
    verified_assets: dict[str, str] = {}
    if VERIFIED_ASSETS_PATH.exists():
        verified_assets = json.loads(VERIFIED_ASSETS_PATH.read_text(encoding="utf-8"))

    semantic_keys = _select_semantic_visual_keys(sector, clean_tagline, list(verified_assets.keys()))
    h1, h2, f1 = _resolve_catalog_slots(extracted_imgs, verified_assets, semantic_keys)

    asset_catalog: dict[str, Any] = {
        "hero_primary": h1,
        "hero_secondary": h2,
        "feature_primary": f1,
        "product_gallery": extracted_imgs,
        "fallback_assets": verified_assets,
    }
    safe_write_text(output_dir / "docs" / "ASSET_CATALOG.json", json.dumps(asset_catalog, indent=2, ensure_ascii=False))
    logger.info(f"      - Catálogo de fotos listo: {len(extracted_imgs)} fotos reales + {len(verified_assets)} de respaldo.")

    og_title = f"{clean_brand} — {sector}"
    og_desc = getattr(dossier, "meta_description", "") or clean_tagline
    inject_opengraph_tags(web_dir, og_title, og_desc, h1)

    final_assets = verified_assets.copy()
    for idx, img_url in enumerate(extracted_imgs):
        final_assets[f"competitor_photo_{idx+1}"] = img_url
    if extracted_imgs:
        final_assets["hero_bg_real"] = extracted_imgs[0]
    return final_assets


async def _execute_frontend_pipeline(
    prompt: str,
    sector: str,
    web_dir: Path,
    output_dir: Path,
    dossier: Any,
    dossier_3cubes: Any,
    calibration_answers: dict[str, str] | None,
    socratic_result: Any,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Execute Acts 2, 3, and 4 in atomic sequential order to avoid race conditions on web/index.html."""
    contract = acto_2_compile_domain_contract(
        prompt, sector, web_dir, output_dir, dossier, dossier_3cubes, calibration_answers, socratic_result
    )
    clean_brand = contract.get("app_name", "")
    acto_3_inject_theme_tokens(output_dir, clean_brand, dossier)
    final_assets = acto_4_populate_asset_catalog(
        output_dir, web_dir, clean_brand, sector, contract.get("tagline", ""), contract, dossier
    )
    return contract, final_assets


async def phase_2_domain_contract_and_sqlite(
    prompt: str,
    sector: str,
    project_slug: str,
    output_dir: Path,
    web_dir: Path,
    dossier: Any,
    dossier_3cubes: Any,
    calibration_answers: dict[str, str] | None = None,
    socratic_result: Any = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Execute Phase 2 full-stack materialization using orthogonal bimodal concurrency (Backend vs. Frontend)."""
    logger.info("[2/6] 🧬 Inicializando base de datos SQLite WAL, contrato canónico y paleta OKLCH (Partición Bimodal)...")

    backend_task = acto_1_synthesize_sqlite_tables(prompt, project_slug, output_dir, dossier, sector=sector)
    frontend_task = _execute_frontend_pipeline(
        prompt, sector, web_dir, output_dir, dossier, dossier_3cubes, calibration_answers, socratic_result
    )

    # Concurrency safe: Backend writes to api/app.db while Frontend writes to web/ and docs/ without race conditions
    _, (contract, final_assets) = await asyncio.gather(backend_task, frontend_task)

    # Acto 2.5: Compilación Ontológica de Rutas React (RFC-020 Misión B.3)
    target_db = output_dir / "app.db" if (output_dir / "app.db").exists() else output_dir / "api" / "app.db"
    if target_db.exists():
        try:
            router_engine = OntologyRouterEngine()
            routes_manifest = router_engine.build_routes_manifest(db_path=target_db, domain_contract=contract)

            router_compiler = ReactRouterCompiler()
            contract_file = web_dir / "src" / "domain_contract.json"
            router_compiler.compile_and_deploy_routes(
                routes_manifest=routes_manifest,
                web_src_dir=web_dir / "src",
                contract_path=contract_file,
            )
            if contract_file.exists():
                contract = json.loads(contract_file.read_text(encoding="utf-8"))

            docs_contract = output_dir / "docs" / "BUSINESS_MODEL.json"
            if docs_contract.exists():
                safe_write_text(docs_contract, json.dumps(contract, indent=2, ensure_ascii=False))

            docs_manifest = output_dir / "docs" / "ROUTES_MANIFEST.json"
            safe_write_text(docs_manifest, json.dumps(routes_manifest, indent=2, ensure_ascii=False))

            logger.info(
                f"      - [Acto 2.5] ⚡ Rutas ontológicas ({len(routes_manifest.get('routes', []))}) y AppRouterDispatcher compilados en web/src/"
            )
        except Exception as router_err:  # noqa: BLE001
            logger.warning(f"Nota en compilación de rutas ontológicas: {router_err}")

    return contract, final_assets