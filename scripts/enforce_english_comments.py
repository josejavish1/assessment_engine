#!/usr/bin/env python3
# golden-path: ignore
"""Language Guard: Deterministic detection and LLM-assisted translation of Spanish comments and docstrings."""

from __future__ import annotations

import argparse
import ast
import asyncio
import io
import os
import re
import sys
import tokenize
from pathlib import Path
from pydantic import BaseModel, Field

# Ensure project source is in path to allow imports of infrastructure modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from assessment_engine.infrastructure.ai_client import call_agent
except ImportError:
    # Fallback to direct import if running in nested path setups
    sys.path.insert(0, str(Path(__file__).parent.parent / "src/assessment_engine"))
    from assessment_engine.infrastructure.ai_client import call_agent


# English stop words (high-frequency syntactical elements)
ENGLISH_STOPWORDS = {
    "the", "and", "with", "for", "this", "that", "from", "which", "each",
    "have", "has", "been", "will", "should", "would", "can", "could", "not",
    "but", "they", "them", "their", "are", "was", "were", "first", "second"
}


# Spanish stop words and common indicators (zero English collisions)
SPANISH_KEYWORDS = {
    "para", "con", "como", "pero", "este", "esta", "todos", "todas", 
    "verificar", "comprobar", "función", "método", "clase", "archivo", 
    "prueba", "ejecución", "reinicio", "guardar", "recuperar", "dentro", 
    "fuera", "sobre", "entre", "desde", "hasta", "cuando", "donde", 
    "quien", "porque", "aunque", "entonces", "luego", "después", "antes", 
    "también", "además", "mientras", "durante", "etiqueta", "idioma",
    "comentario", "línea", "falla", "comprobación", "debe",
    "esperado", "obtenido", "discrepancia", "estructura", "reinicio",
    "sistema", "creando", "nuevo", "sobreescrita", "simulación", "apertura",
    "guardado", "físicamente", "vacía", "básica", "modificación", "respeto"
}


class TranslationResult(BaseModel):
    translated_text: str = Field(description="The precise technical English translation of the input text.")


def is_spanish_text(text: str) -> bool:
    """Check if the text contains Spanish accented characters or high-frequency Spanish technical words."""
    words = set(re.findall(r"\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]{3,}\b", text.lower()))
    # 1. If English syntax is dominant, it is not a Spanish comment/docstring (e.g. English text quoting Spanish strings)
    if len(words & ENGLISH_STOPWORDS) >= 3:
        return False
    # 2. Accented Spanish characters (definite proof)
    if re.search(r"[áéíóúüñÁÉÍÓÚÜÑ¿¡]", text):
        return True
    # 3. Match specific Spanish words
    if len(words & SPANISH_KEYWORDS) >= 2:
        return True
    return False


def load_sobriety_policy() -> str:
    """Load the engineering compliance laws and style guides from AGENTS.md dynamically."""
    try:
        agents_path = Path(__file__).resolve().parent.parent / "AGENTS.md"
        if agents_path.exists():
            content = agents_path.read_text(encoding="utf-8")
            # Extract relevant sections or just return the whole file for context
            return content[:3000] # Return the first 3000 chars for core context
    except Exception:
        pass
    return (
        "All code comments, module descriptions, class/method docstrings and variables "
        "must be written in formal, aseptic, precise technical English. "
        "Strictly avoid any hype-heavy, subjective, dramatic, or sensationalist words (such as SOTA, Elite, Slop, or Chaos)."
    )


