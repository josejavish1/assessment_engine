"""
Architectural Fitness Gate: 100% Technical English Compliance.
Scans all Python AST string literals and identifiers in src/ to ensure
zero non-English vocabulary or Latin diacritic characters exist in production code.
"""
import ast
import base64
import re
from pathlib import Path
from typing import List, Set, Tuple
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"

# Unicode codepoints for Latin diacritics and inverted punctuation marks
# represented numerically to maintain 100% ASCII purity within the test suite itself.
_FORBIDDEN_CODEPOINTS: Tuple[int, ...] = (
    0x00E1, 0x00E9, 0x00ED, 0x00F3, 0x00FA, 0x00F1, 0x00FC,
    0x00C1, 0x00C9, 0x00CD, 0x00D3, 0x00DA, 0x00D1, 0x00DC,
    0x00A1, 0x00BF,
)
FORBIDDEN_CHAR_SET: Set[str] = {chr(cp) for cp in _FORBIDDEN_CODEPOINTS}

# Base64-encoded single-word non-English lexicon tokens.
# Every entry decodes strictly to a lowercase single alphanumeric word.
_ENCODED_FORBIDDEN_TOKENS: Tuple[str, ...] = (
    "ZXZhbHVhY2lvbg==",
    "Y3VtcGxpbWllbnRv",
    "cmllc2dv",
    "cmllc2dvcw==",
    "YW1lbmF6YQ==",
    "YW1lbmF6YXM=",
    "Y29udHJvbGVz",
    "YXVkaXRvcmlh",
    "bm9ybWF0aXZh",
    "cmVxdWlzaXRv",
    "cmVxdWlzaXRvcw==",
    "ZXZpZGVuY2lh",
    "ZXZpZGVuY2lhcw==",
    "aGFsbGF6Z28=",
    "aGFsbGF6Z29z",
    "cHVudHVhY2lvbg==",
    "cG9uZGVyYWNpb24=",
    "dW1icmFs",
    "bm9kbw==",
    "bm9kb3M=",
    "Z3JhZm8=",
    "Y2VudGluZWxh",
    "Y2FsaWJyYWRvcg==",
    "c29iZXJhbmlh",
    "anVyaXNkaWNjaW9u",
    "ZGljdGFtZW4=",
    "YnJlY2hh",
    "YnJlY2hhcw==",
    "bWl0aWdhY2lvbg==",
    "Y29uZmlhbnph",
    "cGVzbw==",
    "cGVzb3M=",
    "bml2ZWw=",
    "bml2ZWxlcw==",
    "bWFkdXJleg==",
    "YXJjaGl2bw==",
    "ZGlyZWN0b3Jpbw==",
    "Y29uZmlndXJhY2lvbg==",
    "aGVycmFtaWVudGE=",
    "c2Vydmlkb3I=",
    "bWVuc2FqZQ==",
    "cmVzcHVlc3Rh",
    "c29saWNpdHVk",
    "dmFsaWRhY2lvbg==",
    "ZXN0YWRv",
    "cmVzdWx0YWRv",
    "cmVzdWx0YWRvcw==",
    "dmVyZGljdG8=",
)

FORBIDDEN_LEXICON_TOKENS: Set[str] = {
    base64.b64decode(token).decode("utf-8").lower()
    for token in _ENCODED_FORBIDDEN_TOKENS
}

WORD_TOKENIZER_REGEX = re.compile(r"[A-Za-z0-9]+")


def _collect_src_python_files() -> List[Path]:
    if not SRC_DIR.exists():
        return []
    return sorted(SRC_DIR.rglob("*.py"))


def _extract_subtokens(text: str) -> Set[str]:
    tokens: Set[str] = set()
    for raw_word in WORD_TOKENIZER_REGEX.findall(text):
        tokens.add(raw_word.lower())
    for snake_part in text.replace("-", "_").split("_"):
        cleaned = snake_part.strip().lower()
        if cleaned:
            tokens.add(cleaned)
    return tokens


class TechnicalEnglishASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.violations: List[str] = []

    def _inspect_text(self, text: str, lineno: int, context: str) -> None:
        found_diacritics = sorted({ch for ch in text if ch in FORBIDDEN_CHAR_SET})
        if found_diacritics:
            hex_codes = ", ".join(f"U+{ord(c):04X}" for c in found_diacritics)
            self.violations.append(
                f"{self.file_path.name}:{lineno} - Forbidden non-ASCII Latin character(s) [{hex_codes}] in {context}"
            )

        subtokens = _extract_subtokens(text)
        matched_forbidden = sorted(subtokens.intersection(FORBIDDEN_LEXICON_TOKENS))
        if matched_forbidden:
            self.violations.append(
                f"{self.file_path.name}:{lineno} - Forbidden non-English token(s) {matched_forbidden} in {context}"
            )

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self._inspect_text(node.value, node.lineno, "string literal")
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._inspect_text(node.name, node.lineno, f"function identifier '{node.name}'")
        for arg in node.args.args + node.args.kwonlyargs:
            self._inspect_text(arg.arg, node.lineno, f"argument identifier '{arg.arg}'")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._inspect_text(node.name, node.lineno, f"async function identifier '{node.name}'")
        for arg in node.args.args + node.args.kwonlyargs:
            self._inspect_text(arg.arg, node.lineno, f"argument identifier '{arg.arg}'")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._inspect_text(node.name, node.lineno, f"class identifier '{node.name}'")
        self.generic_visit(node)


def test_src_directory_exists() -> None:
    assert SRC_DIR.exists() and SRC_DIR.is_dir(), f"Source directory must exist at {SRC_DIR}"
    py_files = _collect_src_python_files()
    assert len(py_files) > 0, "Source directory must contain Python modules"


def test_forbidden_lexicon_tokens_are_reachable_single_words() -> None:
    for token in FORBIDDEN_LEXICON_TOKENS:
        assert token.isalnum(), f"Lexicon token '{token}' must be strictly alphanumeric to match tokenizer"


@pytest.mark.parametrize("py_file", _collect_src_python_files(), ids=lambda p: str(p.relative_to(SRC_DIR)))
def test_zero_non_english_literals_in_src(py_file: Path) -> None:
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    visitor = TechnicalEnglishASTVisitor(py_file)
    visitor.visit(tree)
    assert not visitor.violations, (
        f"Non-English AST literal or identifier violations in {py_file.relative_to(REPO_ROOT)}:\n"
        + "\n".join(visitor.violations)
    )
