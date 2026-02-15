import json

from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Post
from .serializers import PostSerializer
from .permissions import IsOwnerorReadOnly
import logging
from django.core.cache import cache
from rest_framework.response import Response
from django_ratelimit.decorators import ratelimit
from django_redis import get_redis_connection

logger = logging.getLogger("blog")

POSTS_LIST_CACHE_KEY = 'posts:list:published:v1'
POSTS_LIST_CACHE_TTL = 60


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerorReadOnly()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Post.objects.filter(status=Post.Choices.PUBLISHED)
        return Post.objects.all()

    def list(self, request, *args, **kwargs):
        # Manual cache легко проверить
        cached = cache.get(POSTS_LIST_CACHE_KEY)
        if cached is not None:
            logger.debug("Posts retrieved from cache")
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache.set(POSTS_LIST_CACHE_KEY, response.data, POSTS_LIST_CACHE_TTL)
        logger.debug("Posts list cached for %s", POSTS_LIST_CACHE_TTL)
        return response

    @ratelimit(key='user', rate='20/m', method='POST', block=False)
    def create(self, request, *args, **kwargs):
        if getattr(request, 'limited', False):
            logger.warning('Rate limit hit: post create by %s', request.user.email)
            return Response({"detail": 'Too many requests. Try again later'}, status=429)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        logger.info("Post created: %s by %s", post.slug, self.request.user.email)

    def perform_update(self, serializer):
        post = serializer.save()
        logger.info("Post updated: %s", post.slug)

    def perform_destroy(self, instance):
        logger.warning("Post deleted: %s by %s", instance.slug, self.request.user.email)
        instance.delete()


def publish_comments_event(comment):
    conn = get_redis_connection('defaul')
    payload = {
        'event': 'comment_created',
        'author': comment.author.email,
        'created_at': comment.created_at
    }
    conn.publish('comments', json.dumps(payload))
