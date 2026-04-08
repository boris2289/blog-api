import asyncio
import json

from channels.layers import get_channel_layer
from django.http import StreamingHttpResponse

STREAM_GROUP = "posts_stream"


def build_post(post):
    return {
        "post_id": post.id,
        "title": post.title,
        "slug": post.slug,
        "author": {
            "id": post.author.id,
            "email": post.author.email
        },
        "published_at": post.created_at
    }


async def post_event_generator():
    channel_layer = get_channel_layer()
    channel_name = await channel_layer.new_channel()
    await channel_layer.group_add(STREAM_GROUP, channel_name)

    try:
        yield ": connected \n\n"
        while True:
            message = await channel_layer.receive(channel_name)
            payload = json.dumps(message["data"])
            yield f"data {payload} \n\n"
    except asyncio.CancelledError:
        raise
    finally:
        await channel_layer.group_discard(STREAM_GROUP, channel_name)


async def sse_posts_stream_view(request):
    response = StreamingHttpResponse(
        post_event_generator(),
        content_type="text/event-stream"
    )
    return response
