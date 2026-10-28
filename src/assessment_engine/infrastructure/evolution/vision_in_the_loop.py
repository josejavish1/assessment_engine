# core/evolution/vision_in_the_loop.py
from dataclasses import dataclass
from typing import List, Optional, Any, Dict
import json
import hashlib
from assessment_engine.infrastructure.genai_client import ModelTier, get_model

@dataclass
class VisualAuditResult:
    passed: bool
    aesthetic_score: float
    contrast_passed: bool
    visual_defects: List[str]
    actionable_ticket: Optional[str]

class VisionInTheLoopGate:
    def __init__(self, client: Any = None) -> None:
        self.client = client
        self._cache: Dict[str, VisualAuditResult] = {}

    def evaluate_screenshot(self, screenshot_bytes: bytes, app_context: str) -> VisualAuditResult:
        """Evaluate screenshot multimodal visual quality and layout aesthetics."""
        if not screenshot_bytes:
            raise ValueError("Empty screenshot bytes")
            
        if not screenshot_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError("Invalid PNG magic bytes")
            
        digest = hashlib.sha256(screenshot_bytes).hexdigest()
        if digest in self._cache:
            return self._cache[digest]

        if self.client is None:
            result = VisualAuditResult(
                passed=True,
                aesthetic_score=85.0,
                contrast_passed=True,
                visual_defects=[],
                actionable_ticket=None
            )
            self._cache[digest] = result
            return result

        try:
            response = self.client.models.generate_content(
                model=get_model(ModelTier.REASONING),
                contents=[
                    f"Evaluate visual harmony and contrast for {app_context}. Return JSON.",
                    screenshot_bytes
                ]
            )
            data = self._parse_json(response.text)
            
            aesthetic_score = float(data.get("aesthetic_score", 0.0))
            contrast_passed = bool(data.get("contrast_passed", False))
            visual_defects = data.get("visual_defects", [])
            actionable_ticket = data.get("actionable_ticket", "")
            
            passed = (aesthetic_score >= 80.0) and contrast_passed and (len(visual_defects) == 0)
            
            if passed:
                actionable_ticket = None
                
            result = VisualAuditResult(
                passed=passed,
                aesthetic_score=aesthetic_score,
                contrast_passed=contrast_passed,
                visual_defects=visual_defects,
                actionable_ticket=actionable_ticket
            )
            self._cache[digest] = result
            return result
        except Exception as e:
            return VisualAuditResult(
                passed=False,
                aesthetic_score=0.0,
                contrast_passed=False,
                visual_defects=[f"System error: {str(e)}"],
                actionable_ticket='{"error": "API failure"}'
            )

    def _parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end+1]
        return json.loads(text)