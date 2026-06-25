#!/usr/bin/env python
"""
Elevate Documentation Script.
Uses LibCST to parse Python source files, extract comments/docstrings/field descriptions,
translates and elevates them to Tier 1 English engineering standards using the Gemini API,
and safely injects them back preserving all code logic and style.
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Any, Optional

import libcst as cst

# Set up paths to allow importing project modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from infrastructure.ai_client import call_agent

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("elevate_docs")

# Configuration
CONCURRENCY_LIMIT = 5
MODEL_NAME = os.environ.get("MODEL_TIER_PRO", "gemini-2.5-pro")


def get_raw_string_content(orig_str: str) -> str:
    """
    Strips raw/format/bytes prefixes and matching enclosing quotes from a Python string literal
    to isolate the raw text content.
    """
    for i, char in enumerate(orig_str):
        if char in ("'", '"'):
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


def preserve_quotes_and_prefix(orig_str: str, new_str: str) -> str:
    """
    Extracts the original string's prefix and matching enclosing quotes,
    cleans any accidentally generated prefixes/quotes in the new string,
    and returns the new string formatted exactly like the original.
    """
    prefix = ""
    for i, char in enumerate(orig_str):
        if char in ("'", '"'):
            prefix = orig_str[:i]
            orig_str_no_prefix = orig_str[i:]
            break
    else:
        orig_str_no_prefix = orig_str

    if orig_str_no_prefix.startswith('"""') and orig_str_no_prefix.endswith('"""'):
        quotes = '"""'
    elif orig_str_no_prefix.startswith("'''") and orig_str_no_prefix.endswith("'''"):
        quotes = "'''"
    elif orig_str_no_prefix.startswith('"') and orig_str_no_prefix.endswith('"'):
        quotes = '"'
    elif orig_str_no_prefix.startswith("'") and orig_str_no_prefix.endswith("'"):
        quotes = "'"
    else:
        quotes = '"'

    cleaned = new_str.strip()
    # Strip any accidental matching prefix returned by the LLM
    for p in ("f", "r", "b", "u", "F", "R", "B", "U"):
        if cleaned.lower().startswith(p) and (cleaned[len(p):].startswith('"') or cleaned[len(p):].startswith("'")):
            cleaned = cleaned[len(p):].strip()
            
    # Strip matching quotes returned by the LLM
    if cleaned.startswith('"""') and cleaned.endswith('"""'):
        cleaned = cleaned[3:-3]
    elif cleaned.startswith("'''") and cleaned.endswith("'''"):
        cleaned = cleaned[3:-3]
    elif cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1]
    elif cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1]
        
    return f"{prefix}{quotes}{cleaned}{quotes}"


class DocElementCollector(cst.CSTVisitor):
    def __init__(self) -> None:
        self.comments: Set[str] = set()
        self.docstrings: Set[str] = set()
        self.descriptions: Set[str] = set()
        self._current_block_first_stmt: List[bool] = []

    def visit_Module(self, node: cst.Module) -> None:
        self._current_block_first_stmt.append(True)

    def leave_Module(self, node: cst.Module) -> None:
        self._current_block_first_stmt.pop()

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._current_block_first_stmt.append(True)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self._current_block_first_stmt.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._current_block_first_stmt.append(True)

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._current_block_first_stmt.pop()

    def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine) -> None:
        if self._current_block_first_stmt and self._current_block_first_stmt[-1]:
            if len(node.body) == 1 and isinstance(node.body[0], cst.Expr):
                expr = node.body[0]
                if isinstance(expr.value, cst.SimpleString):
                    raw_val = get_raw_string_content(expr.value.value).strip()
                    if raw_val:
                        self.docstrings.add(raw_val)
            self._current_block_first_stmt[-1] = False
        else:
            if self._current_block_first_stmt:
                self._current_block_first_stmt[-1] = False

    def visit_Comment(self, node: cst.Comment) -> None:
        raw_val = node.value.lstrip("#").strip()
        if raw_val:
            self.comments.add(raw_val)

    def visit_Arg(self, node: cst.Arg) -> None:
        if node.keyword and node.keyword.value == "description":
            if isinstance(node.value, cst.SimpleString):
                raw_val = get_raw_string_content(node.value.value).strip()
                if raw_val:
                    self.descriptions.add(raw_val)


