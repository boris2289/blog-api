from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.blog.models import Comment
from apps.notifications.models import Notification


@receiver(post_save, sender=Comment)
def create_notification_on_comment(sender, instance, created, **kwargs):
    post_author = instance.post.author
    comment_author = instance.author

    # сам себе не предупреждать
    if post_author_id := getattr(post_author, "id", None):
        if post_author_id == getattr(comment_author, "id", None):
            return

    Notification.objects.create(
        recipient=post_author,
        comment=instance
    )
