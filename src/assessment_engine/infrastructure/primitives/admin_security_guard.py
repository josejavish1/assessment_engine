"""
Admin Perimeter Security Guard Primitive — GEMA 75 (SOTA 2026).
Protects internal administrative routes (/admin and sensitive /api/* endpoints)
with constant-time HMAC validation, HttpOnly session cookies, and RFC 6750 Bearer headers.
Prevents timing side-channel attacks (CWE-208) and unauthorized control-plane access.
"""

from __future__ import annotations

import hmac
import html
import logging
import os
import secrets
from typing import Any
from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

logger = logging.getLogger("assessment_engine.infrastructure.primitives.admin_security_guard")

COOKIE_NAME = "autonomuos_admin_session"
DEFAULT_SESSION_MAX_AGE = 86400  # 24 horas


async def require_admin_auth(request: Request) -> None:
    """Provide a declarative FastAPI dependency to secure internal factory routers. Require authentication via Bearer token, X-Admin-Token header, or session cookie."""
    if not admin_security_guard.is_enforced():
        return
    if not admin_security_guard.is_request_authenticated(request):
        raise HTTPException(
            status_code=401,
            detail="Acceso administrativo restringido: se requiere FACTORY_ADMIN_TOKEN válido.",
            headers={"WWW-Authenticate": "Bearer realm='Autonomuos Control Plane'"},
        )


class AdminSecurityGuardPrimitive:
    """
    Enforce cryptographic perimeter security for the administrative control plane.
    """

    def __init__(self, admin_token: str | None = None) -> None:
        self._token: str = admin_token or os.environ.get("FACTORY_ADMIN_TOKEN") or ""
        if not self._token:
            self._token = secrets.token_hex(24)
            logger.info(
                f"[AdminSecurityGuard] FACTORY_ADMIN_TOKEN no configurado en entorno. "
                f"Token efímero autogenerado para sesión local: {self._token}"
            )
        self._protected_api_prefixes: tuple[str, ...] = (
            "/api/evolution",
            "/api/build",
            "/api/git",
            "/api/orchestrator",
            "/api/database",
            "/api/planning",
            "/api/publishing",
            "/api/connectors",
            "/api/mcp",
        )

    @property
    def admin_token(self) -> str:
        """Return the administrator authentication token."""
        return self._token

    def set_admin_token(self, token: str) -> None:
        """Update the administrative token (useful for testing and key rotation)."""
        if not token or len(token) < 8:
            raise ValueError("El token de administración debe contener al menos 8 caracteres.")
        self._token = token

    def is_enforced(self) -> bool:
        """Determine whether authentication must be enforced. Default to True, unless ADMIN_AUTH_ENFORCED='0' or running under pytest without an explicit override."""
        enforced_env = os.environ.get("ADMIN_AUTH_ENFORCED")
        if enforced_env is not None:
            return enforced_env.lower() in ("1", "true", "yes")

        if "PYTEST_CURRENT_TEST" in os.environ:
            return False

        return True

    def is_protected_path(self, path: str) -> bool:
        """Determine whether a URL path requires administrative authentication."""
        if path == "/admin" or path.startswith("/admin/"):
            if path in ("/admin/login", "/admin/logout"):
                return False
            return True

        for prefix in self._protected_api_prefixes:
            if path == prefix or path.startswith(f"{prefix}/"):
                return True

        return False

    def validate_token(self, candidate_token: str | None) -> bool:
        """Compare the received token with the admin token in constant time (CWE-208)."""
        if not candidate_token or not self._token:
            return False
        return hmac.compare_digest(candidate_token.strip(), self._token.strip())

    def extract_token_from_request(self, request: Request) -> str | None:
        """Extrae el token desde cabecera Authorization (Bearer), X-Admin-Token, Cookie o Query param."""
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            if token:
                return token

        custom_header = request.headers.get("x-admin-token")
        if custom_header:
            return custom_header.strip()

        cookie_token = request.cookies.get(COOKIE_NAME)
        if cookie_token:
            return cookie_token.strip()

        param_token = request.query_params.get("auth_token")
        if param_token:
            return param_token.strip()

        return None

    def is_request_authenticated(self, request: Request) -> bool:
        """Check whether the incoming request is authorized."""
        token = self.extract_token_from_request(request)
        return self.validate_token(token)

    def attach_session_cookie(
        self,
        response: Response,
        token: str,
        max_age: int = DEFAULT_SESSION_MAX_AGE,
        secure: bool | None = None,
        request: Request | None = None,
    ) -> None:
        """Set a secure browser session cookie with HTTPS auto-detection."""
        if secure is None:
            if request is not None:
                is_https = (
                    request.url.scheme == "https"
                    or request.headers.get("x-forwarded-proto") == "https"
                )
                secure = is_https
            else:
                secure = os.environ.get("APP_ENV") == "production"

        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=max_age,
            path="/",
            httponly=True,
            samesite="lax",
            secure=secure,
        )

    def clear_session_cookie(self, response: Response) -> None:
        """Invalidate and clear the session cookie."""
        response.delete_cookie(key=COOKIE_NAME, path="/")

    def render_login_html(self, error_message: str | None = None) -> str:
        """Generate a dark-themed login interface for /admin."""
        error_banner = ""
        if error_message:
            error_banner = f"""
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #fca5a5; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; font-family: ui-monospace, monospace;">
              ⚠️ {html.escape(error_message)}
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Autonomuos — Control Plane Access</title>
  <style>
    :root {{
      --bg: #07090e;
      --card-bg: #0c1017;
      --border: rgba(255, 255, 255, 0.08);
      --border-focus: #3b82f6;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --primary-hover: #2563eb;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      -webkit-font-smoothing: antialiased;
    }}
    .login-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 36px;
      width: 100%;
      max-width: 420px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
    }}
    .badge {{
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      background: rgba(59, 130, 246, 0.15);
      color: #60a5fa;
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 4px 10px;
      border-radius: 9999px;
      margin-bottom: 16px;
    }}
    h1 {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.4px;
      margin-bottom: 8px;
    }}
    p.desc {{
      color: var(--text-muted);
      font-size: 13px;
      line-height: 1.5;
      margin-bottom: 24px;
    }}
    .form-group {{
      margin-bottom: 20px;
    }}
    label {{
      display: block;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 8px;
    }}
    input[type="password"] {{
      width: 100%;
      background: #05070a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
      color: var(--text);
      font-family: ui-monospace, monospace;
      font-size: 13px;
      outline: none;
      transition: border-color 0.15s ease;
    }}
    input[type="password"]:focus {{
      border-color: var(--border-focus);
    }}
    button.submit-btn {{
      width: 100%;
      background: var(--primary);
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 12px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease;
    }}
    button.submit-btn:hover {{
      background: var(--primary-hover);
    }}
    .footer-link {{
      margin-top: 24px;
      text-align: center;
      font-size: 12px;
    }}
    .footer-link a {{
      color: var(--text-muted);
      text-decoration: none;
      transition: color 0.15s ease;
    }}
    .footer-link a:hover {{
      color: var(--text);
    }}
  </style>
</head>
<body>
  <div class="login-card">
    <div class="badge">Soberanía de Infraestructura</div>
    <h1>Plano de Control Técnico</h1>
    <p class="desc">Introduzca la clave maestra <code>FACTORY_ADMIN_TOKEN</code> para desbloquear la consola de ingeniería de Autonomuos.</p>
    {error_banner}
    <form action="/admin/login" method="POST">
      <div class="form-group">
        <label for="admin_token">Clave de Administración</label>
        <input type="password" id="admin_token" name="admin_token" placeholder="••••••••••••••••••••••••••••" autofocus required />
      </div>
      <button type="submit" class="submit-btn">Desbloquear Consola</button>
    </form>
    <div class="footer-link">
      <a href="/">← Volver al Portal Comercial</a>
    </div>
  </div>
</body>
</html>"""


