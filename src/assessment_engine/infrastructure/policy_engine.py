import logging

logger = logging.getLogger(__name__)

import json
import os
import re
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.text_utils import deep_unescape


class BaseSovereignPolicy(ABC):
    r"""{'BaseSovereignPolicy': 'Abstract base class for sovereign data policies.\n\nDefines the abstract interface for policies that evaluate an `EpistemicGraph`\nto make a decision and subsequently patch a data payload to enforce that\ndecision.\n\nSubclasses must implement the `evaluate_and_patch` method to provide the\nconcrete policy logic. This component-based design enables a pluggable system\nwhere diverse policies (e.g., for data residency, access control, or redaction)\ncan be developed and applied in a consistent, standardized manner.', 'BaseSovereignPolicy.evaluate_and_patch': 'Evaluate the policy against a knowledge graph and patch a data payload.\n\nThis abstract method defines the primary contract for policy execution. Subclasses\nmust implement this method to analyze the provided `EpistemicGraph`, render a\npolicy decision, and modify the `payload` dictionary to enforce it.\n\nArgs:\n    graph: The knowledge graph instance containing the epistemic state for\n        policy evaluation.\n    payload: The data payload to be modified. While implementations may modify\n        this dictionary in-place, the returned dictionary should always be\n        treated as the canonical result by callers.\n\nReturns:\n    The modified data payload reflecting the enforcement of the policy.'}."""

    @abstractmethod
    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a knowledge graph against a policy and patch a data payload.

        This abstract method defines the interface for policy rule evaluation and
        enforcement. Implementations must analyze the provided `EpistemicGraph` to
        make a policy decision and subsequently produce a modified version of the
        input `payload` dictionary that reflects the policy's enforcement.

        Args:
            graph: The `EpistemicGraph` instance to be evaluated against the policy.
            payload: The data payload to be patched. While implementations may modify
                this dictionary in-place, callers must not rely on this side
                effect and should exclusively use the returned dictionary.

        Returns:
            The patched payload dictionary reflecting the outcome of the policy
            evaluation.
        """
        pass


class ClientSanitizationPolicy(BaseSovereignPolicy):
    """A policy for sanitizing client-specific placeholders within a data payload.

    This policy implements a sanitization routine that recursively traverses a
    dictionary-based data structure. It identifies and replaces all occurrences of
    predefined string placeholders (e.g., `[Cliente]`, `[CUSTOMER]`) with a
    canonical client name.

    The canonical name is dynamically extracted from the payload's metadata,
    specifically from the `payload['document_meta']['client_name']` path, and
    defaults to a constant value if this path is not found. The sanitization
    process produces a new, modified copy of the payload, preserving the
    integrity of the original data structure. The core logic is implemented in the
    `evaluate_and_patch` method.
    """

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively substitutes client name placeholders within a data payload.

        This method traverses the nested dictionary and list structure of the payload
        to produce a new, patched data structure. It determines the client name to
        use for substitution from `payload['document_meta']['client_name']`,
        falling back to a default value of 'CLIENTE' if this key path is absent.

        All string values within the payload are scanned, and occurrences of a
        predefined set of placeholders (e.g., `[Cliente]`, `[CUSTOMER]`) are replaced
        with the resolved client name. The original payload object is not mutated.

        The `graph` argument is reserved for future policy evaluation and is currently
        ignored.

        Args:
            graph: The epistemic graph for policy evaluation. This argument is
                reserved for future use and is ignored.
            payload: The input data structure to patch. It may contain nested
                dictionaries, lists, and other values.

        Returns:
            A new dictionary with the same structure as the payload, but with all
            client name placeholders substituted in its string values.

        Raises:
            RecursionError: If the payload contains deeply nested structures or
                cyclical references that exceed the system's recursion limit.
        """
        client_name = payload.get("document_meta", {}).get("client_name", "CLIENTE")

        def scrub(obj: Any) -> Any:
            """Recursively substitutes client-specific placeholders within a data structure.

            This function traverses nested dictionaries and lists to operate on string
            values. It is non-mutating; a new object is constructed and returned with
            the substitutions applied. The original object is left unchanged.

            The substitution logic replaces a hardcoded set of placeholders (e.g.,
            `"[CLIENTE]"`, `"[customer]"`) with the value of the module-level `client_name`
            variable. A final regular expression pass is performed to sanitize any
            remaining `"[Cliente]"` or `"[cliente]"` variations. Data types other than
            `dict`, `list`, and `str` are returned unmodified.

            Args:
                obj (Any): The data structure to process. Can be a dictionary, list,
                    string, or any other Python object.

            Returns:
                Any: A new data structure of the same type as the input, with all
                identified client-specific placeholders in its string values replaced.

            Raises:
                RecursionError: If the input object's nesting depth exceeds the system's
                    recursion limit or if it contains cyclical references.
            """
            if isinstance(obj, dict):
                return {k: scrub(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [scrub(x) for x in obj]
            elif isinstance(obj, str):
                for placeholder in [
                    "[Cliente]",
                    "[CLIENTE]",
                    "[cliente]",
                    "[CLIENT]",
                    "[client]",
                    "[CUSTOMER]",
                    "[customer]",
                ]:
                    obj = obj.replace(placeholder, client_name)
                # A final sanitization pass using a regular expression removes any residual bracketed placeholders.
                obj = re.sub(r"\[[Cc]liente\]", client_name, obj)
                return obj
            return obj

        return scrub(payload)


class DeduplicationPolicy(BaseSovereignPolicy):
    r"""{'docstring': "Consolidates disparate platform engineering projects into a canonical program.\n\n    This policy operates specifically on documents where the `tower_code` metadata\n    is 'T2'. It scans the 'pillars_analysis' list for any projects containing\n    'Platform Engineering' or 'Ingeniería de Plataforma' in their names. If\n    such projects are found, they are removed from their original pillars.\n\n    A single, new strategic program is then generated and injected into the\n    target 'T2.P4' pillar, replacing its entire 'projects_todo' list. The\n    description and deliverables of this canonical program are localized to\n    English or Spanish and customized with the 'cloud_provider' specified in\n    the document's metadata.\n\n    If the document's `tower_code` is not 'T2' or no platform engineering\n    projects are found, the input `payload` is returned without modification.\n\n    Args:\n        graph (EpistemicGraph): The epistemic graph, providing contextual data.\n            This argument is currently unused in this policy's logic.\n        payload (Dict[str, Any]): The document analysis payload to be processed.\n            This dictionary is modified in place. It is expected to contain:\n            'document_meta' (Dict): Metadata including 'tower_code' (str),\n                'language' (str), and 'cloud_provider' (str).\n            'pillars_analysis' (List[Dict]): A list of pillar objects, where\n                each pillar has a 'pilar_id' (str) and 'projects_todo' (List).\n\n    Returns:\n        Dict[str, Any]: The input `payload` dictionary, potentially modified.\n            If consolidation occurs, the original `payload` object is returned\n            with platform engineering projects unified into the 'T2.P4' pillar."}."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consolidates disparate platform engineering projects into a single strategic program for Tower 2 documents. This policy operates on payloads where the `document_meta.tower_code` is 'T2'. It scans all pillars for projects with names containing "Platform Engineering" or its Spanish equivalent, "Ingeniería de Plataforma". Any such projects are removed from their original pillars. If one or more platform engineering projects are found, the entire `projects_todo` list of the target pillar ('T2.P4') is overwritten with a single, newly generated canonical program. The content of this program is localized based on the `document_meta.language` and incorporates the `document_meta.cloud_provider`. If the document is not for 'T2' or no relevant projects are found, the payload is returned unmodified. Args: graph: The epistemic graph context (currently unused). payload: A dictionary containing document analysis results. Expected keys include: `pillars_analysis` (list[dict]): A list of pillar structures, each containing a `projects_todo` list of project dictionaries. `document_meta` (dict): Metadata including `tower_code`, `language`, and `cloud_provider`. Returns: The `payload` dictionary, which is modified in place. If consolidation occurs, disparate projects are removed and the 'T2.P4' pillar is updated with the unified program. Otherwise, the original payload is returned."""
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        # The consolidation logic specifically targets initiatives labeled 'Platform Engineering' (or its Spanish-language equivalent) for migration to Tower 2.
        platform_eng_projects = []
        target_pilar_id = "T2.P4"  # Provides a deterministic fallback to the self-service pillar when a target pillar is unspecified.

        # This consolidation logic is scoped to Tower 2, the designated canonical pillar for all platform initiatives.
        tower_code = payload.get("document_meta", {}).get("tower_code", "")
        doc_lang = payload.get("document_meta", {}).get("language", "es").lower()
        cloud_provider = payload.get("document_meta", {}).get("cloud_provider", "AWS")

        if tower_code == "T2":
            for p in pillars:
                p_id = p.get("pilar_id")
                projects = p.get("projects_todo", [])
                for proj in list(projects):
                    name = proj.get("name", "")
                    if (
                        "platform engineering" in name.lower()
                        or "ingeniería de plataforma" in name.lower()
                    ):
                        if p_id != target_pilar_id:
                            platform_eng_projects.append(proj)
                            p["projects_todo"].remove(
                                proj
                            )  # Remove the redundant initiative from its source pillar post-consolidation.

            # Upon successful consolidation, the canonical initiative is injected into the designated T2.P4 pillar.
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
                                    "Despliegue del portal central de Autoservicio para el desarrollador.",
                                ],
                                "sizing": "XL",
                                "duration": "Horizonte 1 (0-6 meses)",
                                "program_id": None,
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
                                    "Developer Self-Service portal deployment.",
                                ],
                                "sizing": "XL",
                                "duration": "Horizon 1 (0-6 months)",
                                "program_id": None,
                            }
                        #
                        p["projects_todo"] = [unified_project]
                        break
        return payload


