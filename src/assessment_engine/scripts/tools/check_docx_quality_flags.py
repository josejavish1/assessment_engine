"""
Módulo check_docx_quality_flags.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import re
import sys
from pathlib import Path
from docx import Document

BAD_PATTERNS = [
    r"\{\{[^{}]+\}\}",
    r"\{'statement':",
    r'"statement":',
]


def collect_text(doc):
    parts = []
    for p in doc.paragraphs:
        if p.text:
            parts.append(p.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if p.text:
                        parts.append(p.text)
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 2:
        raise SystemExit(
            "Uso: python -m scripts.tools.check_docx_quality_flags <docx_path>"
        )

    path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    if not path.exists():
        raise SystemExit(f"No existe el archivo: {path}")

    doc = Document(str(path))
    text = collect_text(doc)

    flags = []
    for pattern in BAD_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            flags.append((pattern, len(matches)))

    excessive_ellipsis = text.count("...")

    if flags or excessive_ellipsis > 3:
        print("DOCX_QUALITY_FLAGS=YES")
        for pattern, count in flags:
            print(f"pattern={pattern} count={count}")
        if excessive_ellipsis > 3:
            print(f"ellipsis_count={excessive_ellipsis}")
        raise SystemExit(1)

    print("DOCX_QUALITY_FLAGS=NO")


if __name__ == "__main__":
    main()
