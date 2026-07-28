"""JWT authentication that reads the access token from an HttpOnly cookie.

Falls back to the Authorization header (useful for API tooling/tests). When the
token comes from a cookie, CSRF is enforced for unsafe HTTP methods.
"""

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        raw_cookie = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)

        if header is not None:
            return super().authenticate(request)
        if not raw_cookie:
            return None

        validated = self.get_validated_token(raw_cookie)
        self._enforce_csrf(request)
        return self.get_user(validated), validated

    def _enforce_csrf(self, request):
        if request.method in SAFE_METHODS:
            return
        check = _CSRFCheck(lambda req: None)
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise PermissionDenied(f"CSRF Failed: {reason}")
