"""
=============================================================================
StudyAI — Hardened CORS & Security Middleware
=============================================================================
This middleware handles Cross-Origin Resource Sharing (CORS) and enforces
strict HTTP baseline security headers across all responses.

Key Defenses:
1. Exact Origin Allowlist Matching: Never reflects arbitrary untrusted origins.
2. Safe Credentials: Only pairs credentials with verified allowlisted origins.
3. Preflight Handling: Handles OPTIONS preflight securely with caching.
4. Exception Masking: Masks internal tracebacks and schema details in non-debug mode.
5. Baseline Security Headers: Injects nosniff, DENY frame options, and Referrer-Policy.
=============================================================================
"""

import re
import logging
from django.http import HttpResponse, JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class CorsMiddleware:
    """
    Middleware that enforces CORS controls and security headers on HTTP responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def _apply_security_headers(self, request, response):
        origin = request.headers.get("Origin", "").strip()
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        allow_all = getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)
        is_debug = getattr(settings, 'DEBUG', False)
        is_local_dev = is_debug and bool(re.match(r'^https?://(localhost|127\.0\.0\.1)(:\d+)?$', origin))

        # CORS validation: strictly allow only configured origins or local dev origins in debug mode
        if origin and (origin in allowed_origins or is_local_dev):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            req_headers = request.headers.get("Access-Control-Request-Headers")
            response["Access-Control-Allow-Headers"] = (
                req_headers if req_headers else "Content-Type, Authorization, Accept, X-Requested-With, X-CSRFToken"
            )
            response["Access-Control-Max-Age"] = "86400"
            # Prevent cache poisoning on origin variations
            existing_vary = response.get("Vary", "")
            response["Vary"] = f"{existing_vary}, Origin".strip(", ")
        elif allow_all and not getattr(settings, 'CORS_ALLOW_CREDENTIALS', False):
            # Safe wildcard only when credentials are explicitly disabled
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response["Access-Control-Allow-Headers"] = "*"

        # Baseline HTTP Security Headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
            return self._apply_security_headers(request, response)

        response = self.get_response(request)
        return self._apply_security_headers(request, response)

    def process_exception(self, request, exception):
        logger.exception("Unhandled server exception processing %s %s: %s", request.method, request.path, str(exception))

        is_debug = getattr(settings, 'DEBUG', False)
        error_msg = str(exception) if is_debug else "An unexpected internal server error occurred."
        resp = JsonResponse({
            "error": error_msg,
            "code": "INTERNAL_SERVER_ERROR"
        }, status=500)
        return self._apply_security_headers(request, resp)
