"""Unit tests for authoritative multilingual TaxonomyResolver (RFC-022)."""

from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import pytest

from assessment_engine.domain.taxonomy_resolver import TaxonomyResolver, get_taxonomy_resolver


@pytest.fixture
def synthetic_taxonomy_file(tmp_path: Path) -> Path:
    """Fixture providing isolated multilingual taxonomy file without relying on production catalog."""
    catalog = {
        "T1": {
            "canonical_name": "Physical Data Center & Facilities",
            "locales": {
                "en": "Physical Data Center & Facilities",
                "de": "Physisches Rechenzentrum & Einrichtungen",
                "fr": "Centre de Données Physique et Installations",
            },
            "pillars": {
                "T1.P1": {
                    "canonical_name": "Power & Electrical Continuity",
                    "locales": {
                        "en": "Power & Electrical Continuity",
                        "de": "Stromversorgung & Elektrische Kontinuität",
                        "fr": "Alimentation et Continuité Électrique",
                    },
                }
            },
            "capabilities": {
                "Dual Bus Power Feed Redundancy": {
                    "locales": {
                        "en": "Dual Bus Power Feed Redundancy",
                        "de": "Redundanz der Doppelbus-Stromversorgung",
                        "fr": "Redondance d'Alimentation Double Bus",
                    }
                }
            },
        },
        "T2": {
            "canonical_name": "Hybrid Compute & Platforms",
            "locales": {
                "en": "Hybrid Compute & Platforms",
                "de": "Hybride Rechenkapazitäten & Plattformen",
                "ja": "ハイブリッドコンピュート＆プラットフォーム",
            },
            "pillars": {
                "T2.P1": {
                    "canonical_name": "Compute Foundation & Virtualization",
                    "locales": {
                        "en": "Compute Foundation & Virtualization",
                        "de": "Compute-Grundlagen & Virtualisierung",
                        "ja": "コンピュート基盤および仮想化",
                    },
                }
            },
            "capabilities": {
                "Platform Self-Service and Service Catalog": {
                    "locales": {
                        "en": "Platform Self-Service and Service Catalog",
                        "de": "Plattform-Self-Service und Servicekatalog",
                        "ja": "プラットフォームセルフサービスおよびサービスカタログ",
                    }
                }
            },
        },
    }
    file_path = tmp_path / "taxonomy_synthetic.json"
    file_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


@pytest.fixture
def isolated_resolver(synthetic_taxonomy_file: Path) -> TaxonomyResolver:
    """Fixture providing isolated TaxonomyResolver using synthetic multilingual catalog."""
    return TaxonomyResolver(config_path=synthetic_taxonomy_file)


def test_resolve_tower_names_across_locales(isolated_resolver: TaxonomyResolver) -> None:
    """Verify tower name resolution across international target locales."""
    # Tower T1: English, German, French
    assert isolated_resolver.resolve_tower_name("T1", locale="en") == "Physical Data Center & Facilities"
    assert isolated_resolver.resolve_tower_name("T1", locale="de") == "Physisches Rechenzentrum & Einrichtungen"
    assert isolated_resolver.resolve_tower_name("T1", locale="fr") == "Centre de Données Physique et Installations"

    # Tower T2: English, German, Japanese
    assert isolated_resolver.resolve_tower_name("T2", locale="en") == "Hybrid Compute & Platforms"
    assert isolated_resolver.resolve_tower_name("T2", locale="de") == "Hybride Rechenkapazitäten & Plattformen"
    assert isolated_resolver.resolve_tower_name("T2", locale="ja") == "ハイブリッドコンピュート＆プラットフォーム"


def test_resolve_pillar_name_by_immutable_id(isolated_resolver: TaxonomyResolver) -> None:
    """Verify pillar resolution using canonical structural ID across locales."""
    # T2.P1 in German vs English
    de_p1 = isolated_resolver.resolve_pillar_name("T2", "T2.P1", locale="de")
    en_p1 = isolated_resolver.resolve_pillar_name("T2", "T2.P1", locale="en")
    assert de_p1 == "Compute-Grundlagen & Virtualisierung"
    assert en_p1 == "Compute Foundation & Virtualization"

    # T1.P1 in French vs English
    fr_t1_p1 = isolated_resolver.resolve_pillar_name("T1", "T1.P1", locale="fr")
    en_t1_p1 = isolated_resolver.resolve_pillar_name("T1", "T1.P1", locale="en")
    assert fr_t1_p1 == "Alimentation et Continuité Électrique"
    assert en_t1_p1 == "Power & Electrical Continuity"


def test_resolve_pillar_by_canonical_name_fallback(isolated_resolver: TaxonomyResolver) -> None:
    """Verify resilient resolution when input is a canonical English string."""
    resolved_de = isolated_resolver.resolve_pillar_by_any_reference(
        "Compute Foundation & Virtualization", locale="de"
    )
    assert resolved_de == "Compute-Grundlagen & Virtualisierung"

    resolved_fr = isolated_resolver.resolve_pillar_by_any_reference(
        "Power & Electrical Continuity", locale="fr"
    )
    assert resolved_fr == "Alimentation et Continuité Électrique"


def test_resolve_capability_name_in_o1(isolated_resolver: TaxonomyResolver) -> None:
    """Verify capability resolution in O(1) from canonical string."""
    res_de = isolated_resolver.resolve_capability_name(
        "Platform Self-Service and Service Catalog", locale="de"
    )
    assert res_de == "Plattform-Self-Service und Servicekatalog"

    res_en = isolated_resolver.resolve_capability_name(
        "Platform Self-Service and Service Catalog", locale="en"
    )
    assert res_en == "Platform Self-Service and Service Catalog"

    res_ja = isolated_resolver.resolve_capability_name(
        "Platform Self-Service and Service Catalog", locale="ja"
    )
    assert res_ja == "プラットフォームセルフサービスおよびサービスカタログ"


def test_thread_safe_singleton_concurrency() -> None:
    """Verify that get_taxonomy_resolver is strictly thread-safe under parallel execution."""
    instances: list[TaxonomyResolver] = []

    def fetch_instance() -> TaxonomyResolver:
        return get_taxonomy_resolver()

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_instance) for _ in range(16)]
        for f in concurrent.futures.as_completed(futures):
            instances.append(f.result())

    first = instances[0]
    for inst in instances[1:]:
        assert inst is first, "Singleton violation: multiple TaxonomyResolver instances created concurrently."


def test_unknown_reference_returns_default(isolated_resolver: TaxonomyResolver) -> None:
    """Ensure graceful fallback when unknown ID or name is requested."""
    assert isolated_resolver.resolve_tower_name("T99", default="Default Tower") == "Default Tower"
    assert isolated_resolver.resolve_pillar_name("T99", "T99.P1", default="Default Pillar") == "Default Pillar"
    assert isolated_resolver.resolve_pillar_by_any_reference("Nonexistent Capability", default="Default Cap") == "Default Cap"
