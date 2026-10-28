# core/primitives/business_diff_summarizer.py
"""
Business Diff Summarizer (Primitive 81).
Translates technical git diffs into human-readable business impact summaries.
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BusinessDiffSummary:
    diff_sha256: str
    analyzed_at_utc: str
    summary_title: str
    business_impacts: Tuple[str, ...]
    safety_verdict: Literal['SEGURO PARA PUBLICAR', 'REQUIERE REVISIÓN']
    files_affected: Tuple[str, ...]
    is_safe_to_publish: bool
    total_additions: int
    total_deletions: int


class BusinessDiffSummarizer:
    def __init__(self, client: Optional[Any] = None) -> None:
        self.client = client
        self._file_re = re.compile(r'^diff --git a/(.+?) b/(.+?)$', re.MULTILINE)
        self._add_re = re.compile(r'^\+(?!\+)', re.MULTILINE)
        self._del_re = re.compile(r'^-(?!-)', re.MULTILINE)
        self._veto_words = {
            'db', 'migration', 'sql', 'schema', 'secret', 
            'credential', 'billing', 'payment', 'stripe', 'paypal'
        }

    def _get_utc_now(self) -> str:
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _parse_files(self, text: str) -> Tuple[str, ...]:
        matches = self._file_re.findall(text)
        return tuple(sorted(list(set(m[1] for m in matches))))

    def _is_vetoed(self, files: Tuple[str, ...]) -> bool:
        for f in files:
            lower_f = f.lower()
            if any(w in lower_f for w in self._veto_words):
                return True
        return False

    def _extract_impacts(self, text: str, files: Tuple[str, ...]) -> Tuple[str, ...]:
        lower_text = text.lower()
        files_str = " ".join(files).lower()
        combined = f"{lower_text} {files_str}"
        impacts = []
        if any(w in combined for w in ('db', 'migration', 'sql', 'schema', 'base de datos')):
            impacts.append("Base de Datos y Esquemas")
        if any(w in combined for w in ('billing', 'payment', 'stripe', 'paypal', 'pago', 'facturaci')):
            impacts.append("Pagos y Facturación")
        if any(w in combined for w in ('catálogo', 'catalog', 'precio', 'tarifa', 'price', 'servicio')):
            impacts.append("Catálogo y Servicios")
        if any(w in combined for w in ('reserva', 'booking', 'appointment', 'teléfono', 'phone', 'formulario')):
            impacts.append("Sistema de Reservas y Citas")
        
        if not impacts:
            impacts.append("Ajustes Generales de Configuración y Código")
            
        return tuple(impacts)

    def _build_deterministic_summary(
        self, 
        sha: str, 
        now: str, 
        diff_text: str, 
        files: Tuple[str, ...], 
        adds: int, 
        dels: int, 
        vetoed: bool,
        title: Optional[str] = None
    ) -> BusinessDiffSummary:
        impacts = self._extract_impacts(diff_text, files)
        is_safe = not vetoed
        verdict: Literal['SEGURO PARA PUBLICAR', 'REQUIERE REVISIÓN'] = (
            "REQUIERE REVISIÓN" if vetoed else "SEGURO PARA PUBLICAR"
        )
        if title is None:
            title = (
                "Cambios Críticos Detectados en Infraestructura o Finanzas"
                if vetoed
                else f"Actualización segura en {len(files)} componente{'s' if len(files) != 1 else ''}"
            )
        return BusinessDiffSummary(
            diff_sha256=sha,
            analyzed_at_utc=now,
            summary_title=title,
            business_impacts=impacts,
            safety_verdict=verdict,
            files_affected=files,
            is_safe_to_publish=is_safe,
            total_additions=adds,
            total_deletions=dels
        )

    def _query_client_for_summary(self, client: Any, diff_text: str, context: str) -> dict[str, Any]:
        """Query LLM client using either official models.generate_content or generate_summary."""
        if hasattr(client, "models") and getattr(client, "models") is not None:
            prompt = f"Context: {context}\nDiff: {diff_text}"
            resp = client.models.generate_content(prompt)
            text = getattr(resp, "text", "") or ""
            return json.loads(text) if text else {}

        if hasattr(client, "generate_summary"):
            try:
                raw_data = client.generate_summary(diff_text, context)
            except TypeError:
                raw_data = client.generate_summary(diff=diff_text, context=context)

            if not isinstance(raw_data, dict):
                raise ValueError("Formato de respuesta inválido")
            title = raw_data.get("title") or raw_data.get("summary_title", "Actualización")
            impacts = raw_data.get("impacts") or raw_data.get("business_impacts", [])
            return {
                "summary_title": title,
                "business_impacts": impacts,
                "is_safe_to_publish": raw_data.get("is_safe_to_publish", True),
            }

        return {}

    def _merge_impacts(self, det_impacts: Tuple[str, ...], raw_impacts: Any) -> Tuple[str, ...]:
        """Safely combine deterministic security tags with LLM-generated business impacts."""
        llm_impacts = list(raw_impacts) if isinstance(raw_impacts, (list, tuple)) else []
        final_impacts = list(det_impacts)
        for imp in llm_impacts:
            if imp not in final_impacts:
                final_impacts.append(imp)
        return tuple(final_impacts)

    def summarize_diff(self, diff_text: str, context: str = "") -> BusinessDiffSummary:
        """Summarize git diff impacts into clear business explanations and safety verdicts."""
        sha = self._hash(diff_text)
        now = self._get_utc_now()

        if not diff_text.strip():
            return BusinessDiffSummary(
                diff_sha256=sha,
                analyzed_at_utc=now,
                summary_title="Sin cambios detectados",
                business_impacts=("Ningún impacto",),
                safety_verdict="SEGURO PARA PUBLICAR",
                files_affected=(),
                is_safe_to_publish=True,
                total_additions=0,
                total_deletions=0
            )

        files = self._parse_files(diff_text)
        adds = len(self._add_re.findall(diff_text))
        dels = len(self._del_re.findall(diff_text))
        vetoed = self._is_vetoed(files)

        if self.client is None or vetoed:
            return self._build_deterministic_summary(sha, now, diff_text, files, adds, dels, vetoed)

        try:
            data = self._query_client_for_summary(self.client, diff_text, context)
            is_safe = False if vetoed else bool(data.get("is_safe_to_publish", True))
            verdict: Literal['SEGURO PARA PUBLICAR', 'REQUIERE REVISIÓN'] = (
                "REQUIERE REVISIÓN" if vetoed else data.get("safety_verdict", "SEGURO PARA PUBLICAR")
            )
            final_impacts = self._merge_impacts(self._extract_impacts(diff_text, files), data.get("business_impacts", []))

            return BusinessDiffSummary(
                diff_sha256=sha,
                analyzed_at_utc=now,
                summary_title=str(data.get("summary_title", "Actualización")),
                business_impacts=final_impacts,
                safety_verdict=verdict,
                files_affected=files,
                is_safe_to_publish=is_safe,
                total_additions=adds,
                total_deletions=dels
            )
        except Exception as e:
            logger.error("LLM failure during diff summarization: %s", e)
            fallback_title = f"Actualización segura en {len(files)} componente" if not vetoed else "Actualización que requiere revisión"
            return self._build_deterministic_summary(
                sha, now, diff_text, files, adds, dels, vetoed, title=fallback_title
            )