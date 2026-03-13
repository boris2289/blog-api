import asyncio
import json

import redis.asyncio as redis
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Subscribe to Redis channel 'comments' asynchronously and print incoming JSON messages."

    def handle(self, *args, **options):
        asyncio.run(self.listen())

    # Async is used here because the command waits indefinitely on network I/O from Redis.
    # If written synchronously, each blocking read would monopolize the process and compose
    # less naturally with other async I/O operations.
    async def listen(self):
        redis_url = settings.CACHES["default"]["LOCATION"]
        client = redis.from_url(redis_url, decode_responses=True)
        pubsub = client.pubsub()

        await pubsub.subscribe("comments")
        self.stdout.write(self.style.SUCCESS("Listening on Redis channel: comments"))

        try:
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue

                data = message.get("data")

                try:
                    obj = json.loads(data)
                    self.stdout.write(json.dumps(obj, ensure_ascii=False))
                except json.JSONDecodeError:
                    continue
        finally:
            await pubsub.unsubscribe("comments")
            await pubsub.aclose()
            await client.aclose()