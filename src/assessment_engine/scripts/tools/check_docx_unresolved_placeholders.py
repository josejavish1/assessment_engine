"""
Módulo check_docx_unresolved_placeholders.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import re
import sys
from pathlib import Path
from docx import Document

PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 2:
        raise SystemExit(
            "Uso: python -m scripts.tools.check_docx_unresolved_placeholders <docx_path>"
        )

    docx_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    if not docx_path.exists():
        raise SystemExit(f"No existe el archivo: {docx_path}")

    doc = Document(str(docx_path))
    found = []

    for p in doc.paragraphs:
        matches = PLACEHOLDER_RE.findall(p.text or "")
        for m in matches:
            found.append(("paragraph", m, p.text.strip()))

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    matches = PLACEHOLDER_RE.findall(p.text or "")
                    for m in matches:
                        found.append(("table", m, p.text.strip()))

    unique = []
    seen = set()
    for item in found:
        key = (item[0], item[1], item[2])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    if unique:
        print("UNRESOLVED_PLACEHOLDERS=YES")
        for kind, placeholder, context in unique:
            print(f"{kind}: {placeholder} :: {context}")
        raise SystemExit(1)

    print("UNRESOLVED_PLACEHOLDERS=NO")


if __name__ == "__main__":
    main()