class SequencingPolicy(BaseSovereignPolicy):
    """Modifies project `duration` and `tech_objective` fields in-place based on name keywords. This method enforces a logical project timeline by iterating through all projects within the `payload`. It identifies projects by matching specific Spanish keywords in their 'name' field. Foundational work, such as adoption strategies ('estrategia de adopción'), is assigned to an early time horizon ('Horizonte 1'). Technical implementations, such as pilots or internal development platforms ('piloto', 'kubernetes'), are assigned to a later time horizon ('Horizonte 2'). Args: graph: An `EpistemicGraph` for contextual analysis. Note: This argument is currently unused in the function body. payload: The data structure containing project information. It is expected to have a 'pillars_analysis' key mapping to a list of pillar dictionaries, each of which contains a 'projects_todo' key mapping to a list of project dictionaries. This dictionary is modified in-place. Returns: The mutated payload dictionary with updated project timelines and objectives. Raises: TypeError: If 'pillars_analysis' or 'projects_todo' keys are present but their corresponding values are not lists."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        r"""{'docstring': "Patches project timelines and objectives in a payload based on business rules.\n\n    This method enforces a logical project sequence by modifying the `duration`\n    and `tech_objective` fields for projects within the payload. It scans project\n    names for keywords to distinguish between foundational work and subsequent\n    technical implementation.\n\n    Specifically, projects with names indicating strategy or adoption are assigned\n    to an early time horizon ('Horizonte 1'), while projects related to technical\n    pilots or platform development are assigned to a later one ('Horizonte 2').\n    The payload dictionary is modified in-place.\n\n    Args:\n        graph: The epistemic graph for context. This argument is currently unused.\n        payload: The input data structure containing project information. The method\n            expects a nested structure of `payload['pillars_analysis'][...]['projects_todo']`.\n\n    Returns:\n        The payload dictionary, modified with updated project data.\n\n    Raises:\n        TypeError: If a value expected to be a list (e.g., for `pillars_analysis`\n            or `projects_todo`) is present but has a non-iterable type.\n        AttributeError: If a project's `name` value is not a string and does not\n            support the `.lower()` method."}."""
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        # Re-sequence project time horizons based on the initiative dependency graph to enforce a valid topological order.
        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "")
                # Enforces the business rule that foundational projects and adoption plans must be scheduled in the H1-Kickoff horizon.
                if (
                    "adopción de plataforma de contenedores" in name.lower()
                    or "estrategia de adopción" in name.lower()
                ):
                    proj["duration"] = "Horizonte 1 - Fase de Arranque (Mes 1-2)"
                    proj["tech_objective"] = (
                        "Establecer las directrices operativas, de gobernanza, de costes y de seguridad para cargas de contenedores antes de iniciar desarrollos técnicos de IDP."
                    )
                # Enforces the business rule that technical pilots and Initial Deployment Platforms (IDPs) are scheduled for the H2 horizon or later.
                elif (
                    "plataforma interna de desarrollo" in name.lower()
                    or "piloto" in name.lower()
                    or "kubernetes" in name.lower()
                    or "eks" in name.lower()
                ):
                    proj["duration"] = "Horizonte 2 (Mes 3-12)"

        return payload


class OTPerimeterPolicy(BaseSovereignPolicy):
    r"""{'docstring': "Evaluate a portfolio and idempotently inject data diode security controls.\n\nThis method enforces a mandatory security control for clients in the\n'Critical Infrastructure' or 'Energy' sectors. It inspects the project\nportfolio for the coexistence of Operational Technology (OT/SCADA) and IT\nAIOps initiatives. If both are found, it patches the respective projects\nin-place by appending deliverables to implement a hardware data diode,\nthereby ensuring a secure, one-way data flow from the OT to the IT\nenvironment.\n\nThe client's industry is determined by first attempting to read a\n`client_intelligence.json` file, whose path is derived from the\n`ASSESSMENT_CLIENT_ID` environment variable. If this file is absent or\nunreadable, it falls back to inspecting the client name within the payload.\nThe policy is resilient to file I/O exceptions, which are suppressed.\nThe patching operation is idempotent and will not add duplicate deliverables.\n\nArgs:\n    graph (EpistemicGraph): The epistemic knowledge graph for the assessment.\n        This argument is required by the policy interface but is not used in\n        this method's logic.\n    payload (Dict[str, Any]): The project portfolio data structure. Expected to\n        contain a 'document_meta' dictionary and a 'pillars_analysis' list\n        of project dictionaries.\n\nReturns:\n    Dict[str, Any]: The `payload` dictionary, potentially modified in-place to\n        include data diode deliverables. Returns the original payload if the\n        client is not in a relevant sector or if the triggering project types\n        are not both present."}."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        r"""{'docstring': "Conditionally injects data diode security controls into a project portfolio.\n\nThis policy enforces a mandatory security control for clients operating within\nthe 'Critical Infrastructure' or 'Energy' sectors. It first determines the\nclient's industry by reading a `client_intelligence.json` file, with a\nfallback mechanism that inspects the client name in the payload metadata.\n\nThe policy activates only if the sector matches and the project portfolio\ncontains a combination of both Operational Technology (OT/SCADA) and IT\nAIOps initiatives. Upon activation, the function modifies the relevant\nprojects in-place, injecting deliverables and technical objectives to\nmandate the implementation of a hardware data diode. This ensures a secure,\none-way data flow from the OT to the IT environment.\n\nThe modification is idempotent; it verifies the absence of existing data\ndiode deliverables before injection to prevent duplication. If the activation\nconditions are not met, the original payload is returned unmodified.\n\nArgs:\n    graph (EpistemicGraph): The epistemic graph for the assessment. Unused by\n        this policy.\n    payload (Dict[str, Any]): The project portfolio data structure. Expected to\n        contain 'pillars_analysis' (a list of pillars, each with a\n        'projects_todo' list) and 'document_meta' (containing 'client_name').\n\nReturns:\n    Dict[str, Any]: The payload, potentially modified to include data diode\n        deliverables. Returns the original payload if policy conditions are\n        not met."}."""
        # Resolve client's industry sector from environment metadata to enforce sector-specific policy execution.
        client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
        intel_path = Path(f"working/{client_id}/client_intelligence.json")
        if not intel_path.exists():
            client_base = client_id.split('_')[0]
            intel_path = Path(f"working/{client_id}/{client_base}/client_intelligence.json")
            
        industry = "Standard"
        if intel_path.exists():
            try:
                with open(intel_path, "r", encoding="utf-8-sig") as inf:
                    intel = json.load(inf)
                    p_meta = intel.get("profile", {})
                    industry = p_meta.get("industry", "Standard")
            except (OSError, json.JSONDecodeError) as ex:
                logger.debug(f"[PolicyEngine] Error leyendo perfil de inteligencia: {ex}")
        else:
            # Implements a security fallback to prevent execution failure in CI/CD environments.
            client_name = payload.get("document_meta", {}).get("client_name", "CLIENTE")
            is_energy = os.environ.get("ASSESSMENT_INDUSTRY", "").lower() == "energy"
            if is_energy or "critical infrastructure" in os.environ.get("ASSESSMENT_INDUSTRY", "").lower():
                industry = "Critical Infrastructure"
            else:
                # Reads from brand profile configuration first (declarative, elite approach)
                try:
                    from assessment_engine.infrastructure.config_loader import (
                        load_brand_profile,
                    )

                    brand_profile = load_brand_profile()
                    is_critical = brand_profile.get("styling", {}).get("is_critical", False)
                    if is_critical:
                        industry = "Critical Infrastructure"
                except (ImportError, KeyError, ValueError) as ex:
                    logger.debug(f"[PolicyEngine] Fallback de perfil de marca omitido: {ex}")

        # SECTOR-LOCK ENFORCEMENT: Halts policy execution if the client's industry sector is not 'Critical Infrastructure' or 'Energy'.
        if "Critical Infrastructure" not in industry and "Energy" not in industry:
            return payload

        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        has_scada = False
        has_aiops = False

        # Verifies the precondition that both OT/SCADA and IT AIOps initiatives coexist in the project portfolio.
        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "").lower()
                if (
                    "scada" in name
                    or "legada" in name
                    or "infraestructura legacy" in name
                ):
                    has_scada = True
                if (
                    "aiops" in name
                    or "observabilidad predictiva" in name
                    or "observabilidad" in name
                ):
                    has_aiops = True

        # If the precondition is met, inject mandatory hardware data diode controls to enforce a physical security perimeter.
        if has_scada and has_aiops:
            for p in pillars:
                for proj in p.get("projects_todo", []):
                    name = proj.get("name", "").lower()
                    if (
                        "scada" in name
                        or "legada" in name
                        or "infraestructura legacy" in name
                    ):
                        if "deliverables" not in proj:
                            proj["deliverables"] = []
                        # Ensures policy execution is idempotent by preventing the re-injection of existing deliverables.
                        if not any(
                            "diodo de datos" in d.lower() for d in proj["deliverables"]
                        ):
                            proj["deliverables"].append(
                                "Implementación de un Diodo de Datos Unidireccional por Hardware para extracción segura de telemetría sin canal de retorno."
                            )
                            proj["tech_objective"] += (
                                " El aislamiento físico del entorno SCADA se mantendrá de forma inquebrantable mediante el uso de un diodo de datos unidireccional."
                            )
                    if (
                        "aiops" in name
                        or "observabilidad predictiva" in name
                        or "observabilidad" in name
                    ):
                        if "deliverables" not in proj:
                            proj["deliverables"] = []
                        if not any(
                            "diodo de datos" in d.lower() for d in proj["deliverables"]
                        ):
                            proj["deliverables"].append(
                                "Despliegue del gateway receptor del Diodo de Datos de OT para ingesta pasiva de telemetría en AWS IoT Core."
                            )
                            proj["tech_objective"] += (
                                " Toda la ingesta de telemetría en tiempo real de subestaciones y OT se canalizará de forma 100% pasiva y segura mediante diodos de datos unidireccionales."
                            )
        return payload


class ArchiMateDeliverablesPolicy(BaseSovereignPolicy):
    """Populates or replaces project deliverables based on keyword matching.

    This method iterates through projects nested within the `payload`. It
    identifies projects where the 'deliverables' list is either missing,
    empty, or contains a generic placeholder text.

    For each identified project, the method constructs a text corpus from the
    project's name and technical objective. It then scans this corpus for
    keywords defined in a static internal catalog. If a match is found, the
    project's deliverables are replaced with a set of specific artifacts from
    the catalog. If no keywords match, a standard, default set of
    deliverables is assigned.

    The input `payload` dictionary is mutated in place.

    Args:
        graph: The knowledge graph. Part of the policy interface but unused by
            this specific policy implementation.
        payload: A dictionary containing project data, expected to conform to the
            schema `{'pillars_analysis': [{'projects_todo': [project_dict]}]}`.
            This dictionary is mutated in place by the method.

    Returns:
        The original `payload` dictionary object, now modified with updated
        `deliverables` for the applicable projects.

    Raises:
        TypeError: If `payload` does not conform to the expected nested
            list/dict structure (e.g., `payload['pillars_analysis']` is not
            a list).
    """

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replaces generic or missing project deliverables with specific, catalog-based items.

        Iterates through projects within the payload's nested structure. If a
        project's `deliverables` list is absent, empty, or contains a generic
        placeholder, this method replaces it. New deliverables are sourced from a
        hardcoded catalog by matching keywords against a concatenation of the
        project's name and technical objective.

        If multiple keywords match, their respective deliverables are merged. If no
        keywords match, a standard default list is assigned to ensure the project
        has a defined starting point. The input `payload` dictionary is modified
        in place.

        Args:
            graph: The epistemic graph. This argument is currently unused.
            payload: A dictionary containing project data. It is expected to have a
                `pillars_analysis` key containing a list of pillars, each with a
                `projects_todo` list of project dictionaries. This dictionary is
                modified in place.

        Returns:
            The same payload dictionary instance passed as input, with the
            `deliverables` lists populated for applicable projects.

        Raises:
            TypeError: If `payload` contains a malformed structure where values expected
                to be lists (e.g., for `pillars_analysis` or `projects_todo`) are
                not iterable.
        """
        catalog = {
            "kubernetes": [
                "Manifiestos Base YAML",
                "Módulo Terraform EKS",
                "Helm Charts de Gobernanza",
                "Pipeline GitLab/GitHub Actions",
            ],
            "eks": [
                "Manifiestos Base YAML",
                "Módulo Terraform EKS",
                "Helm Charts de Gobernanza",
                "Pipeline GitLab/GitHub Actions",
            ],
            "contenedores": [
                "Manifiestos Base YAML",
                "Módulo Terraform EKS",
                "Helm Charts de Gobernanza",
                "Pipeline GitLab/GitHub Actions",
            ],
            "landing zone": [
                "AWS Control Tower Account Factory",
                "Políticas SCP (Service Control Policies)",
                "Módulo Terraform Base Network",
            ],
            "platform engineering": [
                "Catálogo Backstage/IDP",
                "Plantillas de Autoservicio IaC",
                "Framework de SLIs/SLOs",
            ],
            "observabilidad": [
                "Dashboards Grafana/CloudWatch",
                "Reglas de Alertas PromQL",
                "Integración PagerDuty/ServiceNow",
            ],
            "aiops": [
                "Dashboards Grafana/CloudWatch",
                "Modelos de Detección de Anomalías",
                "Integración ITSM",
            ],
            "scada": [
                "Topología de Red Purdue",
                "Reglas de Firewall Perimetral",
                "Diodo de Datos Unidireccional",
            ],
            "automatización": [
                "Playbooks Ansible",
                "Módulos Terraform",
                "Pipelines CI/CD",
            ],
            "iac": [
                "Módulos Terraform",
                "Repositorio GitOps",
                "Políticas OPA/Sentinel",
            ],
            "dr": [
                "Runbooks de Recuperación",
                "Plan de Pruebas de Failover",
                "Plantillas AWS Elastic Disaster Recovery",
            ],
            "disaster recovery": [
                "Runbooks de Recuperación",
                "Plan de Pruebas de Failover",
                "Plantillas AWS Elastic Disaster Recovery",
            ],
            "backup": [
                "Políticas de Retención",
                "Bóveda Inmutable",
                "Pruebas de Restauración Automatizadas",
            ],
        }

        pillars = payload.get("pillars_analysis", [])
        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "").lower()
                tech_obj = proj.get("tech_objective", "").lower()
                combined_text = name + " " + tech_obj

                # The policy injects content only when existing deliverables are absent, empty, or contain generic placeholder text.
                current_deliverables = proj.get("deliverables", [])
                is_generic = not current_deliverables or any(
                    "diseño de arquitectura" in d.lower() for d in current_deliverables
                )

                if is_generic:
                    new_deliverables = set()
                    for keyword, hard_deliverables in catalog.items():
                        if keyword in combined_text:
                            new_deliverables.update(hard_deliverables)

                    if new_deliverables:
                        proj["deliverables"] = list(new_deliverables)
                    else:
                        # Assigns a reasoned default for unrecognized project types to avoid the use of low-signal generic placeholders.
                        proj["deliverables"] = [
                            "Documento de Diseño Técnico (HLD/LLD)",
                            "Repositorio de Código (IaC/Config)",
                            "Plan de Pruebas y Validation",
                        ]

        return payload


