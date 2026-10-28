"""
Extract competitor structures dynamically (RFC-016 / RFC-017). Pipeline steps:
1. Discover targets via Google Search Grounding with pre-flight HTTP HEAD checks.
2. Enforce SSRF validation against cloud metadata (169.254.169.254) and private networks.
3. Scroll progressively via headless Playwright to trigger lazy loading.
4. Crawl pricing subpaths (/pricing, /tarifas) and dismiss consent banners.
5. Mine customer feedback and vulnerability data for counter-positioning.
6. Generate FAQ matrix and fingerprint technology stacks.
7. Map targets to Soverik platform views (#view=).
8. Emit and persist CompetitorDossier to SQLite WAL.
"""
from __future__ import annotations
import hashlib
import ipaddress
import json
import logging
import re
import asyncio
import socket
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from google.genai import types
from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model
from assessment_engine.infrastructure.primitives.semantic_dom_compressor import asset_inspector, semantic_dom_compressor
logger = logging.getLogger('core.primitives.competitor_miner')

class BusinessArchetype(str, Enum):
    """Taxonomía canónica del modelo operativo y de captación del competidor."""
    APPOINTMENT_QUALIFIED = "appointment_qualified"
    ESTIMATOR_QUOTE = "estimator_quote"
    TRANSACTIONAL_DIRECT = "transactional_direct"
    DIRECT_CONSULTATION = "direct_consultation"

_MEDICAL_SCHEMA_ENTITIES: frozenset[str] = frozenset({
    "dentist", "medicalbusiness", "clinic", "physician", "hospital",
    "medicalorganization", "diagnosticlab", "reserveaction", "scheduleaction"
})

_APPOINTMENT_FORM_INDICATORS: frozenset[str] = frozenset({
    "doctor_id", "date", "patient_name", "cita", "reserva", "appointment",
    "booking", "turnos", "paciente", "agenda"
})

_QUOTE_FORM_INDICATORS: frozenset[str] = frozenset({
    "metros_cuadrados", "presupuesto_estimado", "tipo_reforma", "cotizacion",
    "estimator", "quote", "m2", "sqft", "superficie", "calc", "presupuesto"
})

_CURRENCY_SYMBOLS: frozenset[str] = frozenset({
    "€", "$", "£", "chf", "¥", "₹", "zł", "kr", "eur", "usd", "gbp"
})

_CHECKOUT_GATEWAY_INDICATORS: frozenset[str] = frozenset({
    "stripe", "checkout", "plan", "suscripcion", "subscription",
    "precio", "pricing", "tarifa", "cart", "carrito", "cesta", "comprar"
})

def _parse_raw_type(raw_type: Any) -> Set[str]:
    if isinstance(raw_type, list):
        return {str(t).strip().lower() for t in raw_type if t}
    if raw_type:
        return {str(raw_type).strip().lower()}
    return set()

def _parse_graph(graph: Any) -> Set[str]:
    if not isinstance(graph, list):
        return set()
    return {
        str(node["@type"]).strip().lower()
        for node in graph
        if isinstance(node, dict) and "@type" in node
    }

def _parse_dict_item(item: dict) -> Set[str]:
    types = _parse_raw_type(item.get("@type", ""))
    types.update(_parse_graph(item.get("@graph", [])))
    return types

def _extract_schema_types(schema_org: Optional[Tuple[Any, ...] | List[Any]]) -> Set[str]:
    if not schema_org:
        return set()
    
    types: Set[str] = set()
    for item in schema_org:
        if isinstance(item, str):
            types.add(item.strip().lower())
        elif isinstance(item, dict):
            types.update(_parse_dict_item(item))
            
    return types

def _extract_field_tokens(field: Any) -> Set[str]:
    tokens: Set[str] = set()
    if isinstance(field, dict):
        tokens.add(str(field.get("name", "")).lower())
        tokens.add(str(field.get("id", "")).lower())
    elif isinstance(field, str):
        tokens.add(field.lower())
    return tokens

def _extract_single_form_tokens(form: Dict[str, Any]) -> Set[str]:
    tokens: Set[str] = set()
    for field in form.get("fields", []):
        tokens.update(_extract_field_tokens(field))
    for attr in ("name", "id", "action"):
        val = form.get(attr)
        if val and isinstance(val, str):
            tokens.add(val.lower())
    return tokens

def _extract_form_tokens(sub_forms: Optional[List[Dict[str, Any]] | Tuple[Dict[str, Any], ...]]) -> Set[str]:
    if not sub_forms:
        return set()
    tokens: Set[str] = set()
    for form in sub_forms:
        if isinstance(form, dict):
            tokens.update(_extract_single_form_tokens(form))
    tokens.discard("")
    return tokens

def _has_appointment_indicator(sub_forms: Optional[List[Dict[str, Any]] | Tuple[Dict[str, Any], ...]], schema_org: Optional[Tuple[Any, ...] | List[Any]]) -> bool:
    schema_types = _extract_schema_types(schema_org)
    if bool(schema_types & _MEDICAL_SCHEMA_ENTITIES):
        return True
    form_tokens = _extract_form_tokens(sub_forms)
    return bool(form_tokens & _APPOINTMENT_FORM_INDICATORS)

def _has_quote_indicator(sub_forms: Optional[List[Dict[str, Any]] | Tuple[Dict[str, Any], ...]]) -> bool:
    form_tokens = _extract_form_tokens(sub_forms)
    return bool(form_tokens & _QUOTE_FORM_INDICATORS)

def _has_transactional_direct_indicator(raw_pricing_text: Optional[str]) -> bool:
    if not raw_pricing_text:
        return False
    text_lower = raw_pricing_text.lower()
    has_currency = any(symbol in text_lower for symbol in _CURRENCY_SYMBOLS)
    if not has_currency:
        return False
    return any(token in text_lower for token in _CHECKOUT_GATEWAY_INDICATORS)

def _resolve_business_archetype(raw_pricing_text: Optional[str] = "", sub_forms: Optional[List[Dict[str, Any]] | Tuple[Dict[str, Any], ...]] = None, schema_org: Optional[Tuple[Any, ...] | List[Any]] = None, conversion_channels: Optional[Dict[str, Any]] = None) -> BusinessArchetype:
    if _has_appointment_indicator(sub_forms, schema_org):
        return BusinessArchetype.APPOINTMENT_QUALIFIED
    if _has_quote_indicator(sub_forms):
        return BusinessArchetype.ESTIMATOR_QUOTE
    if _has_transactional_direct_indicator(raw_pricing_text):
        return BusinessArchetype.TRANSACTIONAL_DIRECT
    return BusinessArchetype.DIRECT_CONSULTATION

def _get_cta_label(custom_label: str, default_label: str) -> str:
    return custom_label if custom_label else default_label

def _format_phone_target(phone: Any) -> str:
    phone_str = str(phone)
    return phone_str if phone_str.startswith('tel:') else f"tel:{phone_str}"

def _resolve_channel_routing(channels: dict, custom_label: str) -> dict[str, str] | None:
    if channels.get('whatsapp'):
        return {
            'type': 'external', 
            'target': channels['whatsapp'], 
            'label': _get_cta_label(custom_label, 'Contactar por WhatsApp')
        }
    if channels.get('phone'):
        return {
            'type': 'external', 
            'target': _format_phone_target(channels['phone']), 
            'label': _get_cta_label(custom_label, 'Llamar Ahora')
        }
    return None

def _resolve_primary_cta_routing(archetype: Any, conversion_channels: dict, custom_label: str = '') -> dict[str, str]:
    arch_val = getattr(archetype, 'value', str(archetype))
    
    arch_map = {
        'appointment_qualified': ('modal', '#view=booking', 'Pedir Cita Online'),
        'estimator_quote': ('modal', '#view=estimator', 'Calcular Presupuesto'),
        'transactional_direct': ('modal', '#view=checkout', 'Empezar Ahora')
    }
    
    if arch_val in arch_map:
        r_type, target, def_label = arch_map[arch_val]
        return {'type': r_type, 'target': target, 'label': _get_cta_label(custom_label, def_label)}
        
    channel_route = _resolve_channel_routing(conversion_channels, custom_label)
    if channel_route:
        return channel_route
        
    return {'type': 'modal', 'target': '#view=contact', 'label': _get_cta_label(custom_label, 'Contactar')}
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DB_PATH = REPO_ROOT / 'storage' / 'data' / 'competitor_cache.db'
DB_TAXONOMY_PATH = REPO_ROOT / 'data' / 'enterprise_taxonomy.db'
CACHE_TTL_SECONDS = 2592000.0
_CACHE_WRITE_LOCK = threading.Lock()
SUBPAGE_PATTERNS: dict[str, re.Pattern[str]] = {'pricing': re.compile('(?i)(pricing|precios|tarifas|tarifs|preise|plans|kosten|planos|fees)'), 'booking': re.compile('(?i)(book|reservar|reservas|citas|agenda|appointment|services|servicios|catalogo)'), 'portal': re.compile('(?i)(portal|login|signin|app|client|dashboard|cuenta|acceso|iniciar)')}


async def _abort_unsafe_route(route: Any, request: Any, allow_local: bool) -> None:
    """Abort Playwright network requests targeting non-public or prohibited endpoints."""
    req_url = request.url
    if not is_safe_public_url(req_url, allow_local=allow_local):
        await route.abort('blockedbyclient')
        return
    await route.continue_()

async def _crawl_single_subtab(browser: Any, sub_url: str, sub_type: str, timeout_ms: int=4000, allow_local: bool=False) -> dict[str, Any]:
    """Crawl a single Level-1 operational subpage with isolated routing and anti-SSRF."""
    if not is_safe_public_url(sub_url, allow_local=allow_local):
        return {'type': sub_type, 'url': sub_url, 'status': 'blocked_ssrf'}
    if not browser:
        return {'type': sub_type, 'url': sub_url, 'status': 'no_browser'}
    tab_data: dict[str, Any] = {'type': sub_type, 'url': sub_url, 'headings': [], 'snippets': []}
    page = None
    try:
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        await page.route('**/*', lambda route, req: asyncio.create_task(_abort_unsafe_route(route, req, allow_local)))
        await page.goto(sub_url, wait_until='domcontentloaded', timeout=timeout_ms)
        content = await page.evaluate('() => {\n            const headings = Array.from(document.querySelectorAll(\'h1, h2, h3\'))\n                .map(h => (h.innerText || \'\').trim())\n                .filter(t => t.length > 3 && !/(cookie|consent|aviso)/i.test(t))\n                .slice(0, 5);\n            const containers = Array.from(document.querySelectorAll(\'[class*="pricing"], [class*="booking"], [class*="form"], form, table, section\'));\n            const snippets = containers.map(el => (el.innerText || \'\').trim()).filter(t => t.length > 20 && t.length < 1500).slice(0, 3);\n            return { headings: headings, snippets: snippets };\n        }')
        tab_data['raw_content'] = content
    except Exception as ex:
        logger.debug(f'[CompetitorMiner] Subtab {sub_type} crawl note: {ex}')
    finally:
        if page:
            await page.close()
    return tab_data

async def _crawl_concurrent_subtabs(browser: Any, subpage_candidates: dict[str, str], timeout_ms: int=4000, allow_local: bool=False) -> list[dict[str, Any]]:
    """Concurrently crawl up to 3 operational subpages using asyncio.gather."""
    if not subpage_candidates:
        return []
    if not browser:
        return [{'type': stype, 'url': url, 'status': 'blocked_ssrf' if not is_safe_public_url(url, allow_local=allow_local) else 'no_browser'} for stype, url in subpage_candidates.items()]
    tasks = [_crawl_single_subtab(browser, url, stype, timeout_ms=timeout_ms, allow_local=allow_local) for stype, url in subpage_candidates.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, dict)]

def _extract_domain_from_benchmark(b: Any) -> str | None:
    """Normalize and validate domain from a taxonomy benchmark reference."""
    match = re.search('\\b([a-zA-Z0-9-]+\\.[a-zA-Z]{2,}(?:\\.[a-zA-Z]{2,})?)\\b', str(b or ''))
    if not match:
        return None
    domain = match.group(1).lower()
    if any((d in domain for d in ('leader', 'ejemplo', 'example'))):
        return None
    return f'https://{domain}'

def _extract_taxonomy_benchmark_urls(sector: str) -> list[str]:
    """Extract official benchmark URLs for the given sector from enterprise taxonomy by exact name or code."""
    if not DB_TAXONOMY_PATH.exists():
        return []
    row = None
    try:
        with sqlite3.connect(str(DB_TAXONOMY_PATH), timeout=5.0) as conn:
            cur = conn.cursor()
            cur.execute('SELECT benchmark_1, benchmark_2, benchmark_3 FROM enterprises WHERE sector_name = ? OR sector_code = ? LIMIT 1;', (sector, sector))
            row = cur.fetchone()
    except Exception as ex:
        logger.debug(f'[CompetitorMiner] Fallback de taxonomía: {ex}')
        return []
    if not row:
        return []
    urls = [_extract_domain_from_benchmark(b) for b in row]
    return [u for u in urls if u is not None]


_CONVERSATIONAL_STOPWORDS: set[str] = {
    "quiero", "portal", "web", "como", "para", "hacer", "crear", "plataforma",
    "app", "clon", "tipo", "estilo", "sistema", "sitio", "página", "pagina",
    "need", "want", "like", "clone", "create", "build", "make", "looking"
}

_KNOWN_BENCHMARK_BRANDS: dict[str, str] = {
    "idealista": "https://www.idealista.com",
    "fotocasa": "https://www.fotocasa.es",
    "habitaclia": "https://www.habitaclia.com",
    "zillow": "https://www.zillow.com",
    "spotahome": "https://www.spotahome.com",
    "airbnb": "https://www.airbnb.com",
    "booking": "https://www.booking.com",
    "uber": "https://www.uber.com",
    "turo": "https://turo.com",
    "playtomic": "https://playtomic.io",
    "stripe": "https://stripe.com",
    "linear": "https://linear.app",
    "skool": "https://www.skool.com",
    "substack": "https://substack.com",
    "shopify": "https://www.shopify.com",
}


def _discover_by_token_conditions(cur: sqlite3.Cursor, words: list[str]) -> list[str]:
    """Helper to query enterprise taxonomy benchmarks using token conditions."""
    sorted_words = sorted(words, key=len, reverse=True)
    for word in sorted_words[:4]:
        cur.execute('SELECT benchmark_1, benchmark_2, benchmark_3 FROM enterprises WHERE sector_name LIKE ? LIMIT 1;', (f'%{word}%',))
        row = cur.fetchone()
        if row:
            urls = [_extract_domain_from_benchmark(b) for b in row]
            valid = [u for u in urls if u is not None]
            if valid:
                return valid
    return []


def _discover_by_fts_knowledge(clean: str) -> list[str]:
    """Helper to query SQLite FTS5 competitor knowledge table."""
    try:
        words = [w for w in re.sub(r'[^\w\s]', '', clean).split() if len(w) >= 4 and w.lower() not in _CONVERSATIONAL_STOPWORDS]
        if not words:
            return []
        fts_dossier = competitor_miner.find_similar_competitor_knowledge(" ".join(words[:3]))
        if fts_dossier and fts_dossier.benchmark_url:
            return [fts_dossier.benchmark_url]
    except Exception as ex:
        logger.debug(f'[CompetitorMiner] FTS discovery error: {ex}')
    return []


def _match_known_benchmark_brand(text: str) -> list[str]:
    """Check direct brand references in text against known leaders."""
    lower_text = text.lower()
    for brand, url in _KNOWN_BENCHMARK_BRANDS.items():
        if brand in lower_text:
            return [url]
    return []


def _extract_clean_keywords(text: str) -> list[str]:
    """Extract significant keywords filtering conversational stopwords."""
    return [
        w for w in re.sub(r'[^\w\s]', '', text).split()
        if len(w) >= 4 and w.lower() not in _CONVERSATIONAL_STOPWORDS
    ]


def _discover_taxonomy_urls(prompt: str, sector: str) -> list[str]:
    """Discover benchmark URLs from enterprise taxonomy via exact, token overlap, or FTS5."""
    known = _match_known_benchmark_brand(f"{prompt} {sector}")
    if known:
        return known

    urls = _extract_taxonomy_benchmark_urls(sector)
    if not urls and prompt:
        urls = _extract_taxonomy_benchmark_urls(prompt)
    if urls:
        return urls

    clean = f"{prompt} {sector}".strip()
    words = _extract_clean_keywords(clean)
    if words and DB_TAXONOMY_PATH.exists():
        try:
            with sqlite3.connect(str(DB_TAXONOMY_PATH), timeout=5.0) as conn:
                found = _discover_by_token_conditions(conn.cursor(), words)
                if found:
                    return found
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Token taxonomy search: {ex}')
    return _discover_by_fts_knowledge(clean)


def _consolidate_pricing_sources(
    dom_text: str,
    schema_org: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    api_payloads: dict[str, Any],
) -> str:
    """Consolidate pricing signals from DOM text, Schema.org entities, and API JSON payloads."""
    parts: list[str] = [dom_text] if dom_text else []
    if schema_org:
        parts.append(json.dumps(schema_org, ensure_ascii=False))
    if api_payloads:
        parts.append(json.dumps(api_payloads, ensure_ascii=False))
    return "\n\n".join(parts)

def _init_competitor_cache_schema() -> None:
    """Initialize the SQLite WAL cache database schema and FTS5 virtual table."""
    CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(CACHE_DB_PATH), timeout=10.0) as conn:
        conn.execute('PRAGMA journal_mode = WAL;')
        conn.execute('PRAGMA busy_timeout = 5000;')
        conn.execute('\n            CREATE TABLE IF NOT EXISTS competitor_cache (\n                cache_key TEXT PRIMARY KEY,\n                target_url TEXT NOT NULL,\n                sector TEXT NOT NULL,\n                dossier_json TEXT NOT NULL,\n                cached_at REAL NOT NULL\n            );\n        ')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_competitor_key ON competitor_cache(cache_key);')
        conn.execute('\n            CREATE VIRTUAL TABLE IF NOT EXISTS competitor_knowledge USING fts5(\n                sector,\n                brand_name,\n                target_url,\n                pricing_summary,\n                customer_pain_points,\n                counter_positioning,\n                ux_best_practices,\n                dossier_json UNINDEXED\n            );\n        ')
_init_competitor_cache_schema()

def _get_cache_conn() -> sqlite3.Connection:
    """Open an SQLite connection in WAL mode without DDL locks."""
    conn = sqlite3.connect(str(CACHE_DB_PATH), timeout=5.0)
    conn.execute('PRAGMA busy_timeout = 5000;')
    return conn
ALLOWED_WEB_PORTS = frozenset({80, 443})
ALLOWED_DEV_PORTS = frozenset({80, 443, 8088, 5173, 3000, 8000})

def _is_disallowed_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check whether an IP address belongs to reserved, private, loopback, or cloud metadata ranges."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    disallowed_attrs = ('is_private', 'is_loopback', 'is_link_local', 'is_reserved', 'is_multicast', 'is_unspecified')
    if any((getattr(ip, attr, False) for attr in disallowed_attrs)):
        return True
    ip_str = str(ip)
    if ip_str.startswith('169.254.'):
        return True
    if isinstance(ip, ipaddress.IPv4Address) and ip in ipaddress.ip_network('100.64.0.0/10'):
        return True
    return False

def _is_safe_port(parsed: urllib.parse.ParseResult, allow_local: bool) -> bool:
    """Validate that the URL connects exclusively to standard web ports or allowed local dev ports."""
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    allowed = ALLOWED_DEV_PORTS if allow_local else ALLOWED_WEB_PORTS
    return port in allowed

def _has_valid_scheme_and_host(parsed: urllib.parse.ParseResult) -> bool:
    """Validate that the scheme is http/https and a non-empty hostname exists."""
    return parsed.scheme in ('http', 'https') and bool(parsed.hostname)

def _is_allowed_local_target(parsed: urllib.parse.ParseResult, allow_local: bool) -> bool:
    """Check whether local target is explicitly permitted in test/development environments."""
    return allow_local and parsed.hostname in ('localhost', '127.0.0.1', '::1')

def _has_disallowed_ip_address(hostname: str, port: int) -> bool:
    """Resolve all A/AAAA records for the host in fail-closed mode and check for private or cloud metadata IPs."""
    try:
        addr_info = socket.getaddrinfo(hostname, port)
        if not addr_info:
            return True
        for _, _, _, _, sockaddr in addr_info:
            if _is_disallowed_ip(ipaddress.ip_address(sockaddr[0])):
                return True
        return False
    except Exception:
        return True

def is_safe_public_url(url: str, allow_local: bool=False) -> bool:
    """Validate that the URL is public and prevent SSRF attacks against private networks, non-web ports, and cloud metadata."""
    try:
        parsed = urllib.parse.urlparse(url)
        if not _has_valid_scheme_and_host(parsed) or not _is_safe_port(parsed, allow_local):
            return False
        if _is_allowed_local_target(parsed, allow_local):
            return True
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        return not _has_disallowed_ip_address(parsed.hostname, port)
    except Exception:
        return False

def _try_range_request_fallback(url: str, headers: dict[str, str], timeout: float) -> bool:
    """Attempt a GET request with a range header when HEAD is forbidden or not allowed."""
    try:
        headers['Range'] = 'bytes=0-1024'
        req_get = urllib.request.Request(url, headers=headers, method='GET')
        with urllib.request.urlopen(req_get, timeout=timeout) as resp_get:
            return resp_get.status in (200, 206, 301, 302, 307, 308)
    except Exception as ex:
        logger.debug(f'[CompetitorMiner] Range fallback error: {ex}')
        return False

def is_url_reachable(url: str, timeout: float=2.0) -> bool:
    """Verify via fast HTTP pre-flight request that the URL returns a success or redirect status, with Cloudflare WAF fallback."""
    if not is_safe_public_url(url, allow_local=False):
        return False
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    try:
        req = urllib.request.Request(url, headers=headers, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 301, 302, 307, 308)
    except urllib.error.HTTPError as http_err:
        if http_err.code in (403, 405):
            return _try_range_request_fallback(url, headers, timeout)
    except Exception as ex:
        logger.debug(f'[CompetitorMiner] URL reachability check failed: {ex}')
    return False

def _filter_valid_leader_urls(parsed: Any) -> list[str]:
    """Filter and validate extracted URLs using HTTP pre-flight checks."""
    if not isinstance(parsed, list):
        return []
    valid = [u for u in parsed if isinstance(u, str) and is_safe_public_url(u)]
    reachable = [u for u in valid if is_url_reachable(u)]
    return reachable[:3] or valid[:3]

def _extract_json_array_urls(raw_text: str) -> list[str]:
    """Extract and parse the JSON array of URLs from the search response."""
    clean = re.sub('^```(?:json)?\\s*|\\s*```$', '', raw_text.strip(), flags=re.MULTILINE)
    match = re.search('(\\[.*\\])', clean, flags=re.DOTALL)
    raw_json = match.group(1) if match else clean
    try:
        return _filter_valid_leader_urls(json.loads(raw_json))
    except (json.JSONDecodeError, TypeError):
        return []

def _extract_shortest_brand_token(parts: list[str]) -> str | None:
    """Extract shortest valid token from brand parts."""
    if not parts:
        return None
    shortest = min(parts, key=len)
    return shortest if len(shortest) >= 2 else None

def _clean_brand_name(raw_title: str, fallback_brand: str) -> str:
    """Extract and normalize the brand name, picking the shortest distinct token across separators."""
    if not raw_title or not raw_title.strip():
        return fallback_brand
    for sep in ('➤', '|', '–', '—', '-'):
        if sep in raw_title:
            parts = [p.strip() for p in raw_title.split(sep) if p.strip()]
            candidate = _extract_shortest_brand_token(parts)
            if candidate:
                return candidate
    return raw_title.strip() or fallback_brand

def _extract_dossier_tuples(raw_data: dict[str, Any], base_arch: Any) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[dict[str, str], ...], tuple[str, ...]]:
    """Package and normalize dossier tuples from raw DOM data."""
    headings = tuple(raw_data.get('headings', [])) or base_arch.value_propositions
    images = tuple(raw_data.get('images', []))
    ux = tuple(raw_data.get('uxBestPractices', [])) or ('Barra de navegación fija (sticky) para retención visual.', 'Matriz de precios escalonada con diferenciación clara.')
    faqs = tuple(raw_data.get('faqMatrix', [])) or base_arch.faq_matrix
    stack = tuple(raw_data.get('techStack', [])) or base_arch.tech_stack
    return (headings, images, ux, faqs, stack)

@dataclass(frozen=True)
class ExtractedPricingPlan:
    """Represent a pricing plan extracted from a competitor."""
    title: str
    price_text: str
    frequency: str
    features: tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True)
class ExtractedDesignTokens:
    """Design tokens extracted from the competitor's computed DOM."""
    primary_color: str
    background_color: str
    font_family: str
    border_radius: str
    is_dark_mode: bool = False
    button_style: dict[str, str] = field(default_factory=dict)
    accent_color: str = ""

@dataclass(frozen=True)
class CompetitorDossier:
    """Complete architectural dossier extracted from target sites."""
    sector: str
    benchmark_url: str
    brand_name: str
    pricing_plans: tuple[ExtractedPricingPlan, ...]
    value_propositions: tuple[str, ...]
    sections_topology: tuple[str, ...]
    design_tokens: ExtractedDesignTokens
    extracted_images: tuple[Any, ...] = field(default_factory=tuple)
    ux_best_practices: tuple[str, ...] = field(default_factory=tuple)
    hero_headline: str = ''
    cta_text: str = ''
    customer_pain_points: tuple[str, ...] = field(default_factory=tuple)
    counter_positioning: tuple[str, ...] = field(default_factory=tuple)
    faq_matrix: tuple[dict[str, str], ...] = field(default_factory=tuple)
    tech_stack: tuple[str, ...] = field(default_factory=tuple)
    mapped_features: tuple[str, ...] = field(default_factory=tuple)
    is_live_extraction: bool = False
    compressed_dom_json: str = ''
    extracted_contracts: dict[str, Any] = field(default_factory=dict)
    operational_forms: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    layout_compositions: dict[str, dict[str, str]] = field(default_factory=dict)
    api_payloads: dict[str, Any] = field(default_factory=dict)
    schema_org: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    social_proof: dict[str, Any] = field(default_factory=dict)
    conversion_channels: dict[str, str] = field(default_factory=dict)
    meta_description: str = ""
    infrastructure_signals: dict[str, str] = field(default_factory=dict)
    logo_url: str = ""
    trust_badges: tuple[str, ...] = field(default_factory=tuple)
    business_archetype: str = BusinessArchetype.DIRECT_CONSULTATION.value
    primary_cta_action: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serializa el dossier a formato diccionario."""
        return {
            'sector': self.sector,
            'benchmark_url': self.benchmark_url,
            'brand_name': self.brand_name,
            'pricing_plans': [{'title': p.title, 'price_text': p.price_text, 'frequency': p.frequency, 'features': list(p.features)} for p in self.pricing_plans],
            'value_propositions': list(self.value_propositions),
            'sections_topology': list(self.sections_topology),
            'design_tokens': {
                'primary_color': self.design_tokens.primary_color,
                'background_color': self.design_tokens.background_color,
                'font_family': self.design_tokens.font_family,
                'border_radius': self.design_tokens.border_radius,
                'is_dark_mode': self.design_tokens.is_dark_mode,
                'button_style': dict(self.design_tokens.button_style),
                'accent_color': self.design_tokens.accent_color,
            },
            'extracted_images': list(self.extracted_images),
            'ux_best_practices': list(self.ux_best_practices),
            'hero_headline': self.hero_headline,
            'cta_text': self.cta_text,
            'customer_pain_points': list(self.customer_pain_points),
            'counter_positioning': list(self.counter_positioning),
            'faq_matrix': list(self.faq_matrix),
            'tech_stack': list(self.tech_stack),
            'mapped_features': list(self.mapped_features),
            'is_live_extraction': self.is_live_extraction,
            'compressed_dom_json': self.compressed_dom_json,
            'extracted_contracts': self.extracted_contracts,
            'operational_forms': list(self.operational_forms),
            'layout_compositions': dict(self.layout_compositions),
            'api_payloads': dict(self.api_payloads),
            'schema_org': list(self.schema_org),
            'social_proof': dict(self.social_proof),
            'conversion_channels': dict(self.conversion_channels),
            'meta_description': self.meta_description,
            'infrastructure_signals': dict(self.infrastructure_signals),
            'logo_url': self.logo_url,
            'trust_badges': list(self.trust_badges),
            'business_archetype': self.business_archetype,
            'primary_cta_action': dict(self.primary_cta_action),
        }

def _parse_views_json(raw_text: str) -> tuple[str, ...] | None:
    """Extract and validate platform view hashes from LLM response text."""
    clean = re.sub('^```(?:json)?\\s*|\\s*```$', '', raw_text.strip(), flags=re.MULTILINE)
    match = re.search('(\\[.*\\])', clean, flags=re.DOTALL)
    raw_json = match.group(1) if match else clean
    try:
        items = json.loads(raw_json)
    except Exception:
        return None
    if not isinstance(items, list):
        return None
    valid = [v for v in items if isinstance(v, str) and v.startswith('#view=')]
    return tuple(valid) if valid else None

def _match_technical_slug_fallback(href: str) -> str | None:
    """Match technical URI path tokens based strictly on canonical web specifications (RFC 3986)."""
    path_lower = urllib.parse.urlparse(href).path.lower()
    if any((token in path_lower for token in ('pricing', 'plan', 'rate'))):
        return 'pricing'
    if any((token in path_lower for token in ('book', 'reserve', 'schedul'))):
        return 'booking'
    if any((token in path_lower for token in ('portal', 'login', 'auth', 'signin', 'account'))):
        return 'portal'
    return None

def _filter_valid_category_links(data: dict[str, Any], same_origin_links: list[dict[str, str]]) -> dict[str, str]:
    """Filter category mappings to ensure values match discovered links."""
    valid: dict[str, str] = {}
    known_hrefs = {l.get('href') for l in same_origin_links}
    for k in ('pricing', 'booking', 'portal'):
        val = data.get(k)
        if isinstance(val, str) and val in known_hrefs:
            valid[k] = val
    return valid

def _semantic_classify_subpage_links(same_origin_links: list[dict[str, str]]) -> dict[str, str]:
    """Classify navigational links into operational categories using multilingual zero-shot understanding."""
    if not same_origin_links:
        return {}
    try:
        client = create_genai_client()
        if not client:
            return {}
        payload = [{'href': l.get('href', ''), 'text': l.get('text', '')[:40]} for l in same_origin_links[:30]]
        prompt = f"""Analiza estos enlaces de navegación de una web en cualquier idioma del mundo:\n{json.dumps(payload, ensure_ascii=False)}\n\nIdentifica el enlace más relevante para cada categoría operativa:\n- 'pricing': Tarifas, precios, costes, planes, suscripciones.\n- 'booking': Citas, reservas, agendamiento, turnos, calendario.\n- 'portal': Acceso privado, login, área de clientes, autenticación, dashboard.\n\nDevuelve EXCLUSIVAMENTE un JSON con formato: {{"pricing": "<href o null>", "booking": "<href o null>", "portal": "<href o null>"}}"""
        resp = client.models.generate_content(model=get_model(ModelTier.FAST), contents=prompt, config={'response_mime_type': 'application/json', 'temperature': 0.0})
        if resp and resp.text:
            match = re.search('(\\{.*\\})', resp.text.strip(), flags=re.DOTALL)
            clean_json = match.group(1) if match else resp.text.strip()
            data = json.loads(clean_json)
            return _filter_valid_category_links(data, same_origin_links)
    except (RuntimeError, ValueError, KeyError, OSError, TypeError, json.JSONDecodeError) as ex:
        logger.debug(f'[CompetitorMiner] Zero-shot subpage classification note: {ex}')
    return {}

def _discover_subpage_candidates(links: list[dict[str, str]], base_url: str) -> dict[str, str]:
    """Isolate operational subpages (pricing, booking, portal) within the same domain using Zero-Language-Lock."""
    base_netloc = urllib.parse.urlparse(base_url).netloc.lower()
    same_origin: list[dict[str, str]] = []
    for link in links:
        href = link.get('href', '').strip()
        text = link.get('text', '').strip()
        if not href or href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
            continue
        full_url = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(full_url)
        if parsed.netloc.lower() == base_netloc:
            same_origin.append({'href': href, 'text': text, 'full_url': full_url})
    candidates: dict[str, str] = {}
    semantic_matches = _semantic_classify_subpage_links(same_origin)
    for cat, rel_href in semantic_matches.items():
        candidates[cat] = urllib.parse.urljoin(base_url, rel_href)
    for item in same_origin:
        cat = _match_technical_slug_fallback(item['href'])
        if cat and cat not in candidates:
            candidates[cat] = item['full_url']
    return candidates

def _extract_single_input(tag: str, attrs: str) -> dict[str, Any] | None:
    """Extract a sanitized single input field metadata."""
    name_m = re.search('name=["\\\']([^"\\\']+)["\\\']', attrs, re.IGNORECASE)
    id_m = re.search('id=["\\\']([^"\\\']+)["\\\']', attrs, re.IGNORECASE)
    type_m = re.search('type=["\\\']([^"\\\']+)["\\\']', attrs, re.IGNORECASE)
    field_name = name_m.group(1) if name_m else id_m.group(1) if id_m else ''
    field_type = type_m.group(1).lower() if type_m else 'textarea' if tag.lower() == 'textarea' else 'text'
    is_req = bool(re.search('\\b(required|aria-required=["\\\']true["\\\'])\\b', attrs, re.IGNORECASE))
    if field_name and field_type != 'hidden':
        return {'name': field_name[:40], 'type': field_type, 'required': is_req}
    return None

def _extract_form_schemas(html_content: str) -> list[dict[str, Any]]:
    """Extract form structures, input fields, types, and wizard steps from HTML."""
    if not html_content:
        return []
    form_matches = re.findall('(<form\\b[^>]*>.*?</form>)', html_content, re.IGNORECASE | re.DOTALL)
    if not form_matches:
        form_matches = [html_content]
    forms: list[dict[str, Any]] = []
    for f_html in form_matches[:5]:
        inputs: list[dict[str, Any]] = []
        input_tags = re.findall('<(input|select|textarea)\\b([^>]*)>', f_html, re.IGNORECASE)
        for tag, attrs in input_tags:
            inp = _extract_single_input(tag, attrs)
            if inp:
                inputs.append(inp)
        steps = re.findall('data-step=["\\\']([^"\\\']+)["\\\']', f_html, re.IGNORECASE)
        if inputs:
            forms.append({'fields': inputs[:15], 'steps': list(dict.fromkeys(steps))[:5]})
    return forms

async def _crawl_single_subtab_safe(browser_or_ctx: Any, sub_type: str, url: str, timeout_ms: int, allow_local: bool) -> dict[str, Any]:
    """Crawl a single subtab with SSRF protection."""
    if not is_safe_public_url(url, allow_local=allow_local):
        return {'type': sub_type, 'category': sub_type, 'url': url, 'status': 'blocked_ssrf'}
    if browser_or_ctx is None:
        return {'type': sub_type, 'category': sub_type, 'url': url, 'status': 'skipped_no_context'}
    page = None
    try:
        if hasattr(browser_or_ctx, 'new_page'):
            page = await browser_or_ctx.new_page()
        elif hasattr(browser_or_ctx, 'new_context'):
            ctx = await browser_or_ctx.new_context()
            page = await ctx.new_page()
        else:
            return {'type': sub_type, 'category': sub_type, 'url': url, 'status': 'skipped_no_context'}
        await page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
        text_content = await page.evaluate("() => document.body ? document.body.innerText.slice(0, 5000) : ''")
        page_html = await page.content()
        forms = _extract_form_schemas(page_html)
        return {'type': sub_type, 'category': sub_type, 'url': url, 'status': 'ok', 'raw_content': {'snippets': [text_content]}, 'forms': forms}
    except Exception as ex:
        logger.debug(f'[CompetitorMiner] Error crawling subtab {url}: {ex}')
        return {'type': sub_type, 'category': sub_type, 'url': url, 'status': 'error', 'error': str(ex)}
    finally:
        if page:
            try:
                await page.close()
            except Exception as close_ex:
                logger.debug(f'[CompetitorMiner] Subtab close error: {close_ex}')

async def _crawl_concurrent_subtabs(context: Any, candidates: dict[str, str], timeout_ms: int=4000, allow_local: bool=False) -> list[dict[str, Any]]:
    """Crawl discovered subpage candidates concurrently with SSRF protection."""
    if not candidates:
        return []
    tasks = [_crawl_single_subtab_safe(context, sub_type, url, timeout_ms, allow_local) for sub_type, url in candidates.items()]
    return await asyncio.gather(*tasks)

def _extract_pricing_from_subtabs(sub_results: list[dict[str, Any]], current_pricing: str) -> str:
    """Extract snippet pricing from subtab results if more complete than current."""
    for sub in sub_results:
        snippets = sub.get('raw_content', {}).get('snippets', [])
        if sub.get('type') == 'pricing' and snippets:
            candidate = '\n---\n'.join(snippets)
            if len(candidate) > len(current_pricing):
                return candidate
    return current_pricing

def _is_api_endpoint(url: str) -> bool:
    """Valida si una URL apunta a APIs REST, RPC o GraphQL bajo RFC 3986."""
    parsed = urllib.parse.urlsplit(url)
    host = parsed.netloc.lower().split(':')[0]
    path = parsed.path.lower()
    if host.startswith(('api.', 'backend.')) or '.api.' in host:
        return True
    api_markers = ('/api/', '/v1/', '/v2/', '/graphql', '/trpc/', '/_next/data/', '/gql', '/query')
    return any(marker in path for marker in api_markers)


def _is_javascript_asset(url: str, content_type: str) -> bool:
    """Determina si un recurso es un bundle JS según RFC 9239 o extensiones limpias."""
    if 'application/javascript' in content_type:
        return True
    path = urllib.parse.urlsplit(url).path.lower()
    return path.endswith('.js') or url.split('?')[0].lower().endswith('.js')


def _extract_infrastructure_signals(headers: dict[str, str]) -> dict[str, str]:
    """Extrae cabeceras de infraestructura normalizadas bajo RFC 9110 §5.1."""
    target_headers = {'server', 'x-powered-by', 'cf-ray', 'via'}
    signals: dict[str, str] = {}
    for k, v in headers.items():
        lower_k = str(k).lower()
        if lower_k in target_headers and v:
            signals[lower_k] = str(v).strip()
    return signals


def _schedule_async_capture(collector: Any, url: str, coro: Any) -> bool:
    """Schedule async capture on the running loop if available."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(collector._async_capture(url, coro))
        return True
    except RuntimeError:
        return False

def _extract_callable_json_data(collector: Any, url: str, fn: Any) -> Any:
    """Resolve callable json source handling async coroutines."""
    import inspect
    if inspect.iscoroutinefunction(fn):
        _schedule_async_capture(collector, url, fn())
        return None
    data = fn()
    if inspect.iscoroutine(data):
        _schedule_async_capture(collector, url, data)
        return None
    return data

class _ApiResponseCollector:
    """Collect API endpoints, payloads, JS bundles, and infrastructure signals from responses."""

    def __init__(self) -> None:
        self.endpoints: list[str] = []
        self.api_payloads: dict[str, Any] = {}
        self.js_bundles: list[str] = []
        self.infrastructure_signals: dict[str, str] = {}

    def handle_response(self, res: Any) -> None:
        """Handle individual network response and capture APIs, JS bundles, and infra headers."""
        url = getattr(res, 'url', '')
        headers = getattr(res, 'headers', {})
        headers_dict = headers if isinstance(headers, dict) else {}
        ct = str(headers_dict.get('content-type', '')).lower()

        self.infrastructure_signals.update(_extract_infrastructure_signals(headers_dict))

        if _is_javascript_asset(url, ct) and url not in self.js_bundles:
            if len(self.js_bundles) < 25:
                self.js_bundles.append(url)

        if 'application/json' in ct and _is_api_endpoint(url):
            if url not in self.endpoints and len(self.endpoints) < 4:
                self.endpoints.append(url)
                self._capture_payload(url, res)

    def _capture_payload(self, url: str, res: Any) -> None:
        """Capture JSON payload up to 10KB safely, supporting sync and async Playwright json."""
        if not hasattr(res, 'json'):
            return
        try:
            json_attr = getattr(res, 'json')
            data = _extract_callable_json_data(self, url, json_attr) if callable(json_attr) else json_attr
            if data is not None and len(json.dumps(data)) <= 10240:
                self.api_payloads[url] = data
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError, AttributeError) as ex:
            logger.debug(f'[ApiResponseCollector] JSON capture note on {url}: {ex}')
            logger.debug(f'[ApiResponseCollector] JSON capture note on {url}: {ex}')

    async def _async_capture(self, url: str, coro: Any) -> None:
        """Await async Playwright response.json() and store if <= 10KB."""
        try:
            data = await coro
            if data is not None and len(json.dumps(data)) <= 10240:
                self.api_payloads[url] = data
        except Exception as ex:
            logger.debug(f'[ApiResponseCollector] Async JSON capture note on {url}: {ex}')

def _parse_zero_shot_layout(resp_text: str) -> dict[str, str] | None:
    """Parse JSON response from zero-shot layout model."""
    match = re.search('(\\{.*\\})', resp_text.strip(), flags=re.DOTALL)
    clean_json = match.group(1) if match else resp_text.strip()
    try:
        data = json.loads(clean_json)
        pat = str(data.get('layout_pattern', ''))
        dens = str(data.get('visual_density', ''))
        valid_patterns = ('multi_step_wizard', 'tiered_cards', 'split_screen', 'bento_grid', 'vertical_stack')
        if pat in valid_patterns:
            return {'layout_pattern': pat, 'visual_density': dens if dens in ('compact', 'balanced', 'spacious') else 'balanced'}
    except (json.JSONDecodeError, TypeError):
        pass
    return None

