#!/usr/bin/env python
"""Enrich Docstrings Script.
Parses Python files in src/ports/ and src/infrastructure/, identifies public classes,
functions, and methods, and uses Gemini to enrich/generate Google-style docstrings
complete with Args, Returns, and Raises sections.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import libcst as cst

# Set up paths to allow importing project modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from assessment_engine.infrastructure.ai_client import call_agent

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("enrich_docstrings")

# Configuration
CONCURRENCY_LIMIT = 5
MODEL_NAME = os.environ.get("MODEL_TIER_PRO", "gemini-2.5-pro")


def get_raw_string_content(orig_str: str) -> str:
    """Strips raw/format/bytes prefixes and matching enclosing quotes from a Python string literal."""
    for i, char in enumerate(orig_str):
        if char in ("'", '"'):
            orig_str[:i]
            orig_str_no_prefix = orig_str[i:]
            break
    else:
        orig_str_no_prefix = orig_str

    if orig_str_no_prefix.startswith('"""') and orig_str_no_prefix.endswith('"""'):
        return orig_str_no_prefix[3:-3]
    elif orig_str_no_prefix.startswith("'''") and orig_str_no_prefix.endswith("'''"):
        return orig_str_no_prefix[3:-3]
    elif orig_str_no_prefix.startswith('"') and orig_str_no_prefix.endswith('"'):
        return orig_str_no_prefix[1:-1]
    elif orig_str_no_prefix.startswith("'") and orig_str_no_prefix.endswith("'"):
        return orig_str_no_prefix[1:-1]
    return orig_str_no_prefix


def indent_docstring(doc_text: str, indent: str) -> str:
    """Format a multi-line docstring text with the correct body indentation."""
    lines = doc_text.strip().splitlines()
    if not lines:
        return '"""\n' + indent + '"""'

    indented_lines = [lines[0]]
    for line in lines[1:]:
        if line.strip():
            indented_lines.append(indent + line)
        else:
            indented_lines.append("")

    return '"""' + "\n".join(indented_lines) + "\n" + indent + '"""'


def is_public_name(name: str) -> bool:
    """Checks if a class or function name is public or is __init__."""
    if name == "__init__":
        return True
    return not name.startswith("_")


SYSTEM_INSTRUCTION = """
You are a Staff Infrastructure Engineer at Google. Your goal is to generate or enrich the Python docstring for the provided code block with absolute technical precision and elegance.

Rules:
1. Analyze the complexity of the provided class or function:
   - TRIVIAL HELPERS (e.g., simple getters, setters, mathematical utilities like averages, slugification, string formatters, or simple data wrappers of less than 10 lines with complexity <= 2):
     --> You must write ONLY a single, highly concise, objective one-line summary docstring in the imperative mood (e.g., "Return the mathematical mean of a list of floats.").
     --> Do NOT include "Args:", "Returns:", or "Raises:" sections for these trivial helpers. This prevents over-engineering and reduces noise.
   - COMPLEX LOGIC, PORTS, AND PUBLIC APIS:
     --> You must write a comprehensive, formal Google-style docstring complete with detailed "Args:", "Returns:", and "Raises:" sections based on the code's exact signatures, types, and logic.
