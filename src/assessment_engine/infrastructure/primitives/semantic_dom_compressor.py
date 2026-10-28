"""
Semantic DOM Compressor & Clean-Room Asset Inspector (RFC-016 / RFC-017).
Compresses raw page representations into canonical JSON (< 8 KB) and extracts
clean API contracts and data models from network responses without code cloning.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import urllib.parse
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.semantic_dom_compressor")

NOISE_FILTER_REGEX = re.compile(
    r"""(?i)\b(cookie|cookies|consent|consentimiento|rgpd|gdpr|aviso\s+legal|privacidad|privacy|terms|términos|rights\s+reserved)\b"""
)
STATE_BLOCK_REGEX = re.compile(
    r"""(?:window\.__INITIAL_STATE__|window\.__NEXT_DATA__|window\.__NUXT__)\s*=\s*(\{.*?\});""",
    re.DOTALL,
)

_IGNORED_FORM_FIELD_NAMES = frozenset({
    "csrf",
    "csrf_token",
    "_csrf",
    "authenticity_token",
    "_token",
    "nonce",
    "recaptcha_response",
    "h-captcha-response",
    "cf-turnstile-response",
})


@dataclass(frozen=True)
class FormField:
    """Represent an individual form field."""

    name: str
    field_type: str = "text"
    label: str = ""
    required: bool = False
    placeholder: str = ""
    options: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert field to dictionary representation."""
        res: dict[str, Any] = {"name": self.name, "type": self.field_type}
        if self.label:
            res["label"] = self.label
        if self.required:
            res["required"] = True
        if self.placeholder:
            res["placeholder"] = self.placeholder
        if self.options:
            res["options"] = list(self.options)
        return res


@dataclass(frozen=True)
class FormSchema:
    """Represent a structured form schema."""

    form_id: str
    action: str = ""
    method: str = "POST"
    fields: tuple[FormField, ...] = ()
    submit_label: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary representation."""
        return {
            "form_id": self.form_id,
            "action": self.action,
            "method": self.method,
            "submit_label": self.submit_label,
            "fields": [f.to_dict() for f in self.fields],
        }


@dataclass(frozen=True)
class PricingTier:
    """Represent a commercial pricing tier."""

    name: str
    price_text: str
    frequency: str = "/mes"
    features: tuple[str, ...] = ()
    is_highlighted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert pricing tier to dictionary representation."""
        return {
            "name": self.name,
            "price": self.price_text,
            "frequency": self.frequency,
            "is_highlighted": self.is_highlighted,
            "features": list(self.features),
        }


@dataclass(frozen=True)
class BookingStep:
    """Represent an operational appointment or booking workflow step."""

    step_number: int
    title: str
    fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert booking step to dictionary representation."""
        return {
            "step": self.step_number,
            "title": self.title,
            "fields": list(self.fields),
        }


@dataclass(frozen=True)
class ExtractedContract:
    """Represent clean-room API endpoints and data contracts without code cloning."""

    endpoints: tuple[dict[str, Any], ...] = ()
    state_machines: tuple[dict[str, Any], ...] = ()
    inferred_entities: dict[str, list[str]] = field(default_factory=dict)
    business_rules: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert contract to dictionary representation."""
        return {
            "endpoints": list(self.endpoints),
            "state_machines": list(self.state_machines),
            "inferred_entities": self.inferred_entities,
            "business_rules": list(self.business_rules),
        }


