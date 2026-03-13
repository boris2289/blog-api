import asyncio

import httpx
from asgiref.sync import async_to_sync
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.users.models import User
from .models import Comment, Post


class BlogCountsSerializer(serializers.Serializer):
    total_posts = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    total_users = serializers.IntegerField()


class ExchangeRatesSerializer(serializers.Serializer):
    KZT = serializers.FloatField()
    RUB = serializers.FloatField()
    EUR = serializers.FloatField()


class StatsResponseSerializer(serializers.Serializer):
    blog = BlogCountsSerializer()
    exchange_rates = ExchangeRatesSerializer()
    current_time = serializers.CharField()


class StatsErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


async def fetch_exchange_rates(client: httpx.AsyncClient) -> dict:
    response = await client.get("https://open.er-api.com/v6/latest/USD")
    response.raise_for_status()

    data = response.json()
    rates = data["rates"]

    return {
        "KZT": rates["KZT"],
        "RUB": rates["RUB"],
        "EUR": rates["EUR"],
    }


async def fetch_current_time(client: httpx.AsyncClient) -> str:
    response = await client.get(
        "https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty"
    )
    response.raise_for_status()

    data = response.json()
    return data["dateTime"]


async def fetch_blog_counts() -> dict:
    total_posts = await Post.objects.acount()
    total_comments = await Comment.objects.acount()
    total_users = await User.objects.acount()

    return {
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_users": total_users,
    }


# Async is used here because we wait for multiple independent I/O operations.
# If this were synchronous, the external requests would run one after another
# and total response time would be closer to the sum of both waits.
async def build_stats_payload() -> dict:
    timeout = httpx.Timeout(10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        exchange_rates, current_time, blog_counts = await asyncio.gather(
            fetch_exchange_rates(client),
            fetch_current_time(client),
            fetch_blog_counts(),
        )

    return {
        "blog": blog_counts,
        "exchange_rates": exchange_rates,
        "current_time": current_time,
    }


@extend_schema(
    tags=["Stats"],
    summary="Get blog statistics with external data",
    description=(
        "Returns local blog counts together with exchange rates and current time in Almaty. "
        "Authentication is not required. "
        "The external HTTP calls are executed concurrently via asyncio.gather and httpx.AsyncClient."
    ),
    responses={
        200: OpenApiResponse(
            response=StatsResponseSerializer,
            description="Combined blog statistics and external public API data.",
        ),
        503: OpenApiResponse(
            response=StatsErrorSerializer,
            description="External API request failed.",
        ),
    },
    examples=[
        OpenApiExample(
            "Stats response",
            value={
                "blog": {
                    "total_posts": 42,
                    "total_comments": 137,
                    "total_users": 15,
                },
                "exchange_rates": {
                    "KZT": 450.23,
                    "RUB": 89.10,
                    "EUR": 0.92,
                },
                "current_time": "2024-03-15T18:30:00+05:00",
            },
            response_only=True,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def stats_view(request):
    try:
        payload = async_to_sync(build_stats_payload)()
        return Response(payload, status=status.HTTP_200_OK)
    except (httpx.HTTPError, KeyError, ValueError):
        return Response(
            {"detail": "Failed to fetch external data."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )