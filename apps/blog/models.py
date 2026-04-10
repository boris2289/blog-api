from django.db import models
from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    SlugField,
    TextChoices,
    TextField,
)
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


class Category(models.Model):
    name = CharField(max_length=100, unique=True, verbose_name=_("Name"))
    name_en = CharField(max_length=100, blank=True, default="", verbose_name=_("Name (English)"))
    name_ru = CharField(max_length=100, blank=True, default="", verbose_name=_("Name (Russian)"))
    name_kk = CharField(max_length=100, blank=True, default="", verbose_name=_("Name (Kazakh)"))
    slug = SlugField(unique=True, verbose_name=_("Slug"))

    def get_localized_name(self, language_code):
        language_code = (language_code or "en").split("-")[0].lower()

        if language_code == "ru" and self.name_ru:
            return self.name_ru
        if language_code == "kk" and self.name_kk:
            return self.name_kk
        if self.name_en:
            return self.name_en
        return self.name

    def __str__(self):
        return self.name_en or self.name

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


class Tag(models.Model):
    name = CharField(max_length=50, unique=True, verbose_name=_("Name"))
    slug = SlugField(unique=True, verbose_name=_("Slug"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class Post(models.Model):
    class Choices(TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")
        SCHEDULED = "scheduled"

    author = ForeignKey(User, on_delete=CASCADE, verbose_name=_("Author"))
    title = CharField(max_length=200, verbose_name=_("Title"))
    slug = SlugField(unique=True, verbose_name=_("Slug"))
    body = TextField(verbose_name=_("Body"))
    category = ForeignKey(Category, on_delete=SET_NULL, null=True, blank=True, verbose_name=_("Category"))
    tags = ManyToManyField(Tag, blank=True, verbose_name=_("Tags"))
    status = CharField(max_length=10, choices=Choices.choices, default=Choices.DRAFT, verbose_name=_("Status"))
    created_at = DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    updated_at = DateTimeField(auto_now=True, verbose_name=_("Updated at"))
    publish_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")


class Comment(models.Model):
    post = ForeignKey(Post, on_delete=CASCADE, verbose_name=_("Post"))
    author = ForeignKey(User, on_delete=CASCADE, verbose_name=_("Author"))
    body = TextField(verbose_name=_("Body"))
    created_at = DateTimeField(auto_now_add=True, verbose_name=_("Created at"))

    def __str__(self):
        return f"{self.author} -> {self.post}"

    class Meta:
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")