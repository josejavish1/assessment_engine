"""Deterministic Validation Engine for Technology Tower Synthesis (Semantic Quality Gate).

Enforces lexical density, anti-boilerplate rules, cross-domain contamination boundaries,
executive dignity (anti-pejorative / blameless), and mathematical score-to-prose consistency
across all technology towers.
"""

from __future__ import annotations

import re
from typing import Dict, Final, List, Optional, Set, Tuple

from assessment_engine.application.services.synthesis.exceptions import SemanticQualityError


class SemanticGatekeeper:
    """Deterministic validation engine enforcing lexical density, anti-boilerplate rules,

    cross-domain contamination boundaries, executive dignity, and score-prose coherence.
    """

    MIN_WORDS_DENSE: Final[int] = 220
    MIN_WORDS_SPARSE: Final[int] = 175
    MAX_WORDS: Final[int] = 600

    # Forbidden cross-domain terms per Tower ID (Case-insensitive boundary matching)
    DEFAULT_CONTAMINATION_MATRIX: Final[Dict[str, List[str]]] = {
        "T1": ["endpoint", "impresora", "printer", "vdi", "citrix", "laptop", "mesa de ayuda", "helpdesk", "service desk", "drp", "disaster recovery"],
        "T2": ["servidor físico", "physical server", "rack", "chasis", "fibra oscura", "dark fiber", "bgp", "ospf", "mainframe", "drp", "disaster recovery", "plan de recuperación ante desastres", "plan de continuidad", "business continuity plan"],
        "T3": ["laptop", "impresora", "printer", "BYOD", "móvil", "mobile", "licenciamiento office", "office licensing", "sharepoint"],
        "T4": ["cableado estructurado", "structured cabling", "planta externa", "outside plant", "ups", "generador", "generator", "aire acondicionado", "hvac"],
        "T5": ["bgp", "mpls", "sd-wan", "switch core", "core switch", "almacenamiento san", "san storage", "lun"],
        "T6": ["routing", "switching", "spanning-tree", "vlan trunk", "frecuencia de radio", "radio frequency"],
        "T7": ["cinta lto", "lto tape", "hidratación de datos", "sql injection", "xss", "desarrollo ágil", "agile development"],
        "T8": ["cooler", "pdu", "fibra óptica", "optical fiber", "transceiver", "patch panel"],
        "T9": [
            "servidor físico", "physical server", "san", "nas", "storage array", "bgp", "ospf", "mpls",
            "data center", "racks", "mainframe", "fibra oscura", "dark fiber", "core switch", "lun", "raid"
        ],
        "T10": ["parcheo de cables", "cable patching", "configuración bgp", "bgp routing", "reemplazo de discos", "disk replacement", "tinta", "tóner", "printer toner"]
    }

    # Forbidden consulting boilerplate, punitive tone, and ungrounded analyst filler (Bilingual EN/ES)
    FORBIDDEN_PATTERNS: Final[List[Tuple[str, str]]] = [
        (
            r"\b(?:es esencial|resulta imprescindible|es fundamental|se recomienda encarecidamente|it is essential|it is crucial|it is recommended|strongly recommended)\b",
            "Contains prescriptive consulting boilerplate ('is essential / is recommended'). Describe only As-Is reality.",
        ),
        (
            r"\b(?:mejores prácticas|best practices|estándares de la industria dictan|industry standards dictate)\b",
            "Contains generic 'best practices' filler.",
        ),
        (
            r"\b(?:score\s+\d|nivel de madurez\s+\d|maturity level\s+\d|cuestionario de evaluación|resultado de la encuesta|survey questionnaire|survey result)\b",
            "Leaks assessment survey metadata or raw numerical maturity scores in body text.",
        ),
        (
            r"(?:considerando su escala operativa global|considerando su facturación de|abarcando una facturación de|considering its global operational scale|considering its revenue of)",
            "Contains repetitive formulaic firmographic parrot. Conclude organically within the technical domain.",
        ),
        (
            r"\b(?:inmadurez severa|incompetencia|negligencia|falta de rigor de los equipos|incapacidad de los equipos|severe immaturity|incompetence|negligence|team incompetence)\b",
            "Contains accusatory/punitive tone blaming client personnel. Frame technical debt constructively as natural architectural evolution.",
        ),
        (
            r"\b(?:artesanal|artesanales|artisan execution|artisanal execution|proceso artesanal)\b",
            "Contains pejorative adjective 'artesanal/artisanal'. Use objective phrasing like 'ejecución manual' or 'manual unstandardized execution'.",
        ),
        (
            r"\b(?:chapuza|caótico|caótica|rudimentari[ao]s?|arcaic[ao]s?|shoddy|primitive architecture)\b",
            "Contains subjective, derogatory phrasing. Use sober technical terms like 'heredado', 'descentralizado', or 'manual'.",
        ),
        (
            r"\b(?:un DBA en Croacia|DBA en Croacia|DBA in Croatia|un arquitecto de Kubernetes|especialistas? externos? únicos?)\b",
            "Leaks informal employee references or geographical personnel silos from meeting transcripts. Refer to 'especialistas externos dedicados' or 'gobierno del conocimiento técnico' abstractly.",
        ),
        (
            r"\b(?:wiki MoinMoin|MoinMoin wiki|MoinMoin)\b",
            "Shames internal tooling by name. Refer to 'repositorios documentales previos' or 'legacy documentation platforms'.",
        ),
        (
            r"\b(?:informes de Gartner|Gartner reports?|estudios de Gartner|Gartner research|investigaciones de Google SRE|Google SRE research|estudios de Forrester|Forrester research)\b",
            "Contains generic canned analyst filler (Gartner/Google SRE/Forrester). Ground all observations directly in the client's empirical architecture.",
        ),
        (
            r"^(?:#|\*|-|\d+\.)",
            "Contains Markdown headers, bullet points, or numbered lists. Must be continuous prose.",
        ),
    ]

    # Deterministic dictionary for executive normalization
    EXECUTIVE_DIGNITY_REPLACEMENTS: Final[Tuple[Tuple[re.Pattern[str], str], ...]] = (
        (re.compile(r"\bejecuci[óo]n\s+manual\s+y\s+artesanal\b", re.IGNORECASE), "ejecución manual basada en consola"),
        (re.compile(r"\bmanual\s+y\s+artesanal\b", re.IGNORECASE), "manual y descentralizada"),
        (re.compile(r"\bartesanales\b", re.IGNORECASE), "manuales no automatizados"),
        (re.compile(r"\bartesanal\b", re.IGNORECASE), "manual no automatizado"),
        (re.compile(r"\bartisanal\b", re.IGNORECASE), "manual non-standardized"),
        (re.compile(r"\bwiki\s+MoinMoin\s+obsoleta\b", re.IGNORECASE), "repositorios documentales heredados"),
        (re.compile(r"\bwiki\s+MoinMoin\b", re.IGNORECASE), "repositorio documental previo"),
        (re.compile(r"\bMoinMoin\b", re.IGNORECASE), "plataforma documental previa"),
        (re.compile(r"\bun\s+DBA\s+en\s+Croacia\s+y\s+un\s+arquitecto\s+de\s+Kubernetes\b", re.IGNORECASE), "especialistas técnicos externos dedicados"),
        (re.compile(r"\bun\s+DBA\s+en\s+Croacia\b", re.IGNORECASE), "soporte de base de datos especializado"),
    )

    def __init__(self, custom_contamination_matrix: Dict[str, List[str]] | None = None) -> None:
        self.contamination_matrix = (
            custom_contamination_matrix
            if custom_contamination_matrix is not None
            else self.DEFAULT_CONTAMINATION_MATRIX
        )

    def _count_words(self, text: str) -> int:
        words = re.findall(r"\b\w+\b", text)
        return len(words)

    def _check_word_count(self, text: str, allowed_evidence_text: str = "") -> int:
        count = self._count_words(text)
        evidence_words = self._count_words(allowed_evidence_text)
        
        # Determine dynamic minimum to prevent forcing hallucinations on sparse evidence
        min_required = max(60, min(self.MIN_WORDS_SPARSE, int(evidence_words * 0.8)))
        
        if count < min_required:
            deficit = min_required - count
            raise SemanticQualityError(
                feedback=(
                    f"Semantic Anemia detected: Output is {count} words (Minimum required is {min_required}). "
                    f"You must expand the technical analysis by at least {deficit} words, deepening technical dynamics and operational exposure."
                ),
                failed_text=text,
            )
        if count > self.MAX_WORDS:
            excess = count - self.MAX_WORDS
            raise SemanticQualityError(
                feedback=(
                    f"Verbosity violation: Output is {count} words (Maximum allowed is {self.MAX_WORDS}). "
                    f"Trim {excess} words by tightening prose without losing technical facts."
                ),
                failed_text=text,
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
            pattern = rf"\b{re.escape(term_lower)}(?:s|es)?\b"
            if re.search(pattern, text_lower):
                if not re.search(pattern, evidence_lower):
                    detected_contaminants.add(term)

        if detected_contaminants:
            terms_str = ", ".join(f"'{t}'" for t in sorted(detected_contaminants))
            raise SemanticQualityError(
                feedback=(
                    f"Cross-Domain Contamination in Tower {tower_id}: Text contains forbidden out-of-domain terms [{terms_str}] "
                    f"that do not exist in the source evidence. Remove all references to these concepts and strictly confine analysis to {tower_id}."
                ),
                failed_text=text,
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
                        failed_text=text,
                    )

    def _check_score_consistency(
        self,
        text: str,
        score: float | None = None,
        band_label: str | None = None,
    ) -> None:
        """Enforces bidirectional consistency between the mathematical score and narrative claims."""
        if score is None:
            return

        text_lower = text.lower()
        if score <= 1.50:
            # Low-maturity pillars (Initial / Ad-Hoc) must NEVER claim high technical maturity or Level 5
            high_maturity_patterns = [
                r"\b(?:alta\s+madurez(?:\s+t[ée]cnica)?|high(?:\s+technical)?\s+maturity|madurez\s+avanzada|advanced\s+maturity|altamente\s+madura?|highly\s+mature)\b",
                r"\b(?:nivel\s+5(?:\.0)?|level\s+5(?:\.0)?|evaluado\s+con\s+nivel\s+5(?:\.0)?|scored\s+at\s+level\s+5(?:\.0)?)\b",
                r"\b(?:en\s+optimizaci[óo]n|optimizing\s+regime|fully\s+optimized)\b",
            ]
            for pat in high_maturity_patterns:
                if re.search(pat, text_lower):
                    raise SemanticQualityError(
                        feedback=(
                            f"Score-Narrative Incoherence: Pillar is scored at {score:.2f} ({band_label or 'Initial/Ad-hoc'}), "
                            "but the narrative asserts 'alta madurez técnica' or Level 5.0 capabilities. "
                            "The narrative MUST objectively explain the Initial/Ad-hoc reality and foundational gaps without claiming high maturity."
                        ),
                        failed_text=text,
                    )
        elif score >= 3.50:
            # High-maturity pillars must not claim complete absence of basic controls
            absence_patterns = [
                r"\b(?:inexistencia\s+total|ausencia\s+total\s+de\s+control|completamente\s+inexistente|zero\s+controls?|no\s+control\s+exists)\b",
            ]
            for pat in absence_patterns:
                if re.search(pat, text_lower):
                    raise SemanticQualityError(
                        feedback=(
                            f"Score-Narrative Incoherence: Pillar is scored at {score:.2f} ({band_label or 'Defined/Managed'}), "
                            "but narrative asserts complete absence of controls. Acknowledge existing formalized controls and frame residual risk around stress/scale limits."
                        ),
                        failed_text=text,
                    )

    def sanitize_executive_dignity(self, text: str) -> str:
        """Deterministically replaces pejorative words or informal meeting artifacts with sober enterprise phrasing."""
        sanitized = text
        for pattern, replacement in self.EXECUTIVE_DIGNITY_REPLACEMENTS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    def validate(
        self,
        text: str,
        tower_id: str,
        allowed_evidence_text: str = "",
        evidence_count: int = 3,
        score: float | None = None,
        band_label: str | None = None,
    ) -> int:
        """Runs all deterministic checks sequentially.

        Returns verified word count if valid, or raises SemanticQualityError.
        """
        if not text or not text.strip():
            raise SemanticQualityError("Empty narrative generated.")

        self._check_structural_and_boilerplate_rules(text)
        self._check_score_consistency(text, score=score, band_label=band_label)
        self._check_contamination(text, tower_id, allowed_evidence_text)
        word_count = self._check_word_count(text, allowed_evidence_text=allowed_evidence_text)

        return word_count
