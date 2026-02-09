from django.db.models import (CharField, SlugField, ForeignKey, CASCADE, TextField, SET_NULL, ManyToManyField,
                              TextChoices, DateTimeField)
from django.db import models
from apps.users.models import User


class Category(models.Model):
    name = CharField(max_length=100, unique=True)
    slug = SlugField(unique=True)


class Tag(models.Model):
    name = CharField(max_length=50, unique=True)
    slug = SlugField(unique=True)


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


class Comment(models.Model):
    post = ForeignKey(Post, on_delete=CASCADE)
    author = ForeignKey(User, on_delete=CASCADE)
    body = TextField()
    created_at = DateTimeField(auto_now_add=True)
