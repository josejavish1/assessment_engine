import json
import os
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from infrastructure.epistemic_graph import EpistemicGraph


class BaseSovereignPolicy(ABC):
    """
    Base abstract class for all Sovereign Policies.
    Enforces the polymorphic contract.
    """
    @abstractmethod
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes the EpistemicGraph and patches the payload dictionary in place or returns a copy."""
        pass


class ClientSanitizationPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: Client Sanitization (Universal).
    Recursively scrubs any bracketed placeholder like [Cliente], [CLIENTE], etc.
    with the actual client name resolved from metadata.
    """
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        client_name = payload.get("document_meta", {}).get("client_name", "REDEIA")
        
        def scrub(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: scrub(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [scrub(x) for x in obj]
            elif isinstance(obj, str):
                for placeholder in ["[Cliente]", "[CLIENTE]", "[cliente]", "[CLIENT]", "[client]", "[CUSTOMER]", "[customer]"]:
                    obj = obj.replace(placeholder, client_name)
                # Regex replace to scrub general bracketed client text if any remains
                obj = re.sub(r"\[[Cc]liente\]", client_name, obj)
                return obj
            return obj

        return scrub(payload)


class DeduplicationPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: Semantic Deduplication & Consolidation (Universal).
    Finds redundant initiatives across pillars (specifically Platform Engineering)
    and collapses them into a single master initiative in the designated pillar.
    """
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        # Specifically consolidate "Platform Engineering" or "Ingeniería de Plataforma" for Tower 2
        platform_eng_projects = []
        target_pilar_id = "T2.P4" # Default autoservicio pillar
        
        # Check if we are in Tower 2
        tower_code = payload.get("document_meta", {}).get("tower_code", "")
        doc_lang = payload.get("document_meta", {}).get("language", "es").lower()
        cloud_provider = payload.get("document_meta", {}).get("cloud_provider", "AWS")
        
        if tower_code == "T2":
            for p in pillars:
                p_id = p.get("pilar_id")
                projects = p.get("projects_todo", [])
                for proj in list(projects):
                    name = proj.get("name", "")
                    if "platform engineering" in name.lower() or "ingeniería de plataforma" in name.lower():
                        if p_id != target_pilar_id:
                            platform_eng_projects.append(proj)
                            p["projects_todo"].remove(proj) # Remove duplicate from other pillars

            # If duplicates were found and removed, we inject the consolidated master into T2.P4 (Localized)
            if platform_eng_projects:
                for p in pillars:
                    if p.get("pilar_id") == target_pilar_id:
                        if doc_lang == "es":
                            unified_project = {
                                "node_id": str(uuid.uuid4()),
                                "name": "Programa Estratégico de Platform Engineering y Autoservicio Híbrido",
                                "transformation_typology": "Automation & Platform Engineering",
                                "business_case": f"Reducción de la carga cognitiva de los equipos de desarrollo y operaciones mediante la unificación de portales y catálogos sobre {cloud_provider}.",
                                "tech_objective": "Consolidar las iniciativas de cómputo híbrido, landing zones y provisión automática bajo una única Plataforma Interna de Desarrollo (IDP) unificada y autoservicio.",
                                "deliverables": [
                                    "Definición del catálogo de servicios unificado.",
                                    f"Integración de las APIs de provisión de {cloud_provider} Landing Zones.",
                                    "Despliegue del portal central de Autoservicio para el desarrollador."
                                ],
                                "sizing": "XL",
                                "duration": "Horizonte 1 (0-6 meses)",
                                "program_id": None
                            }
                        else:
                            unified_project = {
                                "node_id": str(uuid.uuid4()),
                                "name": "Platform Engineering and Hybrid Self-Service Strategic Program",
                                "transformation_typology": "Automation & Platform Engineering",
                                "business_case": f"Reduction of developer cognitive load through unified catalogs and self-service portals over {cloud_provider}.",
                                "tech_objective": "Consolidate compute, landing zone, and automated provisioning capabilities under a single Internal Developer Platform (IDP).",
                                "deliverables": [
                                    "Unified service catalog definition.",
                                    f"API integration for {cloud_provider} Landing Zone provisioning.",
                                    "Developer Self-Service portal deployment."
                                ],
                                "sizing": "XL",
                                "duration": "Horizon 1 (0-6 months)",
                                "program_id": None
                            }
                        # Replace or append
                        p["projects_todo"] = [unified_project]
                        break
        return payload


class SequencingPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: Topological Sequencing (Universal).
    Ensures container and platform adoption plans pre-date heavy deployments.
    Uses requirements from the EpistemicGraph to sequence time horizons correctly.
    """
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        # Iterate over all initiatives and sanitize durations to follow logical prerequisites
        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "")
                # If it's a foundation or adoption plan, schedule for H1-Arranque
                if "adopción de plataforma de contenedores" in name.lower() or "estrategia de adopción" in name.lower():
                    proj["duration"] = "Horizonte 1 - Fase de Arranque (Mes 1-2)"
                    proj["tech_objective"] = "Establecer las directrices operativas, de gobernanza, de costes y de seguridad para cargas de contenedores antes de iniciar desarrollos técnicos de IDP."
                # If it's a technical pilot or IDP, schedule for H2 (or after)
                elif "plataforma interna de desarrollo" in name.lower() or "piloto" in name.lower() or "kubernetes" in name.lower() or "eks" in name.lower():
                    proj["duration"] = "Horizonte 2 (Mes 3-12)"
                    
        return payload


class OTPerimeterPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: SCADA / OT Security Isolation Perimeter (Specific).
    Injects physical unidirectional data diode telemetry deliverables
    when an OT containment project coexists with an IT AIOps/observability project.
    
    SOTA 2026: SECTOR-LOCKED. Only executes if the client belongs to "Critical Infrastructure" or "Energy".
    Prevents leaking physical diode controls into financial or retail projects!
    """
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Detectar el sector del cliente en el entorno
        client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "redeia_v3")
        intel_path = Path(f"working/{client_id}/client_intelligence.json")
        industry = "Standard"
        if intel_path.exists():
            try:
                with open(intel_path, "r", encoding="utf-8-sig") as inf:
                    intel = json.load(inf)
                    p_meta = intel.get("profile", {})
                    industry = p_meta.get("industry", "Standard")
            except Exception:
                pass
        else:
            # Fallback de seguridad si el archivo no existe en el CI runner (Gobernanza de Sandbox)
            client_name = payload.get("document_meta", {}).get("client_name", "").upper()
            if "REDEIA" in client_name:
                industry = "Critical Infrastructure"

        # SANEAMIENTO SECTORIAL: Si el cliente no es infraestructura crítica o energía, saltamos la política
        if "Critical Infrastructure" not in industry and "Energy" not in industry:
            return payload
            
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        has_scada = False
        has_aiops = False
        
        # 1. Detect coexistence of SCADA/OT and observability/AIOps
        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "").lower()
                if "scada" in name or "legada" in name or "infraestructura legacy" in name:
                    has_scada = True
                if "aiops" in name or "observabilidad predictiva" in name or "observabilidad" in name:
                    has_aiops = True

        # 2. Inject Hardware Data Diode security safeguards if they coexist
        if has_scada and has_aiops:
            for p in pillars:
                for proj in p.get("projects_todo", []):
                    name = proj.get("name", "").lower()
                    if "scada" in name or "legada" in name or "infraestructura legacy" in name:
                        if "deliverables" not in proj:
                            proj["deliverables"] = []
                        # Avoid duplicate injection
                        if not any("diodo de datos" in d.lower() for d in proj["deliverables"]):
                            proj["deliverables"].append("Implementación de un Diodo de Datos Unidireccional por Hardware para extracción segura de telemetría sin canal de retorno.")
                            proj["tech_objective"] += " El aislamiento físico del entorno SCADA se mantendrá de forma inquebrantable mediante el uso de un diodo de datos unidireccional."
                    if "aiops" in name or "observabilidad predictiva" in name or "observabilidad" in name:
                        if "deliverables" not in proj:
                            proj["deliverables"] = []
                        if not any("diodo de datos" in d.lower() for d in proj["deliverables"]):
                            proj["deliverables"].append("Despliegue del gateway receptor del Diodo de Datos de OT para ingesta pasiva de telemetría en AWS IoT Core.")
                            proj["tech_objective"] += " Toda la ingesta de telemetría en tiempo real de subestaciones y OT se canalizará de forma 100% pasiva y segura mediante diodos de datos unidireccionales."
        return payload


class ArchiMateDeliverablesPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: ArchiMate Mapping (Universal).
    Injects hard, specific technical deliverables based on the project's technology keywords,
    eliminating generic 'Diseño de arquitectura' placeholders.
    """
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        catalog = {
            "kubernetes": ["Manifiestos Base YAML", "Módulo Terraform EKS", "Helm Charts de Gobernanza", "Pipeline GitLab/GitHub Actions"],
            "eks": ["Manifiestos Base YAML", "Módulo Terraform EKS", "Helm Charts de Gobernanza", "Pipeline GitLab/GitHub Actions"],
            "contenedores": ["Manifiestos Base YAML", "Módulo Terraform EKS", "Helm Charts de Gobernanza", "Pipeline GitLab/GitHub Actions"],
            "landing zone": ["AWS Control Tower Account Factory", "Políticas SCP (Service Control Policies)", "Módulo Terraform Base Network"],
            "platform engineering": ["Catálogo Backstage/IDP", "Plantillas de Autoservicio IaC", "Framework de SLIs/SLOs"],
            "observabilidad": ["Dashboards Grafana/CloudWatch", "Reglas de Alertas PromQL", "Integración PagerDuty/ServiceNow"],
            "aiops": ["Dashboards Grafana/CloudWatch", "Modelos de Detección de Anomalías", "Integración ITSM"],
            "scada": ["Topología de Red Purdue", "Reglas de Firewall Perimetral", "Diodo de Datos Unidireccional"],
            "automatización": ["Playbooks Ansible", "Módulos Terraform", "Pipelines CI/CD"],
            "iac": ["Módulos Terraform", "Repositorio GitOps", "Políticas OPA/Sentinel"],
            "dr": ["Runbooks de Recuperación", "Plan de Pruebas de Failover", "Plantillas AWS Elastic Disaster Recovery"],
            "disaster recovery": ["Runbooks de Recuperación", "Plan de Pruebas de Failover", "Plantillas AWS Elastic Disaster Recovery"],
            "backup": ["Políticas de Retención", "Bóveda Inmutable", "Pruebas de Restauración Automatizadas"]
        }
        
        pillars = payload.get("pillars_analysis", [])
        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "").lower()
                tech_obj = proj.get("tech_objective", "").lower()
                combined_text = name + " " + tech_obj
                
                # If deliverables is missing, empty, or contains generic placeholders, replace it
                current_deliverables = proj.get("deliverables", [])
                is_generic = not current_deliverables or any("diseño de arquitectura" in d.lower() for d in current_deliverables)
                
                if is_generic:
                    new_deliverables = set()
                    for keyword, hard_deliverables in catalog.items():
                        if keyword in combined_text:
                            new_deliverables.update(hard_deliverables)
                            
                    if new_deliverables:
                        proj["deliverables"] = list(new_deliverables)
                    else:
                        # Fallback for completely unknown projects, still better than generic
                        proj["deliverables"] = ["Documento de Diseño Técnico (HLD/LLD)", "Repositorio de Código (IaC/Config)", "Plan de Pruebas y Validation"]

        return payload


class BusinessCaseGroundingPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: Business Case Grounding (Universal).
    Connects projects to AS-IS findings to generate real, quantified business cases,
    eliminating generic placeholders.
    """
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        pillars = payload.get("pillars_analysis", [])
        doc_lang = payload.get("document_meta", {}).get("language", "es").lower()
        
        # SANEAMIENTO REGULATORIO: Desacoplar normativas del business case (Punto 2)
        reg_frameworks = payload.get("document_meta", {}).get("regulatory_frameworks")
        if not reg_frameworks:
            reg_frameworks = "ENS/NIS2" if doc_lang == "es" else "applicable regulatory frameworks"
            
        for p in pillars:
            asis_findings = p.get("health_check_asis", [])
            for proj in p.get("projects_todo", []):
                bc = proj.get("business_case", "")
                if not bc or "impacto estratégico basado en la validación" in bc.lower():
                    # Attempt to ground the business case by finding a semantically related AS-IS finding
                    name = proj.get("name", "").lower()
                    tech_obj = proj.get("tech_objective", "").lower()
                    
                    matched_finding = None
                    for finding in asis_findings:
                        f_text = finding.get("finding", finding.get("risk_observed", "")).lower()
                        # Simple word overlap for grounding
                        words = [w for w in f_text.split() if len(w) > 5]
                        if sum(1 for w in words if w in name or w in tech_obj) > 1:
                            matched_finding = finding
                            break
                            
                    if matched_finding:
                        impact = matched_finding.get("impact", matched_finding.get("business_risk", ""))
                        proj["business_case"] = f"Mitigación Directa: Resuelve la vulnerabilidad crítica detectada en el AS-IS, eliminando el riesgo de: '{impact}'." if doc_lang == "es" else f"Direct Mitigation: Resolves the critical vulnerability detected in the AS-IS, eliminating the risk of: '{impact}'."
                        proj["mitigates_risk_id"] = matched_finding.get("node_id")
                    else:
                        proj["business_case"] = f"Habilitador Estratégico: Reduce el TCO operativo, acelera el time-to-market y garantiza el cumplimiento normativo ({reg_frameworks})." if doc_lang == "es" else f"Strategic Enabler: Reduces operational TCO, accelerates time-to-market, and ensures regulatory compliance ({reg_frameworks})."
                        
        return payload


class ReverseTraceabilityPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: Reverse Traceability / Orphan Findings (Universal).
    Ensures every AS-IS gap is addressed by at least one TO-DO project.
    """
    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        pillars = payload.get("pillars_analysis", [])
        for p in pillars:
            asis_findings = p.get("health_check_asis", [])
            projects = p.get("projects_todo", [])
            
            all_proj_text = " ".join([proj.get("name", "") + " " + proj.get("tech_objective", "") for proj in projects]).lower()
            
            for finding in asis_findings:
                f_text = finding.get("finding", finding.get("risk_observed", ""))
                # If a finding is completely unaddressed (orphan)
                words = [w.lower() for w in f_text.split() if len(w) > 5]
                if words and sum(1 for w in words if w in all_proj_text) == 0:
                    # Inject an automatic remediation project
                    fallback_proj = {
                        "node_id": str(uuid.uuid4()),
                        "name": f"Programa de Remediación Táctica: {finding.get('capability', finding.get('target_state', 'Infraestructura'))}",
                        "transformation_typology": "Core Modernization & Risk Mitigation",
                        "business_case": f"Mitigación Directa de Riesgo: {finding.get('impact', finding.get('business_risk', 'Riesgo Operativo'))}",
                        "tech_objective": f"Resolver la brecha detectada en el AS-IS: {f_text}",
                        "deliverables": ["Plan de Remediación", "Ejecución de Parches/Configuraciones", "Informe de Cierre de Brecha"],
                        "sizing": "S",
                        "duration": "Horizonte 1 (Mes 1-3)",
                        "program_id": None,
                        "mitigates_risk_id": finding.get("node_id")
                    }
                    p["projects_todo"].append(fallback_proj)
                    # Update all_proj_text so we don't duplicate fallback projects for similar orphans
                    all_proj_text += " " + fallback_proj["name"].lower() + " " + fallback_proj["tech_objective"].lower()

        return payload


