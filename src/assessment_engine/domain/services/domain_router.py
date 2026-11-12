from __future__ import annotations

import hashlib
import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)


class TowerID(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"
    T5 = "T5"
    T6 = "T6"
    T7 = "T7"
    T8 = "T8"
    T9 = "T9"
    T10 = "T10"
    UNCLASSIFIED = "UNCLASSIFIED"


class AbsenceSemanticEvaluation(BaseModel):
    is_absence_of_control: bool = Field(
        description="True si el hallazgo describe la inexistencia, falta o carencia total de una herramienta, proceso o control necesario. False si el control existe pero presenta degradación o mal funcionamiento."
    )
    missing_capability: Optional[str] = Field(
        default=None,
        description="Si is_absence_of_control es True, describe canónicamente qué capacidad o control falta."
    )


class SemanticRoutingDecision(BaseModel):
    finding_id: Optional[str] = Field(default=None, description="Identificador del hallazgo o texto evaluado.")
    chain_of_thought_jurisdiction: str = Field(
        description="Razonamiento conciso (1-2 oraciones) explicando por qué la causa raíz técnica pertenece a la torre asignada y cómo se aplicaron las exclusiones ontológicas."
    )
    primary_tower: TowerID = Field(
        description="La torre tecnológica propietaria legítima de la causa raíz técnica del hallazgo."
    )
    secondary_impacted_towers: List[TowerID] = Field(
        default_factory=list,
        description="Otras torres que sufren síntomas derivados del fallo, sin ser dueñas del presupuesto o causa raíz."
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, default=1.0,
        description="Nivel de certidumbre semántica de la asignación."
    )
    absence_evaluation: AbsenceSemanticEvaluation = Field(
        default_factory=lambda: AbsenceSemanticEvaluation(is_absence_of_control=False),
        description="Evaluación semántica de ausencia de control."
    )


class BatchSemanticRoutingResponse(BaseModel):
    decisions: List[SemanticRoutingDecision]


class DomainSemanticRouter:
    """
    Tier-1 Neurosymbolic Semantic Router.
    Classifies findings against a formal Scope Ontology without brittle substring keyword matching.
    """

    def __init__(self, llm_client: Any = None, ontology_path: Optional[Path] = None):
        self.llm = llm_client
        self.ontology_path = ontology_path or (ROOT / "engine_config" / "ontology_taxonomies.json")
        self._cache: Dict[str, SemanticRoutingDecision] = {}
        self._ontology: Dict[str, Any] = self._load_ontology()

    def _load_ontology(self) -> Dict[str, Any]:
        if self.ontology_path.exists():
            try:
                return json.loads(self.ontology_path.read_text(encoding="utf-8"))
            except Exception as ex:
                logger.warning(f"Error loading ontology from {self.ontology_path}: {ex}")
        return {}

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    def route_finding(self, text: str, finding_id: Optional[str] = None) -> SemanticRoutingDecision:
        """
        Routes a single technical finding to its canonical technology tower.
        Uses SHA-256 caching to avoid redundant calls.
        """
        clean_text = text.strip()
        if not clean_text:
            return SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="Empty text provided.",
                primary_tower=TowerID.UNCLASSIFIED,
            )

        cache_key = self._hash_text(clean_text)
        if cache_key in self._cache:
            decision = self._cache[cache_key]
            if finding_id and not decision.finding_id:
                decision.finding_id = finding_id
            return decision

        # If LLM client is available, execute reasoning against the ontology
        if self.llm is None:
            try:
                from assessment_engine.infrastructure.genai_client import create_genai_client
                self.llm = create_genai_client()
            except Exception as ex:
                logger.warning(f"Failed to create default genai client: {ex}")

        if self.llm and hasattr(self.llm, "models") and hasattr(self.llm.models, "generate_content"):
            from assessment_engine.infrastructure.genai_client import ModelTier, get_model
            model_name = get_model(ModelTier.REASONING)
            
            ontology_str = json.dumps(self._ontology, ensure_ascii=False, indent=2)
            prompt = f"""You are a Principal Enterprise Systems Architect and Chief Risk Officer.
Assign the following technical finding to its canonical primary technology tower (T1 to T10) based strictly on ROOT CAUSE JURISDICTION and EXPLICIT EXCLUSIONS.

### FORMAL SCOPE ONTOLOGY:
{ontology_str}

### TARGET FINDING:
"{clean_text}"

### MANDATORY INSTRUCTIONS:
1. Apply ROOT_CAUSE_JURISDICTION: Assign to the tower that owns the root technical debt/budget, not systems suffering secondary symptoms.
2. Apply PHYSICAL_ENVIRONMENT_OVERRIDE: Computing or networking assets located in plant floor, concrete mixing, quarries, or factories belong to T10, NOT T1.
3. Apply ORGANIZATIONAL_PROCESS_VS_FACILITY: DRP and BCP software or governance belong to T5, NOT T1.
4. Output MUST be valid JSON adhering strictly to:
{{
  "chain_of_thought_jurisdiction": "1-2 sentences explaining why the root cause belongs to primary_tower and how exclusions apply.",
  "primary_tower": "T1" through "T10",
  "secondary_impacted_towers": ["T2", ...],
  "confidence_score": 0.95,
  "absence_evaluation": {{
    "is_absence_of_control": true or false,
    "missing_capability": "short descriptor if true, else null"
  }}
}}
Output raw JSON only.
"""
            try:
                response = self.llm.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                raw_json = response.text.strip()
                if raw_json.startswith("```json"):
                    raw_json = raw_json[7:]
                if raw_json.startswith("```"):
                    raw_json = raw_json[3:]
                if raw_json.endswith("```"):
                    raw_json = raw_json[:-3]
                
                data = json.loads(raw_json.strip())
                decision = SemanticRoutingDecision(
                    finding_id=finding_id,
                    chain_of_thought_jurisdiction=data.get("chain_of_thought_jurisdiction", "Ontological routing"),
                    primary_tower=TowerID(data.get("primary_tower", "UNCLASSIFIED")),
                    secondary_impacted_towers=[TowerID(t) for t in data.get("secondary_impacted_towers", []) if t in TowerID.__members__],
                    confidence_score=float(data.get("confidence_score", 1.0)),
                    absence_evaluation=AbsenceSemanticEvaluation(
                        is_absence_of_control=data.get("absence_evaluation", {}).get("is_absence_of_control", False),
                        missing_capability=data.get("absence_evaluation", {}).get("missing_capability")
                    )
                )
                self._cache[cache_key] = decision
                return decision
            except Exception as ex:
                logger.error(f"Error executing LLM semantic routing: {ex}")

        # Deterministic fallback based on ontology core keys if LLM fails
        return self._deterministic_fallback(clean_text, finding_id)

    def _deterministic_fallback(self, text: str, finding_id: Optional[str]) -> SemanticRoutingDecision:
        """Deterministic heuristic fallback prioritizing exclusions over inclusions."""
        text_lower = text.lower()
        towers = self._ontology.get("towers", {})
        
        # Check specific jurisdictional overrides
        if any(w in text_lower for w in ["hormigón", "hormigon", "planta periférica", "báscula", "pesaje", "prenet"]):
            return SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="Physical plant and local weighbridge operations belong strictly to T10.",
                primary_tower=TowerID.T10,
            )
        if any(w in text_lower for w in ["drp", "disaster recovery", "plan de recuperación", "conmutación de servicios"]):
            return SemanticRoutingDecision(
                finding_id=finding_id,
                chain_of_thought_jurisdiction="Disaster recovery plans and service failover governance belong strictly to T5.",
                primary_tower=TowerID.T5,
            )
            
        return SemanticRoutingDecision(
            finding_id=finding_id,
            chain_of_thought_jurisdiction="Default fallback.",
            primary_tower=TowerID.UNCLASSIFIED,
        )