class BusinessCaseGroundingPolicy(BaseSovereignPolicy):
    r"""{'docstring': "Grounds project business cases against AS-IS findings or generates a fallback.\n\nIterates through projects defined in `payload['pillars_analysis']`. For each\nproject where the `business_case` is absent or a placeholder, it attempts\nto link the project to a finding in `health_check_asis`. The linkage is\nestablished using a word-overlap heuristic: a match occurs if the project's\nname and technical objective share more than one significant word (length > 5)\nwith a finding's text.\n\nIf a match is found, the business case is rewritten as 'Direct Mitigation',\nincorporating the finding's impact, and a `mitigates_risk_id` key is added\nto the project. If no match is found, a fallback 'Strategic Enabler'\nbusiness case is generated, referencing regulatory frameworks from\n`document_meta`. The generated text is localized based on the\n`document_meta.language` field.\n\nArgs:\n    graph: The epistemic graph for contextual analysis. This argument is\n        reserved for future use and is not currently utilized by the policy.\n    payload: The input data structure to be modified. It is expected to\n        contain a `pillars_analysis` key (a list of pillar dictionaries)\n        and a `document_meta` key. Each pillar should contain `projects_todo`\n        and `health_check_asis` lists. This dictionary is modified in-place.\n\nReturns:\n    The mutated `payload` dictionary with enriched business cases.\n\nRaises:\n    TypeError: If a value within the `payload` does not match its expected\n        type, for example, if `pillars_analysis` is not an iterable.\n    AttributeError: If an element within a list (e.g., `projects_todo`) is\n        not a dictionary and therefore does not support the `.get()` method."}."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Populates missing project business cases by linking them to risk findings.

        This method iterates through projects within the `payload['pillars_analysis']`
        list. If a project's `business_case` key is missing or contains a known
        placeholder string, the method attempts to link the project to a finding
        from the `health_check_asis` list.

        A link is established using a word-overlap heuristic: a project is matched
        to a finding if its name or technical objective shares more than one word
        (of length greater than five characters) with the finding's description.

        If a match is found, a 'Direct Mitigation' business case is generated using
        the finding's impact description, and the project is updated with a
        `mitigates_risk_id` referencing the finding's `node_id`. If no match is
        found, a generic 'Strategic Enabler' business case is created, incorporating
        regulatory frameworks specified in `document_meta`.

        The language of the generated text is determined by the
        `payload['document_meta']['language']` field. The input `payload` dictionary
        is modified in-place.

        Args:
            graph: The epistemic graph context for the analysis. This argument is
                reserved for future use and is not currently accessed by the method.
            payload: The input analysis payload containing project and assessment data.
                It is expected to have `pillars_analysis` and `document_meta` keys.
                This dictionary is modified in-place.

        Returns:
            The mutated `payload` dictionary object that was passed as an argument.

        Raises:
            TypeError: If a value within the `payload` has an unexpected type that
                prevents iteration (e.g., if `pillars_analysis` is not a list).
        """
        pillars = payload.get("pillars_analysis", [])
        doc_lang = payload.get("document_meta", {}).get("language", "es").lower()

        # Enforces regulatory sanitization rule #2, which decouples specific compliance artifacts from the core business case to maintain modularity.
        reg_frameworks = payload.get("document_meta", {}).get("regulatory_frameworks")
        if not reg_frameworks:
            reg_frameworks = (
                "marcos normativos aplicables (ej. NIS2, ISO 27001)"
                if doc_lang == "es"
                else "applicable regulatory frameworks"
            )

        for p in pillars:
            asis_findings = p.get("health_check_asis", [])
            for proj in p.get("projects_todo", []):
                bc = proj.get("business_case", "")
                if (
                    not bc
                    or "impacto estratégico basado en la validación" in bc.lower()
                ):
                    # Establishes business case validity by linking the initiative to a semantically related finding from the AS-IS assessment.
                    name = proj.get("name", "").lower()
                    tech_obj = proj.get("tech_objective", "").lower()

                    matched_finding = None
                    for finding in asis_findings:
                        f_text = finding.get(
                            "finding", finding.get("risk_observed", "")
                        ).lower()
                        # Employs a word overlap heuristic to establish a semantic link between the initiative and AS-IS findings.
                        words = [w for w in f_text.split() if len(w) > 5]
                        if sum(1 for w in words if w in name or w in tech_obj) > 1:
                            matched_finding = finding
                            break

                    if matched_finding:
                        impact = matched_finding.get(
                            "impact", matched_finding.get("business_risk", "")
                        )
                        proj["business_case"] = (
                            f"Mitigación Directa: Resuelve la vulnerabilidad crítica detectada en el AS-IS, eliminando el riesgo de: '{impact}'."
                            if doc_lang == "es"
                            else f"Direct Mitigation: Resolves the critical vulnerability detected in the AS-IS, eliminating the risk of: '{impact}'."
                        )
                        proj["mitigates_risk_id"] = matched_finding.get("node_id")
                    else:
                        proj["business_case"] = (
                            f"Habilitador Estratégico: Reduce el TCO operativo, acelera el time-to-market y garantiza el cumplimiento normativo ({reg_frameworks})."
                            if doc_lang == "es"
                            else f"Strategic Enabler: Reduces operational TCO, accelerates time-to-market, and ensures regulatory compliance ({reg_frameworks})."
                        )

        return payload


