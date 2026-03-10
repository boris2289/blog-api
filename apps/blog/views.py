from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .models import Post
from .permissions import IsOwnerorReadOnly
from .serializers import PostSerializer

import logging

logger = logging.getLogger("blog")
POSTS_LIST_CACHE_TTL = 60


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