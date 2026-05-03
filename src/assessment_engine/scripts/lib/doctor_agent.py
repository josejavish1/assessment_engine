# --- START OF BUSINESS LOGIC ---
import logging
from typing import Any

from assessment_engine.prompts.product_owner_prompts import (
    build_product_owner_doctor_prompt,
    get_product_owner_doctor_instruction,
)
from assessment_engine.scripts.lib.ai_client import call_agent
from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
from assessment_engine.scripts.lib.product_owner_models import (
    ProductOwnerDoctorDiagnosis,
)

logger = logging.getLogger(__name__)


class DoctorAgent:
    """
    Agente supervisor (Gobernanza Inmunitaria).
    Evalúa errores de ejecución del Worker para decidir si es seguro auto-curar
    o si la cura requiere violar invariantes y debe delegarse a un humano.
    """

    @classmethod
    async def diagnose(
        cls, plan: dict[str, Any], task: dict[str, Any], error_log: str
    ) -> ProductOwnerDoctorDiagnosis:
        """
        Analiza un fallo en la ejecución y devuelve un diagnóstico estructurado.
        """
        logger.info(
            "Iniciando Doctor Agent: Evaluando fallo del Worker (Gobernanza Inmunitaria)"
        )

        # Obtenemos el perfil del modelo para el rol de doctor (supervisor)
        model_profile = resolve_model_profile_for_role("product_owner_doctor")

        prompt = build_product_owner_doctor_prompt(plan, task, error_log)
        instruction = get_product_owner_doctor_instruction()

        result = await call_agent(
            model_name=model_profile["model"],
            prompt=prompt,
            instruction=instruction,
            output_schema=ProductOwnerDoctorDiagnosis,
            tools=[],  # El Doctor no necesita herramientas, solo evaluar el error lógicamente
        )

        diagnosis = ProductOwnerDoctorDiagnosis.model_validate(result)

        if diagnosis.is_safe_to_proceed:
            logger.info(
                "Doctor Agent: El fallo es curable y seguro. Se autoriza la auto-reparación."
            )
        else:
            logger.warning(
                "Doctor Agent: [ACTION GATE] La cura viola invariantes o requiere intervención manual."
            )
            if diagnosis.required_invariant_breach:
                logger.warning(
                    f"Invariante comprometido: {diagnosis.required_invariant_breach}"
                )

        return diagnosis
