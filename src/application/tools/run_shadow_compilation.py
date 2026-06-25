import argparse
import time

from adapters.compilers.docx_compiler import DocxCompiler
from adapters.compilers.payload_to_ast import PayloadToASTBridge


def run_shadow_compilation() -> None:
    """Execute the V4 AST shadow compilation pipeline from the command line.

    This function serves as the main entry point for the shadow compilation tool.
    It parses command-line arguments for input JSON payloads (blueprint and
    annex) and a target path for the primary output document.

    Shadow compilation facilitates debugging and validation of the document
    rendering engine by generating multiple document variants from a single
    source Abstract Syntax Tree (AST). After compiling the full, canonical
    document, several "shadow" variants are created by systematically filtering
    specific node types. This process isolates the rendering logic for
    individual components.

    The following DOCX variants are generated in the same directory as the
    primary output file specified by the `--output` argument:

    - *.shadow.docx: The complete, canonical document.
    - *.minimal.docx: Contains all AST nodes except for tables and pictures.
    - *.nopictures.docx: Contains all AST nodes except for pictures.
    - *.notables.docx: Contains all AST nodes except for tables.
    - *.table_N.docx: For each of the first three tables (N=0, 1, 2), a
      document is generated containing that single table along with all
      other non-table content from the original AST.

    Args:
        --blueprint-payload (str): The file path to the main blueprint JSON
            payload.
        --approved-annex (str): The file path to the approved annex JSON payload.
        --output (str): The target file path for the primary compiled DOCX
            document. Filenames for other shadow variants are derived from this
            path.

    Raises:
        FileNotFoundError: If the file specified by `--blueprint-payload` or
            `--approved-annex` does not exist.
        PermissionError: If the file specified by `--output` or its derived
            shadow paths cannot be written due to insufficient permissions.
        ValueError: If the input JSON payloads are malformed or fail validation
            during conversion to an AST.
    """
    parser = argparse.ArgumentParser(description="V4 AST Shadow Compiler Tool")
    parser.add_argument(
        "--blueprint-payload",
        required=True,
        help="Path to the main blueprint_payload.json",
    )
    parser.add_argument(
        "--approved-annex",
        required=True,
        help="Path to the approved_annex.template_payload.json",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Target path for the compiled shadow DOCX document",
    )
    args = parser.parse_args()

    print("🛰️  [V4 AST Shadow Compiler] Iniciando ejecución en sombra para:")
    print(f"   ├─ Blueprint: {args.blueprint_payload}")
    print(f"   ├─ Síntesis: {args.approved_annex}")

    start_time = time.time()

    # The primary step of the compilation pipeline is to deserialize the input JSON into its corresponding Abstract Syntax Tree (AST) object graph. This in-memory representation is the canonical source for all subsequent compilation variants.
    bridge = PayloadToASTBridge()
    ast = bridge.convert(args.blueprint_payload, args.approved_annex)

    conversion_time = time.time() - start_time
    print(
        f"   ├─ Conversión a AST completada en memoria en {conversion_time * 1000:.2f} ms"
    )

    # Execute the standard, full compilation process to generate the canonical DOCX output. This serves as the baseline reference for all shadow compilations.
    DocxCompiler().compile(ast, args.output)

    # Generate a minimal DOCX variant containing only core textual and heading elements. This shadow build isolates the foundational text rendering logic from more complex components like tables and images.
    from domain.schemas.ast import DocumentAST

    minimal_nodes = [
        n for n in ast.nodes if getattr(n, "type", None) not in {"table", "picture"}
    ]
    minimal_ast = DocumentAST(
        title=ast.title + " (Minimal)", metadata=ast.metadata, nodes=minimal_nodes
    )

    minimal_output = args.output.replace(".shadow.docx", ".minimal.docx")
    DocxCompiler().compile(minimal_ast, minimal_output)

    # Generate a tables-only DOCX variant by excluding all image elements. This shadow build is used to isolate and validate the table compilation subsystem.
    nopix_nodes = [n for n in ast.nodes if getattr(n, "type", None) != "picture"]
    nopix_ast = DocumentAST(
        title=ast.title + " (No Pictures)", metadata=ast.metadata, nodes=nopix_nodes
    )
    nopix_output = args.output.replace(".shadow.docx", ".nopictures.docx")
    DocxCompiler().compile(nopix_ast, nopix_output)

    # Generate an images-only DOCX variant by excluding all table elements. This shadow build is used to isolate and validate the image rendering subsystem.
    notab_nodes = [n for n in ast.nodes if getattr(n, "type", None) != "table"]
    notab_ast = DocumentAST(
        title=ast.title + " (No Tables)", metadata=ast.metadata, nodes=notab_nodes
    )
    notab_output = args.output.replace(".shadow.docx", ".notables.docx")
    DocxCompiler().compile(notab_ast, notab_output)

    # The following shadow builds isolate principal table structures for targeted, independent compilation. This allows for focused debugging of individual complex table components without the overhead of a full document compile.
    table_nodes = [n for n in ast.nodes if getattr(n, "type", None) == "table"]

    # Isolate and compile only the "Maturity Scorecard" table (Table 0) to facilitate targeted debugging of this specific component.
    if len(table_nodes) > 0:
        t0_nodes = [
            n
            for n in ast.nodes
            if getattr(n, "type", None) != "table" or n == table_nodes[0]
        ]
        t0_ast = DocumentAST(
            title=ast.title + " (Table 0)", metadata=ast.metadata, nodes=t0_nodes
        )
        t0_output = args.output.replace(".shadow.docx", ".table_0.docx")
        DocxCompiler().compile(t0_ast, t0_output)

    # Isolate and compile only the "Grade Justification Matrix" table (Table 1) to facilitate targeted debugging of this specific component.
    if len(table_nodes) > 1:
        t1_nodes = [
            n
            for n in ast.nodes
            if getattr(n, "type", None) != "table" or n == table_nodes[1]
        ]
        t1_ast = DocumentAST(
            title=ast.title + " (Table 1)", metadata=ast.metadata, nodes=t1_nodes
        )
        t1_output = args.output.replace(".shadow.docx", ".table_1.docx")
        DocxCompiler().compile(t1_ast, t1_output)

    # Isolate and compile only the "5x5 Heatmap" table (Table 2) to facilitate targeted debugging of this specific component.
    if len(table_nodes) > 2:
        t2_nodes = [
            n
            for n in ast.nodes
            if getattr(n, "type", None) != "table" or n == table_nodes[2]
        ]
        t2_ast = DocumentAST(
            title=ast.title + " (Table 2)", metadata=ast.metadata, nodes=t2_nodes
        )
        t2_output = args.output.replace(".shadow.docx", ".table_2.docx")
        DocxCompiler().compile(t2_ast, t2_output)

    compilation_time = time.time() - (start_time + conversion_time)
    total_time = time.time() - start_time

    print(
        f"   ├─ Compilación física de DOCX completada en {compilation_time * 1000:.2f} ms"
    )
    print(
        f"🎉 ¡Compilación en Sombra V4 Completada con Éxito en {total_time * 1000:.2f} ms!"
    )
    print(f"   ├─ Archivo Generado (Full): {args.output}")
    print(f"   ├─ Archivo Generado (Minimal): {minimal_output}")
    print(f"   ├─ Archivo Generado (No Pictures): {nopix_output}")
    print(f"   └─ Archivo Generado (No Tables): {notab_output}")


if __name__ == "__main__":
    run_shadow_compilation()