class AdminSecurityMiddleware(BaseHTTPMiddleware):
    """
    Intercept requests to protected routes via Starlette middleware.
    """

    def __init__(self, app: Any, guard: AdminSecurityGuardPrimitive | None = None) -> None:
        super().__init__(app)
        self.guard = guard or admin_security_guard

    def _try_query_token_exchange(self, request: Request) -> RedirectResponse | None:
        """Consolidate query parameter token into a session cookie and redirect to a clean URL (RFC 6750)."""
        auth_query_token = request.query_params.get("auth_token")
        if auth_query_token and self.guard.validate_token(auth_query_token):
            clean_url = str(request.url.remove_query_params("auth_token"))
            resp = RedirectResponse(url=clean_url, status_code=303)
            self.guard.attach_session_cookie(resp, auth_query_token)
            return resp
        return None

    def _build_unauthorized_response(self, request: Request, path: str) -> Response:
        """Generate the appropriate authentication challenge (HTML for browser or JSON 401 for API)."""
        accept = request.headers.get("accept", "")
        if (path == "/admin" or path.startswith("/admin/")) and ("text/html" in accept or "*/*" in accept):
            return HTMLResponse(self.guard.render_login_html(), status_code=401)

        return JSONResponse(
            status_code=401,
            content={
                "error": "Acceso administrativo restringido: se requiere FACTORY_ADMIN_TOKEN válido.",
                "code": "ADMIN_AUTH_REQUIRED",
                "docs": "Proporcione cabecera 'Authorization: Bearer <TOKEN>', 'X-Admin-Token' o cookie de sesión.",
            },
            headers={"WWW-Authenticate": "Bearer realm='Autonomuos Control Plane'"},
        )

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Dispatch the incoming request through the middleware pipeline."""
        path = request.url.path

        if not self.guard.is_enforced() or not self.guard.is_protected_path(path):
            return await call_next(request)

        redirect_resp = self._try_query_token_exchange(request)
        if redirect_resp is not None:
            return redirect_resp

        if self.guard.is_request_authenticated(request):
            return await call_next(request)

        return self._build_unauthorized_response(request, path)


admin_security_guard = AdminSecurityGuardPrimitive()
