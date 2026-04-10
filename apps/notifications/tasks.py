from celery import shared_task
from asgiref.sync import async_to_sync
from django.utils import timezone
from channels.layers import get_channel_layer

from apps.notifications.models import Notification
from apps.blog.models import Comment, Post


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def process_new_comment(comment_id: int):
    comment = Comment.objects.select_related("post__author", "author").get(id=comment_id)

    post_author = comment.post.author
    comment_author = comment.author

    # себе не слать
    if post_author_id := getattr(post_author, "id", None):
        if post_author_id == getattr(comment_author, "id", None):
            return

    Notification.objects.create(
        recipient=post_author,
        comment=comment,
    )


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def publish_scheduled_posts():
    now = timezone.now()

    channel_layer = get_channel_layer()
    posts = Post.objects.filter(
        status=Post.Choices.SCHEDULED,
        publish_at__lte=now

    )
    for post in posts:
        post.status = Post.Choices.SCHEDULED
        post.publish_at = now
        post.save()

        async_to_sync(channel_layer.group_send)(
            "posts_published",
            {
                "type": "post.published",
                "data": {
                    "post_id": post.id,
                    "title": post.title,
                    "slug": post.slug,
                    "author": {
                        "id": post.author.id,
                        "email": post.author.email
                    },
                    "published_at": post.publish_at.isoformat()
                },
            }
        )

