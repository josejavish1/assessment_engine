"""
Scalar Modern Interactive API Docs Primitive — GEMA 29 (SOTA 2026).
Renders beautiful, fast, high-density OpenAPI documentation using Scalar CDN.
Superior alternative to Swagger UI with built-in dark/light mode and modern client libraries.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("assessment_engine.infrastructure.primitives.scalar_docs")


class ScalarDocsPrimitive:
    """
    Generate Scalar interface for OpenAPI documentation.
    """

    def generate_scalar_html(self, openapi_url: str = "/openapi.json", title: str = "API Documentation") -> str:
        """Generate standalone Scalar HTML pointing to the OpenAPI schema."""
        return f"""<!doctype html>
<html>
  <head>
    <title>{title}</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {{
        margin: 0;
      }}
    </style>
  </head>
  <body>
    <script
      id="api-reference"
      data-url="{openapi_url}"
      data-configuration='{{"theme": "purple"}}'>
    </script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
"""


scalar_docs = ScalarDocsPrimitive()
