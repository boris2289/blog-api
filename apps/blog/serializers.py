from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            'author',
            'title',
            'slug',
            'body',
            'category',
            'tags',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ["author", "title", "created_at"]
