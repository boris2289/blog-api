import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

import settings.conf
from apps.blog.models import Post

User = get_user_model()


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group_name = f"post_comments_{self.slug}"

        token = self.get_token_from_string()

        if not token:
            await self.close(code=4001)
            return

        user = self.get_user_from_string(token)
        if not user:
            await self.close(code=4001)
            return

        post_exists = await self.post_exists(self.slug)
        if not post_exists:
            await self.close(code=4004)
            return

        self.scope["user"] = user
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    def get_token_from_string(self):
        data = self.scope.get("query_string", b"").decode()
        query_params = parse_qs(data)
        token = query_params.get("token", [None])[0]

        return token

    @sync_to_async
    def get_user_from_string(self, token: str):
        jwt_auth = jwt.decode(token, settings.conf.SECRET_KEY)
        user_id = jwt_auth.get("user_id")

        if not user_id:
            return None
        return User.objects.filter(id=user_id).first()

    @sync_to_async
    def post_exists(self, slug: str) -> bool:
        return Post.objects.filter(slug=slug).exists()
