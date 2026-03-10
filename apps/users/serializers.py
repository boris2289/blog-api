from django.contrib.auth import get_user_model
from rest_framework import serializers
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.conf import settings
from django.utils.translation import gettext_lazy as _

User = get_user_model()
SUPPORTED_LANGUAGES = [code for code, _ in settings.LANGUAGES]


def validate_timezone_value(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError:
        raise serializers.ValidationError(_("Invalid timezone"))
    return value


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)
    password_valid = serializers.CharField(write_only=True)
    preferred_language = serializers.ChoiceField(
        choices=SUPPORTED_LANGUAGES,
        required=False,
        label=_("Preferred language")
    )
    timezone = serializers.CharField(required=False, label=_("Timezone"))

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_preferred_language(self, value):
        return value.lower()

    def validate_timezone(self, value):
        return validate_timezone_value(value)

    def validate(self, attrs):
        if attrs["password"] != attrs["password_valid"]:
            raise serializers.ValidationError({
                "password_valid": "Passwords do not match."
            })
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        validated_data.pop("password_valid")
        password = validated_data.pop("password")

        preferred_language = validated_data.pop("preferred_language", None)
        timezone_value = validated_data.pop("timezone_value", None)

        if not preferred_language:
            preferred_language = getattr(request, "LANGUAGE_CODE", settings.LANGUAGE_CODE)

        if not timezone_value:
            timezone_value = "UTC"

        user = User(password=password,
                    preferred_language=preferred_language,
                    timezone=timezone_value,
                    **validated_data)
        user.set_password(password)
        user.save()
        return user


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "preferred_language",
            "timezone",
        ]


class UserLanguageSerializer(serializers.Serializer):
    preferred_language = serializers.ChoiceField(
        choices=SUPPORTED_LANGUAGES,
        label=_("Prefered language"),
    )


class UserTimezoneSerializer(serializers.Serializer):
    timezone = serializers.CharField(label=_("Timezone"))

    def validate_timezone(self, value):
        return validate_timezone_value(value)
