import logging

from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import translation
from rest_framework import permissions
from rest_framework.views import APIView
from .serializers import (
    RegisterSerializer,
    UserLanguageSerializer,
    UserPreferencesSerializer,
    UserTimezoneSerializer,
)
from .services import send_welcome_email

logger = logging.getLogger("users")


class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def create(self, request):
        logger.info("Registration attempt for email: %s", request.data.get("email"))

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        send_welcome_email(user)

        logger.info("User registered successfully: %s", user.email)

        refresh = RefreshToken.for_user(user)

        with translation.override(user.preferred_language):
            response_message = _("Registration sucessfull.")

        return Response(
            {
                "message": response_message,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "preferred_language": user.preferred_language,
                    "timezone": user.timezone,
                },
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class UserPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self, request):
        serializer = UserPreferencesSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLanguageView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserLanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.preferred_language = serializer.validated_data["preffered_language"]
        request.user.save(update_fields=["preferred_language"])

        with translation.override(request.user.preferred_language):
            message = _("Preferred language updated.")

        return Response(
            {
                "message": message,
                "preferred_language": request.user.preferred_language,
            },
            status=status.HTTP_200_OK
        )
class UserTimezoneView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        serializer = UserTimezoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.timezone = serializer.validated_data["timezone"]
        request.user.save(update_fields=["timezone"])

        with translation.override(request.user.timezone):
            message = _("Preferred language updated.")

        return Response(
            {
                "message": message,
                "timezone": request.user.timezone,
            },
            status=status.HTTP_200_OK
        )



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username = attrs.get("username")

        logger.info("Login attempt for username: %s", username)

        try:
            data = super().validate(attrs)
            logger.info("Login success for user: %s", getattr(self.user, "username", None))
            return data
        except Exception:
            logger.warning("Login failed for username: %s", username)
            raise


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        if getattr(request, 'limited', False):
            logger.warning('Rate limit hit: login from IP')
            return Response({"detail": 'Too many requests. Try again later'}, status=429)

        return super().post(request, *args, **kwargs)
