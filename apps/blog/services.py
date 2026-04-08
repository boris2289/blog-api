import logging
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from django_redis import get_redis_connection
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view
)
from rest_framework import permissions, viewsets, serializers
from rest_framework.response import Response

from .models import Post
from .permissions import IsOwnerorReadOnly
from .serializers import PostSerializer
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blog.models import Post
from apps.blog.serializers import CommentCreateSerializer
from apps.blog.sse import build_post, STREAM_GROUP


def publish_post_sse_event(post):
    channel_layer = get_channel_layer()
    payload = build_post(post)

    async_to_sync(channel_layer.group_send)(
        STREAM_GROUP,
        {
            "type": "post.published",
            "data": payload,
        },
    )