_DOM_SCRAPER_SCRIPT = r"""() => {
    const dismissSelectors = [
        'button[id*="accept"]', 'button[class*="accept"]',
        'button[id*="agree"]', 'button[class*="agree"]',
        '#onetrust-accept-btn-handler'
    ];
    for (const sel of dismissSelectors) {
        const el = document.querySelector(sel);
        if (el) { el.click(); break; }
    }
    document.querySelectorAll('div[id*="cookie"], div[class*="cookie-banner"], div[id*="consent"], div[class*="consent-banner"], #onetrust-banner-sdk').forEach(el => {
        if (el && el.tagName !== 'HTML' && el.tagName !== 'BODY' && el.tagName !== 'MAIN') {
            el.remove();
        }
    });

    let heroH1 = '';
    for (const h of document.querySelectorAll('h1')) {
        const t = h.innerText.trim();
        if (t && !/(cookie|consent|aviso legal|privacidad)/i.test(t)) {
            heroH1 = t;
            break;
        }
    }

    const headings = Array.from(document.querySelectorAll('h1, h2, h3'))
        .map(h => h.innerText.trim())
        .filter(t => t.length > 5 && !/(cookie|consent|aviso legal|privacidad)/i.test(t))
        .slice(0, 5);

    const nav = Array.from(document.querySelectorAll('nav a, header a'))
        .map(a => a.innerText.trim())
        .filter(t => t.length > 2 && t.length < 30 && !/(carrito|cart|cookie|privacidad|legal|iniciar)/i.test(t));

    const images = [];
    document.querySelectorAll('img, picture source').forEach(el => {
        const src = el.src || el.getAttribute('data-src') || el.getAttribute('srcset') || el.getAttribute('data-lazy-src') || '';
        const cleanUrl = src.split(' ')[0].split(',')[0].trim();
        if (cleanUrl && cleanUrl.startsWith('http') && !cleanUrl.includes('svg') && !cleanUrl.includes('logo') && !cleanUrl.includes('icon') && !cleanUrl.includes('avatar') && !cleanUrl.includes('pixel')) {
            const w = el.naturalWidth || el.width || 0;
            const h = el.naturalHeight || el.height || 0;
            const ratio = w > h * 1.2 ? 'landscape' : (h > w * 1.2 ? 'portrait' : 'square');
            if (!images.some(i => (typeof i === 'string' ? i : i.url) === cleanUrl) && images.length < 8) {
                images.push({ url: cleanUrl, alt: (el.alt || '').slice(0, 80), aspect_ratio: ratio });
            }
        }
    });

    const bodyEl = document.body || document.documentElement;
    const bodyStyle = (bodyEl && bodyEl instanceof Element) ? window.getComputedStyle(bodyEl) : null;
    const bgColor = bodyStyle ? (bodyStyle.backgroundColor || '#FFFFFF') : '#FFFFFF';
    const fontFamily = bodyStyle ? (bodyStyle.fontFamily || 'sans-serif') : 'sans-serif';

    const genericCtaWords = ['aceptar', 'accept', 'agree', 'allow', 'rechazar', 'reject', 'cerrar', 'close', 'cookies', 'ok', 'consent', 'configurar'];
    let primaryColor = '#0F172A';
    let ctaText = 'Descubrir Selección';
    let buttonStyle = { shape: 'rounded', shadow: 'none' };
    let primaryBtnEl = null;
    const candidates = document.querySelectorAll('main button, main a[class*="btn"], main a[class*="button"], button, a[class*="btn"], a[class*="button"]');
    for (const el of candidates) {
        if (!el || !(el instanceof Element)) continue;
        const txt = (el.innerText || '').trim().toLowerCase();
        if (genericCtaWords.includes(txt) || txt.includes('cookie') || txt.includes('carrito') || txt.includes('cart')) continue;
        try {
            const st = window.getComputedStyle(el);
            const bg = st ? st.backgroundColor : '';
            if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent' && bg !== 'rgb(255, 255, 255)' && bg !== 'rgb(47, 255, 0)') {
                primaryColor = bg;
                primaryBtnEl = el;
                const br = parseInt(st.borderRadius || '0', 10);
                buttonStyle = {
                    shape: br >= 20 ? 'pill' : (br <= 2 ? 'sharp' : 'rounded'),
                    shadow: st.boxShadow && st.boxShadow !== 'none' ? 'shadow' : 'none'
                };
                if (el.innerText && el.innerText.trim().length < 30 && el.innerText.trim().length > 3) {
                    ctaText = el.innerText.trim();
                }
                break;
            }
        } catch (_) {}
    }

    let accentColor = '';
    const secondaryCandidates = Array.from(
        document.querySelectorAll('button:not([class*="primary"]), a[class*="secondary"], a[class*="btn"], a[class*="button"], button')
    ).slice(0, 12);
    for (const el of secondaryCandidates) {
        if (!el || el === primaryBtnEl) continue;
        try {
            const st = window.getComputedStyle(el);
            const bg = st ? st.backgroundColor : '';
            const fg = st ? st.color : '';
            if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent' && bg !== 'rgb(255, 255, 255)' && bg !== primaryColor) {
                accentColor = bg;
                break;
            } else if (!accentColor && fg && fg !== 'rgb(0, 0, 0)' && fg !== 'rgb(255, 255, 255)' && fg !== primaryColor) {
                accentColor = fg;
            }
        } catch (_) {}
    }

    const schemaOrg = [];
    document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
        try {
            const parsed = JSON.parse(s.innerText);
            if (parsed && schemaOrg.length < 5) schemaOrg.push(parsed);
        } catch (_) {}
    });

    let ratingVal = '';
    let reviewCnt = '';
    const ratingEl = document.querySelector('[class*="rating"], [class*="review-score"], [aria-label*="rating"]');
    if (ratingEl) ratingVal = ratingEl.innerText.slice(0, 10).trim();
    const countEl = document.querySelector('[class*="review-count"], [class*="reviews-total"]');
    if (countEl) reviewCnt = countEl.innerText.slice(0, 15).trim();

    const rgbMatch = bgColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    const isDark = Boolean(rgbMatch && (0.2126 * parseInt(rgbMatch[1], 10) + 0.7152 * parseInt(rgbMatch[2], 10) + 0.0722 * parseInt(rgbMatch[3], 10) < 128));

    const ogImgEl = document.querySelector('meta[property="og:image"], meta[name="og:image"]');
    const ogImageUrl = ogImgEl ? (ogImgEl.getAttribute('content') || '').trim() : '';

    const metaDescEl = document.querySelector('meta[name="description"], meta[property="og:description"]');
    const metaDescription = metaDescEl ? (metaDescEl.getAttribute('content') || '').trim() : '';

    let logoUrl = '';
    const logoEl = document.querySelector('link[rel*="icon"], img[class*="logo" i], img[id*="logo" i], img[alt*="logo" i]');
    if (logoEl) {
        const rawLogo = logoEl.tagName.toLowerCase() === 'link' ? (logoEl.getAttribute('href') || '') : (logoEl.currentSrc || logoEl.getAttribute('src') || '');
        if (rawLogo) {
            try { logoUrl = new URL(rawLogo, window.location.href).href; } catch (_) { logoUrl = rawLogo; }
        }
    }

    const conversionChannels = {};
    for (const a of Array.from(document.querySelectorAll('a[href]')).slice(0, 50)) {
        const href = (a.getAttribute('href') || '').trim();
        if (!conversionChannels.whatsapp && /wa\.me|api\.whatsapp\.com|whatsapp:/i.test(href)) conversionChannels.whatsapp = href;
        if (!conversionChannels.tel && href.startsWith('tel:')) conversionChannels.tel = href;
        if (!conversionChannels.mailto && href.startsWith('mailto:')) conversionChannels.mailto = href;
    }

    const uxBestPractices = [];
    if (document.querySelector('header[class*="sticky"], header[class*="fixed"], nav[class*="fixed"]')) {
        uxBestPractices.push('Barra de navegación fija (sticky) para retención visual inmediata.');
    }
    if (document.querySelectorAll('div[class*="card"], div[class*="pricing"], div[class*="tier"]').length > 1) {
        uxBestPractices.push('Matriz de precios escalonada con diferenciación clara de valor.');
    }
    if (document.querySelector('section[id*="faq"], div[class*="faq"], details')) {
        uxBestPractices.push('Sección de preguntas frecuentes (FAQ) para neutralizar objeciones.');
    }
    if (document.querySelector('div[class*="review"], div[class*="rating"], div[class*="testimonial"]')) {
        uxBestPractices.push('Prueba social con testimonios y calificaciones de clientes reales.');
    }

    const faqMatrix = [];
    document.querySelectorAll('details, [class*="faq"], [id*="faq"]').forEach(el => {
        const q = el.querySelector('summary, h3, h4, [class*="question"]');
        const a = el.querySelector('p, [class*="answer"]');
        if (q && a && faqMatrix.length < 4) {
            faqMatrix.push({ question: q.innerText.trim(), answer: a.innerText.trim() });
        }
    });

    const techStack = [];
    if (window.Stripe || document.querySelector('script[src*="stripe"]')) techStack.push('Stripe Elements');
    if (window.gtag || document.querySelector('script[src*="googletagmanager"]')) techStack.push('Google Analytics');
    if (document.querySelector('link[href*="fonts.googleapis.com"]')) techStack.push('Google Fonts');
    if (document.querySelector('script[src*="intercom"], script[src*="crisp"]')) techStack.push('Live Chat Widget');

    const pricingContainers = Array.from(document.querySelectorAll('[class*="pricing"], [class*="tier"], [class*="plan"], [id*="pricing"], [id*="tarifa"], [class*="price"], table, section, article'));
    const pricingText = pricingContainers.map(el => (el.innerText || '').trim()).filter(t => t.length > 20 && t.length < 2000).slice(0, 4).join('\\n---\\n');

    const trustBadges = [];
    document.querySelectorAll('[class*="badge"], [class*="guarantee"], [class*="trust"], [class*="security"], [class*="certif"]').forEach(el => {
        const txt = (el.innerText || '').trim();
        if (txt && txt.length > 3 && txt.length < 50 && !trustBadges.includes(txt) && trustBadges.length < 6) {
            if (!/(cookie|accept|agree)/i.test(txt)) trustBadges.push(txt);
        }
    });

    return {
        title: document.title,
        heroH1: heroH1,
        ctaText: ctaText,
        headings: headings,
        nav: nav,
        images: images,
        pricingText: pricingText,
        primaryColor: primaryColor,
        bgColor: bgColor,
        fontFamily: fontFamily,
        borderRadius: '8px',
        isDarkMode: isDark,
        buttonStyle: buttonStyle,
        accentColor: accentColor,
        schemaOrg: schemaOrg,
        socialProof: { rating_value: ratingVal, review_count: reviewCnt },
        uxBestPractices: uxBestPractices,
        faqMatrix: faqMatrix,
        techStack: techStack,
        ogImageUrl: ogImageUrl,
        metaDescription: metaDescription,
        conversionChannels: conversionChannels,
        logoUrl: logoUrl,
        trustBadges: trustBadges
    };
}"""


def _inject_discovered_endpoints(collector: Any, endpoints: list[str]) -> None:
    """Inject up to 12 discovered endpoints into the collector deduplicated."""
    if not collector or not endpoints:
        return
    for ep in endpoints:
        if ep not in collector.endpoints and len(collector.endpoints) < 12:
            collector.endpoints.append(ep)


