from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models import BooleanField, CharField, DateTimeField, EmailField, ImageField
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email is required"))
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
    class LanguageChoices:
        EN = "en"
        RU = "ru"
        KK = "kk"
        CHOICES = (
            (EN, _("English")),
            (RU, _("Russian")),
            (KK, _("Kazakh")),
        )

    email = EmailField(unique=True, verbose_name=_("Email"))
    first_name = CharField(max_length=50, verbose_name=_("First name"))
    last_name = CharField(max_length=50, verbose_name=_("Last name"))
    preferred_language = CharField(
        max_length=2,
        choices=LanguageChoices.CHOICES,
        default=LanguageChoices.EN,
        verbose_name=_("Preferred language"),
    )
    timezone = CharField(max_length=64, default="UTC", verbose_name=_("Timezone"))
    is_active = BooleanField(default=True, verbose_name=_("Is active"))
    is_staff = BooleanField(default=False, verbose_name=_("Is staff"))
    date_joined = DateTimeField(auto_now_add=True, verbose_name=_("Date joined"))
    avatar = ImageField(blank=True, null=True, verbose_name=_("Avatar"))

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
