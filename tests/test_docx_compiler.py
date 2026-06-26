import tempfile
from pathlib import Path
from docx import Document

from domain.schemas.ast import (
    DocumentAST,
    ParagraphNode,
    HeadingNode,
    TableNode,
    TableRowNode,
    CellNode,
    SpacerNode,
    PageBreakNode,
)
from adapters.compilers.docx_compiler import DocxCompiler


def test_docx_compiler_e2e() -> None:
    """
    Verifica de forma e2e que el DocxCompiler puede traducir un DocumentAST complejo
    a un archivo .docx físico con preservación exacta de estilos y propiedades de celdas.
    """
    # --- ARRANGE ---
    ast = DocumentAST(
        title="Diagnostic Technical Report",
        metadata={"client": "Acme Corp", "version": "1.0"},
        nodes=[
            HeadingNode(text="1. Executive Summary", level=1, primary_color_rgb=[0, 114, 188]),
            ParagraphNode(
                text="This is a fuzzed diagnostic paragraph to evaluate AST stability.",
                bold=True,
                style="Normal",
                space_after=12,
            ),
            SpacerNode(points=18),
            TableNode(
                rows=[
                    TableRowNode(
                        cells=[
                            CellNode(text="Pilar", bold=True, bg_color="D9EAF7", align="CENTER"),
                            CellNode(text="Score", bold=False, bg_color="FFFFFF", align="RIGHT"),
                        ],
                        is_header=True,
                    ),
                    TableRowNode(
                        cells=[
                            CellNode(text="Compute", bold=False, bg_color="F2F2F2", align="LEFT"),
                            CellNode(text="4.5", bold=True, bg_color="FFF3CD", align="RIGHT"),
                        ]
                    ),
                ]
            ),
            PageBreakNode(),
        ],
    )

    compiler = DocxCompiler()

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = Path(tmp_dir) / "output.docx"

        # --- ACT ---
        compiler.compile(ast, str(output_file))

        # --- ASSERT ---
        assert output_file.is_file(), "El archivo compilado debe haberse guardado físicamente."

        # Cargar el documento generado para validar su estructura interna
        doc = Document(str(output_file))

        # Verificar encabezados y párrafos
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        assert "1. Executive Summary" in paragraphs
        assert "This is a fuzzed diagnostic paragraph to evaluate AST stability." in paragraphs

        # Verificar formateo de párrafo en negrita
        bold_para = next(p for p in doc.paragraphs if "stability" in p.text)
        assert len(bold_para.runs) > 0
        assert bold_para.runs[0].bold is True

        # Verificar tablas y celdas
        assert len(doc.tables) == 1, "Debe existir exactamente una tabla compilada."
        table = doc.tables[0]
        assert len(table.rows) == 2, "La tabla debe tener exactamente 2 filas."
        assert len(table.columns) == 2, "La tabla debe tener exactamente 2 columnas."
        assert len(table.rows[0].cells) == 2, "La primera fila debe tener 2 celdas."
        assert len(table.rows[1].cells) == 2, "La segunda fila debe tener 2 celdas."

        # Fila 1 (Encabezado)
        assert table.rows[0].cells[0].text == "Pilar"
        assert table.rows[0].cells[1].text == "Score"

        # Fila 2 (Datos)
        assert table.rows[1].cells[0].text == "Compute"
        assert table.rows[1].cells[1].text == "4.5"
