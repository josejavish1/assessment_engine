# RFC 029: Two-Level Executive Table of Contents, Streamlined Chapter Taxonomy, and Universal Orthographic Diacritic Governance

**Status:** APPROVED FOR IMMEDIATE IMPLEMENTATION  
**Architectural Tier:** Core AST Compiler, Localization Catalog & Upstream AI Prompt Governance  
**Compliance Standard:** Zero Hardcoding, 100% Technical English Codebase, Multi-Locale & Multi-Industry Agnosticism  

---

## 1. Executive Summary & Architectural Objectives

This Request for Comments (RFC 029) defines the engineering specifications to address three critical executive presentation and typographic fidelity requirements:

1. **Two-Level Executive Table of Contents (`max_depth = 2`):** Restricts the Table of Contents (TOC) to Top-Level Chapters (`Heading 1`) and Primary Sections (`Heading 2`), eliminating third-level sub-section clutter (`Heading 3`) from both the OpenXML dynamic field instruction and the pre-rendered fallback entries.
2. **Streamlined Chapter 1 Taxonomy ("Resumen Ejecutivo"):** Simplifies the Chapter 1 heading across all supported locales in `engine_config/locales.json` from verbose compound titles (*"Resumen Ejecutivo y Tesis Estratégica"*) to canonical executive titles (*"Resumen Ejecutivo"*, *"Executive Summary"*, *"Resumo Executivo"*, *"Synthèse Exécutive"*, *"Management Summary"*).
3. **Forensic Root-Cause Resolution for Missing Orthographic Diacritics (Tildes/Accents):** Resolves the omission of diacritical marks in LLM-generated narrative payloads through a dual-layer defense:
   - **Layer 1 (Upstream Prompt Governance):** Injects strict UTF-8 orthographic and diacritic mandates into `annex_executive_synthesizer.yaml` and `blueprint_pilar_architect_prompt.yaml`.
   - **Layer 2 (Deterministic Post-Processing Normalization):** Implements a language-aware, dictionary-backed orthographic normalization pass inside `UniversalPayloadEnricher` (driven externally by `engine_config/orthographic_lexicon.json`) that restores missing diacritics in narrative prose without mutating code identifiers, JSON keys, or non-target locales.

---

## 2. Requirement 1: Two-Level Table of Contents Architecture

### 2.1 Architectural Design
In enterprise deliverables (McKinsey/Gartner standard), a 3-level Table of Contents introduces excessive visual density when documents scale beyond 15 pages. By constraining `TOCNode.max_depth` to `2`:
- **AST Representation (`document_ast.py`):** `TOCNode` defaults `max_depth: int = 2`.
- **AST Transformer (`payload_to_ast.py`):** `_build_precomputed_toc_entries()` filters out any heading where `heading.level > max_depth`.
- **OpenXML Compiler (`docx_compiler.py`):** Dynamically interpolates `node.max_depth` into the Word complex field instruction (`TOC \o "1-2" \h \z \u`) and enforces `entry.get("level", 1) <= node.max_depth` during fallback rendering.

### 2.2 Implementation Specification (`src/ast/document_ast.py` & `src/ast/payload_to_ast.py`)

```python
# File: src/ast/document_ast.py (Excerpt)
from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.ast.document_ast import ASTNode

@dataclass
class TOCNode(ASTNode):
    """
    Represents an Executive Table of Contents in the Document AST.
    Defaults to 2 hierarchy levels (Chapters and Primary Sections).
    """
    title: str
    max_depth: int = 2
    entries: List[Dict[str, Any]] = field(default_factory=list)
```

```python
# File: src/ast/payload_to_ast.py (Excerpt)
from typing import List, Dict, Any
from src.ast.document_ast import ASTNode, HeadingNode, TOCNode

class PayloadToASTTransformer:
    """Transforms validated JSON payloads into a strictly typed Document AST."""

    def _build_toc_node(self, body_nodes: List[ASTNode], max_depth: int = 2) -> TOCNode:
        """
        Constructs a TOCNode restricted to `max_depth` hierarchy levels.
        """
        toc_title = self.i18n.t("toc.title", default="Table of Contents")
        entries: List[Dict[str, Any]] = []

        for node in body_nodes:
            if isinstance(node, HeadingNode) and 1 <= node.level <= max_depth:
                entries.append({
                    "level": node.level,
                    "number": node.section_number,
                    "title": node.text,
                    "page": node.estimated_page or 1
                })

        return TOCNode(
            title=toc_title,
            max_depth=max_depth,
            entries=entries
        )
```

