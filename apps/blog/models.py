from django.db.models import (CharField, SlugField, ForeignKey, CASCADE, TextField, SET_NULL, ManyToManyField,
                              TextChoices, DateTimeField)
from django.db import models
from apps.users.models import User


class Category(models.Model):
    name = CharField(max_length=100, unique=True)
    name_en = CharField(max_length=100, blank=True, default="")
    name_ru = CharField(max_length=100, blank=True, default="")
    name_kk = CharField(max_length=100, blank=True, default="")
    slug = SlugField(unique=True)

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


class Tag(models.Model):
    name = CharField(max_length=50, unique=True)
    slug = SlugField(unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    class Choices(TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    author = ForeignKey(User, on_delete=CASCADE)
    title = CharField(max_length=200)
    slug = SlugField(unique=True)
    body = TextField()
    category = ForeignKey(Category, on_delete=SET_NULL, null=True, blank=True)
    tags = ManyToManyField(Tag, blank=True)
    status = CharField(max_length=10, choices=Choices.choices, default=Choices.DRAFT)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = ForeignKey(Post, on_delete=CASCADE)
    author = ForeignKey(User, on_delete=CASCADE)
    body = TextField()
    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author} -> {self.post}"
