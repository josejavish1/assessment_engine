"""
Cross-Tower Semantic Shielding (Homomorphic Graph Projection).

Applies the Homomorphic Projection Functor to prevent cross-tower
entity leakage (e.g., preventing SCADA, Oracle, or Equinix from leaking into T8).
"""

from enum import Enum
from typing import Dict, Set, List
from pydantic import BaseModel, Field, ConfigDict


class OntologicalLayer(str, Enum):
    PHYSICAL_INFRA = "LAYER_PHYSICAL_INFRA"
    NETWORK_STORAGE = "LAYER_NETWORK_STORAGE"
    APPLICATION_VENDOR = "LAYER_APPLICATION_VENDOR"
    GOVERNANCE_PROCESS = "LAYER_GOVERNANCE_PROCESS"


class EvidenceChunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    chunk_id: str
    verbatim_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_entities: List[str]
    ontological_layer: OntologicalLayer
    hypernym_fallback: str = Field(
        description="Abstract functional class used when node is projected across tower boundaries."
    )


class KPISubgraph(BaseModel):
    kpi_id: str
    kpi_name: str
    quantitative_score: float = Field(ge=1.0, le=5.0)
    evidence_chunks: List[EvidenceChunk] = Field(default_factory=list)


class PillarEpistemicContext(BaseModel):
    pillar_id: str
    tower_id: str
    kpis: List[KPISubgraph]


# Tower Access Control Matrix (TACM)
TOWER_ONTOLOGY_CLEARANCE: Dict[str, Set[OntologicalLayer]] = {
    "T1": {OntologicalLayer.PHYSICAL_INFRA, OntologicalLayer.GOVERNANCE_PROCESS},
    "T2": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T3": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.PHYSICAL_INFRA, OntologicalLayer.GOVERNANCE_PROCESS},
    "T4": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.PHYSICAL_INFRA, OntologicalLayer.GOVERNANCE_PROCESS},
    "T5": {OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T6": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T7": {OntologicalLayer.GOVERNANCE_PROCESS, OntologicalLayer.APPLICATION_VENDOR},
    # T8 & T10 are strictly shielded from physical, network, and vendor specifics
    "T8": {OntologicalLayer.GOVERNANCE_PROCESS},
    "T9": {OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T10": {OntologicalLayer.GOVERNANCE_PROCESS},
}


class CrossTowerGraphProjector:
    """
    Applies the Homomorphic Projection Functor to prevent cross-tower
    entity leakage.
    """

    @staticmethod
    def project_chunk(chunk: EvidenceChunk, target_tower_id: str) -> EvidenceChunk:
        target_tower = target_tower_id.split("_")[0].upper()
        allowed_layers = TOWER_ONTOLOGY_CLEARANCE.get(
            target_tower, {OntologicalLayer.GOVERNANCE_PROCESS}
        )
        if chunk.ontological_layer in allowed_layers:
            return chunk

        # Apply hypernym abstraction across the verbatim text for out-of-scope entities
        abstracted_text = chunk.verbatim_text
        for entity in chunk.extracted_entities:
            abstracted_text = abstracted_text.replace(
                entity, f"[{chunk.hypernym_fallback}]"
            )

        return EvidenceChunk(
            chunk_id=f"{chunk.chunk_id}_PROJ_{target_tower_id}",
            verbatim_text=abstracted_text,
            confidence=round(chunk.confidence * 0.85, 4),
            extracted_entities=[chunk.hypernym_fallback],
            ontological_layer=OntologicalLayer.GOVERNANCE_PROCESS,
            hypernym_fallback=chunk.hypernym_fallback,
        )

    @classmethod
    def compile_shielded_context(
        cls, raw_context: PillarEpistemicContext
    ) -> PillarEpistemicContext:
        projected_kpis: List[KPISubgraph] = []
        for kpi in raw_context.kpis:
            projected_chunks = [
                cls.project_chunk(c, raw_context.tower_id)
                for c in kpi.evidence_chunks
            ]
            projected_kpis.append(
                KPISubgraph(
                    kpi_id=kpi.kpi_id,
                    kpi_name=kpi.kpi_name,
                    quantitative_score=kpi.quantitative_score,
                    evidence_chunks=projected_chunks,
                )
            )
        return PillarEpistemicContext(
            pillar_id=raw_context.pillar_id,
            tower_id=raw_context.tower_id,
            kpis=projected_kpis,
        )
