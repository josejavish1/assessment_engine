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
        falling back to a default value of 'REDEIA' if this key path is absent.

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
        client_name = payload.get("document_meta", {}).get("client_name", "REDEIA")

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
            # Implements a security fallback to prevent execution failure in CI/CD environments.
            # Reads from brand profile configuration first (declarative, elite approach)
            try:
                from assessment_engine.infrastructure.config_loader import load_brand_profile
                brand_profile = load_brand_profile()
                is_critical = brand_profile.get("styling", {}).get("is_critical", False)
                if is_critical:
                    industry = "Critical Infrastructure"
            except Exception:
                pass

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
                "ENS/NIS2" if doc_lang == "es" else "applicable regulatory frameworks"
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
    """Generate random samples from a Beta-PERT distribution defined by minimum, most likely, and maximum values."""

    def _sample_pert(
        self, min_val: float, most_likely: float, max_val: float, size: int = 10000
    ) -> Any:
        import numpy as np

        range_val = max_val - min_val
        alpha = 1.0 + 4.0 * (most_likely - min_val) / range_val
        beta_val = 1.0 + 4.0 * (max_val - most_likely) / range_val
        return min_val + np.random.beta(alpha, beta_val, size=size) * range_val

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

        # Load FAIR model parameters from the canonical governance repository.
        from assessment_engine.infrastructure.config_loader import load_policy_file

        try:
            profiles = load_policy_file("fair_risk_profiles")
        except Exception as e:
            logger.error(f"Fallo cargando fair_risk_profiles de políticas: {e}")
            profiles = {}

        # Load client metadata to ascertain the industry sector for sector-lock policy enforcement.
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

        # Select the risk model preset that is calibrated to the client's organizational scale and data volume.
        preset_key = "MID_MARKET"
        if "Critical Infrastructure" in industry or "Energy" in industry:
            preset_key = "CRITICAL_INFRASTRUCTURE"
        elif "Global" in hierarchy or "Mega" in hierarchy:
            preset_key = "MEGA_ENTERPRISE"

        preset = profiles.get(preset_key, profiles.get("MID_MARKET", {}))

        # Coerce string-based map keys to integer types for compatibility with downstream processing.
        tef_map = {int(k): v for k, v in preset.get("tef_map", {}).items()}
        vuln_map = {int(k): v for k, v in preset.get("vuln_map", {}).items()}
        lm_map = {int(k): v for k, v in preset.get("lm_map", {}).items()}

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

        for p in pillars:
            for finding in p.get("health_check_asis", []):
                text = (
                    finding.get("finding", "") + " " + finding.get("impact", "")
                ).lower()

                # Implements heuristics for mapping qualitative Threat Event Frequency (TEF) ratings (1-5) to quantitative annualized ranges.
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

                # Implements heuristics for mapping qualitative Vulnerability ratings (1-5) to quantitative probability ranges.
                vuln = 3
                if any(
                    k in text
                    for k in [
                        "sin parchear",
                        "sin soporte",
                        "crítico",
                        "vulnerabilidad",
                    ]
                ):
                    vuln = 5
                elif any(
                    k in text for k in ["manual", "falta", "ausencia", "carencia"]
                ):
                    vuln = 4

                # Implements heuristics for mapping qualitative Loss Magnitude (1-5) to quantitative monetary ranges, compliant with international regulatory sanitization rule #4.
                lm = 3
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

                # Define uncertainty for model inputs using a Beta-PERT distribution, as specified by the Open FAIR standard.
                #
                tef_range = tef_map.get(tef, {"min": 0.5, "ml": 1.0, "max": 3.0})
                tef_min = float(tef_range.get("min", 0.5))
                tef_ml = float(tef_range.get("ml", 1.0))
                tef_max = float(tef_range.get("max", 3.0))

                #
                vuln_range = vuln_map.get(vuln, {"min": 0.3, "ml": 0.5, "max": 0.7})
                vuln_min = float(vuln_range.get("min", 0.3))
                vuln_ml = float(vuln_range.get("ml", 0.5))
                vuln_max = float(vuln_range.get("max", 0.7))

                #
                lm_range = lm_map.get(
                    lm, {"min": 10000.0, "ml": 25000.0, "max": 80000.0}
                )
                lm_min = float(lm_range.get("min", 10000.0))
                lm_ml = float(lm_range.get("ml", 25000.0))
                lm_max = float(lm_range.get("max", 80000.0))

                # Execute a 10,000-iteration Monte Carlo simulation to model the loss exposure distribution.
                size = 10000
                tef_samples = self._sample_pert(tef_min, tef_ml, tef_max, size=size)
                vuln_samples = self._sample_pert(vuln_min, vuln_ml, vuln_max, size=size)
                lm_samples = self._sample_pert(lm_min, lm_ml, lm_max, size=size)

                # Models the materialization of a threat event within a one-year period as a Bernoulli trial.
                U = np.random.uniform(0.0, 1.0, size=size)
                losses_occurred = U < vuln_samples

                # Annualized loss is computed as a function of threat event frequency and probable loss magnitude.
                loss_per_run = np.where(losses_occurred, tef_samples * lm_samples, 0.0)

                #
                mean_ale = float(np.mean(loss_per_run))
                p90_ale = float(np.percentile(loss_per_run, 90.0))
                min_ale = float(np.min(loss_per_run))
                max_ale = float(np.max(loss_per_run))

                # Round final computed metrics to a fixed precision for presentation clarity.
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
        self.policies: List[BaseSovereignPolicy] = [
            ClientSanitizationPolicy(),
            FairRiskPolicy(),
            DeduplicationPolicy(),
            SequencingPolicy(),
            OTPerimeterPolicy(),
            ArchiMateDeliverablesPolicy(),
            BusinessCaseGroundingPolicy(),
            ReverseTraceabilityPolicy(),
        ]

    def compile(self, blueprint_payload: Dict[str, Any]) -> Dict[str, Any]:
        r"""{'docstring': "Compiles a blueprint payload by sequentially applying all registered policies.\n\nThis method orchestrates the policy evaluation and transformation process.\nIt first performs a deep unescape operation on the input payload. It then\niterates through each registered policy, with the output from one policy's\nevaluation serving as the input to the next.\n\nArgs:\n    blueprint_payload (Dict[str, Any]): The raw blueprint configuration data\n        to be processed.\n\nReturns:\n    Dict[str, Any]: The fully compiled blueprint payload after the\n    application of all registered policies.\n\nRaises:\n    PolicyEvaluationError: If any policy encounters an irrecoverable error\n        during its evaluation or patching phase.\n    ValueError: If the blueprint payload is malformed or contains data that\n        cannot be processed by a policy."}."""
        blueprint_payload = deep_unescape(blueprint_payload)
        for policy in self.policies:
            blueprint_payload = policy.evaluate_and_patch(self.graph, blueprint_payload)
        return blueprint_payload
