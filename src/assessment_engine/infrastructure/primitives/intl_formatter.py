"""
Provide zero-dependency browser and backend helpers for formatting currencies, dates, and decimal numbers according to user locales (es-ES, en-US, de-DE).
"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger("assessment_engine.infrastructure.primitives.intl_formatter")


class IntlFormatterPrimitive:
    """
    Formateador internacional de monedas y fechas conforme a W3C ECMAScript Intl.
    """

    def format_currency(self, amount: float, currency: str = "EUR", locale: str = "es-ES") -> str:
        """Format a number as currency according to the locale."""
        if locale.startswith("es"):
            # In Spain: 1.250,50 €
            formatted_num = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            symbol = "€" if currency == "EUR" else currency
            return f"{formatted_num} {symbol}"
        else:
            # In the US: $1,250.50
            symbol = "$" if currency == "USD" else ("€" if currency == "EUR" else currency)
            return f"{symbol}{amount:,.2f}"

    def format_date(self, dt: datetime | str, locale: str = "es-ES") -> str:
        """Format a date into a human-readable format."""
        if isinstance(dt, str):
            try:
                dt_obj = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            except (RuntimeError, ValueError, KeyError, OSError, TypeError):
                return dt
        else:
            dt_obj = dt

        if locale.startswith("es"):
            return dt_obj.strftime("%d/%m/%Y")
        return dt_obj.strftime("%Y-%m-%d")

    def generate_browser_intl_helper_js(self) -> str:
        """Generate the frontend TypeScript/JavaScript module without external dependencies."""
        return """// Tier-1 W3C ECMAScript Intl Client Helper
export function formatCurrency(amount: number, currency: string = 'EUR'): string {
  return new Intl.NumberFormat(navigator.language || 'es-ES', {
    style: 'currency',
    currency: currency,
  }).format(amount);
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(navigator.language || 'es-ES', {
    dateStyle: 'medium',
  }).format(d);
}
"""


intl_formatter = IntlFormatterPrimitive()