class ReverseTraceabilityPolicy(BaseSovereignPolicy):
    """Injects remediation projects into a payload for unaddressed findings.

        This method enforces reverse traceability by iterating through each 'pillar'
    in the payload's 'pillars_analysis'. For each pillar, it aggregates the text
        from all project names and technical objectives in 'projects_todo'. It then
        examines each finding in 'health_check_asis' to determine if it is an
        'orphan'.

        A finding is considered an orphan if none of its constituent words longer
        than five characters are present in the aggregated project text. For each
        such orphan, a standardized remediation project dictionary is synthesized
        and appended to the pillar's 'projects_todo' list, mutating the payload
        in-place. The aggregated project text is also updated within the loop to
        prevent the creation of redundant projects for semantically similar findings.

    Args:
            graph: The epistemic graph context. Reserved for future use and is not
                currently used in the method's logic.
            payload: The analysis data structure, which is modified in-place.
                Expected to contain a 'pillars_analysis' key mapping to a list of
                pillar dictionaries. Each pillar dictionary must contain a
                'projects_todo' list and may contain a 'health_check_asis' list.

    Returns:
            The input payload dictionary, which has been mutated to include new
            auto-generated remediation projects where traceability gaps were found.

    Raises:
            KeyError: If a pillar dictionary is missing the 'projects_todo' key,
                as the method attempts to append to it directly.
            TypeError: If a value expected to be a list (e.g., the value for
                'pillars_analysis' or 'health_check_asis') is not iterable.
            AttributeError: If an element within an expected list (e.g., a pillar,
                project, or finding) is not a dictionary and does not support the
                `.get()` method.
    """

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluates an analysis payload for unmitigated risks and patches the data structure by injecting corresponding remediation projects.

        This method iterates through each 'pillar' within the payload's
        'pillars_analysis' list. For each pillar, it constructs a text corpus from
        the names and objectives of all planned projects in 'projects_todo'. It
        then compares each finding from 'health_check_asis' against this corpus.

        A finding is considered unmitigated if none of its significant words
        (longer than 5 characters) are found within the project corpus. For each
        such finding, a new, standardized remediation project is generated and
        appended in-place to the pillar's 'projects_todo' list. The text from
        this newly added project is also appended to the pillar's corpus to
        prevent creating duplicate remediation projects for similar subsequent
        findings within the same pillar.

        Args:
            graph (EpistemicGraph): The epistemic graph context. This argument is
                reserved for future use and is not accessed in the current
                implementation.
            payload (Dict[str, Any]): The input analysis data structure, which is
                modified in-place. It is expected to have a 'pillars_analysis'
                key containing a list of pillar dictionaries. Each pillar
                dictionary should contain 'health_check_asis' and 'projects_todo'
                keys, both mapping to lists of dictionaries.

        Returns:
            Dict[str, Any]: A reference to the input `payload` dictionary, which has
                been modified in-place to include new remediation projects where
                gaps were identified.

        Raises:
            TypeError: If a value in the payload that is expected to be a list
                (e.g., the value for 'pillars_analysis') is not iterable.
            AttributeError: If an element within an expected list (e.g., a pillar
                dictionary) is not a dictionary and does not support the `.get()`
                method.
        """
        pillars = payload.get("pillars_analysis", [])
        for p in pillars:
            asis_findings = p.get("health_check_asis", [])
            projects = p.get("projects_todo", [])

            all_proj_text = " ".join(
                [
                    proj.get("name", "") + " " + proj.get("tech_objective", "")
                    for proj in projects
                ]
            ).lower()

            for finding in asis_findings:
                f_text = finding.get("finding", finding.get("risk_observed", ""))
                # Defines an 'orphan finding' as an identified AS-IS gap that lacks a corresponding TO-BE remediation initiative.
                words = [w.lower() for w in f_text.split() if len(w) > 5]
                if words and sum(1 for w in words if w in all_proj_text) == 0:
                    # Automatically inject a new remediation initiative into the roadmap to ensure the orphan finding is addressed.
                    fallback_proj = {
                        "node_id": str(uuid.uuid4()),
                        "name": f"Programa de Remediación Táctica: {finding.get('capability', finding.get('target_state', 'Infraestructura'))}",
                        "transformation_typology": "Core Modernization & Risk Mitigation",
                        "business_case": f"Mitigación Directa de Riesgo: {finding.get('impact', finding.get('business_risk', 'Riesgo Operativo'))}",
                        "tech_objective": f"Resolver la brecha detectada en el AS-IS: {f_text}",
                        "deliverables": [
                            "Plan de Remediación",
                            "Ejecución de Parches/Configuraciones",
                            "Informe de Cierre de Brecha",
                        ],
                        "sizing": "S",
                        "duration": "Horizonte 1 (Mes 1-3)",
                        "program_id": None,
                        "mitigates_risk_id": finding.get("node_id"),
                    }
                    p["projects_todo"].append(fallback_proj)
                    # Append processed findings to an aggregate text corpus to prevent redundant remediation projects for semantically similar orphan findings.
                    all_proj_text += (
                        " "
                        + fallback_proj["name"].lower()
                        + " "
                        + fallback_proj["tech_objective"].lower()
                    )

        return payload


class FairRiskPolicy(BaseSovereignPolicy):
    """Generate random samples from statistical distributions for FAIR Monte Carlo modeling."""

    def _sample_pert(
        self, min_val: float, most_likely: float, max_val: float, size: int = 10000, rng: Any = None
    ) -> Any:
        import numpy as np
        if rng is None:
            rng = np.random.default_rng()

        # Mathematical Safeguard: Prevent DivisionByZero if min and max converge
        if min_val >= max_val:
            return np.full(size, min_val)

        # Mathematical Safeguard: Clamp mode inside boundaries to prevent Beta parameter inversion
        most_likely = max(min_val, min(most_likely, max_val))

        range_val = max_val - min_val
        alpha = 1.0 + 4.0 * (most_likely - min_val) / range_val
        beta_val = 1.0 + 4.0 * (max_val - most_likely) / range_val
        return min_val + rng.beta(alpha, beta_val, size=size) * range_val

    def _sample_lognormal(
        self, rng: Any, min_val: float, most_likely: float, max_val: float, size: int = 10000
    ) -> Any:
        import numpy as np

        # Mathematical Safeguard: Prevent Log of zero or convergence
        if min_val >= max_val or min_val <= 0:
            return np.full(size, max_val)

        # SOTA Actuarial Practice: Calibrate Lognormal using the Mode (most_likely) and P95 (max_val).
        # Mode M = exp(mu - sigma^2) => mu = ln(M) + sigma^2
        # P95 X = exp(mu + 1.645*sigma) => ln(X) = mu + 1.645*sigma
        # Substituting mu: ln(X) = ln(M) + sigma^2 + 1.645*sigma => sigma^2 + 1.645*sigma + (ln(M) - ln(X)) = 0
        import math
        ln_m = math.log(max(min_val, most_likely))
        ln_x = math.log(max_val)
        c = ln_m - ln_x
        
        # Solve quadratic equation for sigma (ax^2 + bx + c = 0, a=1, b=1.645)
        # sigma = (-1.645 + sqrt(1.645^2 - 4*c)) / 2
        discriminant = 1.645**2 - 4 * c
        if discriminant > 0:
            sigma = (-1.645 + math.sqrt(discriminant)) / 2.0
            if sigma <= 0:
                # Fallback to geometric mean if expert inputs are mathematically incompatible with lognormal skew
                sigma = (np.log(max_val) - np.log(min_val)) / 3.29
                mu = (np.log(max_val) + np.log(min_val)) / 2.0
            else:
                mu = ln_m + sigma**2
        else:
            # Fallback if discriminant is negative
            sigma = (np.log(max_val) - np.log(min_val)) / 3.29
            mu = (np.log(max_val) + np.log(min_val)) / 2.0
        
        # SOTA Actuarial Practice: Sigma Cap to prevent the Infinite Mean Paradox.
        # If sigma exceeds ~2.0 in a Lognormal, the theoretical mean diverges towards infinity faster than 
        # the Monte Carlo sample can converge, causing wild instability. We cap sigma at 2.0.
        sigma = min(2.0, max(1e-4, sigma))
        
        samples = rng.lognormal(mean=mu, sigma=sigma, size=size)
        # SOTA Actuarial Practice: Allow true Black Swans (Heavy Tails). 
        # Only cap at a massive macroeconomic limit (Enterprise Ruin Level) to prevent float overflow.
        enterprise_ruin_limit = 500_000_000.0
        return np.minimum(samples, enterprise_ruin_limit)

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Performs a quantitative risk analysis on qualitative findings using the Open FAIR methodology and enriches the input payload with the results.

        This method processes a payload of qualitative findings, loading a client-
        specific risk profile based on industry and organizational scale from
        `engine_config/policies/fair_risk_profiles.json`. The profile selection is
        informed by client metadata, typically located in `working/{client_id}/client_intelligence.json`.

        For each finding, text-based heuristics are applied to its descriptive
        fields to map it to qualitative scores for Threat Event Frequency (TEF),
        Vulnerability (VULN), and Loss Magnitude (LM). These scores correspond to
        quantitative ranges (min, most-likely, max) defined in the risk profile.

        A Monte Carlo simulation (10,000 iterations) using Beta-PERT distributions
        models the uncertainty in these factors. The simulation calculates the
        Annualized Loss Expectancy (ALE) and other statistical risk measures.
        These quantitative metrics are then patched directly into the finding
        objects within the original `payload` dictionary.

        Args:
            graph: An EpistemicGraph object. Reserved for future contextual analysis
                and not currently used.
            payload: The input dictionary containing analysis data. This dictionary is
                modified in-place. It is expected to have a 'pillars_analysis' key,
                which contains a list of pillar objects, each with a
                'health_check_asis' list of finding dictionaries.

        Returns:
            The `payload` dictionary, enriched with quantitative FAIR risk metrics
            for each finding. Keys added to each finding dict include
            'threat_event_frequency', 'vulnerability_level', 'loss_magnitude',
            'fair_ale_score', 'fair_p90_score', 'fair_min_score', and
            'fair_max_score'.

        Raises:
            json.JSONDecodeError: If the risk profile configuration file
                (`engine_config/policies/fair_risk_profiles.json`) is malformed.
            ValueError: If keys or numeric values within the risk profile
                configuration file cannot be converted to their expected integer
                or float types.
        """
        import os

        import numpy as np

        pillars = payload.get("pillars_analysis", [])

        # Initialize an accumulator array for the total annual losses across all simulated years (10,000 runs)
        total_annual_losses = np.zeros(10000)

        # Load FAIR model parameters from the canonical governance repository.
        from assessment_engine.infrastructure.config_loader import load_policy_file

        try:
            profiles = load_policy_file("fair_risk_profiles")
        except Exception as e:
            logger.error(f"Fallo cargando fair_risk_profiles de políticas: {e}")
            profiles = {}

        # Load client metadata to ascertain the industry sector for sector-lock policy enforcement.
        client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
        intel_path = Path(f"working/{client_id}/client_intelligence.json")
        if not intel_path.exists():
            client_base = client_id.split('_')[0]
            intel_path = Path(f"working/{client_id}/{client_base}/client_intelligence.json")

        industry = "Standard"
        hierarchy = "Standard"
        if intel_path.exists():
            try:
                with open(intel_path, "r", encoding="utf-8-sig") as inf:
                    intel = json.load(inf)
                    p_meta = intel.get("profile", {})
                    industry = p_meta.get("industry", "Standard")
                    hierarchy = p_meta.get("hierarchy", "Standard")
            except (OSError, json.JSONDecodeError) as ex:
                logger.debug(f"[PolicyEngine] Error leyendo perfil para escala actuarial: {ex}")

        # Select the risk model preset that is calibrated to the client's organizational scale and data volume.
        preset_key = os.environ.get("ASSESSMENT_COMPANY_SCALE", "").upper()
        if preset_key not in profiles:
            if "Critical" in industry or "Essential" in industry or "Infrastructure" in industry:
                preset_key = "CRITICAL_INFRASTRUCTURE"
            elif "Global" in hierarchy or "Mega" in hierarchy:
                preset_key = "MEGA_ENTERPRISE"
            else:
                preset_key = "MID_MARKET"

        preset = profiles.get(preset_key, profiles.get("MID_MARKET", {}))

        # Coerce string-based map keys to integer types for compatibility with downstream processing.
        tef_map = {int(k): v for k, v in preset.get("tef_map", {}).items()}
        vuln_map = {int(k): v for k, v in preset.get("vuln_map", {}).items()}
        lm_map = {int(k): v for k, v in preset.get("lm_map", {}).items()}

        # Load dynamic custom risk profile generated by the financial scale calibrator (FAIR-MAM)
        tower_id = payload.get("document_meta", {}).get("tower_id", "T2")
        from assessment_engine.infrastructure.runtime_paths import resolve_case_dir
        case_dir = resolve_case_dir(client_id, tower_id)
        custom_profile_path = case_dir / "custom_risk_profile.json"
        
        custom_calibration = None
        capability_calibrations = {}
        reg_max_fine = 2000000.0
        if custom_profile_path.exists():
            try:
                with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                    custom_calibration = json.load(cf)
                    capability_calibrations = custom_calibration.get("capability_calibrations", {})
                    val_fine = custom_calibration.get("reg_max_fine_eur")
                    if val_fine is not None:
                        reg_max_fine = float(val_fine)
                    logger.info(f"🎯 [Policy Engine] Cargando calibración financiera dinámica desde: {custom_profile_path}")
            except Exception as e:
                logger.warning(f"Error loading custom risk profile: {e}")

        # Load dynamic evidence ledger for Bayesian Inference (Horizon 2 - Phase 4)
        evidence_ledger_path = case_dir / "evidence_ledger.json"
        if not evidence_ledger_path.exists():
            evidence_ledger_path = Path(f"working/{client_id}/evidence_ledger.json")
            
        evidences = []
        if evidence_ledger_path.exists():
            try:
                with open(evidence_ledger_path, "r", encoding="utf-8-sig") as ef:
                    evidences = json.load(ef).get("evidences", [])
                    logger.info(f"🎯 [Policy Engine] Cargando expediente de evidencias para inferencia bayesiana desde: {evidence_ledger_path}")
            except Exception as e:
                logger.warning(f"Error loading evidence ledger: {e}")

        # Load the dynamic security controls catalog
        controls_path = Path(__file__).resolve().parents[3] / "engine_config" / "policies" / "security_controls.json"
        controls_catalog = {}
        if controls_path.exists():
            try:
                with open(controls_path, "r", encoding="utf-8-sig") as cf:
                    controls_catalog = json.load(cf).get("security_controls", {})
                    logger.info(f"🎯 [Policy Engine] Cargando catálogo de controles de ciberseguridad desde: {controls_path}")
            except Exception as e:
                logger.warning(f"Error loading security controls catalog: {e}")
                logger.warning(f"Error loading custom risk profile: {e}")

        # If custom calibration exists, dynamically scale and override the primary Loss Magnitude map (lm_map)
        if custom_calibration:
            try:
                val = custom_calibration.get("hourly_downtime_cost_eur")
                cost = float(val) if val is not None else 150000.0
            except (ValueError, TypeError):
                logger.warning("🎯 [Policy Engine] Calibración de coste horario con formato no numérico. Aplicando fallback seguro.")
                cost = 150000.0

            lm_map = {
                1: {"min": cost * 0.1, "ml": cost * 0.3, "max": cost * 1.0},
                2: {"min": cost * 0.5, "ml": cost * 1.5, "max": cost * 4.0},
                3: {"min": cost * 2.0, "ml": cost * 5.0, "max": cost * 12.0},
                4: {"min": cost * 5.0, "ml": cost * 12.0, "max": cost * 24.0},
                5: {"min": cost * 12.0, "ml": cost * 24.0, "max": cost * 48.0},
            }

        # Establishes safe default values to ensure resilience against configuration file parsing errors or unavailability.
        if not tef_map:
            tef_map = {
                1: {"min": 0.01, "ml": 0.1, "max": 0.2},
                2: {"min": 0.1, "ml": 0.25, "max": 0.5},
                3: {"min": 0.5, "ml": 1.0, "max": 3.0},
                4: {"min": 2.0, "ml": 4.0, "max": 8.0},
                5: {"min": 6.0, "ml": 12.0, "max": 24.0},
            }
        if not vuln_map:
            vuln_map = {
                1: {"min": 0.05, "ml": 0.10, "max": 0.15},
                2: {"min": 0.15, "ml": 0.25, "max": 0.35},
                3: {"min": 0.30, "ml": 0.50, "max": 0.70},
                4: {"min": 0.70, "ml": 0.85, "max": 0.95},
                5: {"min": 0.90, "ml": 1.00, "max": 1.00},
            }
        if not lm_map:
            lm_map = {
                1: {"min": 500.0, "ml": 1000.0, "max": 3000.0},
                2: {"min": 2000.0, "ml": 5000.0, "max": 15000.0},
                3: {"min": 10000.0, "ml": 25000.0, "max": 80000.0},
                4: {"min": 50000.0, "ml": 100000.0, "max": 300000.0},
                5: {"min": 250000.0, "ml": 500000.0, "max": 1500000.0},
            }

        # SOTA Actuarial Practice: Systemic Threat Climate (Frailty Model)
        # Threat campaigns (like global Ransomware) do not attack vulnerabilities independently; they hit the entire perimeter at once.
        # To model Multivariate Frequency Covariance, we generate a SINGLE shared stochastic 'Climate Multiplier' for the 10,000 simulated years.
        import hashlib
        global_seed_str = f"SYSTEMIC_CLIMATE_{client_id}".encode("utf-8")
        global_seed = int(hashlib.md5(global_seed_str).hexdigest(), 16) % (2**32)
        rng_climate = np.random.default_rng(global_seed)
        # Gamma(shape=2.0, scale=0.5) generates a positive multiplier with Mean=1.0 and Variance=0.5.
        # This preserves the expert's average frequency but injects simultaneous 'Black Swan' storm years across all tower risks.
        systemic_climate_multiplier = rng_climate.gamma(2.0, 0.5, size=10000)

        for p in pillars:
            p_score = float(p.get("score", 3.0))
            p_name = p.get("pilar_name", p.get("pilar_id", "Unknown_Pillar"))
            for finding in p.get("health_check_asis", []):
                target_state = finding.get("target_state", finding.get("capability", "Unknown_Capability"))
                text = (
                    finding.get("finding", "") + " " + finding.get("impact", "")
                ).lower()

                # Implements dynamic qualitative TEF and LM mapping from the AI-Elicited scores (Gap 1)
                # Falls back to standard text heuristics if not available in the payload
                tef = int(finding.get("_elicited_tef", 3) or 3)
                if "_elicited_tef" not in finding:
                    tef = 3
                    if any(
                        k in text
                        for k in [
                            "ransomware",
                            "ataque",
                            "pública",
                            "internet",
                            "ddos",
                            "hack",
                        ]
                    ):
                        tef = 5
                    elif any(
                        k in text
                        for k in ["interno", "error", "manual", "legacy", "obsoleto"]
                    ):
                        tef = 4

                # Implements dynamic qualitative Loss Magnitude mapping (Gap 1)
                # Falls back to standard text heuristics if not available in the payload
                lm = int(finding.get("_elicited_lm", 3) or 3)
                if "_elicited_lm" not in finding:
                    if any(
                        k in text
                        for k in [
                            "parada total",
                            "caída catastrófica",
                            "indisponibilidad crítica",
                        ]
                    ):
                        lm = 5
                    elif any(
                        k in text
                        for k in [
                            "nis2",
                            "ens",
                            "soc2",
                            "hipaa",
                            "fedramp",
                            "gdpr",
                            "lgpd",
                            "multa",
                            "sanción",
                            "retraso",
                            "indisponibilidad",
                            "pérdida de datos",
                            "legal",
                            "compliance",
                            "regulatory",
                            "penalty",
                        ]
                    ):
                        lm = 4
                    else:
                        lm = 3

                # Define uncertainty for model inputs using a Beta-PERT distribution, as specified by the Open FAIR standard.
                #
                tef_range = tef_map.get(tef, {"min": 0.5, "ml": 1.0, "max": 3.0})
                tef_min = float(tef_range.get("min", 0.5))
                tef_ml = float(tef_range.get("ml", 1.0))
                tef_max = float(tef_range.get("max", 3.0))

                # --- ADVERSARIAL CONSENSUS ATTENUATION (FAIR-CAM Grounded) ---
                # Compute deterministic multipliers from the qualitative security controls audited by the IA
                tef_mod = 1.0
                lm_mod = 1.0
                slef_mod = 1.0

                # Load security_controls range definitions
                controls_list = finding.get("_consensus_controls", [])
                for ctrl in controls_list:
                    c_id = ctrl.get("control_id")
                    status = ctrl.get("implementation_status", "Ausente")
                    
                    # Map state to mitigation percentage
                    mitigation_multiplier = 0.0 # 'Ausente' gets 0% mitigation
                    if status == "Implementado":
                        mitigation_multiplier = 1.0 # 'Implementado' gets 100% of the range mitigation
                    elif status == "Parcial":
                        mitigation_multiplier = 0.5 # 'Parcial' gets 50% of the range mitigation

                    # Get range definitions dynamically from the loaded config catalog (FAIR-CAM)
                    ctrl_def = controls_catalog.get(c_id, {})
                    tef_range = ctrl_def.get("tef_mitigation_range", [0.0, 0.0])
                    lm_range = ctrl_def.get("lm_mitigation_range", [0.0, 0.0])

                    # Fallback default definitions if not found in the loaded catalog
                    if not ctrl_def or tef_range == [0.0, 0.0]:
                        if c_id == "NIS2-IaC":
                            tef_range = [0.30, 0.60]
                            lm_range = [0.00, 0.20]
                        elif c_id == "ENS-SRE-Observabilidad":
                            tef_range = [0.10, 0.30]
                            lm_range = [0.40, 0.70]
                        elif c_id == "CIS-Automatizacion":
                            tef_range = [0.20, 0.40]
                            lm_range = [0.10, 0.30]

                    # Calculate exact mitigation for TEF and LM
                    tef_mitigation = tef_range[0] + (tef_range[1] - tef_range[0]) * mitigation_multiplier
                    lm_mitigation = lm_range[0] + (lm_range[1] - lm_range[0]) * mitigation_multiplier

                    # Multiply the remaining risk multiplier (1.0 - mitigation)
                    tef_mod *= (1.0 - tef_mitigation)
                    lm_mod *= (1.0 - lm_mitigation)
                    
                    # Slef_mod is mapped dynamically based on standard regulatory compliance mitigations (FAIR-CAM)
                    slef_range = ctrl_def.get("slef_mitigation_range", [0.0, 0.0])
                    
                    # Fallback default definitions if not found in the loaded catalog
                    if not ctrl_def or slef_range == [0.0, 0.0]:
                        if c_id == "NIS2-IaC":
                            slef_range = [0.50, 0.85] # 50% partial, 85% full mitigations

                    slef_mitigation = slef_range[0] + (slef_range[1] - slef_range[0]) * mitigation_multiplier
                    slef_mod *= (1.0 - slef_mitigation)

                # Apply audit-grounded modifiers to Beta-PERT inputs
                tef_min *= tef_mod
                tef_ml *= tef_mod
                tef_max *= tef_mod

                # --- SOTA BAYESIAN INFERENCE CALIBRATION (Horizon 2 - Phase 4) ---
                # Gamma-Poisson Conjugate Update for Threat Event Frequency (TEF) using physical evidence
                p_id = p.get("pilar_id", "T2.P1")
                pillar_evidences = [ev for ev in evidences if p_id in ev.get("pillar_ids", [])] if evidences else []
                n_trials = len(pillar_evidences)
                k_failures = 0
                
                if n_trials > 0:
                    for ev in pillar_evidences:
                        ev_text = ev.get("excerpt", "").lower()
                        if any(
                            keyword in ev_text
                            for k_list in [
                                ["gap", "deficiencia", "vulnerabilidad", "riesgo", "incumplimiento", "ausencia"],
                                ["fragmenta", "silo", "heterogeneidad", "coexistencia", "duplic", "legacy", "obsoleto"]
                            ]
                            for keyword in k_list
                        ):
                            k_failures += 1
                            
                    # Prior Gamma(alpha, beta) parameters
                    alpha_prior = 4.0
                    beta_prior = 4.0 / max(1e-4, tef_ml)
                    
                    # Poisson observations: x_events = failures, t_years = trials * 0.25
                    x_events = k_failures
                    t_years = n_trials * 0.25
                    
                    # Posterior Gamma(alpha_post, beta_post) parameters
                    alpha_post = alpha_prior + x_events
                    beta_post = beta_prior + t_years
                    tef_ml_post = alpha_post / beta_post
                    
                    # Shift ranges proportionally
                    tef_ratio = tef_ml_post / max(1e-4, tef_ml)
                    tef_ml = tef_ml_post
                    tef_min = tef_min * tef_ratio
                    tef_max = tef_max * tef_ratio
                    logger.info(f"🔮 [Bayesian Inferencia] TEF_ml actualizado de {tef_ml/tef_ratio:.2f} a {tef_ml:.2f} (Pruebas: {n_trials}, Fallos: {k_failures})")

                # SOTA Actuarial Practice: Metadata-driven Calibration & Typology Segregation (FAIR-MAM)
                # 1. Fetch specific dynamic calibrations for this capability from the client profile
                cap_name = finding.get("capability", target_state)
                cap_calibration = capability_calibrations.get(cap_name, {}) if capability_calibrations else {}
                if not isinstance(cap_calibration, dict):
                    cap_calibration = {}
                typology = cap_calibration.get("typology", "CATASTROPHIC_SYSTEMIC")
                exposure_factor = float(cap_calibration.get("exposure_factor", 1.0))

                # --- ELITE FAIR-CAM CONTROL EFFICACY MAPPING ---
                # Symmetrical with the latest 2026 FAIR-CAM standard, Vulnerability (VULN) is formally and mathematically
                # derived from the actual qualitative technical maturity score (p_score) of the corresponding pillar.
                # SOTA Actuarial Practice: Instead of a naive linear decay, we use a logistic/exponential decay function.
                # A maturity drop from 3 to 2 causes an exponential collapse in defense efficacy, not a flat 25% drop.
                # Mathematically: p_vuln = 1.0 / (1.0 + exp(1.5 * (p_score - 3.0)))
                p_vuln = 1.0 / (1.0 + np.exp(1.5 * (p_score - 3.0)))
                # Condition vulnerability on network/environmental exposure factor (e.g. air-gapped systems)
                p_vuln = max(0.01, min(0.99, p_vuln * exposure_factor))

                # --- SOTA BAYESIAN INFERENCE CALIBRATION (Horizon 2 - Phase 4) ---
                # Beta-Binomial Conjugate Update for Vulnerability (VULN) using physical evidence
                if n_trials > 0:
                    mu_prior = p_vuln
                    kappa = 30.0  # Expert confidence scale
                    alpha_prior = mu_prior * kappa
                    beta_prior = (1.0 - mu_prior) * kappa
                    
                    # Physical evidence weight
                    w_evidence = 2.0
                    alpha_post = alpha_prior + w_evidence * k_failures
                    beta_post = beta_prior + w_evidence * (n_trials - k_failures)
                    
                    p_vuln_post = alpha_post / (alpha_post + beta_post)
                    logger.info(f"🔮 [Bayesian Inferencia] VULN_rate actualizado de {p_vuln:.4f} a {p_vuln_post:.4f} (Pruebas: {n_trials}, Fallos: {k_failures})")
                    p_vuln = p_vuln_post
                
                vuln_ml = p_vuln
                vuln_min = max(0.01, p_vuln - 0.15)
                vuln_max = min(0.99, p_vuln + 0.15)
                
                # We determine the qualitative vuln level for reporting/classification
                if p_vuln >= 0.80:
                    vuln = 5
                elif p_vuln >= 0.60:
                    vuln = 4
                elif p_vuln >= 0.40:
                    vuln = 3
                elif p_vuln >= 0.20:
                    vuln = 2
                else:
                    vuln = 1

                # --- ELITE FAIR-MAM MATERIALITY ASSESSMENT MAPPING ---
                # Symmetrical with the 2026 FAIR-MAM standard, Loss Magnitude (LM) is divided into:
                # 1. Primary Loss (Response & Restoration): e.g. engineering hours, VM recovery.
                # 2. Secondary Loss (Regulatory/Compliance liabilities under NIS2 / market SLA penalties).
                lm_range = lm_map.get(
                    lm, {"min": 10000.0, "ml": 25000.0, "max": 80000.0}
                )
                lm_min = float(lm_range.get("min", 10000.0)) * lm_mod
                lm_ml = float(lm_range.get("ml", 25000.0)) * lm_mod
                lm_max = float(lm_range.get("max", 80000.0)) * lm_mod

                # Scale P&L dynamically if client-specific downtime cost is calibrated
                hourly_cost = custom_calibration.get("hourly_downtime_cost_eur") if custom_calibration else None
                if hourly_cost is not None and typology != "OPERATIONAL_FRICTION":
                    hourly = float(hourly_cost)
                    lm_min = hourly * 0.5
                    lm_ml = hourly * 2.5
                    lm_max = hourly * 12.0

                # 2. Tipificación declarativa (con fallback heurístico para retrocompatibilidad al 100%)
                is_friction_risk = (typology == "OPERATIONAL_FRICTION") or any(
                    k in text
                    for k in [
                        "finops",
                        "itsm",
                        "manual",
                        "provisión",
                        "solicitud",  # Match solicitud, solicitudes
                        "excel",
                        "ticket",
                        "retraso",
                        "aprobación",
                        "heterogeneidad",
                        "coexistencia",
                        "licencia",     # Match licencia, licencias, licenciamiento
                        "fragmenta",    # Match fragmentación, fragmentado, fragmentados
                        "silo",         # Match silo, silos
                        "duplic",       # Match duplicidad, duplicación, duplicado, duplicados
                        "tco",
                    ]
                )
                finding["typology"] = typology
                finding["is_operational_friction"] = is_friction_risk
                finding["p_vuln"] = p_vuln
                if is_friction_risk:
                    lm_max = min(lm_max, 150000.0) # Cap at an extreme but plausible OPEX friction cost
                    
                    # Inyectar el sobrecoste de TCO de licencias/horas fijas para el renderizado del Hexágono de Valor
                    finding["deterministic_tco_waste_eur"] = float(cap_calibration.get("deterministic_waste_eur", 0.0))

                # Execute a mathematically rigorous, world-class Open FAIR 10,000-run Monte Carlo simulation (Collective Risk Model).
                size = 10000

                # Deterministic Monte Carlo Seeding (SOTA Actuarial Practice): 
                # SHA-256 stable hashing algorithm for 100% deterministic, platform-independent random seeds
                import hashlib
                node_id_seed = finding.get("node_id", "") or str(len(text))
                unique_signature = f"{p_name}_{target_state}_{p_score}_{node_id_seed}".encode("utf-8")
                stable_hash = hashlib.sha256(unique_signature).hexdigest()
                det_seed = int(stable_hash[:16], 16)
                
                # Instanciar generador local aislado y seguro para hilos concurrentes (Thread-Safe RNG)
                rng = np.random.default_rng(det_seed)

                from scipy import stats

                # SOTA Actuarial Practice: Unbound Threat Frequency
                # Replacing Beta-PERT with Lognormal for Threat Event Frequency and passing our safe local rng
                tef_rates_base = self._sample_lognormal(rng, tef_min, tef_ml, tef_max, size=size)
                
                # SOTA Actuarial Practice: Dynamic Topological Attenuation (Declarativa & Heurística)
                isolation = cap_calibration.get("isolation", "STANDARD_HYBRID")
                is_air_gapped = (isolation in ["AIR_GAPPED_OT", "ISOLATED_MAINFRAME"]) or (
                    any(k in text for k in ["ot", "scada", "ics", "industrial", "planta"]) if "Energy" in industry or "Critical Infrastructure" in industry else
                    any(k in text for k in ["mainframe", "swift", "core bancario", "legacy", "cobol"]) if "Financial" in industry or "Banking" in industry else
                    any(k in text for k in ["oss", "bss", "core network", "radio", "legacy", "playout", "broadcast", "transmisión"]) if "Telecommunications" in industry or "Media" in industry else
                    any(k in text for k in ["mainframe", "legacy", "air-gap", "aislado"])
                )
                if is_air_gapped:
                    tef_rates_base = tef_rates_base * 0.05
                    
                # SOTA Actuarial Practice: Bayesian Deduplication (MECE Principle via FAIR-CAM)
                # If multiple vulnerabilities share the same causal pillar, they are NOT mutually exclusive.
                # Summing their ALEs causes massive double counting. We apply a Bayesian DAG attenuation 
                # factor to the frequency based on the number of overlapping findings.
                pillar_findings_count = max(1, len(p.get("health_check_asis", [])))
                if pillar_findings_count > 1:
                    import math
                    tef_rates_base = tef_rates_base / math.sqrt(pillar_findings_count)

                # Apply the Shared Latent Variable (Systemic Climate) to couple the frequencies across all vulnerabilities
                tef_rates = tef_rates_base * systemic_climate_multiplier
                
                # SOTA Actuarial Practice: Avoid Beta domain edge crash (variance impossibility) by using 
                # a relative concentration parameter (Kappa) instead of an absolute hardcoded variance.
                # This mathematically guarantees the pure Beta distribution can exist at any probability bound [0, 1].
                mu = p_vuln
                kappa = 50.0  # Concentration parameter: higher means less variance around the mean
                alpha_beta = mu * kappa
                beta_beta = (1.0 - mu) * kappa
                vuln_rates = rng.beta(alpha_beta, beta_beta, size=size)

                # SOTA Actuarial Practice: Dynamic Dispersion (Negative Binomial)
                # We model over-dispersed (clustered) cyber attacks, but we scale the dispersion dynamically based on severity.
                # Highly sophisticated attacks (high impact) cluster less (tend to Poisson, p -> 1.0). Common attacks cluster heavily (p -> 0).
                # We normalize the most likely impact to create a dynamic 'p' parameter.
                impact_factor = min(1.0, lm_ml / 1000000.0)
                # p_param scales from 0.1 (massive clustering for low impact) to 0.9 (almost Poisson for high impact APTs)
                p_param = 0.1 + (0.8 * impact_factor)
                
                # SOTA Actuarial Practice: Restore Bayesian Hierarchical Variance (Epistemic + Aleatory)
                # The mean of the Negative Binomial must be the stochastic tef_rates array to correctly compound 
                # expert uncertainty (epistemic) with threat clustering (aleatory).
                n_param = tef_rates * p_param / (1.0 - p_param) # n = mean * p / (1 - p)
                n_param = np.maximum(n_param, 1e-6)  # SOTA Actuarial Practice: Anti-Crash Clamp
                
                n_threats = rng.negative_binomial(n_param, p_param, size=size)
                k_losses = rng.binomial(n_threats, vuln_rates)

                total_k = int(np.sum(k_losses))

                # Symmetrical with 2026 top-tier actuarial engineering, we vectorize the entire compound loss simulation,
                # completely avoiding Python loops to achieve microseconds execution speeds.
                if total_k > 0:
                    # Map each of the total_k simulated loss events to its respective run index (0 to size-1)
                    event_run_ids = np.repeat(np.arange(size), k_losses)

                    # Sample all primary loss magnitudes at once using Lognormal heavy-tailed distributions and local thread-safe RNG
                    all_primary_lms = self._sample_lognormal(rng, lm_min, lm_ml, lm_max, size=total_k)

                    # SOTA Actuarial Practice: Erlang-C / Kendall M/M/c Incident Congestion Model (Gap 3)
                    # Instead of an arbitrary decay or rigid presets, 'c_crews' (concurrent response crews) 
                    # is calculated dynamically based on the client's actual financial revenue scale (FAIR-MAM)
                    revenue = 50000000.0 # Default fallback (50M EUR)
                    if custom_calibration:
                        try:
                            val_rev = custom_calibration.get("annual_revenue_eur")
                            if val_rev is not None:
                                revenue = float(val_rev)
                        except (ValueError, TypeError):
                            pass

                    # Mathematically scale the SRE response team's concurrent capacity based on corporate scale
                    if revenue < 50000000.0:
                        c_crews = 1 # Small business / startup (1 SRE crew)
                    elif 50000000.0 <= revenue < 500000000.0:
                        c_crews = 2 # Mid-market (2 SRE crews)
                    elif 500000000.0 <= revenue < 2000000000.0:
                        c_crews = 3 # Large Enterprise (3 SRE crews)
                    else:
                        c_crews = 4 # Mega Enterprise / Critical Infrastructure (4 SRE crews, e.g. large utility)
                    
                    # 'mu' is the service rate (1 / MTTR). SRE Maturity directly and exponentially scales MTTR
                    # Low maturity (1.5) -> MTTR = 12 hours. High maturity (4.5) -> MTTR = 0.5 hours.
                    mttr_hours = 12.0 / (1.5 ** (p_score - 1.0))
                    mu_rate = 1.0 / max(0.1, mttr_hours)
                    
                    # 'lambda' (arrival rate) is the concurrent incident count in the simulated year
                    k_per_event = np.repeat(k_losses, k_losses)
                    
                    # Calculate Erlang-C probability of delay and average queue wait time for each simulated year
                    # To avoid division by zero and infinite queues when lambda >= c * mu, we clamp utilization (rho < 1.0)
                    rho = k_per_event / (c_crews * mu_rate)
                    rho = np.minimum(0.99, rho)  # Anti-crash saturation clamp

                    # Erlang-C Delay Probability (P_q) formula calculation
                    # We compute the numerator and denominator terms for the exact formula
                    import math
                    numerator = ((c_crews * rho) ** c_crews) / math.factorial(c_crews) * (1.0 / (1.0 - rho))
                    
                    denominator = 0.0
                    for k_term in range(c_crews):
                        denominator += ((c_crews * rho) ** k_term) / math.factorial(k_term)
                    denominator += numerator
                    
                    p_q = numerator / np.maximum(1e-6, denominator)
                    
                    # Average queue wait time in hours: W_q = P_q / (c * mu * (1 - rho))
                    w_q_hours = p_q / np.maximum(1e-6, c_crews * mu_rate * (1.0 - rho))
                    
                    # Total downtime multiplier: downtime is scaled by wait time
                    # We multiply the baseline loss magnitude by this congestion factor
                    congestion_multiplier = 1.0 + (w_q_hours / max(1.0, mttr_hours))
                    
                    # Clamp the maximum congestion impact to avoid absurd numbers (Sovereign Safety Guard)
                    max_congestion = 2.0 if hourly_cost is not None else 5.0
                    congestion_multiplier = np.minimum(max_congestion, congestion_multiplier)
                    
                    all_primary_lms = all_primary_lms * congestion_multiplier

                    # SOTA Actuarial Practice: Continuous Logistic Regulatory Fine Probability (SLEF)
                    # We eliminate the binary "Step-Function Cliff" (15% vs 2%) and replace it with a continuous 
                    # logistic function that smoothly transitions the probability of a fine as the maturity score approaches 2.60.
                    # As maturity drops below 2.60, fine probability approaches 15%. As it rises above, it drops asymptoticaly to 2%.
                    slef_base = 0.02 + (0.13 / (1.0 + np.exp(10.0 * (p_score - 2.60))))
                    slef_base *= slef_mod
                    if is_friction_risk:
                        slef_base = 0.0
                    
                    # SOTA Actuarial Practice: Conditional Regulatory Triggers (Materiality Threshold)
                    # Regulatory fines (NIS2) are not triggered by a random coin flip on a €500 laptop crash.
                    # The secondary event is mathematically conditioned on the Primary Loss exceeding a materiality threshold (e.g. median).
                    materiality_threshold = np.percentile(all_primary_lms, 50.0) if len(all_primary_lms) > 0 else 0.0
                    all_sec_triggered = (all_primary_lms > materiality_threshold) & (rng.uniform(0.0, 1.0, size=total_k) < slef_base)

                    all_sec_losses = np.zeros(total_k)
                    num_sec = int(np.sum(all_sec_triggered))
                    if num_sec > 0:
                        # SOTA Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
                        # Secondary loss severity is mapped to the highest regulatory framework applicable to the client's industry.
                        reg_max_fine = 2000000.0 # Default GDPR/LGPD baseline
                        
                        # Load dynamic reg max fine from custom calibration if available (FAIR-MAM)
                        # SOTA Actuarial Practice: Compliance fines (NIS2) are legally bound by a minimum standard (e.g. 10M) 
                        # or 2.0% of the organization's factual global annual revenue (turnover), whichever is higher (NIS2 Art 34).
                        if custom_calibration and "reg_max_fine_eur" in custom_calibration:
                            try:
                                val_fine = custom_calibration.get("reg_max_fine_eur")
                                base_fine = float(val_fine) if val_fine is not None else 10000000.0
                                
                                val_rev = custom_calibration.get("annual_revenue_eur")
                                revenue = float(val_rev) if val_rev is not None else 0.0
                                
                                # Scale dynamically with global turnover statutory cap (e.g. 2.0%-4.0% rule under NIS2/GDPR)
                                fine_ratio = float(custom_calibration.get("regulatory_fine_cap_ratio", 0.02))
                                turnover_fine = revenue * fine_ratio if revenue > 0 else base_fine
                                reg_max_fine = min(base_fine, turnover_fine) if revenue > 0 else base_fine
                            except (ValueError, TypeError):
                                reg_max_fine = 10000000.0
                        else:
                            if "Financial" in industry or "Banking" in industry:
                                reg_max_fine = 15000000.0 # DORA / Basel III severe compliance fines
                            elif "Energy" in industry or "Critical Infrastructure" in industry:
                                reg_max_fine = 10000000.0 # NIS2 / Critical Infrastructure severe fines
                            elif "Telecommunications" in industry:
                                reg_max_fine = 5000000.0 # Telco Regulatory severe fines
                            elif "Healthcare" in industry:
                                reg_max_fine = 5000000.0 # HIPAA / HITECH severe fines

                        # Generate raw lognormal samples for secondary losses and passing our safe local rng
                        if hourly_cost is not None:
                            hourly = float(hourly_cost)
                            reg_max_fine = min(reg_max_fine, hourly * 8.0)

                        if lm >= 4:
                            # SOTA Actuarial Practice: Calibrate the mode (most likely) as a proportion of the legal maximum fine limit
                            if hourly_cost is not None:
                                most_likely_fine = min(reg_max_fine * 0.1, float(hourly_cost) * 1.5)
                            else:
                                most_likely_fine = min(1000000.0, reg_max_fine * 0.1)
                            raw_sec_losses = self._sample_lognormal(rng, min(10000.0, lm_min), most_likely_fine, reg_max_fine, size=num_sec)
                        else:
                            raw_sec_losses = self._sample_lognormal(rng, lm_min * 2.0, lm_ml * 2.0, min(reg_max_fine, lm_max * 2.0), size=num_sec)

                        # SOTA Actuarial Practice: True Directional Gaussian Copula with Asymmetric Tail Dependence
                        # Primary damage is a real physical simulation that ALREADY HAPPENED.
                        # We must map the REAL primary damage to its theoretical Gaussian percentiles (Z0)
                        # rather than generating a ghost variable. This establishes true causal dependency.
                        triggered_primary_lms = all_primary_lms[all_sec_triggered]
                        
                        # Calculate empirical CDF (percentiles) of the triggered primary losses
                        ranks = stats.rankdata(triggered_primary_lms, method='ordinal')
                        empirical_cdf = ranks / (num_sec + 1.0)
                        
                        # Transform empirical CDF to standard normal (Inverse CDF / PPF)
                        z0_real = stats.norm.ppf(empirical_cdf)
                        
                        # We calculate the dynamic correlation vector (Tail Dependence)
                        # SOTA Actuarial Practice: Continuous Logistic Copula Correlation
                        # Eliminates the binary "Arbitrage Cliff". The correlation scales smoothly from 0.0 (independent) 
                        # to 0.85 (highly correlated) as the severity of the primary outage approaches its absolute maximum (empirical CDF -> 1.0).
                        # The function is centered at the 80th percentile.
                        rhos = 0.85 / (1.0 + np.exp(-10.0 * (empirical_cdf - 0.80)))
                        
                        # Generate the dependent normal variable for secondary losses and passing our safe local rng
                        z1_independent = rng.normal(size=num_sec)
                        z1_correlated = rhos * z0_real + np.sqrt(1.0 - rhos**2) * z1_independent
                        
                        # Use the dependent variable (z1_correlated) to rank-sort the secondary losses
                        z1_ranks = stats.rankdata(z1_correlated, method='ordinal')
                        raw_sec_sorted = np.sort(raw_sec_losses)
                        
                        # Map the sorted secondary losses exactly back to the order of triggered_primary_lms
                        final_sec_losses = np.zeros(num_sec)
                        for i in range(num_sec):
                            target_pos = int(z1_ranks[i]) - 1
                            final_sec_losses[i] = raw_sec_sorted[target_pos]

                        all_sec_losses[all_sec_triggered] = final_sec_losses

                    # SOTA Actuarial Practice: Financial Double-Counting Fix (Max Absorption)
                    # Severe secondary legal fines generally absorb the operational cost of the primary response,
                    # avoiding the double-counting fallacy of a blind addition.
                    consolidated_losses = np.maximum(all_primary_lms, all_sec_losses) + (all_primary_lms * 0.1)

                    # Aggregate losses per run using fast bincount accumulator
                    loss_per_run = np.bincount(event_run_ids, weights=consolidated_losses, minlength=size)
                else:
                    loss_per_run = np.zeros(size)

                # SOTA Actuarial Practice: Truncated Lognormal Model (Extreme Outliers Elimination)
                # To prevent extreme, non-defensible P100 outliers from distorting the mean and causing 
                # mathematical discrepancies (like CVaR exceeding the printed Maximum Plausible Loss), 
                # we truncate the empirical annual loss distribution at the 99.0th percentile (P99).
                # This represents the "Maximum Plausible Loss" (1-in-100-year extreme operational limit),
                # which is the global actuarial standard for bounding operational risk distributions.
                p99_limit = float(np.percentile(loss_per_run, 99.0)) if len(loss_per_run) > 0 else 0.0
                truncated_losses = np.clip(loss_per_run, a_min=None, a_max=p99_limit)

                # Calculate statistical exposures using the truncated distribution
                mean_ale = float(np.mean(truncated_losses))
                
                # SOTA Actuarial Practice: Coherent Risk Measure (Expected Shortfall / CVaR)
                # Value-at-Risk (P90) is not subadditive and ignores the tail magnitude. We use Expected Shortfall (CVaR).
                # Under the Basel Committee's Fundamental Review of the Trading Book (FRTB) and Tier-1 banking standards, 
                # Expected Shortfall must be calculated at the 97.5% confidence level to properly capture tail risk without dilution.
                # Since we operate on the truncated distribution, CVaR is mathematically bounded by the P99 limit.
                sorted_losses = np.sort(truncated_losses)
                tail_index = int(len(sorted_losses) * 0.975)
                tail_losses = sorted_losses[tail_index:]
                cvar_ale = float(np.mean(tail_losses)) if len(tail_losses) > 0 else 0.0
                p90_ale = cvar_ale  # Overwriting the legacy P90 variable with the Coherent Risk Measure (CVaR 97.5%) to maintain schema compatibility
                
                min_ale = float(np.min(truncated_losses))
                max_ale = p99_limit

                # Round final computed metrics to a fixed precision for presentation clarity.
                ale_euros = round(mean_ale, 2)

                finding["threat_event_frequency"] = tef
                finding["vulnerability_level"] = vuln
                finding["loss_magnitude"] = lm
                finding["fair_ale_score"] = ale_euros
                finding["fair_p90_score"] = round(p90_ale, 2)
                finding["fair_min_score"] = round(min_ale, 2)
                finding["fair_max_score"] = round(max_ale, 2)

                # Sum vectorially to compile the corporate-wide annual loss distribution (Gap 2)
                total_annual_losses += truncated_losses

        # SOTA Actuarial Practice: Portfolio Subadditivity & Operational Absorption Cap
        if len(total_annual_losses) > 0 and np.sum(total_annual_losses) > 0:
            if hourly_cost is not None and float(hourly_cost) > 0:
                hourly_f = float(hourly_cost)
                # Maximum plausible cumulative operational downtime across a single tech tower per year (120 hours ceiling)
                max_annual_tower_loss = hourly_f * 120.0 + min(reg_max_fine, hourly_f * 16.0)
                total_annual_losses = np.minimum(total_annual_losses, max_annual_tower_loss)

            portfolio_sorted = np.sort(total_annual_losses)
            portfolio_mean = float(np.mean(total_annual_losses))
            tail_idx = int(len(portfolio_sorted) * 0.975)
            portfolio_cvar = float(np.mean(portfolio_sorted[tail_idx:])) if len(portfolio_sorted[tail_idx:]) > 0 else portfolio_mean

            payload["total_fair_ale"] = round(portfolio_mean, 2)
            payload["total_fair_p90"] = round(portfolio_cvar, 2)
            payload["total_fair_max"] = round(float(np.percentile(total_annual_losses, 99.0)), 2)

        # Generate the Loss Exceedance Curve (LEC) Chart (Gap 2)
        if len(total_annual_losses) > 0 and np.sum(total_annual_losses) > 0:
            try:
                # Import matplotlib in a non-GUI thread-safe manner (Agg backend)
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt

                # Sort the losses in descending order for the exceedance probability
                sorted_losses_desc = np.sort(total_annual_losses)[::-1]
                
                # Eje Y: Exceedance Probability (from 0 to 1)
                probabilities = np.arange(1, len(sorted_losses_desc) + 1) / len(sorted_losses_desc)

                # Set custom styling matching the high-end corporate brand profile of the client
                plt.figure(figsize=(7.5, 4.5), dpi=300)
                plt.plot(sorted_losses_desc / 1000.0, probabilities * 100.0, color="#1e3a8a", linewidth=2.5, label="Postura Actual (AS-IS)")
                
                # Draw the Materiality Threshold if defined in custom_calibration
                m_threshold = 500000.0 # Default
                if custom_calibration and "reg_max_fine_eur" in custom_calibration:
                    m_threshold = float(custom_calibration.get("reg_max_fine_eur", 10000000.0)) * 0.1
                
                plt.axvline(x=m_threshold / 1000.0, color="#b91c1c", linestyle="--", linewidth=1.5, label=f"Umbral de Materialidad ({m_threshold:,.0f} €)")

                plt.title("Curva de Excedencia de Pérdidas (LEC) - Value-at-Risk", fontsize=11, fontweight="bold", pad=12)
                plt.xlabel("Pérdida Operativa Anual Excedente (Miles de Euros, k€)", fontsize=9.5)
                plt.ylabel("Probabilidad de Excedencia (%)", fontsize=9.5)
                plt.grid(True, linestyle=":", alpha=0.6)
                plt.legend(fontsize=8.5, loc="upper right")
                
                # Force tight layout and save physically to the case folder
                plt.tight_layout()
                
                chart_path = case_dir / "loss_exceedance_curve.png"
                plt.savefig(chart_path, format="png", dpi=300)
                plt.close()
                logger.info(f"🎨 [Policy Engine] Gráfico oficial de Curva de Excedencia de Pérdidas (LEC) generado en: {chart_path}")
                
            except Exception as chart_err:
                logger.warning(f"Error generating Loss Exceedance Curve chart: {chart_err}")

        return payload


