from abc import ABC, abstractmethod

from domain.schemas.ast import DocumentAST


class DocumentCompiler(ABC):
    r"""['Abstract base class for transforming a DocumentAST into a file.\n\nThis class defines the standard interface for document compilers. Subclasses\nare responsible for implementing the logic to convert a `DocumentAST` object\ninto a concrete file format (e.g., PDF, DOCX, HTML) by overriding the\n`compile` method.', 'Compiles a `DocumentAST` object into a concrete document artifact.\n\nThis abstract method defines the contract for compilation. Subclasses must\nimplement this method to transform the given `DocumentAST` into a specific\noutput format and write it to the specified file path.\n\nArgs:\n    ast: The abstract syntax tree representing the document to compile.\n    output_path: The file system path where the compiled document will be saved.\n\nRaises:\n    ValueError: If the `ast` is malformed or contains nodes unsupported by the\n        concrete compiler implementation.\n    FileNotFoundError: If the parent directory of `output_path` does not exist.\n    PermissionError: If the process lacks write permissions for the `output_path`.']."""

    @abstractmethod
    def compile(self, ast: DocumentAST, output_path: str) -> None:
        r"""{'docstring': 'Compile a `DocumentAST` into a concrete document artifact.\n\nThis abstract method defines the contract for transforming a `DocumentAST`\ninstance into a specific output format (e.g., PDF, HTML) and writing the\nresult to a file. Subclasses must implement this method to provide the\nformat-specific serialization logic.\n\nArgs:\n    ast: The abstract syntax tree to compile.\n    output_path: The file system path where the compiled document artifact\n        will be saved.\n\nRaises:\n    ValueError: If the provided `ast` is malformed or contains nodes\n        unsupported by the specific compiler implementation.\n    FileNotFoundError: If the parent directory of `output_path` does not\n        exist.\n    PermissionError: If the process lacks write permissions for `output_path`.'}."""
        pass
