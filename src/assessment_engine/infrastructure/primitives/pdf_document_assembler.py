"""
Universal Vector PDF Document Assembler — GEMA 22 (SOTA 2026).
Compiles W3C CSS Paged Media compliant HTML and exports vector A4 PDFs
using Chromium's headless Print-to-PDF engine.
Domain-agnostic: generates formal invoices, medical/health certificates, and service agreements.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from playwright.async_api import async_playwright

logger = logging.getLogger("assessment_engine.infrastructure.primitives.pdf_document_assembler")


@dataclass
class InvoiceLine:
    description: str
    quantity: int
    unit_price: float
    vat_rate: float = 21.0


@dataclass
class UniversalDocumentData:
    doc_type: str  # "FACTURA", "CERTIFICADO", "PRESUPUESTO"
    doc_number: str
    issue_date: str
    issuer_name: str
    issuer_tax_id: str
    recipient_name: str
    recipient_id: str
    lines: list[InvoiceLine] = field(default_factory=list)
    notes: str = ""


class PDFDocumentAssemblerPrimitive:
    """
    Ensamblador de documentos en PDF vectorial W3C Paged Media.
    Agnóstico al dominio: produce documentos oficiales para cualquier industria.
    """

    def generate_html_document(self, data: UniversalDocumentData) -> str:
        """Generate structured HTML with A4 page CSS rules."""
        total_net = sum(l.quantity * l.unit_price for l in data.lines)
        total_vat = sum(l.quantity * l.unit_price * (l.vat_rate / 100.0) for l in data.lines)
        total_gross = total_net + total_vat

        lines_html = ""
        for line in data.lines:
            subtotal = line.quantity * line.unit_price
            lines_html += f"""
            <tr>
              <td style="padding: 8px; border-bottom: 1px solid #E2E8F0;">{line.description}</td>
              <td style="padding: 8px; border-bottom: 1px solid #E2E8F0; text-align: center;">{line.quantity}</td>
              <td style="padding: 8px; border-bottom: 1px solid #E2E8F0; text-align: right;">{line.unit_price:.2f} €</td>
              <td style="padding: 8px; border-bottom: 1px solid #E2E8F0; text-align: right;">{subtotal:.2f} €</td>
            </tr>
            """

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{data.doc_type} - {data.doc_number}</title>
  <style>
    @page {{
      size: A4;
      margin: 20mm;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #0F172A;
      margin: 0;
      font-size: 13px;
      line-height: 1.5;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      border-bottom: 2px solid #0D9488;
      padding-bottom: 15px;
      margin-bottom: 25px;
    }}
    .badge {{
      background-color: #CCFBF1;
      color: #0F766E;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 4px;
      text-transform: uppercase;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
    }}
    th {{
      background-color: #F8FAFC;
      border-bottom: 2px solid #CBD5E1;
      padding: 8px;
      text-align: left;
      font-size: 11px;
      text-transform: uppercase;
    }}
    .totals {{
      width: 40%;
      margin-left: auto;
      margin-top: 20px;
    }}
    .total-row {{
      display: flex;
      justify-content: space-between;
      padding: 4px 0;
    }}
    .grand-total {{
      font-size: 16px;
      font-weight: 800;
      color: #0D9488;
      border-top: 2px solid #0D9488;
      padding-top: 6px;
      margin-top: 6px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <span class="badge">{data.doc_type} OFICIAL</span>
      <h1 style="margin: 6px 0; font-size: 22px;">{data.issuer_name}</h1>
      <p style="margin: 0; color: #64748B;">CIF/NIF: {data.issuer_tax_id}</p>
    </div>
    <div style="text-align: right;">
      <h2 style="margin: 0; font-size: 18px; color: #0D9488;">Nº {data.doc_number}</h2>
      <p style="margin: 4px 0; color: #64748B;">Fecha: {data.issue_date}</p>
    </div>
  </div>

  <div style="margin-bottom: 20px; background: #F8FAFC; padding: 12px; border-radius: 6px; border: 1px solid #E2E8F0;">
    <strong>Destinatario / Titular:</strong> {data.recipient_name} (ID: {data.recipient_id})
  </div>

  <table>
    <thead>
      <tr>
        <th>Concepto</th>
        <th style="text-align: center;">Cant.</th>
        <th style="text-align: right;">Precio Unit.</th>
        <th style="text-align: right;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
      {lines_html}
    </tbody>
  </table>

  <div class="totals">
    <div class="total-row"><span>Base Imponible:</span><span>{total_net:.2f} €</span></div>
    <div class="total-row"><span>IVA:</span><span>{total_vat:.2f} €</span></div>
    <div class="total-row grand-total"><span>Total Oficial:</span><span>{total_gross:.2f} €</span></div>
  </div>

  {f'<p style="margin-top: 30px; font-size: 11px; color: #64748B; border-top: 1px solid #E2E8F0; padding-top: 10px;">Notas: {data.notes}</p>' if data.notes else ''}
</body>
</html>"""

    async def render_pdf_to_file(self, data: UniversalDocumentData, target_file: Path) -> Path:
        """Render the document to a vector PDF file using Playwright Chromium."""
        html_content = self.generate_html_document(data)
        target_file.parent.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.set_content(html_content, wait_until="domcontentloaded")
            await page.pdf(
                path=str(target_file),
                format="A4",
                print_background=True,
                margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"}
            )
            await browser.close()

        logger.info(f"[PDFDocumentAssembler] PDF exportado ({target_file.stat().st_size} bytes): {target_file.name}")
        return target_file


pdf_document_assembler = PDFDocumentAssemblerPrimitive()
