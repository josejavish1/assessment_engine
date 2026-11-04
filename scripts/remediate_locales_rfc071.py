#!/usr/bin/env python3
"""Comprehensive Remediator for engine_config/locales.json (RFC 071 Phase 1).

Executes complete purge of single-tenant hardcoding, company names, proprietary locations,
and cement manufacturing references across all catalogs in all 6 languages: `es`, `en`, `pt`, `fr`, `de`, `ja`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

WORD_REPLACEMENTS = [
    # Company names
    (re.compile(r"\bMolins\b"), "{client_name}"),
    (re.compile(r"\bSecil\b"), "filiales corporativas"),
    (re.compile(r"\bSant Vicen[cç] dels Horts\b", re.IGNORECASE), "sedes principales"),
    (re.compile(r"\bSant Vicen[cç]\b", re.IGNORECASE), "sedes principales"),
    # Hardware & Platforms
    (re.compile(r"\bSimpliVity\b", re.IGNORECASE), "Hiperconvergente"),
    (re.compile(r"\bHPE SimpliVity\b", re.IGNORECASE), "Plataforma Hiperconvergente"),
    (re.compile(r"\bNetApp\b", re.IGNORECASE), "Almacenamiento Centralizado"),
    (re.compile(r"\bHuawei/Cisco\b", re.IGNORECASE), "Conmutadores de Núcleo"),
    # Specific Contract Dates
    (re.compile(r"\bmayo de 2027\b", re.IGNORECASE), "próximos ciclos de renovación"),
    (re.compile(r"\bMay 2027\b", re.IGNORECASE), "upcoming renewal cycles"),
    # Industry / Plant equipment
    (re.compile(r"\bPC de b[aá]scula\b", re.IGNORECASE), "Estación de control operativo"),
    (re.compile(r"\bbypass de b[aá]scula\b", re.IGNORECASE), "bypass de contingencia"),
    (re.compile(r"\bb[aá]sculas de pesaje\b", re.IGNORECASE), "sistemas de expedición"),
    (re.compile(r"\bb[aá]sculas de camiones\b", re.IGNORECASE), "estaciones de carga y entrega"),
    (re.compile(r"\bb[aá]sculas locales\b", re.IGNORECASE), "estaciones locales de expedición"),
    (re.compile(r"\bb[aá]sculas\b", re.IGNORECASE), "sistemas de expedición"),
    (re.compile(r"\bb[aá]scula\b", re.IGNORECASE), "sistema de expedición"),
    (re.compile(r"\bl[ií]neas de ensacado\b", re.IGNORECASE), "procesos críticos de distribución"),
    (re.compile(r"\bensacado\b", re.IGNORECASE), "distribución"),
    (re.compile(r"\bweighbridge dispatch\b", re.IGNORECASE), "operational dispatch"),
    (re.compile(r"\bweighbridges\b", re.IGNORECASE), "operational dispatch systems"),
    (re.compile(r"\bweighbridge\b", re.IGNORECASE), "dispatch system"),
    (re.compile(r"\bbagging lines\b", re.IGNORECASE), "distribution workflows"),
    (re.compile(r"\bbagging\b", re.IGNORECASE), "distribution"),
    (re.compile(r"\bcement dispatch\b", re.IGNORECASE), "product dispatch"),
    (re.compile(r"\bexpedici[oó]n de cemento\b", re.IGNORECASE), "expedición de producto"),
    (re.compile(r"\bf[aá]bricas de cemento\b", re.IGNORECASE), "instalaciones operativas"),
    (re.compile(r"\bcement facilities\b", re.IGNORECASE), "operational facilities"),
    (re.compile(r"\bcement plants\b", re.IGNORECASE), "operational facilities"),
    (re.compile(r"\bcement plant\b", re.IGNORECASE), "operational facility"),
    (re.compile(r"\bcement\b", re.IGNORECASE), "operational product"),
    (re.compile(r"\bcemento\b", re.IGNORECASE), "producto"),
    # Concrete financial figures & times
    (re.compile(r"18 (?:pa[ií]ses|countries|pays|L[aä]ndern)", re.IGNORECASE), "las delegaciones internacionales"),
    (re.compile(r"135[.,]000\s*(?:€|EUR)(?:/a[ñn]o|/yr|/year| anuales)?", re.IGNORECASE), "costes redundantes"),
    (re.compile(r"5[.,]000\s*(?:€|EUR)/h", re.IGNORECASE), "impacto operacional significativo"),
]


def clean_string(val: str) -> str:
    res = val
    for pattern, repl in WORD_REPLACEMENTS:
        res = pattern.sub(repl, res)
    return res


def recursively_clean(node: any) -> any:
    if isinstance(node, dict):
        return {k: recursively_clean(v) for k, v in node.items()}
    elif isinstance(node, list):
        return [recursively_clean(x) for x in node]
    elif isinstance(node, str):
        return clean_string(node)
    return node


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Clean recursively
    cleaned_data = recursively_clean(data)

    # 2. Specific structural overrides
    for lang in ["es", "en", "pt", "fr", "de", "ja"]:
        if lang not in cleaned_data:
            continue
        branch = cleaned_data[lang]

        # Fix specific titles and clean keys
        if "tomo_ch4_t10_title" in branch:
            branch["tomo_ch4_t10_title"] = (
                "10. Operaciones Locales & Soporte a Sedes Distribuidas"
                if lang == "es"
                else "10. Local Operations & Distributed Facility Support"
            )
        if "tomo_tower_t10_clean" in branch:
            branch["tomo_tower_t10_clean"] = (
                "Operaciones Locales & Sedes Distribuidas"
                if lang == "es"
                else "Local Operations & Distributed Facilities"
            )

        # Update nexus catalog T10 target title
        for nx in branch.get("tomo_nexus_catalog", []):
            if isinstance(nx, dict) and "T10" in str(nx.get("target", "")):
                nx["target"] = (
                    "T10: Operaciones Locales y Soporte a Sedes"
                    if lang == "es"
                    else "T10: Local Operations & Facility Support"
                )

        # Clean top risks catalog titles
        for rk in branch.get("tomo_top_risks_catalog", []):
            if isinstance(rk, dict):
                title = str(rk.get("title", ""))
                title = clean_string(title)
                rk["title"] = title

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print("Comprehensive remediation completed successfully.")


if __name__ == "__main__":
    main()
