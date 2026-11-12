import re
from typing import Dict, List, Set

from assessment_engine.application.services.synthesis.exceptions import SemanticQualityError

class SemanticGatekeeper:
    """
    Deterministic validation engine enforcing lexical density, anti-boilerplate rules,
    and cross-domain contamination boundaries across all 10 technology towers.
    """

    MIN_WORDS_DENSE: int = 220
    MIN_WORDS_SPARSE: int = 175
    MAX_WORDS: int = 600

    # Forbidden cross-domain terms per Tower ID (Case-insensitive boundary matching)
    DEFAULT_CONTAMINATION_MATRIX: Dict[str, List[str]] = {
        "T1": ["endpoint", "impresora", "vdi", "citrix", "laptop", "mesa de ayuda", "helpdesk", "drp", "disaster recovery", "hormigonera", "prefabricados", "camiones", "báscula"],
        "T2": ["servidor físico", "rack", "chasis", "fibra oscura", "bgp", "ospf", "mainframe", "drp", "disaster recovery", "plan de recuperación ante desastres", "plan de continuidad"],
        "T3": ["laptop", "impresora", "BYOD", "móvil", "licenciamiento office", "sharepoint"],
        "T4": ["cableado estructurado", "planta externa", "ups", "generador", "aire acondicionado"],
        "T5": ["bgp", "mpls", "sd-wan", "switch core", "almacenamiento san", "lun"],
        "T6": ["routing", "switching", "spanning-tree", "vlan trunk", "frecuencia de radio"],
        "T7": ["cinta lto", "hidratación de datos", "sql injection", "xss", "desarrollo ágil"],
        "T8": ["cooler", "pdu", "fibra óptica", "transceiver", "patch panel"],
        "T9": [
            "servidor físico", "san", "nas", "netapp", "bgp", "ospf", "mpls",
            "data center", "racks", "mainframe", "fibra oscura", "core switch", "lun", "raid"
        ],
        "T10": ["parcheo de cables", "configuración bgp", "reemplazo de discos", "tinta", "tóner"]
    }

    # Regex patterns for forbidden consulting boilerplate and score leakage
    FORBIDDEN_PATTERNS: List[tuple[str, str]] = [
        (r"\b(es esencial|resulta imprescindible|es fundamental|se recomienda encarecidamente)\b", "Contains prescriptive consulting boilerplate ('es esencial / se recomienda'). Describe only As-Is reality."),
        (r"\b(mejores prácticas|best practices|estándares de la industria dictan)\b", "Contains generic 'best practices' filler."),
        (r"\b(score\s+\d|nivel de madurez\s+\d|cuestionario de evaluación|resultado de la encuesta)\b", "Leaks assessment survey metadata or numerical maturity scores."),
        (r"(considerando su escala operativa global|considerando su facturación de|abarcando una facturación de)", "Contains repetitive formulaic firmographic parrot. Conclude organically within the technical domain."),
        (r"\b(inmadurez severa|incompetencia|negligencia|falta de rigor de los equipos|incapacidad de los equipos)\b", "Contains accusatory/punitive tone blaming client personnel. Frame technical debt constructively as natural architectural evolution."),
        (r"^(#|\*|-|\d+\.)", "Contains Markdown headers, bullet points, or numbered lists. Must be continuous prose.")
    ]

    def __init__(self, custom_contamination_matrix: Dict[str, List[str]] | None = None):
        self.contamination_matrix = custom_contamination_matrix or self.DEFAULT_CONTAMINATION_MATRIX

    def _count_words(self, text: str) -> int:
        words = re.findall(r'\b\w+\b', text)
        return len(words)

    def _check_word_count(self, text: str, evidence_count: int = 3) -> int:
        count = self._count_words(text)
        min_required = self.MIN_WORDS_SPARSE if evidence_count <= 2 else self.MIN_WORDS_DENSE
        if count < min_required:
            deficit = min_required - count
            raise SemanticQualityError(
                feedback=f"Semantic Anemia detected: Output is {count} words (Minimum required is {min_required}). You must expand the technical analysis by at least {deficit} words, deepening technical dynamics and operational exposure.",
                failed_text=text
            )
        if count > self.MAX_WORDS:
            excess = count - self.MAX_WORDS
            raise SemanticQualityError(
                feedback=f"Verbosity violation: Output is {count} words (Maximum allowed is {self.MAX_WORDS}). Trim {excess} words by tightening prose without losing technical facts.",
                failed_text=text
            )
        return count

    def _check_contamination(self, text: str, tower_id: str, allowed_evidence_text: str) -> None:
        forbidden_terms = self.contamination_matrix.get(tower_id.upper(), [])
        if not forbidden_terms:
            return

        text_lower = text.lower()
        evidence_lower = allowed_evidence_text.lower()
        detected_contaminants: Set[str] = set()

        for term in forbidden_terms:
            term_lower = term.lower()
            # Use word boundary regex with optional plural inflection to prevent evasion
            pattern = rf"\b{re.escape(term_lower)}(?:s|es)?\b"
            if re.search(pattern, text_lower):
                # Exception: If the term was explicitly present in the raw input evidence for this pillar, allow it
                if not re.search(pattern, evidence_lower):
                    detected_contaminants.add(term)

        if detected_contaminants:
            terms_str = ", ".join(f"'{t}'" for t in sorted(detected_contaminants))
            raise SemanticQualityError(
                feedback=f"Cross-Domain Contamination in Tower {tower_id}: Text contains forbidden out-of-domain terms [{terms_str}] that do not exist in the source evidence. Remove all references to these concepts and strictly confine analysis to {tower_id}.",
                failed_text=text
            )

    def _check_structural_and_boilerplate_rules(self, text: str) -> None:
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            for pattern, reason in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, stripped, flags=re.IGNORECASE):
                    raise SemanticQualityError(
                        feedback=f"Style/Constraint Violation: {reason}",
                        failed_text=text
                    )

    def validate(self, text: str, tower_id: str, allowed_evidence_text: str = "", evidence_count: int = 3) -> int:
        """
        Runs all deterministic checks sequentially.
        Returns the verified word count if valid, or raises SemanticQualityError.
        """
        if not text or not text.strip():
            raise SemanticQualityError("Empty narrative generated.")

        self._check_structural_and_boilerplate_rules(text)
        self._check_contamination(text, tower_id, allowed_evidence_text)
        word_count = self._check_word_count(text, evidence_count=evidence_count)

        return word_count