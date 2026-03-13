from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView


class ErrorDetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TokenVerifyRequestSerializer(serializers.Serializer):
    token = serializers.CharField()


class TokenVerifyResponseSerializer(serializers.Serializer):
    pass


class DocumentedTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=["Auth"],
        summary="Refresh JWT access token",
        description="Accepts a refresh token and returns a new access token.",
        request=TokenRefreshRequestSerializer,
        responses={
            200: OpenApiResponse(response=TokenPairSerializer, description="New access token returned."),
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Invalid token or bad request."),
        },
        examples=[
            OpenApiExample(
                "Refresh request",
                value={"refresh": "jwt-refresh-token"},
                request_only=True,
            ),
            OpenApiExample(
                "Refresh response",
                value={"access": "new-jwt-access-token"},
                response_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DocumentedTokenVerifyView(TokenVerifyView):
    @extend_schema(
        tags=["Auth"],
        summary="Verify JWT token",
        description="Checks whether a JWT token is valid.",
        request=TokenVerifyRequestSerializer,
        responses={
            200: OpenApiResponse(description="Token is valid."),
            400: OpenApiResponse(response=ErrorDetailSerializer, description="Invalid token."),
        },
        examples=[
            OpenApiExample(
                "Verify request",
                value={"token": "jwt-access-token"},
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)