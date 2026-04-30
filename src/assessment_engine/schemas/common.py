from typing import List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_validator, ConfigDict

def collect_all_strings(data: Any) -> List[str]:
    out = []
    if isinstance(data, dict):
        for v in data.values():
            out.extend(collect_all_strings(v))
    elif isinstance(data, list):
        for item in data:
            out.extend(collect_all_strings(item))
    elif isinstance(data, str):
        out.append(data)
    return out

class BaseDraftModel(BaseModel):
    section_id: str
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        return []

    @model_validator(mode="after")
    def validate_forbidden_phrases(self) -> "BaseDraftModel":
        forbidden = self.get_forbidden_phrases()
        if not forbidden:
            return self
            
        cleaned_notes = []
        for note in self.notes_for_reviewer:
            if not any(phrase.lower() in note.lower() for phrase in forbidden):
                cleaned_notes.append(note)
        self.notes_for_reviewer = cleaned_notes
        
        data = self.model_dump(exclude={"notes_for_reviewer"})
        all_strings = collect_all_strings(data)
        
        for phrase in forbidden:
            for text in all_strings:
                if phrase.lower() in text.lower():
                    section_name = getattr(self, "section_title", self.section_id)
                    raise ValueError(f"La seccion {section_name} contiene una frase prohibida: '{phrase}'.")
                    
        return self

class Defect(BaseModel):
    severity: str = Field(..., pattern="^(critical|major|minor)$")
    type: str
    message: str
    suggested_fix: str

class SectionReview(BaseModel):
    section_id: str
    status: str = Field(..., pattern="^(approve|revise|human_validation_required)$")
    overall_assessment: str
    defects: List[Defect] = []
    approval_conditions: List[str] = []
    review_notes: List[str] = []

class VersionMetadata(BaseModel):
    artifact_type: str
    artifact_version: str = "1.0.0"
    source_version: Optional[str] = None
    timestamp_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    run_id: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

class VersionedPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    generation_metadata: Optional[VersionMetadata] = Field(
        default=None, alias="_generation_metadata"
    )
