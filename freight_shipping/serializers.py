from . import models
from rest_framework import serializers


class CountrySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Country
        fields = ['id', 'name']


class CitySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.City
        fields = ['id', 'name', 'country']


class DistrictSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.District
        fields = ['id', 'name', 'city']
