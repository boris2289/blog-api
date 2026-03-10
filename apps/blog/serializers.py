from rest_framework import serializers

from .models import Category, Post
from .utils import format_localized_datetime


class CategoryLocalizedSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "slug", "name"]

    def get_name(self, obj):
        request = self.context.get("request")
        language_code = getattr(request, "LANGUAGE_CODE", "en")
        return obj.get_localized_name(language_code)


class PostSerializer(serializers.ModelSerializer):
    category = CategoryLocalizedSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=Category.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "author",
            "title",
            "slug",
            "body",
            "category",
            "category_id",
            "tags",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["author", "created_at", "updated_at"]

    def get_created_at(self, obj):
        request = self.context.get("request")
        return format_localized_datetime(obj.created_at, request)

    def get_updated_at(self, obj):
        request = self.context.get("request")
        return format_localized_datetime(obj.updated_at, request)