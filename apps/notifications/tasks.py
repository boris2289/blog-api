import logging
from datetime import timedelta

from celery import shared_task
from asgiref.sync import async_to_sync
from django.utils import timezone
from channels.layers import get_channel_layer
from django.core.cache import cache

from apps.notifications.models import Notification
from apps.blog.models import Comment, Post
from apps.users.models import User
from apps.users.services import send_welcome_email

logger = logging.getLogger(__name__)

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

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def clear_expired_notifications():
    threshold = timezone.now() - timedelta(days=30)
    Notification.objects.filter(created_at__lt=threshold).delete()

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def generate_dialy_stats():
    now = timezone.now()
    since = now - timedelta(hours=24)

    posts_count = Post.objects.filter(created_at__gte=since).count()
    comments_count = Comment.objects.filter(created_at__gte=since).count()
    users_count = User.objects.filter(date_joined__gre=since).count()

    logger.info(
        "Dialy stats: posts = %s, comments = %s, users = %s",
        posts_count, comments_count, users_count
    )

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def send_welcome_email_task(user: User):
    # Добавляем ретраи так как отправка емейл может сломаться из за ошибки протоколов или соединения
    if not user:
        return
    send_welcome_email(user)

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def invalidate_post_cache():
    # Добавляем ретраи так как кэш может быть недоступен временно
    cache.delete("posts_list")


