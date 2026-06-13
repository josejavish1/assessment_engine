import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SecurityIntegrityViolation(RuntimeError):
    """Lanzada cuando un output de IA viola las leyes físicas del mercado o la integridad del dato."""

    pass


class FidelitySentinel:
    """Garantiza la preservación de entidades técnicas críticas durante la síntesis."""

    @staticmethod
    def verify_field_occupancy(raw_data: List[Any], final_list: List[Any], field_name: str) -> List[str]:
        """Verifica que no haya habido una pérdida masiva de elementos en una lista técnica."""
        violations = []
        if raw_data and not final_list:
            violations.append(f"Estructura Crítica: El campo '{field_name}' está VACÍO en el resultado, pero contenía datos en el material bruto.")
        elif len(raw_data) > 0 and len(final_list) < (len(raw_data) * 0.5):
            violations.append(f"Densidad Insuficiente: El campo '{field_name}' ha sufrido una dilución de datos superior al 50%.")
        return violations

    @staticmethod
    def verify_entity_retention(
        raw_entities: List[str], final_text: str, context: str = "General"
    ) -> List[str]:
        violations = []
        text_lower = final_text.lower()
        for entity in raw_entities:
            if not entity or len(entity) < 3:
                continue
            # Check if entity (or a very close version) is in the text
            entity_norm = entity.lower().strip()
            if entity_norm not in text_lower:
                violations.append(
                    f"[{context}] Fuga de Atributo: La entidad '{entity}' se ha perdido o diluido en la redacción final."
                )
        return violations


class StructuralIntegrityGate:
    """
    GUARDIÁN DE EXCELENCIA TIER 1 (DIPLOMACY EDITION 2026).
    Actúa como un firewall síncrono ultra-rápido. El análisis semántico complejo
    lo delega en los Agentes Auditores asíncronos previos.
    """

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
        violations: List[str] = []

        # 1. Validar Claims y Drivers (Colisiones de Vendors)
        cls._verify_evidence_integrity(data, violations)

        # 2. DETECTOR DE ARROGANCIA (Fast String Matching)
        def check_text_recursive(obj: Any, path: str) -> None:
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
        """Verifica que las evidencias externas tengan trazabilidad y snapshots."""
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
        """Detecta lenguaje no profesional, hiperbólico o agresivo."""
        text_norm = text.lower()
        for term in cls.FORBIDDEN_TONE_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", text_norm):
                violations.append(
                    f"[{context}] Tono inapropiado: El término '{term}' vulnera la sobriedad ejecutiva."
                )

        # Detectar patrones de autocrítica del sistema
        if "engaño" in text_norm or "engañoso" in text_norm:
            violations.append(
                f"[{context}] Error de lógica: Nunca califiques los datos del informe como engañosos."
            )
