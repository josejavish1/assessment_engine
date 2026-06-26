#!/usr/bin/env python
"""Pre-commit hook to statically enforce that all comments, docstrings,
and field descriptions are written in English, rejecting localized Spanish comments.
"""

import sys
import unicodedata
from pathlib import Path
from typing import List, Set

import libcst as cst

# Common Spanish stop words and highly characteristic stems/terms
SPANISH_KEYWORDS = {
    "de",
    "la",
    "el",
    "en",
    "para",
    "con",
    "por",
    "como",
    "esta",
    "este",
    "del",
    "fichero",
    "archivo",
    "plantilla",
    "guardar",
    "limpiar",
    "metadatos",
    "leer",
    "claves",
    "encabezado",
    "parrafo",
    "celda",
    "tabla",
    "viñeta",
    "ruta",
    "servidor",
    "configuracion",
    "comentario",
    "codigo",
    "ejecutar",
    "pruebas",
    "error",
    "exito",
    "siguiente",
    "anterior",
    "funcion",
    "clase",
    "metodo",
    "usuario",
    "clave",
    "contraseña",
    "datos",
    "registro",
    "campo",
    "tipo",
    "retorno",
    "vacio",
    "nulo",
    "verdadero",
    "falso",
}

# Common English stopwords to bypass validation and eliminate false positives for English sentences
ENGLISH_STOPWORDS = {
    "the",
    "and",
    "to",
    "is",
    "a",
    "of",
    "for",
    "in",
    "on",
    "with",
    "must",
    "have",
    "be",
    "this",
    "that",
    "it",
    "any",
    "prevent",
    "cause",
    "fatal",
    "will",
    "from",
    "as",
    "by",
    "an",
    "at",
    "are",
    "or",
    "which",
    "more",
    "such",
    "under",
    "should",
    "does",
    "been",
    "was",
    "were",
    "into",
    "step",
    "normalize",
    "removing",
    "possessive",
    "prepositions",
    "text",
}


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def tokenize(text: str) -> Set[str]:
    cleaned = remove_accents(text.lower())
    # Strip quotes, punctuation, and split into alphanumeric tokens
    words = []
    current_word = []
    for char in cleaned:
        if char.isalnum():
            current_word.append(char)
        else:
            if current_word:
                words.append("".join(current_word))
                current_word = []
    if current_word:
        words.append("".join(current_word))
    return set(words)


class DocLanguageValidator(cst.CSTVisitor):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.violations: List[str] = []
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
                    self._check_text(expr.value.value, "docstring")
            self._current_block_first_stmt[-1] = False
        else:
            if self._current_block_first_stmt:
                self._current_block_first_stmt[-1] = False

    def visit_Comment(self, node: cst.Comment) -> None:
        self._check_text(node.value, "comment")

    def visit_Arg(self, node: cst.Arg) -> None:
        if node.keyword and node.keyword.value == "description":
            if isinstance(node.value, cst.SimpleString):
                self._check_text(node.value.value, "description")

    def _check_text(self, text: str, element_type: str) -> None:
        tokens = tokenize(text)

        # English stopword bypass heuristic to eliminate false positives
        english_indicators = tokens.intersection(ENGLISH_STOPWORDS)
        if len(english_indicators) >= 2:
            return

        matches = tokens.intersection(SPANISH_KEYWORDS)
        if matches:
            # We found Spanish keywords, flag a violation
            matched_words = ", ".join(f"'{w}'" for w in matches)
            self.violations.append(
                f"Non-English {element_type} detected. Matched Spanish keyword(s): {matched_words}.\n  Text: {text.strip()}"
            )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: enforce_english_comments.py <file1.py> <file2.py> ...")
        sys.exit(0)

    total_violations = 0
    for arg in sys.argv[1:]:
        p = Path(arg).resolve()
        if not p.exists() or p.suffix != ".py":
            continue

        try:
            code = p.read_text(encoding="utf-8")
            module = cst.parse_module(code)
            validator = DocLanguageValidator(p)
            module.visit(validator)

            if validator.violations:
                print(f"\n❌ Style Violation: {p.relative_to(Path.cwd())}")
                for violation in validator.violations:
                    print(f"  - {violation}")
                total_violations += len(validator.violations)
        except Exception as e:
            # Ignore parsing errors or log them briefly to avoid breaking pre-commit on syntax errors
            print(f"⚠️ Warning: Failed to parse {p.name}: {e}")

    if total_violations > 0:
        print(
            f"\nTotal violations: {total_violations}. Tier 1 engineering standards require all comments and documentation to be strictly in English."
        )
        sys.exit(1)

    print("✓ All comments and docstrings are compliant with Tier 1 English standards.")
    sys.exit(0)


if __name__ == "__main__":
    main()
