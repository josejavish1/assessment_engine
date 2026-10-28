from fastapi import Response


class CookieHardener:
    COOKIE_NAME = "__Host-session_id"

    @classmethod
    def set_secure_session_cookie(cls, response: Response, session_token: str, max_age_seconds: int = 604800) -> None:
        """Inject the session cookie adhering to RFC 6265bis:
1. `__Host-` prefix (restricted to exact host, blocks subdomains).
2. `httponly=True` (prevents XSS theft).
3. `samesite="lax"` (prevents CSRF attacks).
4. `secure=True` (enforces HTTPS).
5. `path="/"` (required by the `__Host-` specification)."""
        response.set_cookie(
            key=cls.COOKIE_NAME,
            value=session_token,
            max_age=max_age_seconds,
            httponly=True,
            samesite="lax",
            secure=True,
            path="/"
        )
