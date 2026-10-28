"""
Provide semantic print stylesheets for physical and digital media using W3C @media print and the Paged Media Module.
"""

from __future__ import annotations


class PrintStylesheetService:
    @staticmethod
    def get_print_css() -> str:
        """Return the CSS styles for printing."""
        return """
        @media print {
            @page {
                size: A4;
                margin: 1.5cm;
            }
            nav, footer, .sidebar, .btn, .no-print, [role="dialog"], #cookie-consent-modal {
                display: none !important;
            }
            body {
                background: #FFFFFF !important;
                color: #000000 !important;
                font-size: 11pt;
                font-family: system-ui, -apple-system, sans-serif;
            }
            tr, .invoice-totals, .ticket-card {
                break-inside: avoid;
            }
            a[href^="http"]:after {
                content: " (" attr(href) ")";
                font-size: 9pt;
                color: #555555;
            }
        }
        """


PrintStylesheetPrimitive = PrintStylesheetService
print_stylesheet = PrintStylesheetService()

