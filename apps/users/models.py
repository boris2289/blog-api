from django.db.models import EmailField, CharField, BooleanField, DateTimeField, ImageField

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = EmailField(unique=True)
    first_name = CharField(max_length=50)  # required
    last_name = CharField(max_length=50)  # required
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    date_joined = DateTimeField(auto_now_add=True)
    avatar = ImageField(blank=True, null=True)

    objects = UserManager()

    # use EMAIL to auth
    USERNAME_FIELD = "email"

    # required fields
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
