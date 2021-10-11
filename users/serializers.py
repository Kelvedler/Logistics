from rest_framework import serializers
from django.db import transaction
from . import models
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = models.User
        fields = ['id', 'username', 'organization', 'email', 'password']

    def create(self, validated_data):
        with transaction.atomic():
            user = models.User.objects.create_user(
                username=validated_data['username'],
                organization=validated_data['organization'],
                email=validated_data['email'],
                password=validated_data['password'],
            )
            return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])

        if not user:
            raise serializers.ValidationError("Incorrect username or password.")

        return {"user": user}
