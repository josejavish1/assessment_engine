import xml.etree.ElementTree as ET
import zipfile


def extract_tables_xml(path: str):
    r"""{'docstring': 'Extract all `w:tbl` XML elements from a .docx file.\n\n    This function opens a .docx file as a ZIP archive, reads the main\n    `word/document.xml` content, parses it, and finds all elements\n    representing tables using the appropriate WordprocessingML namespace.\n\n    Args:\n        path: The file path to the .docx document.\n\n    Returns:\n        A list of `xml.etree.ElementTree.Element` objects, where each\n        element represents a `<w:tbl>` (table) found in the document.\n\n    Raises:\n        FileNotFoundError: If the file specified by `path` does not exist.\n        zipfile.BadZipFile: If the file at `path` is not a valid ZIP archive\n            or is corrupted.\n        KeyError: If `word/document.xml` is not found within the archive,\n            indicating an invalid .docx file structure.\n        xml.etree.ElementTree.ParseError: If the `word/document.xml` content\n            is malformed and cannot be parsed.'}."""
    with zipfile.ZipFile(path, "r") as z:
        xml_data = z.read("word/document.xml")
        root = ET.fromstring(xml_data)

        #
        tbl_elements = root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl")
        return tbl_elements


def compare_tables():
    """Compare select OOXML properties of the first table in two DOCX documents.

    This debugging utility loads two DOCX files from hardcoded paths, a
    'working' version and a 'shadow' version, to analyze differences in their
    table structures. It uses the `extract_tables_xml` helper to parse all
    tables from each document into their raw XML element representations.

    The function then isolates the first table element from each document and
    prints a side-by-side comparison of its properties to standard output. The
    comparison specifically covers the child elements and attributes of the
    table properties (`w:tblPr`) and the properties of the first table cell
    (`w:tcPr`).

    Args:
        None.

    Raises:
        FileNotFoundError: Propagated from `extract_tables_xml` if either of
            the hardcoded DOCX file paths does not exist.
    """
    working_path = "working/redeia_v3/T2/AS-IS_Anexo_Tecnico_T2.docx"
    shadow_path = "working/redeia_v3/T2/AS-IS_Anexo_Tecnico_T2.shadow.docx"

    print("🔍 Cargando tablas del archivo que funciona (V3)...")
    working_tbls = extract_tables_xml(working_path)
    print(f"   ├─ Tablas encontradas: {len(working_tbls)}")

    print("\n🔍 Cargando tablas del archivo en sombra (V4)...")
    shadow_tbls = extract_tables_xml(shadow_path)
    print(f"   ├─ Tablas encontradas: {len(shadow_tbls)}")

    # The first table element is programmatically assumed to be the Maturity Scorecard based on the document's structural contract.
    if working_tbls and shadow_tbls:
        print("\n⚖️  Comparando la primera tabla (Cuadro de Mando de Madurez)...")
        w_tbl = working_tbls[0]
        s_tbl = shadow_tbls[0]

        w_tblPr = w_tbl.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblPr")
        s_tblPr = s_tbl.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tblPr")

        print("   [w:tblPr en V3]:")
        for child in list(w_tblPr) if w_tblPr is not None else []:
            print(f"      ├─ {child.tag.split('}')[-1]}: {child.attrib}")

        print("   [w:tblPr en V4]:")
        for child in list(s_tblPr) if s_tblPr is not None else []:
            print(f"      ├─ {child.tag.split('}')[-1]}: {child.attrib}")

        #
        w_cell = w_tbl.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc")
        s_cell = s_tbl.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc")

        w_tcPr = w_cell.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcPr") if w_cell is not None else None
        s_tcPr = s_cell.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcPr") if s_cell is not None else None

        print("\n   [w:tcPr de la primera celda en V3]:")
        for child in list(w_tcPr) if w_tcPr is not None else []:
            print(f"      ├─ {child.tag.split('}')[-1]}: {child.attrib}")

        print("   [w:tcPr de la primera celda en V4]:")
        for child in list(s_tcPr) if s_tcPr is not None else []:
            print(f"      ├─ {child.tag.split('}')[-1]}: {child.attrib}")


if __name__ == "__main__":
    compare_tables()
