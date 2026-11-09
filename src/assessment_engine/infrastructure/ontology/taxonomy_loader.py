"""Dynamic Ontological Graph Loader and Taxonomic Indexer Infrastructure Service.

Loads configuration assets (global_tech_ontology.yaml and domain/tower definition JSONs)
at runtime, compiling an in-memory DomainTaxonomyRegistry with positive affinity
lexicons and cross-domain exclusionary boundaries.
Strictly 100% Technical English, zero hardcoding, topology-agnostic, and multi-tenant.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import yaml

from assessment_engine.domain.ontology.models import (
    DomainTaxonomyRule,
    GatekeeperThresholds,
    PillarOntologyProfile,
)
from assessment_engine.domain.validation.semantic_gatekeeper import normalize_text

logger = logging.getLogger(__name__)

_TOKEN_REGEX = re.compile(r"\b[a-z0-9_\-]{2,}\b")


def _extract_filtered_tokens(
    text: str,
    thresholds: GatekeeperThresholds,
) -> Set[str]:
    """Extracts normalized alphanumeric tokens respecting minimum length and whitelisted short acronyms."""
    if not text:
        return set()
    norm = normalize_text(text)
    raw_tokens = _TOKEN_REGEX.findall(norm)
    return {
        t
        for t in raw_tokens
        if len(t) >= thresholds.min_token_length or t in thresholds.allowed_short_acronyms
    }


def _infer_categories_for_domain(
    domain_id: str,
    domain_rule: Optional[DomainTaxonomyRule],
    tower_def: Dict[str, Any],
    all_categories: Set[str],
    explicit_mapping: Dict[str, List[str]],
) -> Set[str]:
    """Dynamically resolves entity categories belonging to a domain without hardcoded T1..T10 maps."""
    resolved: Set[str] = set()

    # 1. Explicit categories declared in ontology domain_taxonomy_rules
    if domain_rule and domain_rule.categories:
        resolved.update(c.lower() for c in domain_rule.categories)

    # 2. Explicit categories declared in tower/domain JSON metadata
    for meta_key in ("ontology_categories", "entity_categories", "categories"):
        raw_cats = tower_def.get(meta_key, [])
        if isinstance(raw_cats, list):
            resolved.update(str(c).strip().lower() for c in raw_cats if str(c).strip())

    # 3. Explicit mapping block from YAML configuration (if present)
    if domain_id in explicit_mapping:
        resolved.update(c.lower() for c in explicit_mapping[domain_id])

    # 4. Lexical overlap inference between domain name/keywords and canonical category slugs
    if not resolved and all_categories:
        domain_tokens: Set[str] = set()
        if domain_rule:
            domain_tokens.update(normalize_text(domain_rule.name).split())
            for kw in domain_rule.keywords:
                domain_tokens.update(normalize_text(kw).split())
        tower_name = str(tower_def.get("tower_name") or tower_def.get("domain_name") or "")
        domain_tokens.update(normalize_text(tower_name).split())

        for cat in all_categories:
            cat_parts = set(cat.lower().split("_"))
            if cat_parts & domain_tokens:
                resolved.add(cat)

    return resolved


class DomainTaxonomyRegistry:
    """Immutable runtime index mapping any N-domain / N-pillar topology to positive lexicons

    and cross-domain exclusionary boundary sets.
    """

    def __init__(
        self,
        domain_rules: Dict[str, DomainTaxonomyRule],
        pillar_profiles: Dict[str, PillarOntologyProfile],
        short_id_index: Optional[Dict[str, List[PillarOntologyProfile]]] = None,
    ) -> None:
        self._domain_rules = dict(domain_rules)
        self._pillar_profiles = dict(pillar_profiles)
        self._short_id_index: Dict[str, List[PillarOntologyProfile]] = short_id_index or {}

    @classmethod
    def from_config_directories(
        cls,
        ontology_file: Path,
        towers_config_dir: Path,
        thresholds: Optional[GatekeeperThresholds] = None,
    ) -> DomainTaxonomyRegistry:
        """Constructs an indexed DomainTaxonomyRegistry dynamically from configuration assets.

        Supports arbitrary domain identifiers (e.g., T1..T10, D1..D8, custom domain slugs).
        """
        if not ontology_file.exists():
            raise FileNotFoundError(f"Global tech ontology file not found at: {ontology_file}")
        if not towers_config_dir.exists():
            raise FileNotFoundError(f"Towers configuration directory not found at: {towers_config_dir}")

        active_thresholds = thresholds or GatekeeperThresholds()

        with open(ontology_file, "r", encoding="utf-8") as f:
            raw_ontology: Dict[str, Any] = yaml.safe_load(f) or {}

        # 1. Extract Canonical Vendor / Technology Entities by Category and Explicit Domain Binding
        category_entities: Dict[str, Set[str]] = {}
        domain_direct_entities: Dict[str, Set[str]] = {}

        for ent in raw_ontology.get("canonical_entities", []):
            if not isinstance(ent, dict):
                continue
            cat = str(ent.get("category", "")).strip().lower()
            name = normalize_text(str(ent.get("canonical_name", "")).strip())
            acronyms = [
                normalize_text(str(a).strip())
                for a in ent.get("acronyms", [])
                if str(a).strip()
            ]
            tokens = {t for t in ({name} | set(acronyms)) if t}
            if cat:
                category_entities.setdefault(cat, set()).update(tokens)

            bound_domains = ent.get("domains") or ent.get("domain_ids") or []
            if isinstance(bound_domains, str):
                bound_domains = [bound_domains]
            for d_id in bound_domains:
                norm_d = str(d_id).strip().upper()
                if norm_d:
                    domain_direct_entities.setdefault(norm_d, set()).update(tokens)

        # Optional YAML-driven category mapping (zero hardcoded topology in Python)
        yaml_category_mapping: Dict[str, List[str]] = {}
        raw_cat_map = raw_ontology.get("domain_category_mapping", {})
        if isinstance(raw_cat_map, dict):
            for k, v in raw_cat_map.items():
                if isinstance(v, list):
                    yaml_category_mapping[str(k).strip().upper()] = [
                        str(item).strip().lower() for item in v if str(item).strip()
                    ]

        domain_rules: Dict[str, DomainTaxonomyRule] = {}
        for d_code, d_meta in raw_ontology.get("domain_taxonomy_rules", {}).items():
            if not isinstance(d_meta, dict):
                continue
            norm_d_code = str(d_code).strip().upper()
            keywords = tuple(
                normalize_text(str(k).strip())
                for k in d_meta.get("keywords", [])
                if str(k).strip()
            )
            categories = tuple(
                str(c).strip().lower()
                for c in d_meta.get("categories", yaml_category_mapping.get(norm_d_code, []))
                if str(c).strip()
            )
            direct_ents = tuple(sorted(domain_direct_entities.get(norm_d_code, set())))
            domain_rules[norm_d_code] = DomainTaxonomyRule(
                domain_id=norm_d_code,
                name=str(d_meta.get("name", norm_d_code)).strip(),
                categories=categories,
                keywords=keywords,
                canonical_entities=direct_ents,
            )

        # 3. Discover and Parse all Domain / Tower Definitions dynamically
        tower_definitions: Dict[str, Dict[str, Any]] = {}
        definition_files = sorted(
            set(towers_config_dir.rglob("tower_definition_*.json"))
            | set(towers_config_dir.rglob("domain_definition_*.json"))
        )
        for def_file in definition_files:
            stem = def_file.stem
            for prefix in ("tower_definition_", "domain_definition_"):
                if stem.startswith(prefix):
                    stem = stem[len(prefix) :]
                    break
            code = stem.strip().upper()
            try:
                with open(def_file, "r", encoding="utf-8-sig") as df:
                    parsed_def = json.load(df)
                    if isinstance(parsed_def, dict):
                        explicit_code = str(
                            parsed_def.get("tower_id")
                            or parsed_def.get("domain_id")
                            or code
                        ).strip().upper()
                        tower_definitions[explicit_code] = parsed_def
            except Exception as exc:
                logger.warning("Failed to parse domain definition at %s: %s", def_file, exc)

        # 4. First Pass: Build Domain-Level Signature Lexicons
        all_known_categories = set(category_entities.keys())
        tower_signature_lexicons: Dict[str, Set[str]] = {}
        all_domain_codes = sorted(set(domain_rules.keys()) | set(tower_definitions.keys()))

        for d_code in all_domain_codes:
            sig_terms: Set[str] = set()
            d_rule = domain_rules.get(d_code)
            t_def = tower_definitions.get(d_code, {})

            if d_rule:
                sig_terms.update(d_rule.keywords)
                sig_terms.update(d_rule.canonical_entities)

            sig_terms.update(domain_direct_entities.get(d_code, set()))

            inferred_cats = _infer_categories_for_domain(
                domain_id=d_code,
                domain_rule=d_rule,
                tower_def=t_def,
                all_categories=all_known_categories,
                explicit_mapping=yaml_category_mapping,
            )
            for cat in inferred_cats:
                sig_terms.update(category_entities.get(cat, set()))

            tower_signature_lexicons[d_code] = {
                t
                for t in sig_terms
                if len(t) >= active_thresholds.min_token_length
                or t in active_thresholds.allowed_short_acronyms
            }

        # 5. Second Pass: Construct Pillar Profiles and Mutually Exclusive Negative Maps
        pillar_profiles: Dict[str, PillarOntologyProfile] = {}
        short_id_index: Dict[str, List[PillarOntologyProfile]] = {}

        for t_code, t_def in tower_definitions.items():
            pillars = t_def.get("pillars", [])
            for p in pillars:
                if not isinstance(p, dict):
                    continue
                raw_p_id = str(p.get("pillar_id", "")).strip().upper()
                p_name = str(p.get("pillar_name") or p.get("name") or "").strip()
                if not raw_p_id:
                    continue

                canonical_p_id = (
                    raw_p_id if "." in raw_p_id else f"{t_code}.{raw_p_id}"
                )

                positive_lexicon: Set[str] = set()
                positive_lexicon.update(_extract_filtered_tokens(p_name, active_thresholds))

                for kpi in p.get("kpis", []):
                    if isinstance(kpi, dict):
                        positive_lexicon.update(
                            _extract_filtered_tokens(str(kpi.get("kpi_name", "")), active_thresholds)
                        )
                        positive_lexicon.update(
                            _extract_filtered_tokens(str(kpi.get("description", "")), active_thresholds)
                        )

                if t_code in tower_signature_lexicons:
                    positive_lexicon.update(tower_signature_lexicons[t_code])

                # Build negative exclusion map from other domains
                negative_exclusion_map: Dict[str, Set[str]] = {}
                for other_code, other_sig in tower_signature_lexicons.items():
                    if other_code == t_code:
                        continue
                    exclusive_foreign_terms = {
                        t
                        for t in other_sig
                        if t not in positive_lexicon
                        and (
                            len(t) >= active_thresholds.min_token_length
                            or t in active_thresholds.allowed_short_acronyms
                        )
                    }
                    if exclusive_foreign_terms:
                        negative_exclusion_map[other_code] = exclusive_foreign_terms

                profile = PillarOntologyProfile(
                    pillar_id=canonical_p_id,
                    pillar_name=p_name,
                    tower_id=t_code,
                    domain_id=t_code,
                    positive_lexicon=positive_lexicon,
                    negative_exclusion_map=negative_exclusion_map,
                )
                pillar_profiles[canonical_p_id] = profile

                short_id = canonical_p_id.split(".")[-1]
                short_id_index.setdefault(short_id, []).append(profile)

        logger.info(
            "DomainTaxonomyRegistry dynamically initialized: %d domain rules, %d canonical pillar profiles indexed.",
            len(domain_rules),
            len(pillar_profiles),
        )
        return cls(
            domain_rules=domain_rules,
            pillar_profiles=pillar_profiles,
            short_id_index=short_id_index,
        )

    def get_profile(
        self,
        pillar_id: str,
        tower_id: Optional[str] = None,
    ) -> Optional[PillarOntologyProfile]:
        """Retrieves the ontological profile for a pillar without cross-tower overwrite collisions.

        Resolution order:
        1. Exact canonical ID match (e.g. 'T1.P4' or 'D2.P1').
        2. Qualified composition using provided tower_id + short_id (e.g. tower_id='T1', pillar_id='P4' -> 'T1.P4').
        3. Unqualified short_id lookup (returns deterministic first registered profile if unambiguous or fallback).
        """
        if not pillar_id:
            return None
        norm_p_id = str(pillar_id).strip().upper()

        if norm_p_id in self._pillar_profiles:
            return self._pillar_profiles[norm_p_id]

        if tower_id:
            norm_t_id = str(tower_id).strip().upper()
            composed_id = f"{norm_t_id}.{norm_p_id}"
            if composed_id in self._pillar_profiles:
                return self._pillar_profiles[composed_id]

        candidates = self._short_id_index.get(norm_p_id, [])
        if candidates:
            return candidates[0]

        return None

    def get_domain_rule(self, domain_id: str) -> Optional[DomainTaxonomyRule]:
        """Retrieves a domain taxonomy rule by domain identifier."""
        if not domain_id:
            return None
        return self._domain_rules.get(str(domain_id).strip().upper())

    def list_indexed_pillars(self) -> List[str]:
        """Returns sorted list of all unique canonical pillar identifiers indexed."""
        return sorted(self._pillar_profiles.keys())