async def translate_text(text: str) -> str:
    """Translate and sanitize Spanish or informal text to formal, aseptic, technical English using the cognitive linter."""
    policy = load_sobriety_policy()
    
    prompt = (
        f"You are a Cognitive Compliance Linter Agent. Your job is to translate and sanitize the following code comment or docstring "
        f"so that it complies strictly with the project's engineering policies and sobriety guidelines.\n\n"
        f"### PROJECT COMPLIANCE LAW (from AGENTS.md):\n{policy}\n\n"
        f"### INPUT TEXT TO SANITIZE (can be Spanish or informal English):\n{text}\n\n"
        f"### INSTRUCTIONS:\n"
        f"1. Translate any Spanish text to highly formal, aseptic, and technical English.\n"
        f"2. Sanitize and remove any sensationalist, dramatic, informal, or 'hype-heavy' expressions (such as SOTA, Elite, Chaos, Slop, emojis, exclamations, etc.) according to the policy.\n"
        f"3. Keep all code identifiers, variables, or system-critical terms intact.\n"
        f"4. Return ONLY the raw sanitized English text, with no additional explanations, markdown wrappers, or notes."
    )
    
    try:
        # Use cheap and fast model (gemini-2.5-flash)
        result = await call_agent(
            model_name="gemini-2.5-flash",
            prompt=prompt,
            instruction="You are an expert software developer translating and sanitizing code comments and docstrings to formal, sober, technical English based on dynamic policy documents.",
            output_schema=TranslationResult,
        )
        if isinstance(result, dict):
            return result.get("translated_text", text).strip()
        return result.translated_text.strip()
    except Exception as e:
        print(f"⚠️ Warning: LLM translation failed, keeping original. Error: {e}", file=sys.stderr)
        return text


def get_docstring_spans(content: str) -> list[tuple[int, int, int, int]]:
    """Use Python's native AST to identify lines and columns of all module, class, and function docstrings."""
    spans = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    # Helper to check if a statement is a Docstring Constant
    def check_docstring_node(node):
        if node.body and isinstance(node.body[0], ast.Expr):
            val = node.body[0].value
            if isinstance(val, (ast.Constant, ast.Str)):
                # Return the line and column spans
                # AST line numbers are 1-based, columns are 0-based
                # end_lineno and end_col_offset are available in Python 3.8+
                if hasattr(val, "end_lineno") and val.end_lineno is not None:
                    return (val.lineno, val.col_offset, val.end_lineno, val.end_col_offset)
        return None

    # Module level docstring
    if tree.body and isinstance(tree.body[0], ast.Expr):
        val = tree.body[0].value
        if isinstance(val, (ast.Constant, ast.Str)):
            if hasattr(val, "end_lineno") and val.end_lineno is not None:
                spans.append((val.lineno, val.col_offset, val.end_lineno, val.end_col_offset))

    # Walk functions and classes
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            span = check_docstring_node(node)
            if span:
                spans.append(span)

    return spans


def is_in_docstring_spans(line: int, col: int, doc_spans: list[tuple[int, int, int, int]]) -> bool:
    """Verify if a given token position is located within any of the detected docstring spans."""
    for s_line, s_col, e_line, e_col in doc_spans:
        if s_line <= line <= e_line:
            # Simple check for same-line docstring
            if s_line == e_line:
                if s_col <= col <= e_col:
                    return True
            else:
                if line == s_line and col >= s_col:
                    return True
                elif line == e_line and col <= e_col:
                    return True
                elif s_line < line < e_line:
                    return True
    return False


