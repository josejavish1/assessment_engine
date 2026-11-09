"""Sanitizes Tower 10 taxonomy across configuration files to establish universal architecture agnosticism.

Remediates:
1. tower_definition_T10.json: Renames 'Legacy & Mainframe' to 'Core Transactional & Mission-Critical Systems' and P1.
2. taxonomy_multilingual.json: Renames T10 and T10.P1 across all 6 languages, purging 'Plant Operations'.
3. locales.json: Renames T10 labels from 'Legacy & Mainframe' to 'Core Transactional Systems'.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEF_FILE = ROOT / "engine_config/towers/T10/tower_definition_T10.json"
TAX_FILE = ROOT / "engine_config/taxonomy_multilingual.json"
LOC_FILE = ROOT / "engine_config/locales.json"


def update_tower_definition() -> None:
    data = json.loads(DEF_FILE.read_text(encoding="utf-8"))
    data["tower_name"] = "Core Transactional & Mission-Critical Systems"
    if "pillars" in data and len(data["pillars"]) > 0:
        data["pillars"][0]["pillar_name"] = "Plataformas Transaccionales Core y Procesamiento Crítico"
    DEF_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated: {DEF_FILE.name}")


def update_taxonomy_multilingual() -> None:
    data = json.loads(TAX_FILE.read_text(encoding="utf-8"))
    t10 = data.get("T10", {})
    t10["canonical_name"] = "Core Transactional & Mission-Critical Systems"
    t10["locales"] = {
        "es": "Sistemas Transaccionales Core y Plataformas Críticas",
        "en": "Core Transactional & Mission-Critical Systems",
        "pt": "Sistemas Transacionais Core e Plataformas Críticas",
        "fr": "Systèmes Transactionnels Core et Plateformes Critiques",
        "de": "Kern-Transaktionssysteme & Missionskritische Plattformen",
        "ja": "ミッションクリティカル基幹系およびトランザクションシステム",
    }

    p1 = t10.get("pillars", {}).get("T10.P1", {})
    p1["canonical_name"] = "Core Transactional Platforms & High-Throughput Processing"
    p1["locales"] = {
        "es": "Plataformas Transaccionales Core y Procesamiento Crítico",
        "en": "Core Transactional Platforms & High-Throughput Processing",
        "pt": "Plataformas Transacionais Core e Processamento Crítico",
        "fr": "Plateformes Transactionnelles Core et Traitement Haute Disponibilité",
        "de": "Kern-Transaktionsplattformen & Hochdurchsatz-Verarbeitung",
        "ja": "基幹トランザクションプラットフォームおよび高スループット処理",
    }

    p2 = t10.get("pillars", {}).get("T10.P2", {})
    p2["canonical_name"] = "Core Change, Release & Configuration Governance"
    if "locales" in p2:
        p2["locales"]["en"] = "Core Change, Release & Configuration Governance"
        p2["locales"]["es"] = "Control de Cambios, Releases y Configuración Core"
        p2["locales"]["de"] = "Core Change-, Release- & Konfigurationskontrolle"

    p4 = t10.get("pillars", {}).get("T10.P4", {})
    p4["canonical_name"] = "Core Integration, Interoperability & Modern APIs"
    if "locales" in p4:
        p4["locales"]["en"] = "Core Integration, Interoperability & Modern APIs"

    TAX_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated: {TAX_FILE.name}")


def update_locales() -> None:
    data = json.loads(LOC_FILE.read_text(encoding="utf-8"))

    replacements = {
        "Legacy & Mainframe": "Core Transactional Systems",
        "legacy & mainframe": "core transactional systems",
        "Legacy & mainframe": "Core transactional systems",
        "Plant Operations": "High-Throughput Processing",
        "Operaciones de Planta": "Procesamiento Crítico",
    }

    def walk_and_replace(obj: any) -> any:
        if isinstance(obj, dict):
            return {k: walk_and_replace(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [walk_and_replace(item) for item in obj]
        elif isinstance(obj, str):
            res = obj
            for old_s, new_s in replacements.items():
                res = res.replace(old_s, new_s)
            return res
        return obj

    sanitized = walk_and_replace(data)
    LOC_FILE.write_text(json.dumps(sanitized, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated: {LOC_FILE.name}")


def main() -> None:
    update_tower_definition()
    update_taxonomy_multilingual()
    update_locales()
    print("\nTower 10 universal taxonomy upgrade complete.")


if __name__ == "__main__":
    main()
