#!/usr/bin/env python3
"""Update Chapter 2 strings in locales.json for asymmetric benchmarks and AS-IS pure scope."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LOCALES_PATH = REPO_ROOT / "engine_config" / "locales.json"

UPDATES = {
    "es": {
        "radar_benchmark_legend": "Referencia Sectorial (Mediana P50)",
        "radar_asis_legend": "Situación Actual AS-IS",
        "tomo_fig_radar_caption": "Figura 2.1: Radiografía Polar CMMI — Madurez Actual AS-IS frente a Referencia Sectorial Industrial (P50).",
        "tomo_ch2_summary": "El diagnóstico CMMI sitúa a Molins en un índice consolidado de 2,55 sobre 5,00 (Nivel 2 — Repetible), con áreas como Almacenamiento (3,30) y Puesto de Trabajo (3,10) operando en niveles estandarizados (Nivel 3 — Definido). Por su parte, dominios como Continuidad Industrial (2,10) y Gobernanza Aplicativa (2,40) presentan las mayores desviaciones respecto a la referencia de sus respectivos sectores, requiriendo planes de actuación específicos para mitigar la deuda técnica acumulada.",
        "tomo_ch2_benchmark_methodology_title": "Metodología de Calibración de la Referencia Sectorial (Mediana P50)",
        "tomo_ch2_benchmark_methodology_body": "A diferencia de modelos genéricos que aplican un umbral plano artificial, la referencia empleada en este diagnóstico refleja la mediana empírica (P50) del sector industrial manufacturero pesado y materiales de construcción, calibrada a partir de datos agregados de CMMI v2.0, Gartner IT Key Metrics Data y normas ISO/IEC. Este perfil reconoce la asimetría real del mercado: mayor madurez en dominios comoditizados como Centros de Datos (3,80) y Puesto de Trabajo (3,75), frente a una menor madurez estructural en entornos de planta y continuidad OT (3,05) o analítica de datos (3,10), condicionada por los largos ciclos de amortización de la maquinaria industrial.",
    },
    "en": {
        "radar_benchmark_legend": "Industry Benchmark (Median P50)",
        "radar_asis_legend": "Current State AS-IS",
        "tomo_fig_radar_caption": "Figure 2.1: CMMI Polar Radiography — Current State AS-IS vs. Industry Benchmark (P50).",
        "tomo_ch2_summary": "The CMMI diagnostic places Molins at a consolidated index of 2.55 out of 5.00 (Level 2 — Repeatable), with domains such as Storage (3.30) and Workplace (3.10) operating at standardized tiers (Level 3 — Defined). Meanwhile, domains like Industrial Continuity (2.10) and Application Governance (2.40) exhibit the largest gaps against their respective sector benchmarks, requiring targeted actions to remediate accumulated technical debt.",
        "tomo_ch2_benchmark_methodology_title": "Sector Benchmark Calibration Methodology (Median P50)",
        "tomo_ch2_benchmark_methodology_body": "Unlike generic models applying an artificial flat threshold, the benchmark employed in this diagnostic reflects the empirical median (P50) of heavy process manufacturing and construction materials, calibrated from CMMI v2.0, Gartner IT Key Metrics Data, and ISO/IEC frameworks. This profile accounts for real market asymmetry: higher maturity in commoditized domains like Data Center (3.80) and Workplace (3.75), contrasted with lower structural maturity in plant-floor OT continuity (3.05) and analytics (3.10) driven by 20-30 year machinery lifecycles.",
    },
    "pt": {
        "radar_benchmark_legend": "Referência Setorial (Mediana P50)",
        "radar_asis_legend": "Situação Atual AS-IS",
        "tomo_fig_radar_caption": "Figura 2.1: Radiografia Polar CMMI — Situação Atual AS-IS vs. Referência Setorial Industrial (P50).",
        "tomo_ch2_summary": "O diagnóstico CMMI situa Molins em um índice consolidado de 2,55 em 5,00 (Nível 2 — Repetível), com áreas como Armazenamento (3,30) operando em níveis padronizados (Nível 3 — Definido).",
        "tomo_ch2_benchmark_methodology_title": "Metodologia de Calibração da Referência Setorial (Mediana P50)",
        "tomo_ch2_benchmark_methodology_body": "A referência reflete a mediana empírica (P50) do setor de manufatura pesada, reconhecendo a assimetria real entre serviços de infraestrutura padronizados e a continuidade operacional em plantas industriais.",
    },
    "fr": {
        "radar_benchmark_legend": "Référence Sectorielle (Médiane P50)",
        "radar_asis_legend": "État Actuel AS-IS",
        "tomo_fig_radar_caption": "Figure 2.1 : Radiographie Polaire CMMI — État Actuel AS-IS vs. Référence Sectorielle Industrielle (P50).",
        "tomo_ch2_summary": "Le diagnostic CMMI situe Molins à un indice consolidé de 2,55 sur 5,00 (Niveau 2 — Répétable), avec des domaines comme le Stockage (3,30) opérant à des niveaux standardisés (Niveau 3 — Défini).",
        "tomo_ch2_benchmark_methodology_title": "Méthodologie d'Étalonnage de la Référence Sectorielle (Médiane P50)",
        "tomo_ch2_benchmark_methodology_body": "La référence reflète la médiane empirique (P50) du secteur de l'industrie lourde, reconnaissant l'asymétrie réelle entre les services informatiques banalisés et la continuité opérationnelle en usine.",
    },
    "de": {
        "radar_benchmark_legend": "Branchen-Benchmark (Median P50)",
        "radar_asis_legend": "Ist-Zustand AS-IS",
        "tomo_fig_radar_caption": "Abbildung 2.1: CMMI-Polardiagramm — Ist-Zustand AS-IS vs. Branchen-Benchmark (P50).",
        "tomo_ch2_summary": "Die CMMI-Diagnose verortet Molins bei einem konsolidierten Index von 2,55 von 5,00 (Stufe 2 — Wiederholbar), wobei Speicher (3,30) auf standardisiertem Niveau operiert (Stufe 3 — Definiert).",
        "tomo_ch2_benchmark_methodology_title": "Kalibrierungsmethodik des Branchen-Benchmarks (Median P50)",
        "tomo_ch2_benchmark_methodology_body": "Der Benchmark spiegelt den empirischen Median (P50) der Schwerindustrie wider und berücksichtigt die reale Asymmetrie zwischen standardisierten IT-Diensten und der industriellen Anlagenkontinuität.",
    },
    "ja": {
        "radar_benchmark_legend": "業界ベンチマーク（中央値 P50）",
        "radar_asis_legend": "現状評価 AS-IS",
        "tomo_fig_radar_caption": "図2.1：CMMI極座標レーダーチャート — 現状評価（AS-IS）対 業界ベンチマーク（P50）。",
        "tomo_ch2_summary": "CMMI診断により、モリンズの統合成熟度指数は 5.00 点中 2.55 点（レベル2 — 反復可能）に位置付けられ、ストレージ（3.30）などのドメインは標準化レベル（レベル3 — 定義済み）で運用されています。",
        "tomo_ch2_benchmark_methodology_title": "業界ベンチマーク調整方法論（中央値 P50）",
        "tomo_ch2_benchmark_methodology_body": "本診断で採用されているベンチマークは、重工業および建築資材セクターの実証的中央値（P50）を反映しており、標準化されたITインフラ領域と長期償却サイクルを伴う工場OT環境との間の構造的な非対称性をモデル化しています。",
    },
}


def main() -> None:
    with open(LOCALES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for loc, items in UPDATES.items():
        if loc in data:
            for k, val in items.items():
                data[loc][k] = val

    with open(LOCALES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Successfully updated Chapter 2 benchmark keys across all 6 locales!")


if __name__ == "__main__":
    main()
