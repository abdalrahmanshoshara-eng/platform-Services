from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from reports.audit import actions
from reports.audit.service import record

from .authentication import CookieJWTAuthentication
from .cookies import clear_auth_cookies, set_auth_cookies
from .serializers import LoginSerializer, RegisterSerializer, UserSummarySerializer
from .throttling import LoginRateThrottle, RefreshRateThrottle


def _issue(response, user):
    refresh = RefreshToken.for_user(user)
    set_auth_cookies(response, str(refresh.access_token), str(refresh))
    return response


@method_decorator(ensure_csrf_cookie, name="post")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            record(
                actions.LOGIN_FAILURE,
                request=request,
                outcome="failure",
                metadata={"username": str(request.data.get("username", ""))[:150]},
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.validated_data["user"]
        response = Response({"user": UserSummarySerializer(user).data})
        _issue(response, user)
        record(actions.LOGIN_SUCCESS, actor=user, request=request, target=user)
        return response


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response = Response({"user": UserSummarySerializer(user).data}, status=status.HTTP_201_CREATED)
        _issue(response, user)
        record("auth.register", actor=user, request=request, target=user)
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RefreshRateThrottle]

    def post(self, request):
        from rest_framework_simplejwt.exceptions import InvalidToken
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer

        raw = request.COOKIES.get("refresh_token")
        if not raw:
            return Response({"detail": "لا يوجد رمز تحديث."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = TokenRefreshSerializer(data={"refresh": raw})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken):
            resp = Response({"detail": "رمز التحديث غير صالح."}, status=status.HTTP_401_UNAUTHORIZED)
            clear_auth_cookies(resp)
            return resp

        data = serializer.validated_data  # rotated per SIMPLE_JWT settings
        response = Response({"detail": "تم تحديث الجلسة."})
        set_auth_cookies(response, data["access"], data.get("refresh", raw))
        record(actions.TOKEN_REFRESH, request=request)
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        raw = request.COOKIES.get("refresh_token") or request.data.get("refresh")
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except TokenError:
                pass
        response = Response({"detail": "تم تسجيل الخروج بنجاح."})
        clear_auth_cookies(response)
        record(actions.LOGOUT, actor=request.user, request=request)
        return response


@method_decorator(ensure_csrf_cookie, name="get")
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSummarySerializer(request.user).data)