2. Maintain strict, impassive, academic English. Never use self-congratulatory, promotional, or hype-laden words (such as "SOTA", "bulletproof", "seamless", "perfect", "flawless", etc.).
3. Return ONLY the raw string text content of the docstring. Do NOT wrap it in triple quotes \"\"\" or any markdown blocks. Do not add conversational preambles or postambles.
"""


async def generate_enriched_docstring(
    node_code: str, existing_doc: str, file_path: Path
) -> str:
    """Asks Gemini to generate/enrich a Google-style docstring based on function context."""
    prompt = f"File: {file_path.name}\n\n"
    if existing_doc:
        prompt += f"Existing Docstring:\n{existing_doc}\n\n"
    prompt += f"Source Code Block:\n{node_code}\n"

    try:
        response_text = await call_agent(
            model_name=MODEL_NAME, prompt=prompt, instruction=SYSTEM_INSTRUCTION
        )

        # Clean any raw response markdown enclosing quotes if the model forgot the rule
        clean_text = str(response_text).strip()
        if clean_text.startswith("```"):
            lines = clean_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_text = "\n".join(lines).strip()

        # Strip enclosing docstring quotes if returned by the model
        if clean_text.startswith('"""') and clean_text.endswith('"""'):
            clean_text = clean_text[3:-3].strip()
        elif clean_text.startswith("'''") and clean_text.endswith("'''"):
            clean_text = clean_text[3:-3].strip()

        return clean_text
    except Exception as e:
        logger.error(f"Failed to generate enriched docstring for node: {e}")
        return ""


class DocstringCollector(cst.CSTVisitor):
    """Pre-collects all ClassDef and FunctionDef nodes that need docstring enrichment."""

    def __init__(self) -> None:
        # Tuple of (node_code, existing_docstring, node_name, is_class)
        self.targets: List[Tuple[str, str, str, bool]] = []

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        if is_public_name(node.name.value):
            node_code = cst.Module(body=[node]).code
            existing_doc = self._get_existing_docstring(node)
            self.targets.append((node_code, existing_doc, node.name.value, True))
        return True

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        if is_public_name(node.name.value):
            node_code = cst.Module(body=[node]).code
            existing_doc = self._get_existing_docstring(node)
            self.targets.append((node_code, existing_doc, node.name.value, False))
        return True

    def _get_existing_docstring(self, node: Any) -> str:
        body = node.body
        if len(body.body) > 0 and isinstance(body.body[0], cst.SimpleStatementLine):
            stmt = body.body[0]
            if len(stmt.body) == 1 and isinstance(stmt.body[0], cst.Expr):
                expr = stmt.body[0]
                if isinstance(expr.value, cst.SimpleString):
                    return get_raw_string_content(expr.value.value).strip()
        return ""


class DocstringEnricherTransformer(cst.CSTTransformer):
    """Transforms docstrings using the pre-computed enriched_mappings."""

    def __init__(
        self, target_file_path: Path, enriched_mappings: Dict[str, str]
    ) -> None:
        self.file_path = target_file_path
        self.mappings = enriched_mappings
        self.nesting_level = 0

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        self.nesting_level += 1
        return True

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        self.nesting_level -= 1
        if is_public_name(original_node.name.value):
            return self._enrich_block_docstring(original_node, updated_node)
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.nesting_level += 1
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        self.nesting_level -= 1
        if is_public_name(original_node.name.value):
            return self._enrich_block_docstring(original_node, updated_node)
        return updated_node

    def _enrich_block_docstring(self, original_node: Any, updated_node: Any) -> Any:
        node_code = cst.Module(body=[original_node]).code

        if node_code not in self.mappings:
            return updated_node

        enriched_text = self.mappings[node_code]
        if not enriched_text:
            return updated_node

        body = original_node.body
        has_docstring = False
        if len(body.body) > 0 and isinstance(body.body[0], cst.SimpleStatementLine):
            stmt = body.body[0]
            if len(stmt.body) == 1 and isinstance(stmt.body[0], cst.Expr):
                expr = stmt.body[0]
                if isinstance(expr.value, cst.SimpleString):
                    has_docstring = True

        # Compute correct indentation
        indent_spaces = " " * (4 * (self.nesting_level + 1))
        indented_doc = indent_docstring(enriched_text, indent_spaces)

        # Create new SimpleStatementLine
        new_doc_stmt = cst.SimpleStatementLine(
            body=[cst.Expr(value=cst.SimpleString(value=indented_doc))]
        )

        # Reconstruct statements list
        if has_docstring:
            new_statements = [new_doc_stmt] + list(updated_node.body.body[1:])
        else:
            new_statements = [new_doc_stmt] + list(updated_node.body.body)

        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=new_statements)
        )


async def process_file(file_path: Path, semaphore: asyncio.Semaphore) -> None:
    async with semaphore:
        try:
            code = file_path.read_text(encoding="utf-8")

            try:
                module = cst.parse_module(code)
            except Exception as e:
                logger.warning(f"Skipping {file_path.name} - Parsing failed: {e}")
                return

            # Step 1: Collect targets
            collector = DocstringCollector()
            module.visit(collector)

            if not collector.targets:
                return

            logger.info(
                f"Collected {len(collector.targets)} potential docstring targets in {file_path.name}"
            )

            # Step 2: Batch process Gemini docstring generation
            enriched_mappings: Dict[str, str] = {}
            api_tasks = []
            block_codes = []

            for node_code, existing_doc, node_name, is_class in collector.targets:
                api_tasks.append(
                    generate_enriched_docstring(node_code, existing_doc, file_path)
                )
                block_codes.append(node_code)

            results = await asyncio.gather(*api_tasks)
            for code_block, enriched_doc in zip(block_codes, results):
                if enriched_doc:
                    enriched_mappings[code_block] = enriched_doc

            if not enriched_mappings:
                logger.warning(f"No docstrings generated for {file_path.name}")
                return

            # Step 3: Securely transform the AST in-place
            transformer = DocstringEnricherTransformer(file_path, enriched_mappings)
            transformed_module = module.visit(transformer)

            # Step 4: Safeguard syntax compile check
            transformed_code = transformed_module.code
            try:
                compile(transformed_code, str(file_path), "exec")
            except Exception as syntax_err:
                logger.error(
                    f"CRITICAL: Failed to compile {file_path.name} after transformation: {syntax_err}"
                )
                return

            # Step 5: Save changes
            file_path.write_text(transformed_code, encoding="utf-8")
            logger.info(f"✓ Successfully enriched docstrings in {file_path.name}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")


async def main() -> None:
    # Target all active files in src/
    target_dir = project_root / "src"
    py_files = sorted(list(target_dir.glob("**/*.py")))

    # Exclude legacy code or external node_modules if present
    ignored_patterns = ["_legacy", "node_modules", ".venv"]
    py_files = [
        f for f in py_files if not any(pat in str(f) for pat in ignored_patterns)
    ]

    # Check for command line arguments
    if len(sys.argv) > 1:
        py_files = []
        for arg in sys.argv[1:]:
            p = Path(arg).resolve()
            if p.is_file() and p.suffix == ".py":
                py_files.append(p)

    logger.info(f"Starting Google-style docstring enrichment on {len(py_files)} files.")

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = [process_file(f, semaphore) for f in py_files]

    await asyncio.gather(*tasks)
    logger.info("Docstring enrichment complete.")


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY is not set. Exiting.")
        sys.exit(1)
    asyncio.run(main())
