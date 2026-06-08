import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EvidenceSnapshotter:
    """
    SISTEMA DE GOBERNANZA DE EVIDENCIAS DIGITALES (TIER 1).
    Responsable de validar, capturar y asegurar la persistencia de fuentes externas.
    Utiliza Playwright para bypassear protecciones Anti-Bot y Muros de Cookies.
    """

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir / "evidence_snapshots"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_ms = 15000
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        }

    async def process_urls(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrae, valida y captura snapshots de las URLs encontradas en un texto.
        Solo devuelve evidencias que hayan sido verificadas al 100%.
        """
        urls = self._extract_urls(text)
        claims: List[Dict[str, Any]] = []

        for url in urls:
            logger.info(f"🛡️ Validando evidencia externa: {url}")
            snapshot = await self.capture_snapshot(url)
            # REGLA DE ÉLITE: Solo permitimos evidencias verificadas
            if snapshot and snapshot.get("status") == "verified":
                claims.append(snapshot)
            else:
                logger.error(
                    f"❌ RECHAZADA: Evidencia externa rota o protegida: {url}. No se incluirá en el Dossier."
                )

        return claims

    def _extract_urls(self, text: str) -> List[str]:
        """Extrae URLs válidas de un bloque de texto."""
        url_pattern = r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*"
        raw_urls = re.findall(url_pattern, text)
        # Limpieza básica de URLs extraídas
        cleaned = []
        for u in raw_urls:
            u = u.strip().rstrip(".").rstrip(")").rstrip("]")
            if u not in cleaned:
                cleaned.append(u)
        return cleaned

    async def capture_snapshot(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Descarga el contenido de la URL. Usa un motor híbrido:
        - Resolución de Redirects para obtener la URL real humana.
        - Descarga Directa para Binarios (PDF, DOCX) para saltar WAFs.
        - Playwright para HTML interactivo y muros de cookies.
        """
        import httpx

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright no está instalado.")
            return None

        # Limpiar URL
        url = url.strip().rstrip(".").rstrip(")").rstrip("]")
        original_input_url = url

        # --- ÉLITE: RESOLUCIÓN DE REDIRECTS (Google Grounding) ---
        final_human_url = url
        if "grounding-api-redirect" in url:
            try:
                async with httpx.AsyncClient(
                    timeout=10.0, follow_redirects=True, headers=self.headers
                ) as client:
                    # Hacemos un HEAD para no bajar el cuerpo aún, solo ver a dónde apunta
                    r = await client.head(url)
                    final_human_url = str(r.url)
                    print(f"      🔗 [REDIRECT] URL real detectada: {final_human_url}")
            except Exception as e:
                logger.warning(f"No se pudo resolver redirect para {url}: {e}")

        url_hash = hashlib.sha256(final_human_url.encode()).hexdigest()[:12]

        # 1. DETECCIÓN DE TIPO DE ARCHIVO (Sobre la URL final)
        is_binary = any(
            final_human_url.lower().endswith(ext)
            for ext in [".pdf", ".docx", ".xlsx", ".zip"]
        )
        file_ext = ".pdf" if final_human_url.lower().endswith(".pdf") else ".html"
        file_path = self.storage_dir / f"snapshot_{url_hash}{file_ext}"

        # 2. VÍA B: DESCARGA DIRECTA (Para Binarios protegidos)
        if is_binary:
            try:
                async with httpx.AsyncClient(
                    timeout=20.0, follow_redirects=True, headers=self.headers
                ) as client:
                    print(f"      📥 [BINARY] Descargando documento: {final_human_url}")
                    r_bin = await client.get(final_human_url)
                    if r_bin.status_code == 200:
                        file_path.write_bytes(r_bin.content)
                        return {
                            "source_type": "EXTERNAL_DOCUMENT",
                            "url": final_human_url,
                            "google_redirect_url": original_input_url
                            if original_input_url != final_human_url
                            else None,
                            "local_snapshot": str(
                                file_path.relative_to(
                                    self.storage_dir.parent.parent.parent
                                )
                            ),
                            "captured_at": datetime.now(timezone.utc).isoformat(),
                            "status": "verified",
                            "content_hash": hashlib.sha256(r_bin.content).hexdigest(),
                        }
            except Exception as e:
                logger.warning(f"Fallo descarga directa de {final_human_url}: {e}")

        # 3. VÍA A: PLAYWRIGHT (Webs)
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.headers["User-Agent"]
                )
                page = await context.new_page()

                print(f"      🌐 [BROWSER] Capturando fuente: {final_human_url}")
                response = await page.goto(
                    final_human_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                if response and response.status < 400:
                    await page.wait_for_timeout(2000)
                    content = (
                        await page.content() if not is_binary else await response.body()
                    )

                    content_bytes: bytes
                    if isinstance(content, str):
                        content_bytes = content.encode("utf-8")
                    else:
                        content_bytes = content

                    file_path.write_bytes(content_bytes)
                    await browser.close()
                    return {
                        "source_type": "EXTERNAL_OSINT",
                        "url": final_human_url,
                        "google_redirect_url": original_input_url
                        if original_input_url != final_human_url
                        else None,
                        "local_snapshot": str(
                            file_path.relative_to(self.storage_dir.parent.parent.parent)
                        ),
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                        "status": "verified",
                        "content_hash": hashlib.sha256(content_bytes).hexdigest(),
                    }
                else:
                    await browser.close()
                    return {
                        "source_type": "EXTERNAL_OSINT",
                        "url": final_human_url,
                        "status": "broken",
                        "error": f"HTTP {response.status if response else 'Unknown'}",
                    }
        except Exception as e:
            return {
                "source_type": "EXTERNAL_OSINT",
                "url": final_human_url,
                "status": "error",
                "error": str(e),
            }

    async def register_wayback(self, url: str) -> None:
        """
        (Opcional) Registra la URL en Archive.org para persistencia histórica.
        """
        pass


class EvidenceIntegrityManager:
    """Orquestador de la integridad de evidencias para el Dossier final."""

    @staticmethod
    def sync_claims_with_dossier(
        dossier: Dict[str, Any], claims: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Vincula los snapshots capturados con las menciones en el dossier.
        """
        if "claims" not in dossier:
            dossier["claims"] = []

        for claim in claims:
            # Evitar duplicados
            if not any(c.get("url") == claim.get("url") for c in dossier["claims"]):
                dossier["claims"].append(claim)

        return dossier