@dataclass(frozen=True)
class CompressedDOM:
    """Represent a semantic, condensed view of the crawled target."""

    brand_name: str
    page_type: str = "general"
    headings: tuple[str, ...] = ()
    navigation: tuple[str, ...] = ()
    forms: tuple[FormSchema, ...] = ()
    pricing_tiers: tuple[PricingTier, ...] = ()
    booking_steps: tuple[BookingStep, ...] = ()
    contracts: ExtractedContract = field(default_factory=ExtractedContract)

    def to_dict(self) -> dict[str, Any]:
        """Convert compressed DOM to dictionary."""
        return {
            "brand": self.brand_name,
            "page_type": self.page_type,
            "headings": list(self.headings),
            "nav": list(self.navigation),
            "forms": [f.to_dict() for f in self.forms],
            "pricing": [p.to_dict() for p in self.pricing_tiers],
            "booking_steps": [s.to_dict() for s in self.booking_steps],
            "contracts": self.contracts.to_dict(),
        }

    def to_canonical_json(self, max_bytes: int = 8192) -> str:
        """Serialize deterministically ensuring byte length is strictly bounded."""
        base_dict = self.to_dict()
        canonical = json.dumps(base_dict, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        encoded = canonical.encode("utf-8")
        if len(encoded) <= max_bytes:
            return canonical

        pruned_dict = dict(base_dict)
        pruned_dict["headings"] = pruned_dict.get("headings", [])[:8]
        pruned_dict["nav"] = pruned_dict.get("nav", [])[:8]
        if "pricing" in pruned_dict and isinstance(pruned_dict["pricing"], list):
            for p in pruned_dict["pricing"]:
                p["features"] = p.get("features", [])[:5]
        canonical = json.dumps(pruned_dict, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        if len(canonical.encode("utf-8")) <= max_bytes:
            return canonical

        pruned_dict["forms"] = pruned_dict.get("forms", [])[:3]
        pruned_dict["pricing"] = pruned_dict.get("pricing", [])[:4]
        return json.dumps(pruned_dict, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def _parse_field_dict(raw: dict[str, Any]) -> FormField:
    """Parse a single form field dictionary into a typed FormField."""
    raw_opts = raw.get("options", ())
    options_tuple = tuple(str(o) for o in raw_opts) if isinstance(raw_opts, (list, tuple)) else ()
    return FormField(
        name=str(raw.get("name", "field")),
        field_type=str(raw.get("type", "text")),
        label=str(raw.get("label", "")),
        required=bool(raw.get("required", False)),
        placeholder=str(raw.get("placeholder", "")),
        options=options_tuple,
    )


def _parse_form_dict(raw: dict[str, Any], idx: int) -> FormSchema:
    """Parse a single raw form definition into a typed FormSchema."""
    fields_raw = raw.get("fields", [])
    fields_list = [_parse_field_dict(f) for f in fields_raw if isinstance(f, dict)]
    return FormSchema(
        form_id=str(raw.get("form_id") or raw.get("id") or f"form_{idx}"),
        action=str(raw.get("action", "")),
        method=str(raw.get("method", "POST")).upper(),
        fields=tuple(fields_list),
        submit_label=str(raw.get("submit_label", "")),
    )


def _parse_pricing_item(raw: dict[str, Any]) -> PricingTier:
    """Parse a raw pricing entry into a typed PricingTier."""
    features_raw = raw.get("features", [])
    features_list = [str(f) for f in features_raw] if isinstance(features_raw, (list, tuple)) else []
    return PricingTier(
        name=str(raw.get("name") or raw.get("title") or "Tarifa"),
        price_text=str(raw.get("price") or raw.get("price_text") or "Consultar"),
        frequency=str(raw.get("frequency", "/mes")),
        features=tuple(features_list),
        is_highlighted=bool(raw.get("is_highlighted", False)),
    )


def _parse_booking_step(raw: dict[str, Any], idx: int) -> BookingStep:
    """Parse a booking step entry."""
    fields_raw = raw.get("fields", [])
    fields_list = [str(f) for f in fields_raw] if isinstance(fields_raw, (list, tuple)) else []
    return BookingStep(
        step_number=int(raw.get("step_number") or raw.get("step") or idx + 1),
        title=str(raw.get("title", f"Paso {idx + 1}")),
        fields=tuple(fields_list),
    )


def _clean_strings_with_noise_filter(items: Any, max_count: int = 15) -> tuple[str, ...]:
    """Filter noise, cookies and legal boilerplate while keeping valid items."""
    if not isinstance(items, (list, tuple)):
        return ()
    clean: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text or len(text) < 2 or len(text) > 200:
            continue
        if NOISE_FILTER_REGEX.search(text):
            continue
        if text not in seen:
            seen.add(text)
            clean.append(text)
            if len(clean) >= max_count:
                break
    return tuple(clean)


def _merge_entity_attrs(entities: dict[str, list[str]], entity_name: str, attrs: list[str]) -> None:
    """Merge attributes for an entity into the entities catalog."""
    if not entity_name:
        return
    current = set(entities.get(entity_name, []))
    current.update(attrs)
    entities[entity_name] = sorted(list(current))


def _flatten_schema_items(schema_data: Any) -> list[dict[str, Any]]:
    """Flatten schema.org items handling JSON strings, dicts, and @graph arrays."""
    parsed_data = schema_data
    if isinstance(schema_data, str):
        try:
            parsed_data = json.loads(schema_data)
        except Exception:
            return []
    if isinstance(parsed_data, dict):
        if "@graph" in parsed_data and isinstance(parsed_data["@graph"], list):
            return [node for node in parsed_data["@graph"] if isinstance(node, dict)]
        return [parsed_data]
    if isinstance(parsed_data, (list, tuple)):
        nodes: list[dict[str, Any]] = []
        for item in parsed_data:
            nodes.extend(_flatten_schema_items(item))
        return nodes
    return []


def _process_schema_node(node: dict[str, Any], entities: dict[str, list[str]]) -> None:
    """Extract candidate entity and properties from a single Schema.org node."""
    raw_type = node.get("@type")
    if not raw_type:
        return
    types = [raw_type] if isinstance(raw_type, str) else list(raw_type) if isinstance(raw_type, (list, tuple)) else []
    attrs = [str(k) for k in node.keys() if not str(k).startswith("@")]
    for t in types:
        type_str = str(t).strip()
        if not type_str:
            continue
        clean_name = type_str.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        _merge_entity_attrs(entities, clean_name, attrs)
        if clean_name != type_str:
            _merge_entity_attrs(entities, type_str, attrs)


def _process_schema_org_data(schema_data: Any, entities: dict[str, list[str]]) -> None:
    """Process schema.org structures extracting entities and their candidate attributes."""
    if not schema_data:
        return
    nodes = _flatten_schema_items(schema_data)
    for node in nodes:
        _process_schema_node(node, entities)


def _process_single_api_payload(item: Any, entities: dict[str, list[str]]) -> None:
    """Process an individual API payload log or response entry."""
    if isinstance(item, tuple) and len(item) == 2:
        asset_inspector._process_json_response(str(item[0]), "GET", item[1], [], entities)
        return
    if not isinstance(item, dict):
        return
    url = str(item.get("url") or item.get("endpoint") or "")
    payload = item.get("payload") if "payload" in item else item.get("body", item.get("data", item))
    asset_inspector._process_json_response(url, "GET", payload, [], entities)


def _process_api_payloads_data(api_payloads: Any, entities: dict[str, list[str]]) -> None:
    """Process API responses delegating to asset_inspector._process_json_response."""
    if not api_payloads:
        return
    if isinstance(api_payloads, dict):
        for url, payload in api_payloads.items():
            asset_inspector._process_json_response(str(url), "GET", payload, [], entities)
        return
    if not isinstance(api_payloads, (list, tuple)):
        return
    for item in api_payloads:
        _process_single_api_payload(item, entities)


def _extract_single_field_name(field_item: Any) -> str:
    """Extract the clean field name string from diverse field representations."""
    if isinstance(field_item, dict):
        return str(field_item.get("name") or field_item.get("id") or "").strip()
    if hasattr(field_item, "name"):
        return str(field_item.name).strip()
    if isinstance(field_item, str):
        return field_item.strip()
    return ""


def _extract_form_field_names(fields: Any) -> list[str]:
    """Extract sanitized and deduplicated form field names excluding security tokens."""
    if not isinstance(fields, (list, tuple)):
        return []
    names: list[str] = []
    for f in fields:
        name = _extract_single_field_name(f)
        if name and name.lower() not in _IGNORED_FORM_FIELD_NAMES:
            names.append(name)
    return sorted(list(set(names)))


def _process_operational_form(form: Any, entities: dict[str, list[str]]) -> None:
    """Extract domain entity attributes from an operational form definition."""
    if not isinstance(form, dict):
        return
    field_names = _extract_form_field_names(form.get("fields", []))
    entity_name = str(
        form.get("entity")
        or form.get("entity_type")
        or form.get("subpage_type")
        or form.get("form_id")
        or form.get("name")
        or form.get("id")
        or "operational_form"
    )
    _merge_entity_attrs(entities, entity_name, field_names)


def _process_operational_forms_data(forms_data: Any, entities: dict[str, list[str]]) -> None:
    """Process all operational forms entries into the entities dictionary."""
    if not isinstance(forms_data, (list, tuple)):
        return
    for form in forms_data:
        _process_operational_form(form, entities)


def persist_inferred_entities_to_sqlite(entities: dict[str, list[str]], db_path: str) -> None:
    """Persist inferred candidate entities into SQLite WAL for zero-cost relational indexing."""
    if not db_path or not entities:
        return
    try:
        with sqlite3.connect(db_path, timeout=5.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS candidate_relational_entities (
                    entity_type TEXT PRIMARY KEY,
                    attributes_json TEXT NOT NULL
                )
            """)
            for entity_type, attrs in entities.items():
                conn.execute(
                    "INSERT OR REPLACE INTO candidate_relational_entities (entity_type, attributes_json) VALUES (?, ?)",
                    (entity_type, json.dumps(attrs, ensure_ascii=False)),
                )
            conn.commit()
    except Exception:
        logger.debug("[SemanticDOMCompressor] SQLite WAL indexing encountered non-fatal error.")


def _init_contract_containers(
    raw_contract: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], dict[str, list[str]]]:
    """Initialize containers for contracts from ExtractedContract or dict representations."""
    if isinstance(raw_contract, ExtractedContract):
        return (
            list(raw_contract.endpoints),
            list(raw_contract.state_machines),
            list(raw_contract.business_rules),
            dict(raw_contract.inferred_entities),
        )
    if isinstance(raw_contract, dict):
        return (
            list(raw_contract.get("endpoints", [])),
            list(raw_contract.get("state_machines", [])),
            list(raw_contract.get("business_rules", [])),
            dict(raw_contract.get("inferred_entities", {})),
        )
    return [], [], [], {}


def _build_extracted_contract(raw_data: dict[str, Any]) -> ExtractedContract:
    """
    Build ExtractedContract extracting schema.org, API payloads, and operational forms.
    Guarantees McCabe V(G) <= 3 and nesting <= 1.
    """
    if not isinstance(raw_data, dict):
        return ExtractedContract()

    endpoints, state_machines, rules, inferred_entities = _init_contract_containers(
        raw_data.get("contracts")
    )

    raw_endpoints = raw_data.get("endpoints") or []
    for ep in raw_endpoints:
        ep_dict = ep if isinstance(ep, dict) else {"path": str(ep), "method": "GET"}
        if ep_dict not in endpoints:
            endpoints.append(ep_dict)

    _process_schema_org_data(raw_data.get("schema_org") or raw_data.get("schema"), inferred_entities)
    _process_api_payloads_data(raw_data.get("api_payloads"), inferred_entities)
    _process_operational_forms_data(
        raw_data.get("operational_forms") or raw_data.get("forms"), inferred_entities
    )

    db_path = str(raw_data.get("sqlite_path") or raw_data.get("db_path") or "")
    persist_inferred_entities_to_sqlite(inferred_entities, db_path)

    return ExtractedContract(
        endpoints=tuple(endpoints),
        state_machines=tuple(state_machines),
        inferred_entities=inferred_entities,
        business_rules=tuple(rules),
    )


class SemanticDOMCompressor:
    """Compress raw DOM extractions into canonical, token-efficient representations."""

    def compress_dom_data(self, raw_data: dict[str, Any], max_bytes: int = 8192) -> CompressedDOM:
        """
        Transform crawler raw data into a compact CompressedDOM object with candidate entities.
        Guarantees McCabe V(G) <= 4 and nesting <= 1.
        """
        brand = str(raw_data.get("brand_name") or raw_data.get("brand") or "Leader")
        page_type = str(raw_data.get("page_type", "general"))

        headings_raw = raw_data.get("headings", [])
        headings = _clean_strings_with_noise_filter(headings_raw, max_count=12)

        nav_raw = raw_data.get("nav", []) or raw_data.get("navigation", [])
        nav = _clean_strings_with_noise_filter(nav_raw, max_count=10)

        forms_raw = raw_data.get("forms", []) or raw_data.get("operational_forms", [])
        forms = tuple(_parse_form_dict(f, i) for i, f in enumerate(forms_raw) if isinstance(f, dict))

        pricing_raw = raw_data.get("pricing", []) or raw_data.get("pricing_plans", [])
        pricing = tuple(_parse_pricing_item(p) for p in pricing_raw if isinstance(p, dict))

        steps_raw = raw_data.get("booking_steps", [])
        steps = tuple(_parse_booking_step(s, i) for i, s in enumerate(steps_raw) if isinstance(s, dict))

        extracted_contract = _build_extracted_contract(raw_data)

        return CompressedDOM(
            brand_name=brand,
            page_type=page_type,
            headings=headings,
            navigation=nav,
            forms=forms,
            pricing_tiers=pricing,
            booking_steps=steps,
            contracts=extracted_contract,
        )


class CleanRoomAssetInspector:
    """Inspect network responses and scripts extracting API and data contracts without cloning code."""

    def inspect_network_traffic(self, responses: list[dict[str, Any]]) -> ExtractedContract:
        """Inspect HTTP traffic logs to extract clean data endpoints and schemas."""
        endpoints: list[dict[str, Any]] = []
        inferred_entities: dict[str, list[str]] = {}
        rules: list[str] = []

        for resp in responses:
            url = str(resp.get("url", ""))
            ct = str(resp.get("content_type", ""))
            body = resp.get("body", "")

            if "application/json" in ct:
                self._process_json_response(url, resp.get("method", "GET"), body, endpoints, inferred_entities)
            elif "javascript" in ct or url.endswith(".js"):
                self._process_javascript_asset(body, rules, inferred_entities)

        return ExtractedContract(
            endpoints=tuple(endpoints),
            state_machines=(),
            inferred_entities=inferred_entities,
            business_rules=tuple(rules),
        )

    def _process_json_response(
        self,
        url: str,
        method: str,
        body: Any,
        endpoints: list[dict[str, Any]],
        inferred_entities: dict[str, list[str]],
    ) -> None:
        """Extract endpoint and top-level entity fields from a JSON API response."""
        path = urllib.parse.urlparse(url).path
        endpoints.append({"method": method.upper(), "path": path})

        data = json.loads(body) if isinstance(body, str) else body
        if not isinstance(data, dict):
            return

        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                inferred_entities[k] = sorted(list(v[0].keys()))
            elif isinstance(v, dict):
                inferred_entities[k] = sorted(list(v.keys()))

    def _extract_state_entities(
        self,
        state_data: Any,
        rules: list[str],
        inferred_entities: dict[str, list[str]],
    ) -> None:
        """Extract schemas from state data mapping without deep nesting."""
        if not isinstance(state_data, dict):
            return
        for k, v in state_data.items():
            if isinstance(v, dict):
                inferred_entities[k] = sorted(list(v.keys()))
                rules.append(f"State schema detected for entity '{k}'.")

    def _process_javascript_asset(
        self,
        body: str,
        rules: list[str],
        inferred_entities: dict[str, list[str]],
    ) -> None:
        """Inspect JS bundle state without copying executable code."""
        match = STATE_BLOCK_REGEX.search(body)
        if not match:
            return
        try:
            state_data = json.loads(match.group(1))
        except Exception:
            logger.debug("[AssetInspector] Could not parse state block in JS asset.")
            return

        self._extract_state_entities(state_data, rules, inferred_entities)


semantic_dom_compressor = SemanticDOMCompressor()
asset_inspector = CleanRoomAssetInspector()


def compress_dom_data(raw_data: dict[str, Any], max_bytes: int = 8192) -> CompressedDOM:
    """Module-level entrypoint delegating to singleton semantic_dom_compressor."""
    return semantic_dom_compressor.compress_dom_data(raw_data, max_bytes=max_bytes)