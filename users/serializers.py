from rest_framework import serializers
from serializers import DynamicFieldsModelSerializer
from django.db import transaction
from . import models
from django.contrib.auth import authenticate


class UserSerializer(DynamicFieldsModelSerializer):

    def __init__(self, *args, **kwargs):
        super(UserSerializer, self).__init__(*args, **kwargs)
        group = self.context.get('group')
        if group != models.USER_GROUPS['Administrator']:
            self.fields['group'] = serializers.ChoiceField(read_only=True, choices=models.USER_GROUPS_CHOICE_FIELDS)

    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = models.User
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            user = models.User.objects.create_user(
                username=validated_data['username'],
                organization=validated_data['organization'],
                email=validated_data['email'],
                password=validated_data['password'],
            )
            return user

    def update(self, instance, validated_data):
        with transaction.atomic():
            password = validated_data.pop('password', None)
            if password:
                instance.set_password(password)
            instance = serializers.ModelSerializer.update(self, instance, validated_data)
            return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        group = representation.get('group')
        if group:
            for name, abbreviation in models.USER_GROUPS.items():
                if group == abbreviation:
                    representation['group'] = name
                    break
        return representation

    def to_internal_value(self, data):
        group = data.get('group')
        if group:
            for name, abbreviation in models.USER_GROUPS.items():
                if group == name:
                    data['group'] = abbreviation
        value = super().to_internal_value(data)
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])

        if not user:
            raise serializers.ValidationError("Incorrect username or password.")

        return {"user": user}