### 2.3 Implementation Specification (`src/compilers/docx_compiler.py`)

```python
# File: src/compilers/docx_compiler.py (Excerpt)
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches
from src.ast.document_ast import TOCNode

class DocxCompiler:
    """Compiles the Document AST into a native OpenXML (.docx) executive deliverable."""

    def _compile_toc_node(self, node: TOCNode) -> None:
        """
        Renders a 2-level Executive Table of Contents using native OpenXML field codes
        and pre-computed fallback entries restricted to `node.max_depth`.
        """
        # 1. Render TOC Heading
        toc_heading = self.doc.add_paragraph(node.title, style="TOCHeading")
        toc_heading.paragraph_format.space_after = Pt(12)

        # 2. Construct OpenXML Dynamic Field Instruction: TOC \o "1-2" \h \z \u
        p = self.doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run()

        fld_char_begin = OxmlElement("w:fldChar")
        fld_char_begin.set(qn("w:fldCharType"), "begin")
        fld_char_begin.set(qn("w:dirty"), "true")

        instr_text = OxmlElement("w:instrText")
        instr_text.set(qn("xml:space"), "preserve")
        instr_text.text = f'TOC \\o "1-{node.max_depth}" \\h \\z \\u'

        fld_char_separate = OxmlElement("w:fldChar")
        fld_char_separate.set(qn("w:fldCharType"), "separate")

        run._r.append(fld_char_begin)
        run._r.append(instr_text)
        run._r.append(fld_char_separate)

        # 3. Render Pre-Computed Fallback Entries (Strictly Level 1 and Level 2)
        filtered_entries = [
            e for e in (node.entries or [])
            if int(e.get("level", 1)) <= node.max_depth
        ]

        for entry in filtered_entries:
            level = int(entry.get("level", 1))
            entry_p = self.doc.add_paragraph()
            entry_p.paragraph_format.left_indent = Inches(0.25 * (level - 1))
            entry_p.paragraph_format.space_after = Pt(4 if level == 1 else 2)

            label = f"{entry.get('number', '')} {entry.get('title', '')}".strip()
            entry_run = entry_p.add_run(label)
            entry_run.bold = (level == 1)
            entry_run.font.size = Pt(10.5 if level == 1 else 9.5)

        # 4. Close Complex Field
        end_p = self.doc.add_paragraph()
        end_run = end_p.add_run()
        fld_char_end = OxmlElement("w:fldChar")
        fld_char_end.set(qn("w:fldCharType"), "end")
        end_run._r.append(fld_char_end)

        self.doc.add_page_break()
```

---

## 3. Requirement 2: Streamlined Chapter 1 Title ("Resumen Ejecutivo")

### 3.1 Architectural Design
Because Word's native `Heading 1` style applies automatic outline numbering (`1. `), the localized catalog key `sections.executive_summary` (and `annex.sections.executive_summary`) must provide the concise executive title without redundant numbering or secondary clauses.

### 3.2 Localization Catalog Update (`engine_config/locales.json`)

```json
{
  "es": {
    "toc": {
      "title": "Índice de Contenidos"
    },
    "sections": {
      "executive_summary": "Resumen Ejecutivo",
      "financial_exposure": "Exposición Financiera y Costo de Inacción",
      "technical_findings": "Hallazgos Técnicos y Evidencia Forense",
      "remediation_roadmap": "Hoja de Ruta de Remediación y Caso de Negocio",
      "strategic_pillars": "Pilares de Transformación Arquitectónica"
    }
  },
  "en": {
    "toc": {
      "title": "Table of Contents"
    },
    "sections": {
      "executive_summary": "Executive Summary",
      "financial_exposure": "Financial Exposure & Cost of Inaction",
      "technical_findings": "Technical Findings & Forensic Evidence",
      "remediation_roadmap": "Remediation Roadmap & Business Case",
      "strategic_pillars": "Architectural Transformation Pillars"
    }
  },
  "pt": {
    "toc": {
      "title": "Índice"
    },
    "sections": {
      "executive_summary": "Resumo Executivo"
    }
  },
  "fr": {
    "toc": {
      "title": "Table des Matières"
    },
    "sections": {
      "executive_summary": "Synthèse Exécutive"
    }
  },
  "de": {
    "toc": {
      "title": "Inhaltsverzeichnis"
    },
    "sections": {
      "executive_summary": "Management Summary"
    }
  }
}
```

