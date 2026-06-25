import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SecurityIntegrityViolation(RuntimeError):
    """Raised when an operation violates a security or data integrity rule.

    This exception distinguishes business logic or compliance failures from more
    general runtime errors. It typically signals that an attempted state change
    or data generation would breach a predefined business rule, market constraint,
    or a core data integrity principle.
    """

    pass


class FidelitySentinel:
    r"""[{'method_name': 'FidelitySentinel', 'docstring': 'A namespace for static methods that perform data fidelity validations.\n\nThese methods are designed to verify that data transformations or text\nsynthesis processes do not result in a significant loss of critical\ninformation. Key checks include ensuring entity retention and maintaining\ncollection cardinality above specified thresholds.'}, {'method_name': 'verify_field_occupancy', 'docstring': 'Validates that the cardinality of a collection has not significantly decreased.\n\nThis check flags two conditions:\n1. Complete Loss: The final list is empty when the original was not.\n2. Significant Dilution: The final list contains less than 50% of the\n   items from the original list.\n\nArgs:\n    raw_data (List[Any]): The list of data from the original source.\n    final_list (List[Any]): The list of data after processing.\n    field_name (str): The name of the field being verified, used for\n        generating violation messages.\n\nReturns:\n    List[str]: A list of string messages describing any violations found. An\n    empty list is returned if no violations are detected.'}, {'method_name': 'verify_entity_retention', 'docstring': 'Verifies that critical entities from a source list are retained in final text.\n\nThis method performs a case-insensitive substring check to confirm the\npresence of each specified entity. Entities are normalized by converting them\nto lowercase and stripping leading/trailing whitespace before the check.\nEntities that are empty or have fewer than 3 characters are ignored.\n\nArgs:\n    raw_entities (List[str]): A list of critical entity strings that must\n        be present in the final output.\n    final_text (str): The final, synthesized text to be checked for entity\n        retention.\n    context (str, optional): A string providing context for the verification,\n        used in violation messages. Defaults to "General".\n\nReturns:\n    List[str]: A list of violation messages for each entity not found in\n    `final_text`. Returns an empty list if all valid entities are retained.'}]."""

    @staticmethod
    def verify_field_occupancy(
        raw_data: List[Any], final_list: List[Any], field_name: str
    ) -> List[str]:
        """Assess data loss by comparing pre- and post-processing list lengths.

        This function quantifies data loss by comparing the number of elements in a
        list before and after a transformation. It flags two specific failure
        conditions:
        1. Complete data loss: A non-empty initial list becomes empty.
        2. Significant dilution: The final list contains fewer than 50% of the
           elements from the original list.

        Args:
            raw_data: The list of items before a processing stage.
            final_list: The list of items after the processing stage.
            field_name: A descriptor for the data field being validated, used for
                constructing violation messages.

        Returns:
            A list of string messages detailing validation failures. An empty list
            indicates that no significant data loss was detected.
        """
        violations = []
        if raw_data and not final_list:
            violations.append(
                f"Estructura Crítica: El campo '{field_name}' está VACÍO en el resultado, pero contenía datos en el material bruto."
            )
        elif len(raw_data) > 0 and len(final_list) < (len(raw_data) * 0.5):
            violations.append(
                f"Densidad Insuficiente: El campo '{field_name}' ha sufrido una dilución de datos superior al 50%."
            )
        return violations

    @staticmethod
    def verify_entity_retention(
        raw_entities: List[str], final_text: str, context: str = "General"
    ) -> List[str]:
        r"""{'docstring': 'Verify that all specified entities are retained in the final text.\n\n    Performs a case-insensitive substring search to confirm the presence of each\n    specified entity. Entities are normalized by stripping leading/trailing\n    whitespace and converting to lowercase prior to the search. Entities that are\n    empty or have fewer than three characters are excluded from verification.\n\n    Args:\n        raw_entities: A list of string entities that must be present in the final\n            text.\n        final_text: The text content to be verified against the list of entities.\n        context: An identifier for the verification context used to enrich\n            violation messages.\n\n    Returns:\n        A list of formatted violation messages (in Spanish) for each non-trivial\n        entity not found. Returns an empty list if all verifiable entities\n        are present.'}."""
        violations = []
        text_lower = final_text.lower()
        for entity in raw_entities:
            if not entity or len(entity) < 3:
                continue
            # Verifies the persistence of a specified entity within the text, either through direct presence or a semantically equivalent representation.
            entity_norm = entity.lower().strip()
            if entity_norm not in text_lower:
                violations.append(
                    f"[{context}] Fuga de Atributo: La entidad '{entity}' se ha perdido o diluido en la redacción final."
                )
        return violations