class FairRiskPolicy(BaseSovereignPolicy):
    """
    Polymorphic Policy: SOTA 2026 Quantitative FAIR Risk Engine.
    Executes a true, academic-grade 10,000-run Monte Carlo simulation for each finding,
    sampling Threat Event Frequency (TEF), Vulnerability, and Loss Magnitude (LM) from
    calibrated Beta-PERT distributions to calculate the mean ALE and P90 worst-case exposure.
    """
    def _sample_pert(self, min_val: float, most_likely: float, max_val: float, size: int = 10000) -> Any:
        import numpy as np
        range_val = max_val - min_val
        alpha = 1.0 + 4.0 * (most_likely - min_val) / range_val
        beta_val = 1.0 + 4.0 * (max_val - most_likely) / range_val
        return min_val + np.random.beta(alpha, beta_val, size=size) * range_val

    def evaluate_and_patch(self, graph: EpistemicGraph, payload: Dict[str, Any]) -> Dict[str, Any]:
        import os

        import numpy as np
        pillars = payload.get("pillars_analysis", [])
        
        # 1. Cargar el JSON de perfiles de riesgo FAIR de la gobernanza
        profiles_path = Path("engine_config/policies/fair_risk_profiles.json")
        profiles = {}
        if profiles_path.exists():
            with open(profiles_path, "r", encoding="utf-8") as pf:
                profiles = json.load(pf)
                
        # 2. Cargar client_intelligence.json de forma segura para detectar el sector y jerarquía del cliente
        client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "redeia_v3")
        intel_path = Path(f"working/{client_id}/client_intelligence.json")
        
        industry = "Standard"
        hierarchy = "Standard"
        if intel_path.exists():
            try:
                with open(intel_path, "r", encoding="utf-8-sig") as inf:
                    intel = json.load(inf)
                    p_meta = intel.get("profile", {})
                    industry = p_meta.get("industry", "Standard")
                    hierarchy = p_meta.get("hierarchy", "Standard")
            except Exception:
                pass
                
        # 3. Clasificar el preset dinámicamente según la volumetría del cliente
        preset_key = "MID_MARKET"
        if "Critical Infrastructure" in industry or "Energy" in industry:
            preset_key = "CRITICAL_INFRASTRUCTURE"
        elif "Global" in hierarchy or "Mega" in hierarchy:
            preset_key = "MEGA_ENTERPRISE"
            
        preset = profiles.get(preset_key, profiles.get("MID_MARKET", {}))
        
        # Traducir los mapas a diccionarios de tipos nativos (int keys)
        tef_map = {int(k): v for k, v in preset.get("tef_map", {}).items()}
        vuln_map = {int(k): v for k, v in preset.get("vuln_map", {}).items()}
        lm_map = {int(k): v for k, v in preset.get("lm_map", {}).items()}
        
        # Fallbacks de seguridad en caso de que falle la carga del JSON
        if not tef_map: tef_map = {
            1: {"min": 0.01, "ml": 0.1, "max": 0.2},
            2: {"min": 0.1, "ml": 0.25, "max": 0.5},
            3: {"min": 0.5, "ml": 1.0, "max": 3.0},
            4: {"min": 2.0, "ml": 4.0, "max": 8.0},
            5: {"min": 6.0, "ml": 12.0, "max": 24.0}
        }
        if not vuln_map: vuln_map = {
            1: {"min": 0.05, "ml": 0.10, "max": 0.15},
            2: {"min": 0.15, "ml": 0.25, "max": 0.35},
            3: {"min": 0.30, "ml": 0.50, "max": 0.70},
            4: {"min": 0.70, "ml": 0.85, "max": 0.95},
            5: {"min": 0.90, "ml": 1.00, "max": 1.00}
        }
        if not lm_map: lm_map = {
            1: {"min": 500.0, "ml": 1000.0, "max": 3000.0},
            2: {"min": 2000.0, "ml": 5000.0, "max": 15000.0},
            3: {"min": 10000.0, "ml": 25000.0, "max": 80000.0},
            4: {"min": 50000.0, "ml": 100000.0, "max": 300000.0},
            5: {"min": 250000.0, "ml": 500000.0, "max": 1500000.0}
        }
        
        for p in pillars:
            for finding in p.get("health_check_asis", []):
                text = (finding.get("finding", "") + " " + finding.get("impact", "")).lower()
                
                # Heurísticas para TEF (Threat Event Frequency) 1-5
                tef = 3
                if any(k in text for k in ["ransomware", "ataque", "pública", "internet", "ddos", "hack"]): tef = 5
                elif any(k in text for k in ["interno", "error", "manual", "legacy", "obsoleto"]): tef = 4
                
                # Heurísticas para Vulnerabilidad (1-5)
                vuln = 3
                if any(k in text for k in ["sin parchear", "sin soporte", "crítico", "vulnerabilidad"]): vuln = 5
                elif any(k in text for k in ["manual", "falta", "ausencia", "carencia"]): vuln = 4
                
                # Heurísticas para Loss Magnitude (1-5) - SANEAMIENTO REGULACIONES INTERNACIONALES (Punto 4)
                lm = 3
                if any(k in text for k in ["parada total", "caída catastrófica", "indisponibilidad crítica"]): lm = 5
                elif any(k in text for k in ["nis2", "ens", "soc2", "hipaa", "fedramp", "gdpr", "lgpd", "multa", "sanción", "retraso", "indisponibilidad", "pérdida de datos", "legal", "compliance", "regulatory", "penalty"]): lm = 4
                
                # 4. DETERMINAR RANGOS DE INCERTIDUMBRE (Beta-PERT standard - O-FAIR compliant)
                # TEF range
                tef_range = tef_map.get(tef, {"min": 0.5, "ml": 1.0, "max": 3.0})
                tef_min = float(tef_range.get("min", 0.5))
                tef_ml = float(tef_range.get("ml", 1.0))
                tef_max = float(tef_range.get("max", 3.0))
                
                # Vuln range
                vuln_range = vuln_map.get(vuln, {"min": 0.3, "ml": 0.5, "max": 0.7})
                vuln_min = float(vuln_range.get("min", 0.3))
                vuln_ml = float(vuln_range.get("ml", 0.5))
                vuln_max = float(vuln_range.get("max", 0.7))
                
                # LM range
                lm_range = lm_map.get(lm, {"min": 10000.0, "ml": 25000.0, "max": 80000.0})
                lm_min = float(lm_range.get("min", 10000.0))
                lm_ml = float(lm_range.get("ml", 25000.0))
                lm_max = float(lm_range.get("max", 80000.0))
                
                # 5. SIMULACIÓN DE MONTE CARLO (10.000 iteraciones en numpy)
                size = 10000
                tef_samples = self._sample_pert(tef_min, tef_ml, tef_max, size=size)
                vuln_samples = self._sample_pert(vuln_min, vuln_ml, vuln_max, size=size)
                lm_samples = self._sample_pert(lm_min, lm_ml, lm_max, size=size)
                
                # Sorteo de Bernoulli para materialización de la pérdida
                U = np.random.uniform(0.0, 1.0, size=size)
                losses_occurred = U < vuln_samples
                
                # El coste por iteración es el impacto ponderado por la frecuencia de incidentes
                loss_per_run = np.where(losses_occurred, tef_samples * lm_samples, 0.0)
                
                # Métricas estadísticas SOTA
                mean_ale = float(np.mean(loss_per_run))
                p90_ale = float(np.percentile(loss_per_run, 90.0))
                min_ale = float(np.min(loss_per_run))
                max_ale = float(np.max(loss_per_run))
                
                # Redondeo limpio
                ale_euros = round(mean_ale, 2)
                
                finding["threat_event_frequency"] = tef
                finding["vulnerability_level"] = vuln
                finding["loss_magnitude"] = lm
                finding["fair_ale_score"] = ale_euros
                finding["fair_p90_score"] = round(p90_ale, 2)
                finding["fair_min_score"] = round(min_ale, 2)
                finding["fair_max_score"] = round(max_ale, 2)
                
        return payload

class SovereignPolicyEngine:
    """
    Sovereign Policy Engine Compiler (SL4).
    Orchestrates the execution of registered polymorphic policies
    to deliver 10/10 zero-defect assessments.
    """
    def __init__(self, graph: EpistemicGraph):
        self.graph = graph
        self.policies: List[BaseSovereignPolicy] = [
            ClientSanitizationPolicy(),
            FairRiskPolicy(),
            DeduplicationPolicy(),
            SequencingPolicy(),
            OTPerimeterPolicy(),
            ArchiMateDeliverablesPolicy(),
            BusinessCaseGroundingPolicy(),
            ReverseTraceabilityPolicy()
        ]

    def compile(self, blueprint_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compiles the payload by passing it through all active policy filters."""
        for policy in self.policies:
            blueprint_payload = policy.evaluate_and_patch(self.graph, blueprint_payload)
        return blueprint_payload