---

## 4. Requirement 3: Forensic Root-Cause Analysis & Universal Solution for Missing Diacritics

### 4.1 Forensic Root-Cause Analysis
A forensic inspection of the pipeline reveals an asymmetry between static UI strings and synthesized narrative content:
1. **Static Catalog Strings (`engine_config/locales.json`):** Maintain 100% orthographic fidelity (*"Índice"*, *"Exposición"*, *"Diagnóstico"*, *"Cómputo"*).
2. **LLM-Synthesized Payloads (`blueprint_payload.json` & `approved_annex_payload.json`):** Contain unaccented tokens (*"saturacion"*, *"computo"*, *"mas"*, *"energia"*, *"electrica"*, *"critica"*, *"operacion"*).
3. **Why This Occurred:**
   - **Cause A (Prompt Constraint Ambiguity):** Upstream YAML prompt registries (`annex_executive_synthesizer.yaml` and `blueprint_pilar_architect_prompt.yaml`) instructed the LLM to output strict JSON schemas and avoid special characters that could break JSON parsing. Without an explicit counter-directive mandating native UTF-8 orthographic diacritics for human-readable string values, LLMs frequently fall back to ASCII-stripped tokens when generating structured JSON under high token constraints.
   - **Cause B (Absence of Post-Generation Orthographic Sanitization):** `UniversalPayloadEnricher` validated numerical invariants and schema completeness, but lacked a deterministic linguistic normalization stage to repair ASCII-degraded tokens in cached or freshly generated payloads.

### 4.2 Layer 1: Upstream Prompt Registry Governance (YAML Updates)

Both prompt registries are updated to enforce native UTF-8 orthographic compliance across **any** target language while keeping JSON keys in strict ASCII Technical English.

```yaml
# File: prompts/annex_executive_synthesizer.yaml (Excerpt)
version: "2.4.0"
id: "annex_executive_synthesizer"
system_directives:
  orthographic_and_typographic_governance: |
    CRITICAL ORTHOGRAPHIC MANDATE (UTF-8 DIACRITICS & ACCENTS):
    1. All JSON keys and schema identifiers MUST remain strictly in ASCII Technical English.
    2. All human-readable narrative values, titles, table cells, and rationales MUST be written in the requested target locale (`{{target_language}}`) using 100% grammatically and orthographically accurate native UTF-8 diacritics.
    3. NEVER strip accents or diacritical marks to simplify JSON serialization.
       - For Spanish (`es`): Mandatory use of acute accents (tildes: á, é, í, ó, ú), dieresis (ü), and eñe (ñ) in all required words (e.g., "saturación", "cómputo", "energía", "eléctrica", "crítica", "más", "operación", "financiera").
       - For French (`fr`): Mandatory use of é, è, ê, à, ç, œ.
       - For German (`de`): Mandatory use of ä, ö, ü, ß.
       - For Portuguese (`pt`): Mandatory use of ã, õ, ç, á, é, ê, ó, ô.
    4. Omitting native diacritics in executive deliverables is a critical quality failure.
```

```yaml
# File: prompts/blueprint_pilar_architect_prompt.yaml (Excerpt)
version: "2.4.0"
id: "blueprint_pilar_architect_prompt"
system_directives:
  orthographic_and_typographic_governance: |
    CRITICAL ORTHOGRAPHIC MANDATE (UTF-8 DIACRITICS & ACCENTS):
    1. Maintain strict separation between machine identifiers (ASCII Technical English JSON keys) and executive prose (native UTF-8 target language `{{target_language}}`).
    2. Every narrative string, pillar title, architectural rationale, and risk description MUST strictly adhere to the official orthographic rules of `{{target_language}}`, including all mandatory diacritical marks, tildes, umlauts, and accents.
    3. ASCII-degraded words (such as writing "computo", "saturacion", "energia", or "electrica" instead of "cómputo", "saturación", "energía", "eléctrica" in Spanish) are strictly forbidden.
```

### 4.3 Layer 2: Externalized Multi-Language Orthographic Lexicon (`engine_config/orthographic_lexicon.json`)

