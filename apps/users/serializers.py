from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    password = serializers.CharField(write_only=True)
    password_valid = serializers.CharField(write_only=True)

    def validate(self, passwords):
        if passwords['password'] != passwords['password_valid']:
            return serializers.ValidationError('{"password_valid": "Passwords does not match"}')

        return passwords

    def create(self, validated):
        validated.pop('password_valid')
        password = validated.pop('password')
        user = User(**validated)
        user.set_password(password)
        user.save()
        return user
