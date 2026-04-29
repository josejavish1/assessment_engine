from pydantic import BaseModel, Field
from typing import List, Dict

class RegulatoryHarvest(BaseModel):
    sector: str
    frameworks: List[str]
    source_evidence: str

class BusinessHarvest(BaseModel):
    ceo_agenda: str
    business_drivers: List[str]
    financial_tier: str = Field(..., pattern="^(Tier 1|Tier 2|Tier 3)$")
    source_evidence: str

class TechHarvest(BaseModel):
    tech_footprint: str
    tech_trends: List[str]
    source_evidence: str

class ClientDossier(BaseModel):
    client_name: str
    industry: str
    financial_tier: str
    regulatory_frameworks: List[str]
    ceo_agenda: str
    technological_drivers: List[str]
    osint_footprint: str
    transformation_horizon: str
    target_maturity_matrix: Dict[str, float]
    evidences: List[str]