class DocElementTransformer(cst.CSTTransformer):
    def __init__(self, mapping: Dict[str, str]) -> None:
        self.mapping = mapping
        self._current_block_first_stmt: List[bool] = []

    def visit_Module(self, node: cst.Module) -> None:
        self._current_block_first_stmt.append(True)

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        self._current_block_first_stmt.pop()
        return updated_node

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self._current_block_first_stmt.append(True)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        self._current_block_first_stmt.pop()
        return updated_node

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._current_block_first_stmt.append(True)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        self._current_block_first_stmt.pop()
        return updated_node

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        if self._current_block_first_stmt and self._current_block_first_stmt[-1]:
            if len(original_node.body) == 1 and isinstance(original_node.body[0], cst.Expr):
                expr = original_node.body[0]
                if isinstance(expr.value, cst.SimpleString):
                    orig_val = expr.value.value
                    raw_val = get_raw_string_content(orig_val).strip()
                    if raw_val in self.mapping:
                        new_raw_val = self.mapping[raw_val]
                        if not isinstance(new_raw_val, str):
                            new_raw_val = str(new_raw_val)
                        wrapped_val = preserve_quotes_and_prefix(orig_val, new_raw_val)
                        new_expr = expr.with_changes(value=expr.value.with_changes(value=wrapped_val))
                        updated_node = updated_node.with_changes(body=[new_expr])
            self._current_block_first_stmt[-1] = False
        else:
            if self._current_block_first_stmt:
                self._current_block_first_stmt[-1] = False
        return updated_node

    def leave_Comment(self, original_node: cst.Comment, updated_node: cst.Comment) -> cst.Comment:
        orig_val = original_node.value
        raw_val = orig_val.lstrip("#").strip()
        if raw_val in self.mapping:
            new_raw_val = self.mapping[raw_val]
            if not isinstance(new_raw_val, str):
                new_raw_val = str(new_raw_val)
            if not new_raw_val:
                # If mapped to empty, map to an empty comment node
                return updated_node.with_changes(value="#")
            
            # Clean possible leading '#' and outer quotes returned by the LLM
            cleaned = new_raw_val.lstrip("#").strip()
            if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
                cleaned = cleaned[1:-1].strip()
                
            if not cleaned:
                return updated_node.with_changes(value="#")
            return updated_node.with_changes(value=f"# {cleaned}")
        return updated_node

    def leave_Arg(self, original_node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
        if original_node.keyword and original_node.keyword.value == "description":
            if isinstance(original_node.value, cst.SimpleString):
                orig_val = original_node.value.value
                raw_val = get_raw_string_content(orig_val).strip()
                if raw_val in self.mapping:
                    new_raw_val = self.mapping[raw_val]
                    if not isinstance(new_raw_val, str):
                        new_raw_val = str(new_raw_val)
                    wrapped_val = preserve_quotes_and_prefix(orig_val, new_raw_val)
                    return updated_node.with_changes(
                        value=original_node.value.with_changes(value=wrapped_val)
                    )
        return updated_node


SYSTEM_INSTRUCTION = """
You are a Staff Principal Engineer at Anthropic. Your goal is to elevate all code comments, docstrings, and Pydantic schema field descriptions in our codebase to strict, professional, clinical English.

Rules:
1. Translate all Spanish or localized comments and docstrings into formal, technical English.
2. STRICT HYPED-WORD PROHIBITION (Anti-AI-Bro / Anti-Slop):
   - You must NEVER use self-congratulatory, marketing, or hype words in any comment, docstring, or description.
   - Specifically, ban words like: "SOTA", "State-of-the-Art", "sovereign", "bulletproof", "ultra-robust", "robust", "flawless", "seamlessly", "beautifully", "lethal", "power artifact", "perfect".
   - If an existing comment contains any of these words, rewrite it to be completely objective, academic, dry, and factual. For example, replace "SOTA 2026 Standard" with standard engineering facts or standard designations (like "ECMA-376", "ISO/IEC 29500", "i18n", or simply omit the hype prefix).
3. Elevate redundant or obvious "what" comments into high-signal "why" comments.
   - If a comment simply restates the code (e.g., "Save document" right before "doc.save()"), set its elevated value to "" (empty string) to indicate it should be deprecated/deleted.
   - If the comment explains non-obvious logic, math, standard constraints, or architectural decisions, rewrite it to be extremely professional, sober, and objective.
4. For Pydantic field descriptions: translate them to clean, concise, precise technical English optimized for LLM/agent interpretation. Never use hype words or subjective adjectives in descriptions.
5. Maintain all technical references, variable names, libraries, code syntax, or logical placeholders intact.
6. Return ONLY a valid JSON object mapping each original raw string to its elevated string. Do NOT output markdown code blocks or any conversational preambles/postambles.
   {
     "original_string": "elevated_string"
   }
"""

async def translate_elements(elements_dict: Dict[str, List[str]], file_path: Path) -> Dict[str, str]:
    """
    Calls the Gemini API to elevate the collected comments/docstrings/descriptions in a single batch.
    """
    # Build prompt
    prompt = f"File: {file_path.relative_to(project_root)}\n\n"
    prompt += "Docstrings to translate and elevate:\n"
    for d in elements_dict["docstrings"]:
        prompt += f"- {repr(d)}\n"
    prompt += "\nComments to translate and elevate (if redundant, map to empty string \"\"):\n"
    for c in elements_dict["comments"]:
        prompt += f"- {repr(c)}\n"
    prompt += "\nField Descriptions to translate and elevate:\n"
    for desc in elements_dict["descriptions"]:
        prompt += f"- {repr(desc)}\n"

    try:
        response_text = await call_agent(
            model_name=MODEL_NAME,
            prompt=prompt,
            instruction=SYSTEM_INSTRUCTION
        )
        
        # Parse the JSON response
        if isinstance(response_text, dict):
            return response_text
            
        # Clean response if wrapped in code blocks
        clean_text = str(response_text).strip()
        if clean_text.startswith("```"):
            lines = clean_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_text = "\n".join(lines).strip()
            
        mapping = json.loads(clean_text)
        return mapping
    except Exception as e:
        logger.error(f"Failed to translate elements for {file_path}: {e}")
        return {}


async def process_file(file_path: Path, semaphore: asyncio.Semaphore) -> None:
    async with semaphore:
        try:
            code = file_path.read_text(encoding="utf-8")
            
            # Parse using LibCST
            try:
                module = cst.parse_module(code)
            except Exception as e:
                logger.warning(f"Skipping {file_path} - Failed to parse with LibCST: {e}")
                return

            # Collect doc elements
            collector = DocElementCollector()
            module.visit(collector)

            if not collector.docstrings and not collector.comments and not collector.descriptions:
                # Nothing to translate in this file
                return

            elements_dict = {
                "docstrings": sorted(list(collector.docstrings)),
                "comments": sorted(list(collector.comments)),
                "descriptions": sorted(list(collector.descriptions)),
            }

            logger.info(f"Processing {file_path.relative_to(project_root)}: {len(elements_dict['docstrings'])} docstrings, {len(elements_dict['comments'])} comments, {len(elements_dict['descriptions'])} descriptions.")

            # Translate in batch
            mapping = await translate_elements(elements_dict, file_path)
            if not mapping:
                logger.warning(f"No translations returned for {file_path}.")
                return

            # Transform source code using mapping
            transformer = DocElementTransformer(mapping)
            transformed_module = module.visit(transformer)

            # Safeguard: verify python syntax compile on transformed code
            transformed_code = transformed_module.code
            try:
                compile(transformed_code, str(file_path), "exec")
            except Exception as syntax_err:
                logger.error(f"CRITICAL: Refusing to save {file_path} - Transformed code has syntax error: {syntax_err}")
                return

            # Save elevated code
            file_path.write_text(transformed_code, encoding="utf-8")
            logger.info(f"✓ Successfully elevated documentation in {file_path.relative_to(project_root)}")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")


async def main() -> None:
    # Check for command line arguments
    if len(sys.argv) > 1:
        py_files: List[Path] = []
        for arg in sys.argv[1:]:
            p = Path(arg).resolve()
            if p.is_file() and p.suffix == ".py":
                py_files.append(p)
            elif p.is_dir():
                py_files.extend(p.glob("**/*.py"))
        # Exclude ignored patterns
        ignored_patterns = ["_legacy", "node_modules", ".venv"]
        py_files = [
            f for f in py_files 
            if not any(pat in str(f) for pat in ignored_patterns)
        ]
    else:
        # We only scan files in src/ domain, infrastructure, application, ports, adapters
        target_dir = project_root / "src"
        all_py_files = sorted(list(target_dir.glob("**/*.py")))
        
        # Exclude legacy code or external node_modules if present
        ignored_patterns = ["_legacy", "node_modules", ".venv"]
        py_files = [
            f for f in all_py_files 
            if not any(pat in str(f) for pat in ignored_patterns)
        ]

    logger.info(f"Starting SOTA documentation elevation on {len(py_files)} files.")
    
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = [process_file(f, semaphore) for f in py_files]
    
    await asyncio.gather(*tasks)
    logger.info("Documentation elevation batch execution finished.")

if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        logger.error("GEMINI_API_KEY environment variable is not set. Exiting.")
        sys.exit(1)
    asyncio.run(main())