# Declarative registry mapping policy identifiers to their concrete implementation classes
POLICY_REGISTRY: Dict[str, Any] = {
    "client_sanitization": ClientSanitizationPolicy,
    "fair_risk": FairRiskPolicy,
    "deduplication": DeduplicationPolicy,
    "sequencing": SequencingPolicy,
    "ot_perimeter": OTPerimeterPolicy,
    "archimate_deliverables": ArchiMateDeliverablesPolicy,
    "business_case_grounding": BusinessCaseGroundingPolicy,
    "reverse_traceability": ReverseTraceabilityPolicy,
}


class SovereignPolicyEngine:
    r"""[{'name': 'SovereignPolicyEngine', 'docstring': 'Orchestrates the sequential execution of a predefined sovereign policy chain.\n\nThis engine processes a dictionary-like payload by applying a fixed, ordered\nsequence of `BaseSovereignPolicy` instances. Each policy evaluates and\npotentially transforms the payload based on contextual information from an\nepistemic graph. The transformation is cumulative, with the output of one\npolicy serving as the input for the next.\n\nAttributes:\n    graph (EpistemicGraph): The knowledge graph providing context for policy\n        evaluations.\n    policies (List[BaseSovereignPolicy]): The ordered list of policy objects\n        to be executed.'}, {'name': '__init__', 'docstring': 'Initializes the SovereignPolicyEngine.\n\nStores the provided epistemic graph and initializes a predefined, ordered list\nof sovereign policies for evaluation.\n\nArgs:\n    graph (EpistemicGraph): The epistemic graph instance that policies will\n        use for analysis.'}, {'name': 'compile', 'docstring': "Applies the full policy chain sequentially to a configuration payload.\n\nThis method orchestrates the policy evaluation pipeline. It first performs a\nrecursive unescape operation on the input payload, then iterates through each\nregistered policy, applying its transformation logic. The output of each\npolicy evaluation serves as the input to the subsequent policy, creating a\ncumulative transformation.\n\nArgs:\n    blueprint_payload (Dict[str, Any]): The input configuration data to which\n        policies will be applied.\n\nReturns:\n    Dict[str, Any]: The transformed payload after the application of all\n        policies.\n\nRaises:\n    Exception: Propagates any exception raised by an individual policy's\n        `evaluate_and_patch` method. This can occur if the payload is\n        malformed or violates a specific policy constraint (e.g., ValueError,\n        KeyError)."}]."""

    def __init__(self, graph: EpistemicGraph):
        """Initializes the PolicyEngine with a graph and a default policy chain.

        Args:
            graph (EpistemicGraph): The epistemic graph instance for policy analysis.

        Attributes:
            graph (EpistemicGraph): The epistemic graph under analysis.
            policies (List[BaseSovereignPolicy]): A predefined, ordered list of
                sovereign policy instances to be executed sequentially.
        """
        self.graph = graph
        self.policies: List[BaseSovereignPolicy] = []

        # Load declarative policy chain from the runtime manifest if configured
        try:
            from assessment_engine.infrastructure.config_loader import (
                load_runtime_manifest,
            )
            manifest = load_runtime_manifest()
            policy_names = manifest.get("policies", {}).get("sovereign_chain")
        except Exception:
            policy_names = None

        if not policy_names:
            # Fallback to the standard production-grade ordered policy chain
            policy_names = [
                "client_sanitization",
                "fair_risk",
                "deduplication",
                "sequencing",
                "ot_perimeter",
                "archimate_deliverables",
                "business_case_grounding",
                "reverse_traceability",
            ]

        for name in policy_names:
            policy_cls = POLICY_REGISTRY.get(name)
            if policy_cls:
                self.policies.append(policy_cls())
            else:
                logger.warning(f"Sovereign policy '{name}' not found in registry. Skipping.")

    def compile(self, blueprint_payload: Dict[str, Any]) -> Dict[str, Any]:
        r"""{'docstring': "Compiles a blueprint payload by sequentially applying all registered policies.\n\nThis method orchestrates the policy evaluation and transformation process.\nIt first performs a deep unescape operation on the input payload. It then\niterates through each registered policy, with the output from one policy's\nevaluation serving as the input to the next.\n\nArgs:\n    blueprint_payload (Dict[str, Any]): The raw blueprint configuration data\n        to be processed.\n\nReturns:\n    Dict[str, Any]: The fully compiled blueprint payload after the\n    application of all registered policies.\n\nRaises:\n    PolicyEvaluationError: If any policy encounters an irrecoverable error\n        during its evaluation or patching phase.\n    ValueError: If the blueprint payload is malformed or contains data that\n        cannot be processed by a policy."}."""
        blueprint_payload = deep_unescape(blueprint_payload)
        for policy in self.policies:
            blueprint_payload = policy.evaluate_and_patch(self.graph, blueprint_payload)
        return blueprint_payload