To comply with **Law 2 (Zero Hardcoding in Python Code)**, language-specific diacritic restoration rules are stored in an external configuration file (`engine_config/orthographic_lexicon.json`). This file supports both deterministic suffix morphologies (e.g., words ending in `-cion` -> `-ción` in Spanish) and unambiguous whole-word technical/executive lexicons per ISO 639-1 language code.

```json
{
  "es": {
    "unambiguous_tokens": {
      "computo": "cómputo",
      "energia": "energía",
      "electrica": "eléctrica",
      "electrico": "eléctrico",
      "critica": "crítica",
      "critico": "crítico",
      "criticos": "críticos",
      "criticas": "críticas",
      "tecnica": "técnica",
      "tecnico": "técnico",
      "tecnicos": "técnicos",
      "diagnostico": "diagnóstico",
      "analisis": "análisis",
      "perdida": "pérdida",
      "perdidas": "pérdidas",
      "metrica": "métrica",
      "metricas": "métricas",
      "arquitectonica": "arquitectónica",
      "arquitectonico": "arquitectónico",
      "estrategica": "estratégica",
      "estrategico": "estratégico",
      "economica": "económica",
      "economico": "económico",
      "exito": "éxito",
      "indice": "índice",
      "codigo": "código",
      "trafico": "tráfico",
      "numero": "número",
      "minimo": "mínimo",
      "maximo": "máximo",
      "optimo": "óptimo",
      "unico": "único",
      "unica": "única",
      "ademas": "además",
      " a traves ": " a través ",
      " mas ": " más "
    },
    "suffix_rules": [
      {
        "pattern": "\\b([a-zA-ZñÑáéíóúÁÉÍÓÚ]{3,})(cion)\\b",
        "replacement": "\\1ción"
      },
      {
        "pattern": "\\b([a-zA-ZñÑáéíóúÁÉÍÓÚ]{3,})(sion)\\b",
        "replacement": "\\1sión"
      },
      {
        "pattern": "\\b([a-zA-ZñÑáéíóúÁÉÍÓÚ]{3,})(logia)\\b",
        "replacement": "\\1logía"
      }
    ]
  },
  "pt": {
    "unambiguous_tokens": {
      "critico": "crítico",
      "critica": "crítica",
      "tecnico": "técnico",
      "tecnica": "técnica",
      "diagnostico": "diagnóstico",
      "analise": "análise",
      "indice": "índice"
    },
    "suffix_rules": []
  },
  "fr": {
    "unambiguous_tokens": {
      "synthese": "synthèse",
      "strategique": "stratégique",
      "securite": "sécurité",
      "reseau": "réseau"
    },
    "suffix_rules": []
  }
}
```

### 4.4 Layer 2 Implementation: Language-Aware Orthographic Normalizer (`src/enrichment/orthographic_normalizer.py` & `UniversalPayloadEnricher`)

The `OrthographicNormalizer` recursively traverses narrative fields in any JSON payload, preserving casing (Title Case, UPPERCASE, lowercase), skipping technical identifiers (URLs, snake_case keys, code blocks, metric IDs), and applying only the rules corresponding to the active `locale`.

```python
# File: src/enrichment/orthographic_normalizer.py
import json
import re
from pathlib import Path
from typing import Any, Dict, Set

class OrthographicNormalizer:
    """
    Deterministic, language-aware post-processing filter that restores missing
    orthographic diacritics in LLM-synthesized narrative strings while protecting
    technical identifiers, keys, and code artifacts.
    """

    PROTECTED_KEY_NAMES: Set[str] = {
        "id", "code", "metric_id", "pillar_id", "finding_id", "currency",
        "locale", "language", "status", "severity_code", "file_path", "url"
    }

    IDENTIFIER_REGEX = re.compile(r"^[A-Z0-9_]+$|^[a-z0-9_]+_[a-z0-9_]+$|^https?://")

    def __init__(self, lexicon_path: Path) -> None:
        self.lexicon_data: Dict[str, Any] = {}
        if lexicon_path.exists():
            with lexicon_path.open("r", encoding="utf-8") as fh:
                self.lexicon_data = json.load(fh)

    def normalize_payload(self, payload: Any, locale: str) -> Any:
        """
        Recursively normalizes human-readable string values in a payload dictionary
        for the specified ISO 639-1 locale.
        """
        lang_key = (locale or "en").split("-")[0].split("_")[0].lower()
        if lang_key not in self.lexicon_data:
            return payload

        rules = self.lexicon_data[lang_key]
        return self._walk(payload, rules, parent_key=None)

    def _walk(self, node: Any, rules: Dict[str, Any], parent_key: str | None) -> Any:
        if isinstance(node, dict):
            return {
                k: self._walk(v, rules, parent_key=k)
                for k, v in node.items()
            }
        if isinstance(node, list):
            return [self._walk(item, rules, parent_key=parent_key) for item in node]
        if isinstance(node, str):
            if parent_key in self.PROTECTED_KEY_NAMES or self.IDENTIFIER_REGEX.match(node):
                return node
            return self._normalize_text(node, rules)
        return node

    def _normalize_text(self, text: str, rules: Dict[str, Any]) -> str:
        result = text

        # 1. Apply morphological suffix rules while preserving case
        for suffix_rule in rules.get("suffix_rules", []):
            pattern = suffix_rule.get("pattern")
            replacement = suffix_rule.get("replacement")
            if pattern and replacement:
                result = re.sub(
                    pattern,
                    lambda m: self._preserve_suffix_case(m, replacement),
                    result
                )

        # 2. Apply unambiguous whole-word and phrase replacements
        unambiguous: Dict[str, str] = rules.get("unambiguous_tokens", {})
        for raw_token, accented_token in unambiguous.items():
            if raw_token.startswith(" ") and raw_token.endswith(" "):
                result = result.replace(raw_token, accented_token)
            else:
                word_regex = re.compile(rf"\b{re.escape(raw_token)}\b", flags=re.IGNORECASE)
                result = word_regex.sub(
                    lambda m, target=accented_token: self._match_casing(m.group(0), target),
                    result
                )

        return result

    @staticmethod
    def _match_casing(source: str, target: str) -> str:
        if source.isupper():
            return target.upper()
        if source[0].isupper():
            return target.capitalize()
        return target.lower()

    @staticmethod
    def _preserve_suffix_case(match: re.Match, replacement_template: str) -> str:
        full_word = match.group(0)
        expanded = match.expand(replacement_template)
        if full_word.isupper():
            return expanded.upper()
        return expanded
```

```python
# File: src/enrichment/universal_payload_enricher.py (Integration Excerpt)
from pathlib import Path
from typing import Dict, Any
from src.enrichment.orthographic_normalizer import OrthographicNormalizer

class UniversalPayloadEnricher:
    """
    Enriches, validates, and normalizes raw LLM payloads prior to AST transformation.
    """

    def __init__(self, config_dir: Path) -> None:
        self.config_dir = config_dir
        self.orthographic_normalizer = OrthographicNormalizer(
            lexicon_path=self.config_dir / "orthographic_lexicon.json"
        )

    def enrich(self, payload: Dict[str, Any], target_locale: str) -> Dict[str, Any]:
        """
        Executes deterministic financial, structural, and orthographic enrichment.
        """
        # Step 1: Restore and enforce native UTF-8 orthographic diacritics
        normalized_payload = self.orthographic_normalizer.normalize_payload(
            payload=payload,
            locale=target_locale
        )

        # Step 2: Proceed with existing structural & financial enrichment passes
        return normalized_payload
```

---

## 5. Verification & Acceptance Criteria Matrix

| Requirement ID | Verification Target | Expected Outcome |
| :--- | :--- | :--- |
| **REQ-1 (2-Level TOC)** | `TOCNode.max_depth` & OpenXML Field | Word TOC field equals `TOC \o "1-2" \h \z \u` and fallback entries contain only `level <= 2`. |
| **REQ-2 (Chapter 1 Title)** | `locales.json` -> `sections.executive_summary` | Renders cleanly as `1. Resumen Ejecutivo` (`es`) or `1. Executive Summary` (`en`) with zero redundant clauses. |
| **REQ-3A (Prompt Governance)** | `annex_executive_synthesizer.yaml` & `blueprint_pilar_architect_prompt.yaml` | Mandates strict UTF-8 diacritics in all target languages while keeping JSON keys in ASCII Technical English. |
| **REQ-3B (Payload Normalization)** | `OrthographicNormalizer` inside `UniversalPayloadEnricher` | Automatically repairs ASCII-stripped Spanish/French/Portuguese tokens (`saturacion` $\rightarrow$ `saturación`, `computo` $\rightarrow$ `cómputo`, `energia electrica` $\rightarrow$ `energía eléctrica`) prior to AST compilation without altering code identifiers. |