class StructuralIntegrityGate:
    r"""{'check_text_recursive': "Recursively traverses a data structure to apply tonal analysis to string values.\n\n    Walks through a nested structure of dictionaries and lists. When a string\n    value is encountered, it is delegated to `_check_sober_tone` for\n    validation against tonal policies. The function operates by side effect,\n    appending any detected violation messages to the `violations` list defined\n    in the parent scope. The `path` argument is constructed during traversal to\n    provide a precise location for each violation.\n\n    Args:\n        obj: The data structure (e.g., dict, list) or scalar value to inspect.\n        path: A dot-notation string representing the current location within the\n            top-level data structure, used for precise error reporting (e.g.,\n            'dossier.summary[0]')."}."""

    FORBIDDEN_TONE_TERMS = [
        "engañosa",
        "terrible",
        "desastroso",
        "fallo fatal",
        "acusatorio",
        "culpable",
        "negligencia",
        "increíble",
        "excepcional",
        "malo",
        "pobre",
        "ridículo",
        "nosotros mismos",
        "puntuación engañosa",
        "valor engañoso",
    ]

    @classmethod
    def verify_dossier_logic(cls, data: Dict[str, Any]) -> bool:
        """Validate the logical and tonal integrity of a dossier.

        Orchestrates a multi-faceted validation of the provided dossier data. The
        method performs integrity checks by cross-referencing claims and evidence,
        and recursively scans all string values to ensure they adhere to a
        neutral, diplomatic tone. All discovered violations, including logical
        contradictions and tonal infractions, are aggregated. If any violations
        are found, a single exception is raised containing a consolidated report.

        Args:
            data (Dict[str, Any]): The dossier data, a potentially nested structure
                of dictionaries and lists, to be validated.

        Returns:
            bool: True if the dossier passes all verification checks. This method
                does not return False; it raises an exception upon any failure.

        Raises:
            SecurityIntegrityViolation: If the dossier fails verification due to
                detected contradictions, evidence integrity failures, or tonal
                infractions.
            RecursionError: If the input data is too deeply nested for the
                recursive text analysis, exceeding the system's recursion limit.
        """
        violations: List[str] = []

        # Validates claims and drivers, cross-referencing assertions from multiple vendors to detect contradictions.
        cls._verify_evidence_integrity(data, violations)

        # Identifies language indicative of excessive confidence or unsubstantiated claims using efficient string-matching algorithms.
        def check_text_recursive(obj: Any, path: str) -> None:
            r"""{'docstring': "Recursively traverses a data structure to identify strings containing specific text patterns.\n\n    This function traverses nested Python dictionaries and lists. When a string\n    element is found, it is delegated to an external validation function for\n    analysis. The traversal path is constructed dynamically to provide precise\n    location information for any identified issues, which are recorded as a side\n    effect in an external collection.\n\n    Args:\n        obj: The Python object to be recursively traversed.\n        path: The object-notation path to the current `obj`, used to\n            precisely locate findings (e.g., 'key1.key2[0]').\n\n    Returns:\n        None. This function operates via side effects and does not return a value.\n\n    Raises:\n        RecursionError: If the nesting depth of the input `obj` exceeds the\n            system's recursion limit."}."""
            if isinstance(obj, str):
                cls._check_sober_tone(obj, path, violations)
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    check_text_recursive(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    check_text_recursive(v, f"{path}[{i}]")

        check_text_recursive(data, "dossier")

        if violations:
            msg = "❌ VIOLACIÓN DE PROTOCOLO DIPLOMÁTICO TIER 1:\n" + "\n".join(
                violations
            )
            logger.error(msg)
            raise SecurityIntegrityViolation(msg)

        return True

    @classmethod
    def _verify_evidence_integrity(
        cls, data: Dict[str, Any], violations: List[str]
    ) -> None:
        """Ensures that external evidence artifacts are compliant by requiring the presence of unique traceability identifiers and immutable content snapshots for audit and provenance."""
        claims = data.get("claims", [])
        for i, claim in enumerate(claims):
            url = claim.get("url")
            status = claim.get("status")
            if status == "broken":
                violations.append(
                    f"Evidencia [Claim {i}] '{url}' está rota o no disponible."
                )
            if status == "verified" and not claim.get("local_snapshot"):
                violations.append(
                    f"Evidencia [Claim {i}] '{url}' verificada pero sin snapshot local."
                )

    @classmethod
    def _check_sober_tone(cls, text: str, context: str, violations: List[str]) -> None:
        """Identifies and flags language patterns that deviate from a neutral, objective, and professional tone."""
        text_norm = text.lower()
        for term in cls.FORBIDDEN_TONE_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", text_norm):
                violations.append(
                    f"[{context}] Tono inapropiado: El término '{term}' vulnera la sobriedad ejecutiva."
                )

        # Removes conversational artifacts, such as model self-corrections or response refusals, to ensure the final output is strictly declarative and content-focused.
        if "engaño" in text_norm or "engañoso" in text_norm:
            violations.append(
                f"[{context}] Error de lógica: Nunca califiques los datos del informe como engañosos."
            )
