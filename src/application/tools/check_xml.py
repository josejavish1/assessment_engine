import xml.etree.ElementTree as ET
import zipfile


def check_docx_zip(path: str):
    """Inspects a DOCX file as a ZIP archive to validate its core structure.

    This function performs a lightweight validation of an Office Open XML (OOXML)
    .docx file. It treats the file as a standard ZIP archive and verifies two
    primary conditions: the presence of the main document part ('word/document.xml')
    and its well-formedness as XML.

    The function is designed for diagnostic purposes. All findings and errors,
    such as `zipfile.BadZipFile` or `xml.etree.ElementTree.ParseError`, are
    caught and printed to standard output rather than being raised.

    Args:
        path (str): The file system path to the .docx document to validate.

    Returns:
        None. All results are printed to standard output.
    """
    print(f"📦 Validando estructura ZIP de {path}...")
    try:
        with zipfile.ZipFile(path, "r") as z:
            # The Office Open XML (OOXML) standard defines a package of multiple XML-based files. This stage isolates the core document components to ensure focused and efficient validation against the standard's structural and content requirements.
            files = z.namelist()
            print(f"   ├─ Archivos en ZIP: {len(files)}")
            has_document_xml = "word/document.xml" in files
            print(f"   ├─ Contiene word/document.xml: {has_document_xml}")

            #
            if has_document_xml:
                xml_data = z.read("word/document.xml")
                root = ET.fromstring(xml_data)
                print(f"   └─ word/document.xml parseado con éxito (raíz: {root.tag})")
    except Exception as e:
        print(f"   ❌ ERROR al leer o parsear ZIP: {e}")


if __name__ == "__main__":
    check_docx_zip("working/redeia_v3/T2/AS-IS_Anexo_Tecnico_T2.docx")
    print()
    check_docx_zip("working/redeia_v3/T2/AS-IS_Anexo_Tecnico_T2.shadow.docx")
