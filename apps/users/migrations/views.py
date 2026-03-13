import logging

from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    RegisterSerializer,
    UserLanguageSerializer,
    UserPreferencesSerializer,
    UserTimezoneSerializer,
)
from .services import send_welcome_email

logger = logging.getLogger("users")


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class ErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class RegisterSuccessSerializer(serializers.Serializer):
    message = serializers.CharField()
    user = UserPreferencesSerializer()
    refresh = serializers.CharField()
    access = serializers.CharField()


class TokenPairSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class TokenVerifyRequestSerializer(serializers.Serializer):
    token = serializers.CharField()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


@extend_schema_view(
    create=extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        description=(
                "Creates a new user account. Authentication is not required. "
                "This endpoint validates email uniqueness, password confirmation, language, and timezone. "
                "A welcome email is sent using the language selected at registration. "
                "Rate limiting is applied."
        ),
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(response=RegisterSuccessSerializer, description="User created successfully."),
            400: OpenApiResponse(response=RegisterSerializer, description="Validation error."),
            429: OpenApiResponse(response=ErrorDetailSerializer, description="Too many requests."),
        },
        examples=[
            OpenApiExample(
                "Register request",
                value={
                    "email": "hw2test1@kbtu.kz",
                    "first_name": "Boris",
                    "last_name": "Dubovoy",
                    "password": "testpass123",
                    "password_valid": "testpass123",
                    "preferred_language": "ru",
                    "timezone": "Asia/Almaty"
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register response",
                value={
                    "message": "Регистрация прошла успешно.",
                    "user": {
                        "email": "hw2test1@kbtu.kz",
                        "first_name": "Boris",
                        "last_name": "Dubovoy",
                        "preferred_language": "ru",
                        "timezone": "Asia/Almaty"
                    },
                    "refresh": "jwt-refresh-token",
                    "access": "jwt-access-token"
                },
                response_only=True,
            ),
        ],
    )
)
class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=False))
    def create(self, request):
        if getattr(request, "limited", False):
            return Response(
                {"detail": _("Too many requests. Try again later.")},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        logger.info("Registration attempt for email: %s", request.data.get("email"))

        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        send_welcome_email(user)

        logger.info("User registered successfully: %s", user.email)

        refresh = RefreshToken.for_user(user)

        with translation.override(user.preferred_language):
            response_message = _("Registration successful.")

        return Response(
            {
                "message": response_message,
                "user": {
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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        login_value = attrs.get(self.username_field)

        logger.info("Login attempt for %s: %s", self.username_field, login_value)

        try:
            data = super().validate(attrs)
            logger.info("Login success for user: %s", getattr(self.user, "email", None))
            return data
        except Exception:
            logger.warning("Login failed for %s: %s", self.username_field, login_value)
            raise


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        tags=["Auth"],
        summary="Obtain JWT tokens",
        description=(
                "Authenticates a user with email and password and returns JWT access and refresh tokens. "
                "Authentication is not required. "
                "Rate limiting may apply depending on project settings."
        ),
        request=TokenObtainPairSerializer,
        responses={
            200: OpenApiResponse(response=TokenPairSerializer, description="Tokens returned successfully."),
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Invalid credentials or bad request."),
            429: OpenApiResponse(response=ErrorDetailSerializer, description="Too many requests."),
        },
        examples=[
            OpenApiExample(
                "Login request",
                value={"email": "hw2test1@kbtu.kz", "password": "testpass123"},
                request_only=True,
            ),
            OpenApiExample(
                "Login response",
                value={"refresh": "jwt-refresh-token", "access": "jwt-access-token"},
                response_only=True,
            ),
        ],
    )
    @method_decorator(ratelimit(key="ip", rate="10/m", method="POST", block=False))
    def post(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            logger.warning("Rate limit hit: login from IP")
            return Response(
                {"detail": _("Too many requests. Try again later.")},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return super().post(request, *args, **kwargs)


class UserPreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Get current user preferences",
        description=(
                "Returns the authenticated user's profile preferences including preferred language and timezone. "
                "Authentication is required."
        ),
        responses={
            200: UserPreferencesSerializer,
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Authentication required."),
        },
        examples=[
            OpenApiExample(
                "Preferences response",
                value={
                    "email": "hw2test1@kbtu.kz",
                    "first_name": "Boris",
                    "last_name": "Dubovoy",
                    "preferred_language": "ru",
                    "timezone": "Asia/Almaty"
                },
                response_only=True,
            ),
        ],
    )
    def get(self, request):
        serializer = UserPreferencesSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLanguageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Update preferred language",
        description=(
                "Updates the authenticated user's preferred language. "
                "Authentication is required. "
                "The saved profile language has the highest priority in future requests."
        ),
        request=UserLanguageSerializer,
        responses={
            200: OpenApiResponse(response=MessageSerializer, description="Language updated successfully."),
            400: OpenApiResponse(response=UserLanguageSerializer, description="Validation error."),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Authentication required."),
        },
        examples=[
            OpenApiExample(
                "Language request",
                value={"preferred_language": "kk"},
                request_only=True,
            ),
            OpenApiExample(
                "Language response",
                value={"message": "Таңдаулы тіл сәтті жаңартылды.", "preferred_language": "kk"},
                response_only=True,
            ),
        ],
    )
    def patch(self, request):
        serializer = UserLanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.preferred_language = serializer.validated_data["preferred_language"]
        request.user.save(update_fields=["preferred_language"])

        with translation.override(request.user.preferred_language):
            message = _("Preferred language updated successfully.")

        return Response(
            {
                "message": message,
                "preferred_language": request.user.preferred_language,
            },
            status=status.HTTP_200_OK,
        )


class UserTimezoneView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Update timezone",
        description=(
                "Updates the authenticated user's timezone using a real IANA timezone identifier. "
                "Authentication is required."
        ),
        request=UserTimezoneSerializer,
        responses={
            200: OpenApiResponse(response=MessageSerializer, description="Timezone updated successfully."),
            400: OpenApiResponse(response=UserTimezoneSerializer, description="Validation error."),
            401: OpenApiResponse(response=ErrorDetailSerializer, description="Authentication required."),
        },
        examples=[
            OpenApiExample(
                "Timezone request",
                value={"timezone": "Asia/Almaty"},
                request_only=True,
            ),
            OpenApiExample(
                "Timezone response",
                value={"message": "Timezone updated successfully.", "timezone": "Asia/Almaty"},
                response_only=True,
            ),
        ],
    )
    def patch(self, request):
        serializer = UserTimezoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.timezone = serializer.validated_data["timezone"]
        request.user.save(update_fields=["timezone"])

        return Response(
            {
                "message": _("Timezone updated successfully."),
                "timezone": request.user.timezone,
            },
            status=status.HTTP_200_OK,
        )