async def process_file(filepath: Path, autofix: bool) -> bool:
    """Scan file for Spanish comments and docstrings, and optionally translate them using LLM."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return False

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
    except tokenize.TokenError as e:
        print(f"Tokenization error in {filepath}: {e}", file=sys.stderr)
        return False

    docstring_spans = get_docstring_spans(content)
    
    replacements = []
    issues_found = 0

    for token in tokens:
        # Ignore comments like type ignores or golden paths
        if token.type == tokenize.COMMENT:
            comment_text = token.string
            if "type:" in comment_text or "golden-path:" in comment_text or "pragma:" in comment_text:
                continue
            
            # Extract raw comment content
            match = re.match(r"^(#\s*)(.*)$", comment_text)
            if match:
                prefix = match.group(1)
                raw_comment = match.group(2).strip()
                if raw_comment and is_spanish_text(raw_comment):
                    issues_found += 1
                    print(f"🚨 Found Spanish Comment in {filepath}:{token.start[0]}: {token.string}")
                    
                    if autofix:
                        translated = await translate_text(raw_comment)
                        new_comment_string = prefix + translated
                        replacements.append({
                            "start_line": token.start[0],
                            "start_col": token.start[1],
                            "end_line": token.end[0],
                            "end_col": token.end[1],
                            "new_text": new_comment_string
                        })

        # Check docstrings (only string tokens matching AST docstring spans)
        elif token.type == tokenize.STRING:
            if is_in_docstring_spans(token.start[0], token.start[1], docstring_spans):
                # Triple-quoted strings
                if (token.string.startswith('"""') and token.string.endswith('"""')) or \
                   (token.string.startswith("'''") and token.string.endswith("'''")):
                    
                    quote_style = '"""' if token.string.startswith('"""') else "'''"
                    raw_doc = token.string[3:-3].strip()
                    
                    if raw_doc and is_spanish_text(raw_doc):
                        issues_found += 1
                        first_line = raw_doc.splitlines()[0] if raw_doc else ""
                        print(f"🚨 Found Spanish Docstring in {filepath}:{token.start[0]}: {quote_style}{first_line}...")
                        
                        if autofix:
                            translated = await translate_text(raw_doc)
                            new_doc_string = f"{quote_style}{translated}{quote_style}"
                            replacements.append({
                                "start_line": token.start[0],
                                "start_col": token.start[1],
                                "end_line": token.end[0],
                                "end_col": token.end[1],
                                "new_text": new_doc_string
                            })

    if issues_found > 0:
        if autofix and replacements:
            print(f"✨ Auto-healing {filepath} ({len(replacements)} translations)...")
            
            # Apply replacements descending to avoid offset drift
            replacements.sort(key=lambda r: (r['start_line'], r['start_col']), reverse=True)
            lines = content.splitlines(keepends=True)
            
            for rep in replacements:
                s_line = rep['start_line'] - 1
                s_col = rep['start_col']
                e_line = rep['end_line'] - 1
                e_col = rep['end_col']
                new_text = rep['new_text']
                
                if s_line == e_line:
                    original_line = lines[s_line]
                    lines[s_line] = original_line[:s_col] + new_text + original_line[e_col:]
                else:
                    first_line = lines[s_line]
                    last_line = lines[e_line]
                    lines[s_line] = first_line[:s_col] + new_text
                    for i in range(s_line + 1, e_line):
                        lines[i] = ""
                    lines[e_line] = last_line[e_col:]
            
            try:
                filepath.write_text("".join(lines), encoding="utf-8")
                print(f"✅ Successfully auto-healed {filepath}.")
            except Exception as e:
                print(f"❌ Failed to write updates to {filepath}: {e}", file=sys.stderr)
                return False
        return False # Return False because there were issues detected (and resolved or unresolved)
    
    return True


async def main() -> int:
    parser = argparse.ArgumentParser(description="Enforce English on all code comments and docstrings.")
    parser.add_argument("files", nargs="*", help="List of files to scan.")
    parser.add_argument("--autofix", action="store_true", help="Auto-heal and translate Spanish comments/docstrings using Gemini LLM.")
    
    args = parser.parse_args()
    
    target_files = []
    if args.files:
        target_files = [Path(f) for f in args.files if f.endswith(".py")]
    else:
        # Recursive scan of src/ and tests/ if no files specified
        for folder in ["src", "tests"]:
            target_files.extend(list(Path(folder).rglob("*.py")))
            
    # Filter out _legacy and local environments
    target_files = [
        f for f in target_files 
        if "_legacy" not in f.as_posix() 
        and "node_modules" not in f.as_posix()
        and ".venv" not in f.as_posix()
    ]
    
    if not target_files:
        print("No files to scan.")
        return 0
        
    print(f"🔍 Scanning {len(target_files)} files for Spanish comments and docstrings...")
    
    results = await asyncio.gather(*(process_file(f, args.autofix) for f in target_files))
    
    success = all(results)
    if not success:
        if args.autofix:
            print("\n✨ Auto-healing cycle complete. Please review the translated files and run again to verify.")
            return 0
        else:
            print("\n❌ Language Guard failed: Non-English comments/docstrings found.")
            return 1
            
    print("\n✅ Language Guard passed: All comments and docstrings are in compliant Technical English.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
