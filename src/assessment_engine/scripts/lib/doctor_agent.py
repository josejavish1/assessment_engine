#
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
    """Asynchronously analyzes a runtime failure to produce a structured diagnosis.

    This coroutine acts as a safety gate for automated remediation by invoking a
    specialized AI agent. It performs a root cause analysis of a failed task by
    evaluating the execution plan, the specific task's context, and the
    associated error logs. The analysis determines if the failure is
    recoverable via automated means and whether a proposed remediation would
    violate predefined system invariants, thus requiring human intervention.

    Args:
        plan (dict[str, Any]): The execution plan context in which the task
            failure occurred.
        task (dict[str, Any]): A dictionary representing the specific task that
            failed.
        error_log (str): The captured standard output, error streams, or logs
            from the failed task execution.

    Returns:
        ProductOwnerDoctorDiagnosis: A Pydantic model containing the structured
            diagnosis. This includes the assessed cause of failure, a proposed
            remediation plan, and a boolean safety assessment for automated
            execution.

    Raises:
        pydantic.ValidationError: If the response from the underlying AI model does
            not conform to the `ProductOwnerDoctorDiagnosis` schema.
    """

    @classmethod
    async def diagnose(
        cls, plan: dict[str, Any], task: dict[str, Any], error_log: str
    ) -> ProductOwnerDoctorDiagnosis:
        """Analyzes a runtime task failure using an AI agent to produce a diagnosis.

        This coroutine invokes a specialized AI agent to perform a root cause
        analysis on a failed task. It constructs a detailed prompt from the
        execution plan, the failed task's specification, and the associated error
        logs. The agent's structured response is then parsed and validated to assess
        the failure's cause, propose an automated remediation ('cure'), and evaluate
        whether applying the cure is safe and adheres to system invariants.

        Args:
            plan: The execution plan context in which the failure occurred.
            task: The specification of the task that failed.
            error_log: The captured standard output, error streams, or logs from
                the failed task execution.

        Returns:
            An instance of `ProductOwnerDoctorDiagnosis` containing the structured
            diagnosis, including the root cause, a proposed cure, and a safety
            assessment for automated remediation.

        Raises:
            pydantic.ValidationError: If the AI agent's response payload does not
                conform to the `ProductOwnerDoctorDiagnosis` schema.
        """
        logger.info(
            "Iniciando Doctor Agent: Evaluando fallo del Worker (Gobernanza Inmunitaria)"
        )

        #
        model_profile = resolve_model_profile_for_role("product_owner_doctor")

        prompt = build_product_owner_doctor_prompt(plan, task, error_log)
        instruction = get_product_owner_doctor_instruction()

        result = await call_agent(
            model_name=model_profile["model"],
            prompt=prompt,
            instruction=instruction,
            output_schema=ProductOwnerDoctorDiagnosis,
            tools=[],  # The Doctor agent operates in a purely diagnostic capacity. It performs a logical evaluation of the error state without reliance on external tools for its assessment.
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