class CompetitorMinerPrimitive:
    """Extract competitor data using Google Search grounding, Voice of Customer mining, Playwright browser automation, and SQLite WAL persistence."""
    SECTOR_ARCHETYPES: dict[str, dict[str, Any]] = {'insurance_gestoria': {'url': 'https://cleverea.com/', 'brand': 'Cleverea Insurtech', 'plans': (ExtractedPricingPlan('Seguro Moto 125cc', '12€', 'al mes', ('Asistencia 24h', 'Gestión DGT')), ExtractedPricingPlan('Coche a Todo Riesgo', '29€', 'al mes', ('Sin franquicia', 'Coche de sustitución')), ExtractedPricingPlan('Patinete Eléctrico', '4.50€', 'al mes', ('Responsabilidad civil 150.000€',))), 'value_props': ('Seguros 100% digitales sin papeleo ni permanencia', 'Gestión exprés de trámites de vehículos y notificaciones DGT', 'Atención personal en menos de 2 minutos vía WhatsApp'), 'sections': ('Header', 'Hero QuoteFlow', 'CoverageGrid', 'TestimonialsCarousel', 'FAQAccordion', 'Footer'), 'tokens': ExtractedDesignTokens('#1E3A8A', '#F8FAFC', 'Inter, sans-serif', '12px')}, 'sports_padel': {'url': 'https://playtomic.io/', 'brand': 'Playtomic Community', 'plans': (ExtractedPricingPlan('Alquiler Pista Valle', '24€', 'por hora y media', ('Pistas panorámicas', 'Luz LED')), ExtractedPricingPlan('Alquiler Pista Pico', '36€', 'por hora y media', ('Cámara de repetición', 'Vestuario VIP')), ExtractedPricingPlan('Bono 10 Partidos', '190€', 'tarifa plana', ('Descuento 15%', 'Reserva prioritaria 7 días'))), 'value_props': ('Reserva tu pista en menos de 3 clics y divide el pago entre 4', 'Únete a partidas abiertas de tu mismo nivel de juego (Nivel Playtomic)', 'Clases particulares con monitores certificados FEP'), 'sections': ('Header', 'Hero CourtFinder', 'OpenMatchesLive', 'TournamentsSection', 'PricingCards', 'Footer'), 'tokens': ExtractedDesignTokens('#10B981', '#FFFFFF', 'Inter, sans-serif', '8px')}, 'luxury_horlogerie': {'url': 'https://www.christies.com/', 'brand': "Christie's Haute Horlogerie", 'plans': (ExtractedPricingPlan('Catálogo Exclusivo', '0€', 'acceso libre', ('Verificación de procedencia', 'Fotos macro')), ExtractedPricingPlan('Puja en Sala VIP', '1.500€', 'fianza reembolsable', ('Asiento reservado', 'Línea telefónica')), ExtractedPricingPlan('Custodia Acorazada', '250€', 'al trimestre', ('Bóveda en Ginebra', 'Seguro Lloyds 100%'))), 'value_props': ('Subastas privadas de alta relojería suiza y piezas históricas', 'Certificación criptográfica de originalidad mediante peritaje forense', 'Transacciones discretas en francos suizos (CHF) con custodia asegurada'), 'sections': ('Header', 'Hero LotSpotlight', 'CuratedLotsGrid', 'ProvenanceInspection', 'BiddingRules', 'Footer'), 'tokens': ExtractedDesignTokens('#B45309', '#09090B', 'Cinzel, serif', '2px')}, 'b2b_saas': {'url': 'https://linear.app/', 'brand': 'Linear Software Craft', 'plans': (ExtractedPricingPlan('Starter Developer', '$0', 'siempre gratis', ('Hasta 250 incidencias', 'Teclas rápidas')), ExtractedPricingPlan('Standard Pro', '$8', 'por usuario/mes', ('Incidencias ilimitadas', 'SLA 99.9%')), ExtractedPricingPlan('Enterprise Scale', '$14', 'por usuario/mes', ('SAML SSO', 'Historial ilimitado'))), 'value_props': ('Velocidad de sincronización sub-50ms', 'Navegación completa por teclado', 'Diseñado para equipos de ingeniería de élite'), 'sections': ('Header', 'Hero InteractiveDemo', 'FeatureBento', 'ChangelogWall', 'PricingGrid', 'Footer'), 'tokens': ExtractedDesignTokens('#5E6AD2', '#0B0C0E', 'Inter, sans-serif', '8px')}}

    @staticmethod
    def _deserialize_dossier(data: dict[str, Any]) -> CompetitorDossier | None:
        """Safely reconstruct a CompetitorDossier preserving all 31 SOTA dimensions.

        Rejects legacy records from previous schemas (e.g. missing operational_forms).
        """
        if not isinstance(data, dict):
            return None
        if "operational_forms" not in data or "business_archetype" not in data:
            return None
        try:
            raw_plans = data.get("pricing_plans", [])
            plans = tuple(
                ExtractedPricingPlan(
                    title=p["title"],
                    price_text=p["price_text"],
                    frequency=p["frequency"],
                    features=tuple(p.get("features", ())),
                )
                for p in raw_plans
                if isinstance(p, dict)
            )
            tokens = ExtractedDesignTokens(**data.get("design_tokens", {}))
            return CompetitorDossier(
                sector=data["sector"],
                benchmark_url=data["benchmark_url"],
                brand_name=data["brand_name"],
                pricing_plans=plans,
                value_propositions=tuple(data.get("value_propositions", ())),
                sections_topology=tuple(data.get("sections_topology", ())),
                design_tokens=tokens,
                extracted_images=tuple(data.get("extracted_images", ())),
                ux_best_practices=tuple(data.get("ux_best_practices", ())),
                hero_headline=data.get("hero_headline", ""),
                cta_text=data.get("cta_text", ""),
                customer_pain_points=tuple(data.get("customer_pain_points", ())),
                counter_positioning=tuple(data.get("counter_positioning", ())),
                faq_matrix=tuple(data.get("faq_matrix", ())),
                tech_stack=tuple(data.get("tech_stack", ())),
                mapped_features=tuple(data.get("mapped_features", ())),
                is_live_extraction=bool(data.get("is_live_extraction", True)),
                compressed_dom_json=data.get("compressed_dom_json", ""),
                extracted_contracts=dict(data.get("extracted_contracts", {})),
                operational_forms=tuple(data.get("operational_forms", ())),
                layout_compositions=dict(data.get("layout_compositions", {})),
                api_payloads=dict(data.get("api_payloads", {})),
                schema_org=tuple(data.get("schema_org", ())),
                social_proof=dict(data.get("social_proof", {})),
                conversion_channels=dict(data.get("conversion_channels", {})),
                meta_description=str(data.get("meta_description", "")),
                infrastructure_signals=dict(data.get("infrastructure_signals", {})),
                logo_url=str(data.get("logo_url", "")),
                trust_badges=tuple(data.get("trust_badges", ())),
                business_archetype=str(data.get("business_archetype", BusinessArchetype.DIRECT_CONSULTATION.value)),
                primary_cta_action=dict(data.get("primary_cta_action", {})),
            )
        except Exception as ex:
            logger.debug(f"[CompetitorMiner] Error deserializing dossier: {ex}")
            return None

    def _get_from_cache(self, key: str) -> tuple[CompetitorDossier | None, bool]:
        """Retrieve the cached dossier from SQLite WAL under RFC 5861 SWR (Stale-While-Revalidate)."""
        try:
            with _get_cache_conn() as conn:
                cur = conn.cursor()
                cur.execute('SELECT dossier_json, cached_at FROM competitor_cache WHERE cache_key = ?', (key,))
                row = cur.fetchone()
                if row:
                    dossier_json, cached_at = row
                    is_stale = time.time() - float(cached_at) >= CACHE_TTL_SECONDS
                    data = json.loads(dossier_json)
                    dossier = self._deserialize_dossier(data)
                    if dossier is None:
                        return (None, False)
                    return (dossier, is_stale)
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Error lectura caché: {ex}')
        return (None, False)

    def _save_to_cache(self, key: str, dossier: CompetitorDossier) -> None:
        """Persist the dossier to the SQLite WAL database and index it in FTS5 under thread-safe lock."""
        try:
            dossier_str = json.dumps(dossier.to_dict())
            pricing_str = ' | '.join((f'{p.title} {p.price_text} {p.frequency}' for p in dossier.pricing_plans))
            pains_str = ' | '.join(dossier.customer_pain_points)
            counters_str = ' | '.join(dossier.counter_positioning)
            ux_str = ' | '.join(dossier.ux_best_practices)
            with _CACHE_WRITE_LOCK:
                with _get_cache_conn() as conn:
                    conn.execute('INSERT OR REPLACE INTO competitor_cache (cache_key, target_url, sector, dossier_json, cached_at) VALUES (?, ?, ?, ?, ?)', (key, dossier.benchmark_url, dossier.sector, dossier_str, time.time()))
                    conn.execute('INSERT INTO competitor_knowledge (sector, brand_name, target_url, pricing_summary, customer_pain_points, counter_positioning, ux_best_practices, dossier_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (dossier.sector, dossier.brand_name, dossier.benchmark_url, pricing_str, pains_str, counters_str, ux_str, dossier_str))
                    conn.commit()
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Error escritura caché/FTS5: {ex}')

    def find_similar_competitor_knowledge(self, query: str) -> CompetitorDossier | None:
        """Search accumulated intelligence using SQLite FTS5 (BM25)."""
        clean_query = re.sub(r'[^\w\s]', '', query).strip()
        tokens = [tok for tok in clean_query.split() if len(tok) > 2]
        if not tokens:
            return None
        fts_query = ' OR '.join((f'"{tok}"' for tok in tokens[:5]))
        try:
            with _get_cache_conn() as conn:
                cur = conn.cursor()
                cur.execute('SELECT dossier_json FROM competitor_knowledge WHERE competitor_knowledge MATCH ? ORDER BY rank LIMIT 1', (fts_query,))
                row = cur.fetchone()
                if row:
                    data = json.loads(row[0])
                    return self._deserialize_dossier(data)
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Error búsqueda FTS5: {ex}')
        return None

    def _match_archetype_key(self, prompt: str, sector: str) -> str:
        """Determine the closest archetype key based on the formal enterprise taxonomy database."""
        macro = ''
        try:
            from assessment_engine.infrastructure.primitives.design_system_synthesizer import _resolve_macro_category_from_db
            macro = _resolve_macro_category_from_db(prompt, sector)
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Archetype macro lookup: {ex}')
        if macro in ('SPORTS', 'FITNESS_SPORTS_CLUBS'):
            return 'sports_padel'
        if macro in ('LUXURY', 'RETAIL_COMMERCE_D2C'):
            return 'luxury_horlogerie'
        if macro in ('LEGAL_CORP', 'CIVICTECH_EMPLOYMENT', 'LOCAL_HOME_SERVICES'):
            return 'insurance_gestoria'
        return 'b2b_saas'

    def parse_dom_pricing(self, raw_pricing_data: list[dict[str, Any]]) -> tuple[ExtractedPricingPlan, ...]:
        """Convert DOM pricing data into immutable ExtractedPricingPlan instances."""
        plans: list[ExtractedPricingPlan] = []
        for item in raw_pricing_data[:4]:
            title = item.get('title', 'Tarifa').strip() or 'Tarifa Comercial'
            price = item.get('price', '0€').strip() or 'Consultar'
            freq = item.get('frequency', 'por servicio').strip() or 'único'
            feats = tuple(item.get('features', []))
            plans.append(ExtractedPricingPlan(title=title, price_text=price, frequency=freq, features=feats))
        return tuple(plans)

    def _parse_json_pricing_items(self, raw_text: str) -> tuple[ExtractedPricingPlan, ...]:
        """Parse JSON array of plans into ExtractedPricingPlan objects."""
        clean = re.sub('^```(?:json)?\\s*|\\s*```$', '', raw_text.strip(), flags=re.MULTILINE)
        match = re.search('(\\[.*\\])', clean, flags=re.DOTALL)
        raw_json = match.group(1) if match else clean
        try:
            items = json.loads(raw_json)
            if not isinstance(items, list):
                return ()
            plans: list[ExtractedPricingPlan] = []
            for item in items[:4]:
                title = str(item.get('title') or 'Tarifa Comercial').strip()
                price = str(item.get('price_text') or 'Consultar').strip()
                freq = str(item.get('frequency') or 'al mes').strip()
                feats = tuple((str(f) for f in item.get('features', [])))
                plans.append(ExtractedPricingPlan(title=title, price_text=price, frequency=freq, features=feats))
            return tuple(plans)
        except Exception:
            return ()

    def _semantic_extract_pricing_plans(self, raw_pricing_text: str, brand_name: str, sector: str) -> tuple[ExtractedPricingPlan, ...]:
        """Extract structured pricing plans from unstructured worldwide text using zero-shot semantic understanding."""
        if not raw_pricing_text or len(raw_pricing_text.strip()) < 10:
            return ()
        try:
            client = create_genai_client()
            prompt = f'''Analiza este texto extraído de la sección de tarifas/precios de '{brand_name}' ({sector}) en cualquier idioma o divisa:\n\n"""\n{raw_pricing_text[:2500]}\n"""\n\nExtrae hasta 3-4 planes comerciales reales en formato JSON.\nFormato exacto:\n[\n  {{\n    "title": "Nombre del plan en su idioma original",\n    "price_text": "Precio exacto con su divisa original tal como aparece",\n    "frequency": "Frecuencia normalizada concisa en español (ej. 'al mes', 'al año', 'por uso', 'único', 'por hora')",\n    "features": ["característica 1", "característica 2"]\n  }}\n]'''
            resp = client.models.generate_content(model=get_model(ModelTier.FAST), contents=prompt, config={'response_mime_type': 'application/json', 'temperature': 0.0})
            if resp and resp.text:
                return self._parse_json_pricing_items(resp.text)
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Semantic pricing extraction note: {ex}')
        return ()

    def parse_dom_navigation(self, nav_links: list[str]) -> tuple[str, ...]:
        """Extract and deduplicate navigation taxonomy from the target site."""
        seen: set[str] = set()
        clean: list[str] = []
        for link in nav_links:
            text = link.strip()
            if text and len(text) < 30 and (text not in seen):
                seen.add(text)
                clean.append(text)
        return tuple(clean[:8])

    def discover_leader_urls(self, prompt: str, sector: str) -> list[str]:
        """Discover competitor URLs using taxonomy fast-path or Google Search Grounding fallback."""
        taxonomy_urls = _discover_taxonomy_urls(prompt, sector)
        if taxonomy_urls:
            return taxonomy_urls
        fallback_url = self.SECTOR_ARCHETYPES[self._match_archetype_key(prompt, sector)]['url']
        urls = [fallback_url]
        try:
            client = create_genai_client()
            search_prompt = f"Busca en Google las 3 mejores plataformas o páginas web de referencia real para: '{prompt}' (sector: '{sector}').\nEmite EXCLUSIVAMENTE un array JSON con 3 URLs oficiales HTTPS válidas. Formato exacto: ['https://...', 'https://...']"
            resp = client.models.generate_content(model=get_model(ModelTier.FAST), contents=search_prompt, config=types.GenerateContentConfig(temperature=0.1, tools=[types.Tool(google_search=types.GoogleSearch())]))
            if resp and resp.text:
                extracted = _extract_json_array_urls(resp.text)
                if extracted:
                    return extracted
        except Exception as exc:
            logger.debug(f'[CompetitorMiner] Fallback a URL de taxonomía o arquetípica: {exc}')
        return urls

    def get_fallback_dossier(self, prompt: str, sector: str) -> CompetitorDossier:
        """Return a deterministic fallback competitor dossier without network calls, preferring taxonomy benchmarks."""
        key = self._match_archetype_key(prompt, sector)
        arch = self.SECTOR_ARCHETYPES[key]
        taxonomy_urls = _extract_taxonomy_benchmark_urls(sector)
        target_url = taxonomy_urls[0] if taxonomy_urls else arch['url']
        brand_name = arch['brand']
        if taxonomy_urls:
            brand_name = target_url.replace('https://', '').replace('www.', '').split('.')[0].capitalize()
        return CompetitorDossier(
            sector=sector,
            benchmark_url=target_url,
            brand_name=brand_name,
            pricing_plans=arch['plans'],
            value_propositions=arch['value_props'],
            sections_topology=arch['sections'],
            design_tokens=arch['tokens'],
            hero_headline=arch['value_props'][0] if arch.get('value_props') else 'Servicio de Élite',
            cta_text='Reservar Ahora',
            customer_pain_points=('Cancelación compleja o con penalización', 'Atención al cliente lenta o impersonal', 'Costes ocultos en la pasarela de pago'),
            counter_positioning=('Cancelación instantánea en 1 clic sin coste', 'Soporte directo por WhatsApp en menos de 2 minutos', 'Precios 100% transparentes sin cargos sorpresa'),
            faq_matrix=({'question': '¿Cómo funciona la reserva?', 'answer': 'Selecciona la franja horaria y confirma en 3 clics.'}, {'question': '¿Puedo cancelar en cualquier momento?', 'answer': 'Sí, cancelación libre hasta 2 horas antes.'}),
            tech_stack=('Stripe Elements', 'Tailwind CSS', 'React 19'),
            mapped_features=('#view=booking', '#view=pricing', '#view=login'),
            is_live_extraction=False,
            layout_compositions={'pricing': {'layout_pattern': 'grid', 'visual_density': 'medium'}, 'booking': {'layout_pattern': 'multi_step_wizard', 'visual_density': 'compact'}, 'portal': {'layout_pattern': 'split_screen', 'visual_density': 'balanced'}},
            schema_org=(),
            social_proof={'rating_value': '4.9', 'review_count': '500+'},
            infrastructure_signals={},
            logo_url="",
            trust_badges=('Garantía de Satisfacción 100%', 'Soporte Oficial 24/7', 'Certificado SSL Seguro'),
            business_archetype=BusinessArchetype.DIRECT_CONSULTATION.value,
            primary_cta_action=_resolve_primary_cta_routing(BusinessArchetype.DIRECT_CONSULTATION.value, {}, 'Reservar Ahora'),
        )

    def _synthesize_dynamic_plans_if_empty(self, target_url: str, sector: str) -> tuple[ExtractedPricingPlan, ...]:
        """Synthesize dynamic pricing plans when no pricing is exposed on the target site."""
        try:
            client = create_genai_client()
            prompt = f"""Para este competidor del sector '{sector}' (URL: '{target_url}'):\nGenera exactamente 3 planes de tarifas comerciales realistas en formato JSON.\nFormato exacto:\n[\n  {{"title": "Nombre del Plan", "price_text": "XX €|CHF|$", "frequency": "al mes|por servicio|por hora", "features": ["Ventaja 1", "Ventaja 2"]}}\n]"""
            resp = client.models.generate_content(model=get_model(ModelTier.FAST), contents=prompt, config={'response_mime_type': 'application/json', 'temperature': 0.2})
            if resp and resp.text:
                items = json.loads(resp.text)
                if isinstance(items, list) and items:
                    return tuple((ExtractedPricingPlan(title=it.get('title', 'Tarifa').strip(), price_text=it.get('price_text', 'Consultar').strip(), frequency=it.get('frequency', 'por servicio').strip(), features=tuple(it.get('features', ()))) for it in items[:3]))
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Dynamic plan synthesis note: {ex}')
        key = self._match_archetype_key(target_url, sector)
        return self.SECTOR_ARCHETYPES[key]['plans']

    def _mine_voice_of_customer(self, prompt: str, sector: str, brand_name: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Extract customer complaints regarding the competitor and formulate counter-positioning angles."""
        try:
            client = create_genai_client()
            search_prompt = f"""Investiga en Google qué quejas, fricciones y problemas reales suelen tener los clientes con empresas líderes como '{brand_name}' en el sector '{sector}' (ej. '{prompt}').\nEmite EXCLUSIVAMENTE un objeto JSON con este esquema:\n{{\n  "pain_points": ["Queja/Fricción real 1", "Queja/Fricción real 2", "Queja/Fricción real 3"],\n  "counter_positioning": ["Cómo resolver la queja 1 agresivamente", "Cómo resolver la queja 2", "Cómo resolver la queja 3"]\n}}"""
            resp = client.models.generate_content(model=get_model(ModelTier.FAST), contents=search_prompt, config=types.GenerateContentConfig(temperature=0.1, tools=[types.Tool(google_search=types.GoogleSearch())]))
            if resp and resp.text:
                match = re.search('(\\{.*\\})', resp.text.strip(), flags=re.DOTALL)
                clean = match.group(1) if match else resp.text.strip()
                data = json.loads(clean)
                pains = tuple((str(x) for x in data.get('pain_points', [])))
                counters = tuple((str(x) for x in data.get('counter_positioning', [])))
                if pains and counters:
                    return (pains[:3], counters[:3])
        except Exception as exc:
            logger.debug(f'[CompetitorMiner] Voice of customer note: {exc}')
        return (('Cancelación compleja o con penalización', 'Atención al cliente lenta o impersonal', 'Costes ocultos en la pasarela de pago'), ('Cancelación instantánea en 1 clic sin coste', 'Soporte directo por WhatsApp en menos de 2 minutos', 'Precios 100% transparentes sin cargos sorpresa'))

    async def _infer_subpage_layout(self, subpage_type: str, page_text_or_html: str, screenshot_bytes: bytes | None=None) -> dict[str, str]:
        """Infer the visual layout pattern and density for a subpage via multilingual zero-shot or structural fallback."""
        if not page_text_or_html and (not screenshot_bytes):
            return {'layout_pattern': 'standard', 'visual_density': 'medium'}
        text_snippet = page_text_or_html[:1500] if page_text_or_html else ''
        content_lower = page_text_or_html.lower() if page_text_or_html else ''
        try:
            client = create_genai_client()
            prompt = f"""Analiza la siguiente página web o fragmento de contenido en cualquier idioma del mundo:\n'{text_snippet}'\n\nTipo de subpágina declarada: '{subpage_type}'\n\nClasifica su topología espacial en exactamente uno de estos patrones:\n- 'multi_step_wizard': Formularios paso a paso, selección de fechas/citas, wizards guiados.\n- 'tiered_cards': Columnas o tarjetas comparativas de precios, tarifas, suscripciones.\n- 'split_screen': Pantallas divididas de login, autenticación o portal de clientes.\n- 'bento_grid': Cuadrículas asimétricas de características o servicios.\n- 'vertical_stack': Estructura lineal estándar.\n\nEmite EXCLUSIVAMENTE un JSON: {{"layout_pattern": "multi_step_wizard"|"tiered_cards"|"split_screen"|"bento_grid"|"vertical_stack", "visual_density": "compact"|"balanced"|"spacious"}}"""
            resp = client.models.generate_content(model=get_model(ModelTier.FAST), contents=prompt, config={'response_mime_type': 'application/json', 'temperature': 0.0})
            if resp and resp.text:
                parsed = _parse_zero_shot_layout(resp.text)
                if parsed:
                    return parsed
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Multilingual layout zero-shot note: {ex}')
        pattern = self._resolve_structural_layout_fallback(subpage_type, content_lower)
        density = self._resolve_visual_density(len(content_lower))
        return {'layout_pattern': pattern, 'visual_density': density}

    def _resolve_structural_layout_fallback(self, subpage_type: str, content_lower: str) -> str:
        """Language-agnostic structural heuristic using DOM attributes and international signals."""
        if subpage_type == 'booking':
            return 'multi_step_wizard'
        if subpage_type == 'pricing':
            return 'tiered_cards'
        if subpage_type == 'portal':
            return 'split_screen'
        if re.search('\\b(data-step|aria-current=["\\\']step["\\\']|type=["\\\']date["\\\'])\\b', content_lower):
            return 'multi_step_wizard'
        if re.search('(\\d+[\\s,.]*\\d*\\s*([€$£¥₹]|chf|aed|usd|eur|gbp))|(([€$£¥₹]|chf|aed|usd|eur|gbp)\\s*\\d+)', content_lower):
            return 'tiered_cards'
        if re.search('\\b(type=["\\\']password["\\\']|autocomplete=["\\\']current-password["\\\'])\\b', content_lower):
            return 'split_screen'
        if re.search('\\b(grid-cols-|bento|display:\\s*grid)\\b', content_lower):
            return 'bento_grid'
        return 'vertical_stack'

    def _resolve_visual_density(self, text_length: int) -> str:
        """Resolve visual density bucket."""
        if text_length > 3000:
            return 'compact'
        if text_length < 500:
            return 'spacious'
        return 'balanced'

    def _map_features_to_platform_paradigms(self, sections: tuple[str, ...], value_props: tuple[str, ...]) -> tuple[str, ...]:
        """Route requests to platform paradigms using multilingual zero-shot semantic classification."""
        try:
            client = create_genai_client()
            prompt = f"Analiza estas secciones y servicios extraídos de una web en cualquier idioma: {list(sections + value_props)[:10]}\n\nCatálogo oficial de aplicaciones de la plataforma Soverik:\n- #view=booking: Citas, reservas horarias, turnos, pistas deportivas, reservas de espacio.\n- #view=seating: Selección visual en plano de pista, mesa, butaca o aforo.\n- #view=directorio: Directorio de miembros, comunidad, ranking ELO, ligas, torneos.\n- #view=pricing: Configurador dinámico de tarifas, suscripciones, membresías, bonos.\n- #view=comms: Centro de soporte, WhatsApp, mensajería, notificaciones.\n- #view=login: Autenticación con Passkeys FIDO2, cuenta de usuario.\n- #view=checkout: Pasarela de pago, contratación y facturación.\n- #view=canvas: Lienzo colaborativo en tiempo real.\n- #view=analytics: Panel de control de KPIs y analítica.\n\nDevuelve EXCLUSIVAMENTE un array JSON con los hashes #view= aplicables a este negocio. Ejemplo: ['#view=booking', '#view=pricing']"
            resp = client.models.generate_content(model=get_model(ModelTier.FAST), contents=prompt, config={'response_mime_type': 'application/json', 'temperature': 0.0})
            if resp and resp.text:
                parsed_views = _parse_views_json(resp.text)
                if parsed_views:
                    return parsed_views
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Semantic routing note: {ex}')
        return ('#view=booking', '#view=pricing', '#view=login')

    async def _execute_progressive_scroll(self, page: Any) -> None:
        """Trigger IntersectionObserver and activate lazy loading throughout the page scroll."""
        try:
            await page.evaluate('async () => {\n                const totalHeight = Math.min(document.body.scrollHeight, 3500);\n                const step = 700;\n                for (let y = 0; y < totalHeight; y += step) {\n                    window.scrollTo(0, y);\n                    await new Promise(r => setTimeout(r, 50));\n                }\n                window.scrollTo(0, 0);\n            }')
        except Exception as ex:
            logger.debug(f'Smooth scroll ignored exception: {ex}')

    async def _crawl_pricing_subpage_if_needed(self, page: Any, raw_pricing_text: str, allow_local: bool) -> str:
        """Locate and navigate to the pricing subpage or anchor if no pricing is found on the landing page."""
        if raw_pricing_text and len(raw_pricing_text.strip()) > 30:
            return raw_pricing_text
        try:
            pricing_url = await page.evaluate('() => {\n                const links = Array.from(document.querySelectorAll(\'a[href]\'));\n                for (const a of links) {\n                    const href = a.href || \'\';\n                    const txt = (a.innerText || \'\').toLowerCase();\n                    if (/(pricing|rates|precios|tarifas|tarifs|preise|plans|kosten|planos|fees)/i.test(href) || /(pricing|rates|precios|tarifas|tarifs|preise|plans)/i.test(txt)) {\n                        if (href.includes(\'#\')) {\n                            const hash = href.split(\'#\')[1];\n                            const targetEl = document.getElementById(hash) || document.querySelector(`[name="${hash}"]`);\n                            if (targetEl) {\n                                targetEl.scrollIntoView({ behavior: \'smooth\' });\n                                return \'__SCROLLED_TO_ANCHOR__\';\n                            }\n                        }\n                        if (href.startsWith(\'http\')) return href;\n                    }\n                }\n                return null;\n            }')
            if pricing_url == '__SCROLLED_TO_ANCHOR__':
                await page.wait_for_timeout(400)
            elif pricing_url and is_safe_public_url(pricing_url, allow_local=allow_local):
                await page.goto(pricing_url, wait_until='domcontentloaded', timeout=4000)
            sub_pricing_text = await page.evaluate('() => {\n                const containers = Array.from(document.querySelectorAll(\'[class*="pricing"], [class*="tier"], [class*="plan"], [id*="pricing"], [id*="tarifa"], table, section, article\'));\n                const texts = containers.map(el => (el.innerText || \'\').trim()).filter(t => t.length > 20 && t.length < 2000);\n                return texts.slice(0, 4).join(\'\\n---\\n\');\n            }')
            if sub_pricing_text:
                return sub_pricing_text
        except Exception as ex:
            logger.debug(f'Pricing crawl ignored exception: {ex}')
        return raw_pricing_text

    async def _revalidate_in_background(self, target_url: str, sector: str='SaaS Infrastructure', timeout_ms: int=8000, allow_local: bool=False) -> None:
        """Asynchronously revalidate competitor in background using Chromium without blocking."""
        try:
            logger.info(f'[CompetitorMiner] 🔄 Revalidando competidor en background: {target_url}')
            await self._crawl_fresh_dossier(target_url, sector, timeout_ms, allow_local)
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Background revalidation note for {target_url}: {ex}')

    async def mine_competitor_live(self, target_url: str, sector: str='SaaS Infrastructure', timeout_ms: int=8000, allow_local: bool=False) -> CompetitorDossier:
        """Navigate to the target website using Playwright and extract DOM data with RFC 5861 SWR caching, anti-SSRF, and cookie dismissal."""
        cache_key = hashlib.sha256(f'{target_url}:{sector}'.encode()).hexdigest()
        cached, is_stale = self._get_from_cache(cache_key)
        if cached:
            if is_stale:
                logger.info(f"[CompetitorMiner] ⚡ HIT SWR (>30d) para '{target_url}'. Entregando en 0.001s y programando refresco en background.")
                try:
                    asyncio.create_task(self._revalidate_in_background(target_url, sector, timeout_ms, allow_local))
                except Exception as ex:
                    logger.debug(f'[CompetitorMiner] Background dispatch note: {ex}')
            else:
                logger.info(f"[CompetitorMiner] ⚡ Reutilizando dossier en caché SQLite WAL para '{target_url}' (0.001s).")
            return cached
        return await self._crawl_fresh_dossier(target_url, sector, timeout_ms, allow_local)

    async def _crawl_fresh_dossier(self, target_url: str, sector: str='SaaS Infrastructure', timeout_ms: int=8000, allow_local: bool=False) -> CompetitorDossier:
        """Execute live crawl against competitor pages and persist fresh dossier in SQLite WAL."""
        cache_key = hashlib.sha256(f'{target_url}:{sector}'.encode()).hexdigest()
        if not is_safe_public_url(target_url, allow_local=allow_local):
            logger.warning(f'[CompetitorMiner] URL bloqueada por política anti-SSRF: {target_url}')
            return self.get_fallback_dossier(target_url, sector)
        try:
            dossier = await self._execute_playwright_crawl(target_url, sector, timeout_ms, allow_local)
            self._save_to_cache(cache_key, dossier)
            return dossier
        except Exception as exc:
            logger.debug(f'[CompetitorMiner] Fallback a arquetipo seguro tras error de red ({target_url}): {exc}')
            return self.get_fallback_dossier(target_url, sector)

    async def _execute_playwright_crawl(self, target_url: str, sector: str, timeout_ms: int, allow_local: bool) -> CompetitorDossier:
        """Perform Playwright Chromium navigation and extract structured data."""
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={'width': 1440, 'height': 900})
                collector = _ApiResponseCollector()
                page.on('response', collector.handle_response)
                await page.route('**/*', lambda route, req: asyncio.create_task(_abort_unsafe_route(route, req, allow_local)))
                await page.goto(target_url, wait_until='domcontentloaded', timeout=timeout_ms)
                await self._execute_progressive_scroll(page)
                return await self._build_dossier_from_page(browser, page, target_url, sector, timeout_ms, allow_local, collector=collector)
            finally:
                await browser.close()

    async def _enrich_tech_stack_with_bundles(
        self, base_stack: tuple[str, ...], js_bundles: list[str], collector: _ApiResponseCollector | None = None
    ) -> tuple[str, ...]:
        """Enrich tech stack and internal API endpoints by mining JavaScript bundles agnostically."""
        if not js_bundles:
            return base_stack
        tech_list = list(base_stack)
        try:
            from assessment_engine.infrastructure.primitives.competitor_bundle_miner import mine_javascript_bundles
            bundle_res = await mine_javascript_bundles(js_bundles)
            libs = bundle_res if isinstance(bundle_res, list) else bundle_res.get("libraries", [])
            for item in libs:
                if item not in tech_list:
                    tech_list.append(item)
            if isinstance(bundle_res, dict):
                _inject_discovered_endpoints(collector, bundle_res.get("endpoints", []))
        except Exception as ex:
            logger.debug(f'[CompetitorMiner] Bundle miner execution note: {ex}')
        return tuple(tech_list)

    async def _build_dossier_from_page(self, browser: Any, page: Any, target_url: str, sector: str, timeout_ms: int, allow_local: bool, collector: _ApiResponseCollector | None=None) -> CompetitorDossier:
        """Extract DOM metrics, subpages, and build canonical CompetitorDossier."""
        raw_data = await page.evaluate(_DOM_SCRAPER_SCRIPT)
        tokens = ExtractedDesignTokens(
            primary_color=raw_data.get('primaryColor', '#0F172A'),
            background_color=raw_data.get('bgColor', '#FFFFFF'),
            font_family=raw_data.get('fontFamily', 'sans-serif'),
            border_radius=raw_data.get('borderRadius', '8px'),
            is_dark_mode=bool(raw_data.get('isDarkMode', False)),
            button_style=raw_data.get('buttonStyle', {'shape': 'rounded', 'shadow': 'none'}),
            accent_color=str(raw_data.get('accentColor', '')),
        )
        base_arch = self.get_fallback_dossier(target_url, sector)
        headings_tuple, live_images, live_ux, live_faqs, detected_stack = _extract_dossier_tuples(raw_data, base_arch)
        raw_pricing_text = raw_data.get('pricingText', '')
        discovered_links = await page.evaluate("() => {\n            return Array.from(document.querySelectorAll('a[href]')).map(a => ({\n                href: a.getAttribute('href') || '',\n                text: (a.innerText || '').trim()\n            })).filter(item => item.href.length > 1).slice(0, 40);\n        }")
        sub_candidates = _discover_subpage_candidates(discovered_links, target_url)
        sub_results = await _crawl_concurrent_subtabs(browser, sub_candidates, timeout_ms=min(timeout_ms, 4000), allow_local=allow_local)
        raw_pricing_text = _extract_pricing_from_subtabs(sub_results, raw_pricing_text)
        if not raw_pricing_text:
            raw_pricing_text = await self._crawl_pricing_subpage_if_needed(page, raw_pricing_text, allow_local)
        sub_forms: list[dict[str, Any]] = []
        layout_maps: dict[str, dict[str, str]] = {}
        for sub in sub_results:
            stype = sub.get('type', 'unknown')
            snippet = ''.join(sub.get('raw_content', {}).get('snippets', []))
            layout_maps[stype] = await self._infer_subpage_layout(stype, snippet)
            for f in sub.get('forms', []):
                f_entry = dict(f)
                f_entry['subpage_type'] = stype
                f_entry['subpage_url'] = sub.get('url', '')
                sub_forms.append(f_entry)
        brand = _clean_brand_name(raw_data.get('title', base_arch.brand_name), base_arch.brand_name)
        schema_org_tuple = tuple(raw_data.get('schemaOrg', ()))
        api_payloads_dict = collector.api_payloads if collector else {}
        infra_signals = dict(collector.infrastructure_signals) if collector else {}
        js_bundles = collector.js_bundles if collector else []
        final_tech_stack = await self._enrich_tech_stack_with_bundles(detected_stack, js_bundles, collector=collector)

        unified_pricing_text = _consolidate_pricing_sources(raw_pricing_text, schema_org_tuple, api_payloads_dict)
        live_plans = self._semantic_extract_pricing_plans(unified_pricing_text, brand, sector)
        if not live_plans:
            live_plans = self._synthesize_dynamic_plans_if_empty(target_url, sector)
        raw_nav = raw_data.get('nav', [])
        live_nav = self.parse_dom_navigation(raw_nav) if raw_nav else base_arch.sections_topology
        pains, counters = self._mine_voice_of_customer(target_url, sector, brand)
        mapped_apps = self._map_features_to_platform_paradigms(live_nav, headings_tuple)
        compressed_dom = semantic_dom_compressor.compress_dom_data({
            'brand_name': brand,
            'page_type': 'competitor_aggregate',
            'headings': list(headings_tuple),
            'nav': list(live_nav),
            'pricing': [{'name': p.title, 'price': p.price_text, 'frequency': p.frequency, 'features': list(p.features)} for p in live_plans],
            'schema_org': list(schema_org_tuple),
            'api_payloads': api_payloads_dict,
            'operational_forms': list(sub_forms),
            'endpoints': list(collector.endpoints) if collector else [],
        })
        compressed_json = compressed_dom.to_canonical_json()
        
        resolved_archetype = _resolve_business_archetype(
            raw_pricing_text=unified_pricing_text,
            sub_forms=sub_forms,
            schema_org=schema_org_tuple,
            conversion_channels=dict(raw_data.get('conversionChannels', {})),
        )
        
        cta_action = _resolve_primary_cta_routing(
            resolved_archetype,
            dict(raw_data.get('conversionChannels', {})),
            raw_data.get('ctaText', base_arch.cta_text)
        )

        return CompetitorDossier(
            sector=sector,
            benchmark_url=target_url,
            brand_name=brand,
            pricing_plans=live_plans,
            value_propositions=headings_tuple,
            sections_topology=live_nav,
            design_tokens=tokens,
            extracted_images=live_images,
            ux_best_practices=live_ux,
            hero_headline=raw_data.get('heroH1', base_arch.hero_headline),
            cta_text=raw_data.get('ctaText', base_arch.cta_text),
            customer_pain_points=pains,
            counter_positioning=counters,
            faq_matrix=live_faqs,
            tech_stack=final_tech_stack,
            mapped_features=mapped_apps,
            is_live_extraction=True,
            compressed_dom_json=compressed_json,
            extracted_contracts=compressed_dom.contracts.to_dict(),
            operational_forms=tuple(sub_forms),
            layout_compositions=layout_maps,
            api_payloads=api_payloads_dict,
            schema_org=schema_org_tuple,
            social_proof=raw_data.get('socialProof', {}),
            conversion_channels=dict(raw_data.get('conversionChannels', {})),
            meta_description=str(raw_data.get('metaDescription', '')),
            infrastructure_signals=infra_signals,
            logo_url=str(raw_data.get('logoUrl', '')),
            trust_badges=tuple(raw_data.get('trustBadges', ())),
            business_archetype=resolved_archetype.value,
            primary_cta_action=cta_action,
        )
competitor_miner = CompetitorMinerPrimitive()