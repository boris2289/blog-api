from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .serializers import RegisterSerializer
import logging
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger("users")


class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="5/m", method="POST", block=True))
    def create(self, request):
        logger.info("Registration attempt for email: %s", request.data.get("email"))

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        logger.info("User registered successfully: %s", user.email)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
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
