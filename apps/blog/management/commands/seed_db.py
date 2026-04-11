from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.blog.models import Category, Tag, Post, Comment
from apps.users.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        users = self.seed_users()
        categories = self.seed_categories()
        tags = self.seed_tags()
        posts = self.seed_posts(users, categories, tags)
        self.seed_comments(users, posts)

    def seed_users(self):
        users = {}

        users_data = [
            {
                "email": "admin@kbtu-demo.local",
                "password": "admin12345",
                "first_name": "Admin",
                "last_name": "KBTU",
                "preferred_language": "en",
                "timezone": "Asia/Almaty",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "syed.shah@kbtu-demo.local",
                "password": "teacher12345",
                "first_name": "Syed Imran",
                "last_name": "Moazzam Shah",
                "preferred_language": "en",
                "timezone": "Asia/Almaty",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "zhanat.dauletbekova@kbtu-demo.local",
                "password": "teacher12345",
                "first_name": "Zhanat",
                "last_name": "Dauletbekova",
                "preferred_language": "ru",
                "timezone": "Asia/Almaty",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "raikhan.bekenova@kbtu-demo.local",
                "password": "teacher12345",
                "first_name": "Raikhan",
                "last_name": "Bekenova",
                "preferred_language": "ru",
                "timezone": "Asia/Almaty",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "kairgali.dusaliev@kbtu-demo.local",
                "password": "teacher12345",
                "first_name": "Kairgali",
                "last_name": "Dusaliev",
                "preferred_language": "en",
                "timezone": "Asia/Almaty",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "aitbek.akhmetzhanov@kbtu-demo.local",
                "password": "teacher12345",
                "first_name": "Aitbek",
                "last_name": "Akhmetzhanov",
                "preferred_language": "kk",
                "timezone": "Asia/Almaty",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "email": "student1@kbtu-demo.local",
                "password": "student12345",
                "first_name": "Aruzhan",
                "last_name": "Sarsenova",
                "preferred_language": "en",
                "timezone": "Asia/Almaty",
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "student2@kbtu-demo.local",
                "password": "student12345",
                "first_name": "Dias",
                "last_name": "Mukhanov",
                "preferred_language": "ru",
                "timezone": "Asia/Almaty",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for data in users_data:
            password = data.pop("password")

            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults=data,
            )

            updated = False

            for field, value in data.items():
                if getattr(user, field) != value:
                    setattr(user, field, value)
                    updated = True

            if created:
                user.set_password(password)
                updated = True

            if updated:
                user.save()

            users[user.email] = user

        return users

    def seed_categories(self):
        categories = {}

        categories_data = [
            {
                "name": "Computer Science",
                "name_en": "Computer Science",
                "name_ru": "Компьютерные науки",
                "name_kk": "Компьютерлік ғылымдар",
                "slug": "computer-science",
            },
            {
                "name": "Engineering",
                "name_en": "Engineering",
                "name_ru": "Инженерия",
                "name_kk": "Инженерия",
                "slug": "engineering",
            },
            {
                "name": "University News",
                "name_en": "University News",
                "name_ru": "Новости университета",
                "name_kk": "Университет жаңалықтары",
                "slug": "university-news",
            },
        ]

        for data in categories_data:
            category, _ = Category.objects.update_or_create(
                slug=data["slug"],
                defaults=data,
            )
            categories[category.slug] = category

        return categories

    def seed_tags(self):
        tags = {}

        tags_data = [
            {"name": "python", "slug": "python"},
            {"name": "django", "slug": "django"},
            {"name": "algorithms", "slug": "algorithms"},
            {"name": "robotics", "slug": "robotics"},
            {"name": "education", "slug": "education"},
            {"name": "students", "slug": "students"},
            {"name": "research", "slug": "research"},
            {"name": "engineering", "slug": "engineering"},
        ]

        for data in tags_data:
            tag, _ = Tag.objects.update_or_create(
                slug=data["slug"],
                defaults=data,
            )
            tags[tag.slug] = tag

        return tags

    def seed_posts(self, users, categories, tags):
        posts = {}
        now = timezone.now()

        posts_data = [
            {
                "slug": "intro-to-python-for-first-year-students",
                "author": users["syed.shah@kbtu-demo.local"],
                "title": "Intro to Python for First-Year Students",
                "body": (
                    "This post introduces first-year students to Python basics: "
                    "variables, loops, functions, and simple problem solving. "
                    "It is intended as a short and friendly guide before the first lab."
                ),
                "category": categories["computer-science"],
                "status": Post.Choices.PUBLISHED,
                "publish_at": now,
                "tags": ["python", "education", "students"],
            },
            {
                "slug": "how-to-prepare-for-django-coursework",
                "author": users["zhanat.dauletbekova@kbtu-demo.local"],
                "title": "How to Prepare for Django Coursework",
                "body": (
                    "A simple checklist for students working on Django projects: "
                    "understand models, learn migrations, work with views and serializers, "
                    "and practice Docker-based project setup."
                ),
                "category": categories["computer-science"],
                "status": Post.Choices.PUBLISHED,
                "publish_at": now,
                "tags": ["django", "python", "education"],
            },
            {
                "slug": "engineering-project-guidelines",
                "author": users["kairgali.dusaliev@kbtu-demo.local"],
                "title": "Engineering Project Guidelines",
                "body": (
                    "This post explains how to structure a small engineering project: "
                    "define the objective, describe the method, keep the code clean, "
                    "and present results clearly."
                ),
                "category": categories["engineering"],
                "status": Post.Choices.PUBLISHED,
                "publish_at": now,
                "tags": ["engineering", "research"],
            },
            {
                "slug": "why-algorithms-matter",
                "author": users["aitbek.akhmetzhanov@kbtu-demo.local"],
                "title": "Why Algorithms Matter",
                "body": (
                    "Algorithms are important because they help students think clearly "
                    "about efficiency, structure, and problem decomposition. "
                    "This note gives several simple examples from everyday programming."
                ),
                "category": categories["computer-science"],
                "status": Post.Choices.DRAFT,
                "publish_at": None,
                "tags": ["algorithms", "education"],
            },
            {
                "slug": "student-club-meeting-announcement",
                "author": users["raikhan.bekenova@kbtu-demo.local"],
                "title": "Student Club Meeting Announcement",
                "body": (
                    "We invite students to the weekly academic club meeting. "
                    "The agenda includes project ideas, peer discussion, and short demos."
                ),
                "category": categories["university-news"],
                "status": Post.Choices.PUBLISHED,
                "publish_at": now,
                "tags": ["students", "education"],
            },
        ]

        for data in posts_data:
            tag_slugs = data.pop("tags")

            missing_tags = [tag_slug for tag_slug in tag_slugs if tag_slug not in tags]
            if missing_tags:
                raise ValueError(f"Missing tags in seed data: {missing_tags}")

            post, _ = Post.objects.update_or_create(
                slug=data["slug"],
                defaults={
                    "author": data["author"],
                    "title": data["title"],
                    "body": data["body"],
                    "category": data["category"],
                    "status": data["status"],
                    "publish_at": data["publish_at"],
                },
            )

            post.tags.set([tags[tag_slug] for tag_slug in tag_slugs])
            posts[post.slug] = post

        return posts

    def seed_comments(self, users, posts):
        comments_data = [
            {
                "post": posts["intro-to-python-for-first-year-students"],
                "author": users["student1@kbtu-demo.local"],
                "body": "Very clear introduction. It would be great to have one more practice task.",
            },
            {
                "post": posts["intro-to-python-for-first-year-students"],
                "author": users["student2@kbtu-demo.local"],
                "body": "Thanks, this helps me understand where to start before the lab.",
            },
            {
                "post": posts["how-to-prepare-for-django-coursework"],
                "author": users["student1@kbtu-demo.local"],
                "body": "The Docker checklist is especially useful.",
            },
            {
                "post": posts["student-club-meeting-announcement"],
                "author": users["syed.shah@kbtu-demo.local"],
                "body": "Please prepare one short idea for discussion before the meeting.",
            },
        ]

        for data in comments_data:
            Comment.objects.get_or_create(
                post=data["post"],
                author=data["author"],
                body=data["body"],
            )