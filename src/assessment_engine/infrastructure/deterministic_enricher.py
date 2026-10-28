"""Deterministic FinOps, MECE Deduplication, and Linguistic Sanitization Engine.

Neuro-Symbolic Architecture Tier-1: Eliminates prompt-based heuristics and replaces
probabilistic LLM arithmetic with deterministic Python business logic.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class DeterministicFinOpsEngine:
    """Calculates OpEx and CapEx through formal cost accounting rather than LLM prompts."""

    TYPOLOGY_CAPEX_RATIOS: Dict[str, float] = {
        "hardware_infrastructure": 0.65,  # Data center, switches, servers, physical appliances
        "network_telecom": 0.55,          # SD-WAN appliances, routers, optical transceivers
        "software_platform": 0.35,        # Initial enterprise platform licenses
        "cloud_enablement": 0.15,         # Setup subscriptions, landing zone base
        "governance_process": 0.0,        # Pure OpEx consulting, cero CapEx
        "security_operations": 0.40,      # Security appliances, SIEM initial licensing
    }

    @staticmethod
    def infer_typology(project_name: str, objective: str) -> str:
        text = f"{project_name} {objective}".lower()
        if any(w in text for w in ["gobernanza", "marco", "proceso", "política", "estandarización", "auditoría", "capacitación"]):
            return "governance_process"
        if any(w in text for w in ["sd-wan", "conmutador", "switch", "enlace", "dci", "red ", "fibra", "lan"]):
            return "network_telecom"
        if any(w in text for w in ["climatización", "eléctric", "cpd", "data center", "rack", "ups", "sai", "servidor"]):
            return "hardware_infrastructure"
        if any(w in text for w in ["seguridad", "firewall", "perímetro", "ciberseguridad", "nis2", "sase"]):
            return "security_operations"
        if any(w in text for w in ["nube", "cloud", "landing zone", "azure", "aws", "gcp"]):
            return "cloud_enablement"
        return "software_platform"

    @classmethod
    def calculate_project_costs(
        cls,
        wbs_tasks: List[Dict[str, Any]],
        rate_card: Dict[str, Any],
        project_name: str,
        tech_objective: str,
        sizing: str = "M",
    ) -> tuple[str, str]:
        """Calculates precise (OpEx, CapEx) formatted strings via deterministic accounting."""
        rates = rate_card.get("tarifas_hora", {
            "gerente_cuenta": 70,
            "arquitecto": 65,
            "experto": 58,
            "project_manager": 45,
            "tecnico_medio": 36,
            "tecnico_junior": 28,
        })
        margin = rate_card.get("margenes", {}).get("consultoria", 0.45)

        # 1. Deterministic OpEx (WBS engineering effort / (1 - margin))
        total_internal_cost = 0.0
        for task in wbs_tasks:
            profile = task.get("required_profile", "experto")
            hours = float(task.get("estimated_hours", 0))
            hourly_rate = float(rates.get(profile, 58))
            total_internal_cost += hours * hourly_rate

        sell_price_opex = total_internal_cost / max(0.1, (1.0 - margin)) if total_internal_cost > 0 else 35000.0

        formatted_opex = f"{sell_price_opex:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

        # 2. Deterministic CapEx based on Typology and Scale
        typology = cls.infer_typology(project_name, tech_objective)
        ratio = cls.TYPOLOGY_CAPEX_RATIOS.get(typology, 0.30)

        sz = sizing.upper().strip()
        if sz in ["L", "XL"]:
            ratio_mult = 1.2
        elif sz == "S":
            ratio_mult = 0.6
        else:
            ratio_mult = 1.0

        final_ratio = ratio * ratio_mult

        if final_ratio <= 0.05 or typology == "governance_process":
            formatted_capex = "Bajo / Nulo (Suscripción OpEx o servicios de consultoría)"
        else:
            raw_capex = round(sell_price_opex * final_ratio, -3)
            # Bound between 15k and 200k for enterprise sanity
            raw_capex = max(15000.0, min(250000.0, raw_capex))
            formatted_capex = (
                f"~{raw_capex:,.2f} € (Inversión paramétrica de equipamiento y licencias base)"
                .replace(",", "X").replace(".", ",").replace("X", ".")
            )

        return formatted_opex, formatted_capex


class MeceClusteringEngine:
    """Consolidates overlapping or redundant initiatives within the same architectural pillar."""

    STOPWORDS = {
        "de", "la", "el", "en", "y", "a", "los", "las", "del", "para", "por",
        "con", "un", "una", "iniciativa", "programa", "proyecto", "estrategia",
        "plan", "molins", "estratégico", "estratégica", "operacional", "operativa",
    }

    @classmethod
    def get_token_signature(cls, text: str) -> set[str]:
        words = re.findall(r"\b[a-záéíóúñ]{4,}\b", text.lower())
        return {w for w in words if w not in cls.STOPWORDS}

    @classmethod
    def are_overlapping(cls, init_a: Dict[str, Any], init_b: Dict[str, Any]) -> bool:
        """Determines if two initiatives address the same functional scope."""
        # 1. Exact mitigated risk match
        risk_a = init_a.get("mitigates_risk_id")
        risk_b = init_b.get("mitigates_risk_id")
        if risk_a and risk_b and risk_a == risk_b:
            return True

        # 2. Jaccard similarity on core keywords
        sig_a = cls.get_token_signature(f"{init_a.get('name', '')} {init_a.get('tech_objective', '')}")
        sig_b = cls.get_token_signature(f"{init_b.get('name', '')} {init_b.get('tech_objective', '')}")

        if not sig_a or not sig_b:
            return False

        intersection = len(sig_a & sig_b)
        union = len(sig_a | sig_b)
        jaccard = intersection / union if union > 0 else 0.0

        return jaccard >= 0.40

    @classmethod
    def merge_initiatives(cls, primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
        """Merges secondary initiative into primary, creating a robust, unified initiative."""
        merged = dict(primary)

        # Merge deliverables
        delivs_a = set(primary.get("deliverables", []))
        delivs_b = set(secondary.get("deliverables", []))
        merged["deliverables"] = sorted(list(delivs_a | delivs_b))[:5]

        # Take longest/richest objective
        obj_a = primary.get("tech_objective", "")
        obj_b = secondary.get("tech_objective", "")
        if len(obj_b) > len(obj_a):
            merged["tech_objective"] = obj_b

        # Take highest sizing
        sizings = ["S", "M", "L", "XL"]
        sz_a = primary.get("sizing", "M").upper()
        sz_b = secondary.get("sizing", "M").upper()
        idx_a = sizings.index(sz_a) if sz_a in sizings else 1
        idx_b = sizings.index(sz_b) if sz_b in sizings else 1
        merged["sizing"] = sizings[max(idx_a, idx_b)]

        return merged

    @classmethod
    def consolidate_pillar_projects(cls, projects: List[Dict[str, Any]], max_projects: int = 2) -> List[Dict[str, Any]]:
        """Applies MECE consolidation to guarantee 1 to 2 distinct, comprehensive projects."""
        if not projects:
            return []

        consolidated: List[Dict[str, Any]] = []

        for proj in projects:
            merged = False
            for idx, existing in enumerate(consolidated):
                if cls.are_overlapping(existing, proj):
                    consolidated[idx] = cls.merge_initiatives(existing, proj)
                    merged = True
                    break
            if not merged:
                consolidated.append(dict(proj))

        # Enforce strict maximum limit per pillar
        return consolidated[:max_projects]


class LinguisticLinter:
    """Enforces European Spanish executive quality and eliminates English technical naming leaks."""

    TRANSLATION_MAP: Dict[str, str] = {
        r"\bproactive capacity assurance\b": "Gestión Proactiva de Capacidad",
        r"\bfor business continuity\b": "para la Continuidad de Negocio",
        r"\bnetwork foundation\b": "Fundamentos de Red",
        r"\blanding zone\b": "Zona de Aterrizaje Cloud (Landing Zone)",
        r"\bbranch connectivity\b": "Conectividad de Sedes y Plantas",
        r"\bwork breakdown structure\b": "Estructura de Desglose de Trabajo",
        r"\bcloud guard\b": "Gobernanza Cloud y Seguridad Continua",
        r"\bsecure-ai\b": "Inteligencia y Seguridad Operativa",
        r"\bdigital core\b": "Núcleo Digital",
        r"\bglobal connect\b": "Conectividad Global",
    }

    @classmethod
    def sanitize_title(cls, text: str) -> str:
        """Translates known English leakage and removes markdown artifacts."""
        if not text:
            return ""

        cleaned = text.strip()
        # Remove markdown asterisks
        cleaned = re.sub(r"\*+", "", cleaned)

        # Apply deterministic translations
        for pattern, replacement in cls.TRANSLATION_MAP.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]

        return cleaned
