"""Late-binding commercial filename presentation builder for deliverable edge delivery."""

from __future__ import annotations

import re
import urllib.parse

from assessment_engine.infrastructure.artifacts.domain import (
    ArtifactContext,
    ArtifactVersionRecord,
)


class PresentationFilenameBuilder:
    """Constructs human-readable, localized commercial filenames at the delivery edge."""

    @classmethod
    def build_display_filename(
        cls,
        record: ArtifactVersionRecord,
        ctx: ArtifactContext,
        doc_title_override: str = "",
    ) -> str:
        """Constructs commercial executive display filename without mutating storage."""
        meta = record.presentation_metadata
        tenant_display = meta.get("tenant_display_name") or ctx.tenant_id.replace("_", " ").title()
        domain_display = meta.get("domain_unit_display") or ctx.domain_unit_id.replace("_", " ").title()
        doc_title = doc_title_override or meta.get("doc_title_localized") or ctx.doc_type.value.replace("_", " ").title()
        period_display = ctx.period.upper()
        ext = ctx.extension.value

        return f"{tenant_display} - {doc_title} - {domain_display} ({period_display}) v{record.version}.{ext}"

    @classmethod
    def build_http_content_disposition(cls, display_filename: str) -> str:
        """Constructs RFC 5987 and RFC 6266 compliant Content-Disposition HTTP header.

        Provides strict ASCII fallback and percent-encoded UTF-8 filename.
        """
        # Create safe ASCII fallback filename replacing non-ASCII characters
        ascii_fallback = re.sub(r"[^\x20-\x7E]", "_", display_filename)
        ascii_fallback = ascii_fallback.replace('"', '\\"')

        # RFC 5987 percent-encoding for UTF-8
        encoded_utf8 = urllib.parse.quote(display_filename, safe="")

        return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_utf8}'
