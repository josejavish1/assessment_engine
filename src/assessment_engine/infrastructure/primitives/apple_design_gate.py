"""
Apple HIG Deterministic Design Gate — Sub-5ms Mathematical Design Auditor.
Distilled from dickwu/apple-design-skill (123 pages of developer.apple.com HIG).
Audits UI code against real numbers: type scale, 8pt spacing grid, color budget,
two-layer discipline, and motion physics without LLM hallucination or latency.
"""

from __future__ import annotations

import re
from typing import Any

# Define the official Apple HIG harmonic scale.
VALID_APPLE_TYPE_SIZES = {
    "text-[10px]", "text-[11px]", "text-xs",   # 10 - 12 pt: micro, captions
    "text-sm", "text-[13px]", "text-[15px]",  # 13 - 15 pt: body, labels
    "text-base", "text-lg", "text-xl",        # 16 - 20 pt: titles, highlights
    "text-2xl", "text-3xl", "text-4xl",       # 24 - 36 pt: section headers
    "text-5xl", "text-6xl"                    # 44 - 60 pt: hero headlines
}


def _audit_typography_scale(source_code: str, findings: list[dict[str, Any]], penalty: int) -> int:
    found_sizes = set(re.findall(r"\btext-(?:xs|sm|base|lg|xl|[2-6]xl)\b", source_code))
    if len(found_sizes) > 4:
        penalty += 15
        findings.append({
            "rank": 1, "category": "Typography",
            "issue": f"Caos tipográfico detectado ({len(found_sizes)} tamaños distintos en una sola vista: {sorted(found_sizes)}).",
            "rule": "Apple HIG Typography: Colapsar a un máximo de 4 escalones armónicos.",
            "impact": "Alto"
        })
    arbitrary_sizes = re.findall(r"\btext-\[(\d+)px\]\b", source_code)
    for sz in arbitrary_sizes:
        if int(sz) not in {10, 11, 13, 15, 20, 28, 44}:
            penalty += 10
            findings.append({
                "rank": 3, "category": "Typography",
                "issue": f"Tamaño arbitrario 'text-[{sz}px]' rompe la escala armónica.",
                "rule": "Apple HIG: Reemplazar por tamaño estándar más cercano.",
                "impact": "Medio"
            })
            break
    return penalty

def _audit_spacing_and_rhythm(source_code: str, findings: list[dict[str, Any]], penalty: int) -> int:
    arbitrary_paddings = re.findall(r"(?:p|m)[xytbrl]?-\[(\d+)px\]", source_code)
    for pad in arbitrary_paddings:
        if int(pad) % 4 != 0:
            penalty += 10
            findings.append({
                "rank": 2, "category": "Spacing",
                "issue": f"Padding arbitrario de {pad}px no respeta el ritmo de la rejilla de 8pt de Apple.",
                "rule": "Apple HIG Layout: Alinear espaciados a múltiplos de 8px (16, 24, 32, 48px).",
                "impact": "Medio"
            })
            break
    return penalty

def _audit_color_budget(source_code: str, findings: list[dict[str, Any]], penalty: int) -> int:
    primary_buttons = len(re.findall(r"<button[^>]*className=[\"'][^\"']*(?:glin-key(?!-white)\b|bg-amber-500|bg-emerald-500|bg-blue-600)[^\"']*[\"']", source_code))
    if primary_buttons > 2:
        penalty += 15
        findings.append({
            "rank": 1, "category": "Color Budget",
            "issue": f"Exceso de acciones primarias tintadas ({primary_buttons} botones compitiendo visualmente).",
            "rule": "Apple HIG Branding & Buttons: Limitar a 1 o 2 acciones primarias con color por vista.",
            "impact": "Alto"
        })
    return penalty

def _audit_materials_and_motion(source_code: str, findings: list[dict[str, Any]], penalty: int) -> int:
    glass_in_tables = bool(re.search(r"<(?:table|td|tr|tbody)[^>]*backdrop-blur", source_code))
    if glass_in_tables:
        penalty += 15
        findings.append({
            "rank": 1, "category": "Materials",
            "issue": "Liquid Glass detectado dentro de la capa de contenido (tablas de datos).",
            "rule": "Apple HIG Materials (Liquid Glass): El cristal translúcido pertenece EXCLUSIVAMENTE a la capa funcional flotante.",
            "impact": "Alto"
        })
    linear_slow_transitions = re.findall(r"transition.*?(?:linear|all\s*[0-9.]+s)", source_code)
    if linear_slow_transitions:
        penalty += 10
        findings.append({
            "rank": 2, "category": "Motion",
            "issue": f"Transición lineal o genérica detectada ('{linear_slow_transitions[0][:40]}').",
            "rule": "Apple HIG Motion: Reemplazar por transiciones ágiles de muelle (0.15s cubic-bezier(0.16, 1, 0.3, 1)).",
            "impact": "Medio"
        })
    return penalty

def audit_apple_design_compliance(source_code: str) -> dict[str, Any]:
    """
    Performs deterministic mathematical review of React/Tailwind source code.
    """
    findings: list[dict[str, Any]] = []
    penalty = 0

    penalty = _audit_typography_scale(source_code, findings, penalty)
    penalty = _audit_spacing_and_rhythm(source_code, findings, penalty)
    penalty = _audit_color_budget(source_code, findings, penalty)
    penalty = _audit_materials_and_motion(source_code, findings, penalty)

    score = max(0, 100 - penalty)
    is_passed = score >= 80

    return {
        "score": score,
        "passed": is_passed,
        "penalties_count": len(findings),
        "findings": sorted(findings, key=lambda x: x["rank"]),
        "verdict": "CERTIFIED_APPLE_HIG" if is_passed else "REWORK_REQUIRED"
    }
