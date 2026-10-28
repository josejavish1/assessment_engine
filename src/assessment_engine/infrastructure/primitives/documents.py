"""
Assemble PDF documents and manage statutory compliance bundles. Features:
1. Generate vector A4 PDF documents (invoices, medical records, certificates).
2. Apply W3C Paged Media CSS with print-color-adjust and page counters.
3. Generate statutory legal bundles matching official AEPD and INCIBE templates: - Legal Notice (Art. 10 LSSI-CE). - Privacy Policy with ARCO-POL rights (Art. 13 GDPR). - Technical table of exempt and third-party cookies.
"""

from __future__ import annotations

from assessment_engine.infrastructure.primitives.pdf_document_assembler import (
    PDFDocumentAssemblerPrimitive,
    pdf_document_assembler
)
from assessment_engine.infrastructure.primitives.legal_engine import (
    LegalEnginePrimitive,
    LegalCompanyIdentity,
    legal_engine
)
from assessment_engine.infrastructure.primitives.print_stylesheet import PrintStylesheetPrimitive, print_stylesheet

document_engine = pdf_document_assembler
legal_suite = legal_engine
