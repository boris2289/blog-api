from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.blog.models import Comment


def broadcast_comment(comment: Comment):
    channel_layer = get_channel_layer()
    group_name = f"post_comments_{comment.post.slug}"

    data = {
        "post_id": comment.post.slug,
        "title": comment.body,
        "author_id": comment.author.id,
        "author_email": comment.author.email,
        "published_at": comment.created_at.isoformat()
    }

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "comment_created",
            "data": data,
        }
    )
