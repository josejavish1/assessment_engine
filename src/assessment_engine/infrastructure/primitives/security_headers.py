from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from dataclasses import dataclass

@dataclass
class SecurityHeadersConfig:
    enable_hsts: bool = True
    hsts_max_age: int = 31536000
    enable_csp: bool = True
    allowed_script_sources: tuple[str, ...] = ("'self'", "'unsafe-inline'", "https://js.stripe.com")
    allowed_style_sources: tuple[str, ...] = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
    allowed_font_sources: tuple[str, ...] = ("'self'", "https://fonts.gstatic.com", "data:")
    frame_options: str = "SAMEORIGIN"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, config: SecurityHeadersConfig | None = None):
        super().__init__(app)
        self.config = config or SecurityHeadersConfig()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch the incoming request to the next handler in the middleware chain."""
        response = await call_next(request)
        h = response.headers

        if self.config.enable_hsts:
            h["Strict-Transport-Security"] = f"max-age={self.config.hsts_max_age}; includeSubDomains"

        if self.config.enable_csp:
            scripts = " ".join(self.config.allowed_script_sources)
            styles = " ".join(self.config.allowed_style_sources)
            fonts = " ".join(self.config.allowed_font_sources)
            h["Content-Security-Policy"] = (
                f"default-src 'self'; script-src {scripts}; style-src {styles}; font-src {fonts}; "
                f"img-src 'self' data: https: blob:; connect-src 'self' https: wss:; frame-ancestors 'self';"
            )

        h["X-Frame-Options"] = self.config.frame_options
        h["X-Content-Type-Options"] = "nosniff"
        h["Referrer-Policy"] = "strict-origin-when-cross-origin"
        h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
