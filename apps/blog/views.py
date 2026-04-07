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

logger = logging.getLogger("blog")
POSTS_LIST_CACHE_TTL = 60


class RateLimitErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class UnauthorizedErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class ForbiddenErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


class NotFoundErrorSerializer(serializers.Serializer):
    detail = serializers.CharField()


def build_posts_list_cache_key(request):
    language = getattr(request, "LANGUAGE_CODE", "en")
    page = request.query_params.get("page", "1")
    return f"posts:list:published:{language}:page:{page}"


def invalidate_posts_list_cache():
    if hasattr(cache, "delete_pattern"):
        cache.delete_pattern("posts:list:published:*")
    else:
        for language in ("en", "ru", "kk"):
            for page in range(1, 21):
                cache.delete(f"posts:list:published:{language}:page:{page}")


@extend_schema_view(
    list=extend_schema(
        tags=["Posts"],
        summary="List published posts",
        description=(
                "Returns a paginated list of posts. "
                "Authentication is not required"
                "The response in cached in Redis per active language and page. "
                "Examples: English and Russian users receive separate cache entries. "
                "Dates and category translations depend on the active language/timezone logic already configured"
        ),
        parameters=[
            OpenApiParameter(
                name="lang",
                description="Optional language override",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name="page",
                description="Pagination page number. ",
                required=False,
                type=int,
                location=OpenApiParameter.QUERY
            )
        ],
        responses={
            200: OpenApiResponse(
                response=PostSerializer(many=True),
                description="Published posts list returned succesfully."
            ),
        },
        examples=[
            OpenApiExample(
                "List posts request",
                value=None,
                request_only=True,
            ),
            OpenApiExample(
                "List posts response",
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "author": 1,
                            "title": "My first post",
                            "slug": "my-first_post",
                            "body": "Hello from hw1 post",
                            "category": {
                                "id": 1,
                                "slug": "news",
                                "name": "Новости"
                            },
                            "tags": [],
                            "status": "published",
                            "created_at": "7 march 2026 15:00",
                            "updated_at": "7 march 2026 15:10",
                        }
                    ]
                },
                response_only=True
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=["Posts"],
        summary="Retrieve published post by slug",
        description=(
                "Returns one published post by slug. "
                "Authentication is not required"
                "Language-sensitive fields such as localized category name and formatted dates depend on active lang/timezone. "
        ),
        parameters=[
            OpenApiParameter(
                name="lang",
                description="Optional language override",
                required=False,
                type=str,
                location=OpenApiParameter.QUERY
            ),
        ],
        responses={
            200: PostSerializer,
            404: OpenApiResponse(response=NotFoundErrorSerializer, description="Post not found. ")
        },
        examples=[
            OpenApiExample(
                "Retrieve post response",
                value={
                    "author": 1,
                    "title": "My first post",
                    "slug": "my-first_post",
                    "body": "Hello from hw1 post",
                    "category": {
                        "id": 1,
                        "slug": "news",
                        "name": "Новости"
                    },
                    "tags": [],
                    "status": "published",
                    "created_at": "7 march 2026 15:00",
                    "updated_at": "7 march 2026 15:10",
                },
                request_only=True,
            ),
        ],
    ),
    create=extend_schema(
        tags=["Posts"],
        summary="Create a post",
        description=(
                "Creates a new post. Authentication is required. "
                "The authenticated user becomes the author automatically. "
                "This endpoint invalidates the Redis posts list cache for all languages after a successful write. "
                "Rate limiting is applied."
        ),
        request=PostSerializer,
        responses={
            201: PostSerializer,
            400: OpenApiResponse(response=PostSerializer, description="Validation error."),
            401: OpenApiResponse(response=UnauthorizedErrorSerializer, description="Authentication required."),
            403: OpenApiResponse(response=ForbiddenErrorSerializer, description="Permission denied."),
            429: OpenApiResponse(response=RateLimitErrorSerializer, description="Too many requests."),
        },
        examples=[
            OpenApiExample(
                "Create post request",
                value={
                    "title": "My first post",
                    "slug": "my-first-post",
                    "body": "Hello from hw2 post.",
                    "category_id": 1,
                    "tags": [],
                    "status": "published"
                },
                request_only=True,
            ),
            OpenApiExample(
                "Create post response",
                value={
                    "author": 1,
                    "title": "My first post",
                    "slug": "my-first-post",
                    "body": "Hello from hw2 post.",
                    "category": {
                        "id": 1,
                        "slug": "news",
                        "name": "News"
                    },
                    "tags": [],
                    "status": "published",
                    "created_at": "March 7, 2026, 15:00",
                    "updated_at": "March 7, 2026, 15:00"
                },
                response_only=True,
            ),
        ],
    ),
    partial_update=extend_schema(
        tags=["Posts"],
        summary="Partially update a post",
        description=(
                "Updates selected fields of a post by slug. Authentication is required. "
                "Only the owner may modify the post. "
                "Any successful write invalidates the Redis posts list cache for all languages."
        ),
        request=PostSerializer,
        responses={
            200: PostSerializer,
            400: OpenApiResponse(response=PostSerializer, description="Validation error."),
            401: OpenApiResponse(response=UnauthorizedErrorSerializer, description="Authentication required."),
            403: OpenApiResponse(response=ForbiddenErrorSerializer, description="Permission denied."),
            404: OpenApiResponse(response=NotFoundErrorSerializer, description="Post not found."),
        },
        examples=[
            OpenApiExample(
                "Patch post request",
                value={"title": "My first post updated"},
                request_only=True,
            ),
            OpenApiExample(
                "Patch post response",
                value={
                    "author": 1,
                    "title": "My first post updated",
                    "slug": "my-first-post",
                    "body": "Hello from hw2 post.",
                    "category": {
                        "id": 1,
                        "slug": "news",
                        "name": "News"
                    },
                    "tags": [],
                    "status": "published",
                    "created_at": "March 7, 2026, 15:00",
                    "updated_at": "March 7, 2026, 15:10"
                },
                response_only=True,
            ),
        ],
    ),
    update=extend_schema(
        tags=["Posts"],
        summary="Fully update a post",
        description=(
                "Replaces a post by slug. Authentication is required. "
                "Only the owner may modify the post. "
                "Any successful write invalidates the Redis posts list cache for all languages."
        ),
        request=PostSerializer,
        responses={
            200: PostSerializer,
            400: OpenApiResponse(response=PostSerializer, description="Validation error."),
            401: OpenApiResponse(response=UnauthorizedErrorSerializer, description="Authentication required."),
            403: OpenApiResponse(response=ForbiddenErrorSerializer, description="Permission denied."),
            404: OpenApiResponse(response=NotFoundErrorSerializer, description="Post not found."),
        },
    ),
    destroy=extend_schema(
        tags=["Posts"],
        summary="Delete a post",
        description=(
                "Deletes a post by slug. Authentication is required. "
                "Only the owner may delete the post. "
                "Successful deletion invalidates the Redis posts list cache for all languages."
        ),
        responses={
            204: OpenApiResponse(description="Post deleted successfully."),
            401: OpenApiResponse(response=UnauthorizedErrorSerializer, description="Authentication required."),
            403: OpenApiResponse(response=ForbiddenErrorSerializer, description="Permission denied."),
            404: OpenApiResponse(response=NotFoundErrorSerializer, description="Post not found."),
        },
        examples=[
            OpenApiExample(
                "Delete response",
                value=None,
                response_only=True,
            ),
        ],
    )
)
class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Post.objects.select_related("author", "category").prefetch_related("tags")
        if self.action in ["list", "retrieve"]:
            return queryset.filter(status=Post.Choices.PUBLISHED)
        return queryset

    def get_permissions(self):
        if self.action in ["create", "partial_update", "update", "destroy"]:
            return [permissions.IsAuthenticated(), IsOwnerorReadOnly()]
        return [permissions.AllowAny()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def list(self, request, *args, **kwargs):
        cache_key = build_posts_list_cache_key(request)
        cached = cache.get(cache_key)

        if cached is not None:
            logger.debug("Posts retrieved from cache: %s", cache_key)
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, POSTS_LIST_CACHE_TTL)
        logger.debug("Posts list cached: %s", cache_key)
        return response

    @method_decorator(ratelimit(key="user", rate="20/m", method="POST", block=False))
    def create(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            logger.warning("Rate limit hit: post create by %s", request.user.email)
            return Response({"detail": _("Too many requests. Try again later.")}, status=429)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        invalidate_posts_list_cache()
        logger.info("Post created: %s by %s", post.slug, self.request.user.email)

    def perform_update(self, serializer):
        post = serializer.save()
        invalidate_posts_list_cache()
        logger.info("Post updated: %s", post.slug)

    def perform_destroy(self, instance):
        logger.warning("Post deleted: %s by %s", instance.slug, self.request.user.email)
        instance.delete()
        invalidate_posts_list_cache()


def publish_comments_event(comment):
    channel_layer = get_channel_layer()

    payload = {
        "comment_id": comment.id,
        "author": {
            "id": comment.author.id,
            "email": comment.author.email,
        },
        "body": comment.body,
        "created_at": comment.created_at.isoformat(),
    }

    async_to_sync(channel_layer.group_send)(
        f"post_comments_{comment.post.slug}",
        {
            "type": "comment_created",
            "data": payload,
        },
    )


@extend_schema(
    tags=["Comments"],
    summary="Create comment for a post",
    description="Creates a comment for a published post and broadcasts it to WebSocket subscribers.",
    request=CommentCreateSerializer,
    responses={201: CommentCreateSerializer},
)
class PostCommentCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug, status=Post.Choices.PUBLISHED)

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.save(
            post=post,
            author=request.user,
        )

        publish_comments_event(comment)

        return Response(
            {
                "id": comment.id,
                "author": {
                    "id": comment.author.id,
                    "email": comment.author.email,
                },
                "body": comment.body,
                "created_at": comment.created_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )
