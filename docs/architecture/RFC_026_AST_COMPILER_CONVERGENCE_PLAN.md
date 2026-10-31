---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
- docs/architecture/split_brain_remediation_plan.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# RFC-026: AST Compiler Convergence & Zero-Entropy Document Synthesis

**Status:** APPROVED FOR IMMEDIATE EXECUTION  
**Authors:** Principal Systems Architecture & Core Infrastructure Group  
**Target Subsystem:** `Assessment Engine` / Document Synthesis Pipeline  
**Classification:** Tier-1 Architectural Remediation (Split-Brain Elimination)  

---

## 1. Executive Summary & Problem Formalization

### 1.1 Context & Symptom Topology
The Assessment Engine currently suffers from a critical **Split-Brain Architecture (Split-Brain #1)** within its document synthesis layer. Two diametrically opposed compilation paradigms coexist in the runtime graph:

1. **Engine A (Legacy Imperative Mutator — `render_tower_annex_from_template.py`):** Operates via fragile string interpolation (`{{TAG}}`) directly against a binary OpenXML `.docx` template. It forces complex domain narratives into 17 rigid micro-tables. Because it mutates XML runs without maintaining a unified style state tree, it strips background shading `<w:shd>` nodes while preserving `<w:color w:val="FFFFFF"/>`, resulting in the catastrophic **White-on-White (`#FFFFFF` on `#FFFFFF`) visibility bug**.
2. **Engine B (Modern Declarative AST — `payload_to_ast.py` $\rightarrow$ `DocxCompiler`):** Implements a deterministic, multi-pass compilation pipeline. It transforms rich domain payloads into a 5-chapter Abstract Syntax Tree (AST), synthesizing a 144-paragraph, 11-table executive technical book with strict typographic hierarchy and consulting-grade formatting.

Currently, the Model Context Protocol entrypoint (`mcp_server.py`) routes automated execution calls to **Engine A**, bypassing **Engine B**. Consequently, the high-precision output of our Counterexample-Guided Abstraction Refinement (CEGAR) engine—which calculates granular risk exposures such as the **1.05M € Annualized Loss Expectancy (ALE)** across HPE SimpliVity hyperconverged nodes, NetApp AFF storage arrays, thermal CRAH units, and remote quarry links for the Molins CIO—is truncated and rendered illegible. Furthermore, missing localization keys in `engine_config/locales.json` cause raw fallback tokens (e.g., `chapter3title`) to leak into production artifacts.

```
                      CURRENT SPLIT-BRAIN TOPOLOGY (BROKEN)
                      =====================================
                                        
                  +---> [Engine A: Binary Mutator] ---> 17 Micro-Tables / #FFFFFF Bug
                  |     (render_tower_annex_from_template.py)
[CEGAR Payload] --+
(1.05M€ ALE,      |
 HPE, NetApp)     +---> [Engine B: AST Compiler]   ---> 5-Chapter Book (144 Paras, 11 Tables)
                        (payload_to_ast.py -> DocxCompiler)


                      TARGET CONVERGED TOPOLOGY (RFC-026)
                      ===================================

[CEGAR Payload] ------> [IR Builder: payload_to_ast.py] ------> [AST Root: DocumentNode]
                                                                       |
                        +----------------------------------------------+
                        | Pass 1: i18n Resolution (Strict Dictionary Lookup)
                        | Pass 2: Contrast Invariant Verifier (WCAG Luminance Gate)
                        v
                  [Backend Codegen: DocxCompiler (GoF Visitor)]
                        |
                        v
          [Golden Master .docx Artifact] (Zero-Entropy, Full Narrative Synthesis)
```

### 1.2 Theoretical Justification: LLVM Multi-Pass Compilation & GoF Visitor Pattern
String-replacement templating over binary formats violates the fundamental principles of compiler design by conflating **syntax tree construction**, **semantic analysis**, and **physical code generation** into a single, untestable pass.

To achieve **Zero-Entropy Document Synthesis**, RFC-026 formalizes the document generation pipeline as a **Multi-Pass Compiler** modeled after the **LLVM Architecture**:

1. **Frontend (Domain Payload to Intermediate Representation):** `payload_to_ast.py` acts as the compiler frontend. It ingests the strongly-typed CEGAR JSON payload and lowers it into a platform-agnostic Intermediate Representation (IR)—our **Document Abstract Syntax Tree (AST)**. This layer structures the 5 chapters, narrative prose, financial tables, and cross-cutting diagnostics without any awareness of OpenXML (`python-docx`).
2. **Middle-End (Optimization & Invariant Verification Passes):** Before emitting a single byte of OpenXML, the AST undergoes pure functional transformation passes:
   - *Lexical Localization Pass:* Resolves all semantic i18n symbolic references against `locales.json`, guaranteeing zero raw token leakage.
   - *Contrast & Style Safety Pass:* Evaluates node style descriptors against physical contrast invariants, mathematically eliminating the possibility of `#FFFFFF` text on light backgrounds.
3. **Backend (Code Generation via GoF Visitor Pattern):** `DocxCompiler` implements the classic **Gang of Four (GoF) Visitor Pattern** (`NodeVisitor`). It traverses the verified AST deterministically (`visit_DocumentNode`, `visit_ChapterNode`, `visit_ParagraphNode`, `visit_TableNode`), translating high-level semantic constructs into physical OpenXML `<w:p>`, `<w:tbl>`, and `<w:tcPr>` structures. 

By severing Engine A and enforcing this strict separation of concerns, we guarantee that the rich narrative context required by the CIO of Molins—explaining *why* the quarry environments and data center CRAH units yield a 1.05M € ALE—is synthesized with 100% structural and visual fidelity.

---

## 2. The 4 Non-Negotiable Architectural Invariants

All code merged under RFC-026 must satisfy four mathematical and structural invariants enforced at compile-time, runtime, and CI/CD gate execution:

### Invariant I: Zero Split-Brain (Single Path of Synthesis)
$$\forall r \in \text{Requests}_{\text{Synthesis}}, \quad \text{Route}(r) \equiv \text{Pipeline}_{\text{AST}}(\text{Payload}) \circ \text{DocxCompiler}$$
There shall exist exactly **one** execution path for converting domain assessment payloads into `.docx` binaries. Imperative binary template mutation (`render_tower_annex_from_template.py`) is permanently excised from the runtime call graph.

### Invariant II: Physical Contrast & Luminance Guarantee
$$\forall n \in \text{AST}_{\text{TextNodes}}, \quad \text{Color}(n) = \text{\#FFFFFF} \implies \text{Luminance}(\text{BgColor}(\text{Parent}(n))) < 0.18$$
No AST text run or table cell may be compiled with white foreground color (`#FFFFFF` or RGB `(255, 255, 255)`) unless its immediate bounding container explicitly declares a dark background shading fill (e.g., Primary Navy `#0A192F` or Slate `#1E293B`) verified via relative luminance calculation. If background shading is `None`, `auto`, or light, foreground color **must** deterministically fall back to Charcoal (`#111827`).

### Invariant III: Total Declarative i18n Bijection
$$\forall k \in \text{Keys}_{\text{AST}}, \quad k \in \text{dom}(\text{Locales}_{\text{JSON}}) \land \text{Locales}_{\text{JSON}}(k) \neq \emptyset$$
Every structural heading, table title, and cross-cutting diagnostic label emitted by `payload_to_ast.py` must resolve bijectively against `engine_config/locales.json` across all supported languages (`es`, `en`, `ca`). Heuristic string normalization (e.g., stripping underscores to produce `chapter3title`) is strictly prohibited; missing keys must raise a hard `MissingLocalizationKeyError` during AST construction.

### Invariant IV: Pure Clean Architecture Separation
$$\text{Dependencies}(\text{Domain AST}) \cap \text{Dependencies}(\text{OpenXML Infrastructure}) = \emptyset$$
The AST intermediate representation (`ast_nodes.py`, `payload_to_ast.py`) must remain 100% pure Python data structures (`dataclasses` / `Pydantic`), completely agnostic of `python-docx`, XML namespaces, or file I/O. All OpenXML manipulation is strictly encapsulated within the `DocxCompiler` visitor backend.

---

## 3. Detailed 4-Step Surgical Implementation Roadmap

### PR-1: Declarative i18n Resolution (`engine_config/locales.json`)
* **Objective:** Eliminate raw fallback token leakage (`chapter3title`, etc.) by registering the missing structural keys in the localization registry and upgrading the i18n resolver to fail-fast mode.
* **Target Files:**
  - `engine_config/locales.json`
  - `src/assessment_engine/i18n/resolver.py`
* **Surgical Diff Specification (`engine_config/locales.json`):**
  Inject the three missing canonical keys across `es` (Spanish - Primary Molins target) and `en` (English):
  ```json
  {
    "es": {
      "chapter_3_diagnosis_cross_cutting": "Capítulo 3: Diagnóstico Transversal y Correlación de Riesgos Sistémicos",
      "diagnosis_performance_matrix_title": "Matriz de Rendimiento Operativo, Resiliencia y Degradación de Activos",
      "decision_matrix_title": "Matriz de Decisión Ejecutiva y Priorización de Inversiones (CAPEX/OPEX)"
    },
    "en": {
      "chapter_3_diagnosis_cross_cutting": "Chapter 3: Cross-Cutting Diagnosis & Systemic Risk Correlation",
      "diagnosis_performance_matrix_title": "Operational Performance, Resilience & Asset Degradation Matrix",
      "decision_matrix_title": "Executive Decision & Investment Prioritization Matrix (CAPEX/OPEX)"
    }
  }
  ```
* **Resolver Hardening:** Remove regex-based alphanumeric fallback stripping (`re.sub(r'[^a-zA-Z0-9]', '', key)`). Enforce strict dictionary lookup with explicit exception raising if a key is absent.

---

### PR-2: DocxCompiler AST Invariant Hardening (`src/assessment_engine/compiler/docx_compiler.py`)
* **Objective:** Enforce **Invariant II** at the AST-to-OpenXML boundary, making the white-on-white bug physically impossible regardless of upstream style misconfigurations.
* **Target Files:**
  - `src/assessment_engine/compiler/docx_compiler.py`
  - `src/assessment_engine/compiler/style_invariants.py` (New Module)
* **Implementation Details:**
  1. Implement WCAG 2.1 relative luminance calculation for hex RGB colors:
     $$L = 0.2126 \times R_s + 0.7152 \times G_s + 0.0722 \times B_s$$
  2. Create a compiler gate `enforce_contrast_invariant(fg_hex: str, bg_hex: Optional[str]) -> str` invoked inside `DocxCompiler._apply_run_formatting()` and `DocxCompiler._apply_cell_formatting()`.
  3. Whenever `bg_hex` is `None`, `"FFFFFF"`, `"AUTO"`, or has $L > 0.45$, and `fg_hex` has $L > 0.80$ (such as `"FFFFFF"`), the compiler logs a structured warning and overrides `fg_hex` to `"111827"` (Executive Dark Charcoal).
  4. When `bg_hex` is dark (e.g., Table Header Navy `"0A192F"`), the compiler explicitly constructs and appends the OpenXML `<w:shd w:val="clear" w:color="auto" w:fill="0A192F"/>` element to `<w:tcPr>` *before* setting `<w:color w:val="FFFFFF"/>` on the child run.

---

### PR-3: Single Source of Truth Cutover in MCP Server & Facade
* **Objective:** Sever Engine A (`render_tower_annex_from_template.py`) from `mcp_server.py` and route all document synthesis requests through the declarative AST pipeline (`payload_to_ast.py` $\rightarrow$ `DocxCompiler`), ensuring full integration of CEGAR domain narratives.
* **Target Files:**
  - `src/mcp_server.py`
  - `src/assessment_engine/facade/document_synthesizer.py`
  - `src/assessment_engine/legacy/render_tower_annex_from_template.py` (Tombstoned/Removed)
* **Implementation Details:**
  1. Refactor the MCP tool handler `generate_tower_annex` in `mcp_server.py` to invoke `DocumentSynthesizerFacade.compile_tower_annex(payload, locale, output_path)`.
  2. Inside `payload_to_ast.py`, verify that the CEGAR output nodes (specifically the quantitative risk models detailing the **1.05M € ALE**, **HPE SimpliVity** cluster saturation, **NetApp** storage latency, **CRAH** thermal single-points-of-failure, and **industrial quarry** network SPOFs) are mapped into structured `ChapterNode` narratives (Chapters 1 through 5), combining executive prose paragraphs with the 11 analytical tables.
  3. Replace the body of `render_tower_annex_from_template.py` with a hard `RuntimeError("DEPRECATED_SPLIT_BRAIN_ENGINE: Use AST DocxCompiler via RFC-026")` before deleting the file in the final commit of the PR, ensuring no dynamic imports silently succeed.

---

### PR-4: Architectural Fitness Gate & Molins Golden Master Verification
* **Objective:** Establish an automated CI/CD fitness function (`test_no_binary_template_split_brain.py`) that prevents regression into template mutation and validates the compiled Molins artifact against strict structural and visual telemetry.
* **Target Files:**
  - `tests/architecture/test_no_binary_template_split_brain.py`
  - `tests/integration/test_molins_golden_master_ast.py`
* **Verification Scope:**
  1. **Static AST Inspection of Codebase:** Parse the Python AST of `src/` to verify zero imports or references to `render_tower_annex_from_template` or `{{TAG}}` regex patterns.
  2. **OpenXML Binary Inspection of Output:** Compile the canonical Molins CEGAR payload and inspect the resulting `.docx` XML tree (`word/document.xml`):
     - Assert Paragraph Count $\ge 140$ (Target: 144 paragraphs of cohesive narrative prose).
     - Assert Table Count $== 11$ (Eliminating the 17 broken micro-tables).
     - Assert Zero Raw i18n Tokens (`chapter3title`, `chapter_3_diagnosis_cross_cutting`, etc. must not appear in `document.xml`).
     - Assert Domain Telemetry Presence: Verify exact occurrences of `"1,05M €"` (or `"1.05M €"`), `"HPE SimpliVity"`, `"NetApp"`, `"CRAH"`, and `"canteras"` across narrative paragraphs and decision matrices.
     - Assert Zero White-on-White Runs: XPath query over all `<w:r>` nodes containing `<w:color w:val="FFFFFF"/>` must prove that their ancestor `<w:tcPr>` or `<w:pPr>` contains a valid dark `<w:shd w:fill="..."/>` attribute.

---

## 4. Exact Class & Function Signatures

The following production-grade signatures and core implementations define the exact contract for RFC-026.

### 4.1 `src/assessment_engine/i18n/resolver.py`
```python
from pathlib import Path
from typing import Dict, Any
import json


class MissingLocalizationKeyError(KeyError):
    """Raised when an AST node requests an unregistered i18n key (Invariant III)."""
    pass


class DeclarativeI18nResolver:
    """Strict, zero-fallback localization resolver for AST compilation."""

    def __init__(self, locales_path: Path) -> None:
        self._locales_path: Path = locales_path
        self._registry: Dict[str, Dict[str, str]] = self._load_registry()

    def _load_registry(self) -> Dict[str, Dict[str, str]]:
        if not self._locales_path.exists():
            raise FileNotFoundError(f"Locales configuration missing at: {self._locales_path}")
        with self._locales_path.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        return data

    def resolve(self, key: str, locale: str = "es") -> str:
        if locale not in self._registry:
            raise MissingLocalizationKeyError(f"Unsupported locale '{locale}' requested.")
        
        locale_map = self._registry[locale]
        if key not in locale_map or not str(locale_map[key]).strip():
            raise MissingLocalizationKeyError(
                f"Invariant III Violation: Localization key '{key}' is missing or empty "
                f"for locale '{locale}' in {self._locales_path}."
            )
        return locale_map[key]
```

### 4.2 `src/assessment_engine/compiler/style_invariants.py`
```python
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ContrastInvariantViolationError(ValueError):
    """Raised when strict mode is enabled and a contrast violation is detected."""
    pass


class StyleInvariantGuard:
    """Enforces Invariant II: Physical Contrast & Luminance Guarantee."""

    DEFAULT_DARK_TEXT_HEX: str = "111827"  # Executive Charcoal
    DEFAULT_LIGHT_TEXT_HEX: str = "FFFFFF"  # Pure White
    DARK_BG_LUMINANCE_THRESHOLD: float = 0.18
    LIGHT_FG_LUMINANCE_THRESHOLD: float = 0.80

    @staticmethod
    def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
        clean = hex_str.strip().lstrip("#").upper()
        if len(clean) != 6:
            raise ValueError(f"Invalid RGB hex string: '{hex_str}'")
        return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)

    @classmethod
    def relative_luminance(cls, hex_str: str) -> float:
        """Calculates WCAG 2.1 relative luminance from a 6-char hex string."""
        r, g, b = cls.hex_to_rgb(hex_str)
        
        def _channel(c: int) -> float:
            s = c / 255.0
            return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4

        return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)

    @classmethod
    def enforce_safe_foreground(
        cls,
        fg_hex: Optional[str],
        bg_hex: Optional[str],
        *,
        strict: bool = False
    ) -> str:
        """
        Guarantees that light/white text is never emitted over an unshaded or light background.
        Returns a validated 6-character uppercase hex string (without '#').
        """
        normalized_fg = (fg_hex or cls.DEFAULT_DARK_TEXT_HEX).strip().lstrip("#").upper()
        normalized_bg = (bg_hex or "").strip().lstrip("#").upper()

        fg_lum = cls.relative_luminance(normalized_fg)

        # Check if foreground is dangerously light (e.g., #FFFFFF)
        if fg_lum >= cls.LIGHT_FG_LUMINANCE_THRESHOLD:
            is_bg_missing = normalized_bg in ("", "NONE", "AUTO", "CLEAR")
            bg_lum = 1.0 if is_bg_missing else cls.relative_luminance(normalized_bg)

            if bg_lum >= cls.DARK_BG_LUMINANCE_THRESHOLD:
                msg = (
                    f"Invariant II Triggered: Prohibited light foreground #{normalized_fg} "
                    f"(L={fg_lum:.2f}) over background '{bg_hex}' (L={bg_lum:.2f}). "
                    f"Coercing foreground to #{cls.DEFAULT_DARK_TEXT_HEX}."
                )
                if strict:
                    raise ContrastInvariantViolationError(msg)
                logger.warning(msg)
                return cls.DEFAULT_DARK_TEXT_HEX

        return normalized_fg
```

### 4.3 `src/assessment_engine/compiler/docx_compiler.py`
```python
from pathlib import Path
from typing import Optional
import docx
from docx.shared import RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.table import _Cell
from docx.text.run import Run

from src.assessment_engine.ast.nodes import (
    ASTNode,
    DocumentNode,
    ChapterNode,
    ParagraphNode,
    TableNode,
    TableCellNode,
)
from src.assessment_engine.compiler.style_invariants import StyleInvariantGuard


class NodeVisitor:
    """GoF Visitor Base Class for AST Traversal."""

    def visit(self, node: ASTNode) -> None:
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node: ASTNode) -> None:
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined in compiler.")


class DocxCompiler(NodeVisitor):
    """
    Deterministic Multi-Pass AST Backend Compiler for OpenXML (.docx).
    Enforces Invariants II and IV.
    """

    def __init__(self, strict_contrast: bool = False) -> None:
        self._doc = docx.Document()
        self._strict_contrast = strict_contrast
        self._current_bg_context: Optional[str] = None

    def compile(self, root: DocumentNode, output_path: Path) -> Path:
        self.visit(root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._doc.save(str(output_path))
        return output_path

    def visit_DocumentNode(self, node: DocumentNode) -> None:
        for chapter in node.chapters:
            self.visit(chapter)

    def visit_ChapterNode(self, node: ChapterNode) -> None:
        heading_para = self._doc.add_heading(level=node.level)
        run = heading_para.add_run(node.title)
        self._apply_run_style(run, fg_hex=node.fg_color_hex, bg_hex=None, bold=True)
        for child in node.children:
            self.visit(child)

    def visit_ParagraphNode(self, node: ParagraphNode) -> None:
        para = self._doc.add_paragraph()
        for span in node.spans:
            run = para.add_run(span.text)
            self._apply_run_style(
                run=run,
                fg_hex=span.fg_color_hex,
                bg_hex=self._current_bg_context,
                bold=span.bold,
                italic=span.italic,
            )

    def visit_TableNode(self, node: TableNode) -> None:
        table = self._doc.add_table(rows=len(node.rows), cols=node.col_count)
        for r_idx, row_node in enumerate(node.rows):
            for c_idx, cell_node in enumerate(row_node.cells):
                 docx_cell = table.cell(r_idx, c_idx)
                 self._compile_table_cell(docx_cell, cell_node)

    def _compile_table_cell(self, docx_cell: _Cell, cell_node: TableCellNode) -> None:
        prev_bg = self._current_bg_context
        self._current_bg_context = cell_node.bg_color_hex

        if cell_node.bg_color_hex:
            self._set_cell_background_xml(docx_cell, cell_node.bg_color_hex)

        # Clear default empty paragraph before visiting cell children
        docx_cell.text = ""
        for idx, para_node in enumerate(cell_node.paragraphs):
            para = docx_cell.paragraphs[0] if idx == 0 else docx_cell.add_paragraph()
            for span in para_node.spans:
                run = para.add_run(span.text)
                self._apply_run_style(
                    run=run,
                    fg_hex=span.fg_color_hex,
                    bg_hex=self._current_bg_context,
                    bold=span.bold,
                    italic=span.italic,
                )

        self._current_bg_context = prev_bg

    @staticmethod
    def _set_cell_background_xml(cell: _Cell, bg_hex: str) -> None:
        """Physically writes <w:shd w:val='clear' w:color='auto' w:fill='HEX'/> into <w:tcPr>."""
        clean_hex = bg_hex.strip().lstrip("#").upper()
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), clean_hex)
        tc_pr.append(shd)

    def _apply_run_style(
        self,
        run: Run,
        fg_hex: Optional[str],
        bg_hex: Optional[str],
        bold: bool = False,
        italic: bool = False,
    ) -> None:
        safe_fg = StyleInvariantGuard.enforce_safe_foreground(
            fg_hex=fg_hex,
            bg_hex=bg_hex,
            strict=self._strict_contrast,
        )
        r, g, b = StyleInvariantGuard.hex_to_rgb(safe_fg)
        run.font.color.rgb = RGBColor(r, g, b)
        run.bold = bold
        run.italic = italic
```

### 4.4 `src/assessment_engine/ast/payload_to_ast.py` & `src/mcp_server.py` Cutover
```python
# src/assessment_engine/ast/payload_to_ast.py
from pathlib import Path
from typing import Dict, Any
from src.assessment_engine.ast.nodes import DocumentNode
from src.assessment_engine.i18n.resolver import DeclarativeI18nResolver


def build_tower_annex_ast(
    cegar_payload: Dict[str, Any],
    i18n: DeclarativeI18nResolver,
    locale: str = "es",
) -> DocumentNode:
    """
    Compiler Frontend: Lowers CEGAR Domain Payload into a 5-Chapter DocumentNode AST.
    Resolves 'chapter_3_diagnosis_cross_cutting', 'diagnosis_performance_matrix_title',
    and 'decision_matrix_title' deterministically via DeclarativeI18nResolver.
    """
    # Implementation constructs the 5 chapters, 144 narrative paragraphs, and 11 tables
    ...
```

```python
# src/mcp_server.py (Cutover Entrypoint)
from pathlib import Path
from typing import Dict, Any
from src.assessment_engine.i18n.resolver import DeclarativeI18nResolver
from src.assessment_engine.ast.payload_to_ast import build_tower_annex_ast
from src.assessment_engine.compiler.docx_compiler import DocxCompiler

LOCALES_PATH = Path("engine_config/locales.json")


def mcp_compile_tower_annex(
    payload: Dict[str, Any],
    output_docx_path: str,
    locale: str = "es",
) -> Dict[str, Any]:
    """
    MCP Tool Entrypoint (RFC-026 Converged).
    Routes 100% of synthesis workloads through the Declarative AST Pipeline.
    """
    resolver = DeclarativeI18nResolver(locales_path=LOCALES_PATH)
    ast_root = build_tower_annex_ast(cegar_payload=payload, i18n=resolver, locale=locale)
    
    compiler = DocxCompiler(strict_contrast=False)
    compiled_path = compiler.compile(root=ast_root, output_path=Path(output_docx_path))

    return {
        "status": "SUCCESS",
        "compiler_engine": "AST_DOCX_COMPILER_V2",
        "artifact_path": str(compiled_path.resolve()),
        "chapters_synthesized": len(ast_root.chapters),
    }
```

### 4.5 `tests/architecture/test_no_binary_template_split_brain.py`
```python
import ast
from pathlib import Path
import docx
from docx.oxml.ns import qn
import pytest

from src.mcp_server import mcp_compile_tower_annex

SRC_ROOT = Path("src")
FORBIDDEN_MODULES = {"render_tower_annex_from_template"}


def test_invariant_i_no_legacy_template_imports_in_src() -> None:
    """Ensures Engine A is completely severed from the runtime import graph."""
    for py_file in SRC_ROOT.rglob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert all(f not in alias.name for f in FORBIDDEN_MODULES), (
                        f"Split-Brain Violation in {py_file}: Forbidden import '{alias.name}'"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert all(f not in node.module for f in FORBIDDEN_MODULES), (
                    f"Split-Brain Violation in {py_file}: Forbidden import from '{node.module}'"
                )


def test_molins_golden_master_ast_synthesis(
    molins_cegar_payload: dict,
    tmp_path: Path,
) -> None:
    """
    Validates Invariants II, III, and IV on the compiled Molins Golden Master artifact.
    """
    out_file = tmp_path / "Molins_Tower_Annex_AST.docx"
    result = mcp_compile_tower_annex(
        payload=molins_cegar_payload,
        output_docx_path=str(out_file),
        locale="es",
    )
    assert result["status"] == "SUCCESS"
    assert out_file.exists()

    doc = docx.Document(str(out_file))

    # 1. Structural Book Topology Verification (5-Chapter AST Book vs 17 Micro-tables)
    non_empty_paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    assert len(non_empty_paras) >= 140, f"Expected ~144 narrative paragraphs, got {len(non_empty_paras)}"
    assert len(doc.tables) == 11, f"Expected exactly 11 analytical tables, got {len(doc.tables)}"

    full_text = "\n".join(non_empty_paras) + "\n" + "\n".join(
        cell.text for tbl in doc.tables for row in tbl.rows for cell in row.cells
    )

    # 2. Invariant III: Zero Raw i18n Token Leakage
    forbidden_tokens = [
        "chapter3title",
        "chapter_3_diagnosis_cross_cutting",
        "diagnosis_performance_matrix_title",
        "decision_matrix_title",
        "{{",
        "}}",
    ]
    for token in forbidden_tokens:
        assert token not in full_text, f"Raw localization/template token leaked: '{token}'"

    # Verify exact localized Spanish headers are present
    assert "Capítulo 3: Diagnóstico Transversal y Correlación de Riesgos Sistémicos" in full_text
    assert "Matriz de Rendimiento Operativo, Resiliencia y Degradación de Activos" in full_text
    assert "Matriz de Decisión Ejecutiva y Priorización de Inversiones (CAPEX/OPEX)" in full_text

    # 3. CEGAR Domain Narrative Fidelity Check (Molins Specifics)
    required_domain_entities = ["HPE SimpliVity", "NetApp", "CRAH", "canteras", "1,05M €"]
    for entity in required_domain_entities:
        assert entity in full_text, f"Missing critical CEGAR domain narrative entity: '{entity}'"

    # 4. Invariant II: Physical XML Inspection for White-on-White (#FFFFFF) Bug
    xml_root = doc._element
    for color_el in xml_root.iter(qn("w:color")):
        val = color_el.get(qn("w:val"), "").upper()
        if val == "FFFFFF":
            # Ascend to enclosing cell <w:tc> or paragraph <w:p> and verify dark <w:shd>
            parent = color_el.getparent()
            has_dark_shading = False
            while parent is not None:
                if parent.tag in (qn("w:tc"), qn("w:p")):
                    shd_elements = parent.findall(f".//{qn('w:shd')}")
                    for shd in shd_elements:
                        fill = shd.get(qn("w:fill"), "").upper()
                        if fill not in ("", "FFFFFF", "AUTO", "CLEAR"):
                            has_dark_shading = True
                            break
                if has_dark_shading:
                    break
                parent = parent.getparent()

            assert has_dark_shading, (
                "Invariant II Violation: Found <w:color w:val='FFFFFF'/> without an enclosing "
                "dark <w:shd w:fill='...'/> element in OpenXML tree!"
            )
```

---

## 5. Definition of Done & Success Metrics

RFC-026 shall be marked **COMPLETE** and closed only when all metrics in the verification matrix below transition from their legacy baseline to the target threshold in the main CI/CD pipeline:

| Telemetry Dimension | Legacy Baseline (Engine A Split-Brain) | Target Threshold (RFC-026 AST Converged) | Verification Mechanism |
| :--- | :--- | :--- | :--- |
| **Active Synthesis Engines** | `2` (Imperative Template + AST) | **`1` (Pure AST `DocxCompiler`)** | `test_invariant_i_no_legacy_template_imports_in_src` |
| **Narrative Paragraph Count** | `< 25` (Fragmented snippets) | **`144` Paragraphs ($\ge 140$ gate)** | `test_molins_golden_master_ast_synthesis` |
| **Structural Table Count** | `17` (Broken micro-tables) | **`11` Consulting-Grade Tables** | OpenXML `<w:tbl>` count assertion |
| **White-on-White (`#FFFFFF`) Runs** | $> 40$ illegible table cells | **`0` Occurrences (Mathematically Prohibited)** | `StyleInvariantGuard` + XPath `<w:color>` audit |
| **Unresolved i18n Tokens** | `3` (`chapter3title`, etc.) | **`0` Unresolved Keys (Fail-Fast Gate)** | `DeclarativeI18nResolver` + String audit |
| **CEGAR Narrative Completeness** | Truncated metrics, zero prose | **100% Entity Retention** (`1,05M €`, `HPE SimpliVity`, `NetApp`, `CRAH`, `canteras`) | Golden Master corpus assertion |