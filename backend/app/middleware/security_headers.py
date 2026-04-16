"""
Security Headers Middleware

Adds security headers to all responses to protect against:
- XSS attacks
- Clickjacking
- MIME sniffing
- Information disclosure
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses

    Headers added:
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Force HTTPS
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """

    def __init__(
        self,
        app,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        enable_csp: bool = True,
    ):
        super().__init__(app)
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.enable_csp = enable_csp

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Add security headers to response

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # MIME sniffing protection
        # Prevents browsers from MIME-sniffing responses
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking Protection
        # Prevents page from being displayed in iframe
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        # Enables XSS filter in older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HTTPS enforcement (HSTS)
        # Forces HTTPS for specified duration
        if self.enable_hsts and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains; preload"
            )

        # Content Security Policy
        # Restricts resource loading to prevent XSS
        if self.enable_csp:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow inline scripts (adjust for production)
                "style-src 'self' 'unsafe-inline'",  # Allow inline styles
                "img-src 'self' data: https:",  # Allow images from self and data URIs
                "font-src 'self' data:",
                "connect-src 'self'",  # API calls to same origin
                "frame-ancestors 'none'",  # No framing allowed
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Referrer Policy
        # Controls referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        # Disables unnecessary browser features
        permissions = [
            "geolocation=()",  # Disable geolocation
            "microphone=()",   # Disable microphone
            "camera=()",       # Disable camera
            "payment=()",      # Disable payment API
            "usb=()",          # Disable USB
            "magnetometer=()", # Disable magnetometer
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # Remove Information Disclosure Headers
        # Remove headers that reveal server information
        headers_to_remove = ["Server", "X-Powered-By"]
        for header in headers_to_remove:
            if header in response.headers:
                del response.headers[header]

        return response


# Configuration examples

"""
DEVELOPMENT CSP (More Permissive):
```python
csp_directives = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow inline for dev
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "connect-src 'self' ws: wss:",  # Allow WebSocket for hot reload
]
```

PRODUCTION CSP (Strict):
```python
csp_directives = [
    "default-src 'self'",
    "script-src 'self'",  # No unsafe-inline/eval
    "style-src 'self'",   # No unsafe-inline
    "img-src 'self' https://cdn.amstar.com",  # Specific CDN only
    "connect-src 'self' https://api.amstar.com",  # Specific API only
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests",  # Force HTTPS
]
```

USAGE IN main.py:
```python
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(
    SecurityHeadersMiddleware,
    enable_hsts=settings.is_production,  # Only in production
    enable_csp=True,
)
```
"""
