from rest_framework import generics
from . import models
from . import serializers


class CountryList(generics.ListCreateAPIView):
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer


class CityList(generics.ListCreateAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = serializers.CitySerializer


class CityDetail(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = serializers.CitySerializer


class DistrictList(generics.ListCreateAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = serializers.DistrictSerializer


class DistrictDetail(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = serializers.DistrictSerializer
