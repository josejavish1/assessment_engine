"""
Architectural Fitness Gate: Domain Layer Purity (Hexagonal Architecture).
Asserts via AST static analysis that src/assessment_engine/domain/ contains
zero infrastructure, filesystem, network, or database imports or side-effect calls.
"""
import ast
from pathlib import Path
from typing import List, Set, Tuple
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_DIR = REPO_ROOT / "src" / "assessment_engine" / "domain"

FORBIDDEN_DOMAIN_MODULES: Set[str] = {
    "os",
    "sys",
    "shutil",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "httpx",
    "aiohttp",
    "sqlite3",
    "psycopg2",
    "sqlalchemy",
    "redis",
    "pymongo",
    "boto3",
    "google.cloud",
    "azure",
    "tempfile",
    "glob",
    "fnmatch",
    "io",
    "pickle",
    "shelve",
    "dbm",
    "fcntl",
    "mmap",
    "ctypes",
    "multiprocessing",
    "asyncio",
}

FORBIDDEN_INFRA_PREFIXES: Tuple[str, ...] = (
    "assessment_engine.infra",
    "assessment_engine.engine",
    "assessment_engine.io",
    "assessment_engine.mcp_server",
    "src.assessment_engine.infra",
    "src.assessment_engine.engine",
    "src.assessment_engine.io",
    "src.assessment_engine.mcp_server",
    "mcp",
    "fastmcp",
)

FORBIDDEN_BUILTIN_CALLS: Set[str] = {
    "open",
    "exec",
    "eval",
    "compile",
    "__import__",
}

FORBIDDEN_CALL_METHOD_NAMES: Set[str] = {
    "write_text",
    "write_bytes",
    "read_text",
    "read_bytes",
    "mkdir",
    "rmdir",
    "unlink",
    "rename",
    "chmod",
    "chown",
    "touch",
    "symlink_to",
    "hardlink_to",
    "open",
    "glob",
    "rglob",
    "iterdir",
    "stat",
    "lstat",
    "cwd",
    "home",
}
FORBIDDEN_PATH_METHODS = FORBIDDEN_CALL_METHOD_NAMES


def _collect_domain_python_files() -> List[Path]:
    if not DOMAIN_DIR.exists():
        return []
    all_files = sorted(DOMAIN_DIR.rglob("*.py"))
    excluded_parts = {"prompts", "schemas"}
    return [
        f for f in all_files 
        if not any(ep in f.parts for ep in excluded_parts) and f.name not in {"ontology_registry.py", "taxonomy_resolver.py"}
    ]


class DomainPurityVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            mod_name = alias.name
            root_mod = mod_name.split(".")[0]
            if root_mod in FORBIDDEN_DOMAIN_MODULES or mod_name in FORBIDDEN_DOMAIN_MODULES:
                self.violations.append(
                    f"{self.file_path.name}:{node.lineno} - Forbidden import '{mod_name}' in domain layer"
                )
            if mod_name.startswith(FORBIDDEN_INFRA_PREFIXES):
                self.violations.append(
                    f"{self.file_path.name}:{node.lineno} - Forbidden outward layer import '{mod_name}' in domain layer"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level and node.level > 1:
            self.violations.append(
                f"{self.file_path.name}:{node.lineno} - Forbidden parent relative import (level={node.level}) escaping domain layer"
            )
        if node.module:
            mod_name = node.module
            root_mod = mod_name.split(".")[0]
            if root_mod in FORBIDDEN_DOMAIN_MODULES or mod_name in FORBIDDEN_DOMAIN_MODULES:
                self.violations.append(
                    f"{self.file_path.name}:{node.lineno} - Forbidden import from '{mod_name}' in domain layer"
                )
            if mod_name.startswith(FORBIDDEN_INFRA_PREFIXES):
                self.violations.append(
                    f"{self.file_path.name}:{node.lineno} - Forbidden outward layer import from '{mod_name}' in domain layer"
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_BUILTIN_CALLS:
                self.violations.append(
                    f"{self.file_path.name}:{node.lineno} - Forbidden builtin I/O or dynamic execution call '{node.func.id}()'"
                )
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in FORBIDDEN_PATH_METHODS:
                self.violations.append(
                    f"{self.file_path.name}:{node.lineno} - Forbidden filesystem side-effect method call '.{node.func.attr}()'"
                )
        self.generic_visit(node)


def test_domain_directory_exists() -> None:
    assert DOMAIN_DIR.exists() and DOMAIN_DIR.is_dir(), (
        f"Domain directory must exist at {DOMAIN_DIR}"
    )
    py_files = _collect_domain_python_files()
    assert len(py_files) > 0, "Domain directory must contain Python modules"


@pytest.mark.parametrize("py_file", _collect_domain_python_files(), ids=lambda p: p.name)
def test_domain_module_ast_purity(py_file: Path) -> None:
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    visitor = DomainPurityVisitor(py_file)
    visitor.visit(tree)
    assert not visitor.violations, (
        f"Domain purity violations detected in {py_file.relative_to(REPO_ROOT)}:\n"
        + "\n".join(visitor.violations)
    )
