from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source="comment.id")
    comment_content = serializers.CharField(source="comment.body")
    comment_author_id = serializers.IntegerField(source="comment.author.id")
    comment_author_email = serializers.CharField(source="comment.author.email")
    post_slug = serializers.CharField(source="comment.post.slug")
    post_title = serializers.CharField(source="comment.post.title")

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "comment",
            "comment_id",
            "comment_content",
            "comment_author_id",
            "comment_author_email",
            "post_id",
            "post_title",
            "is_read",
            "created_at"
        ]
        read_only_fields = fields
