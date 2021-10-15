from rest_framework import generics
from . import models
from users import models as user_models
from .serializers import CountrySerializer, CitySerializer, DistrictSerializer, VehicleSerializer
from rest_framework import serializers


class CountryList(generics.ListCreateAPIView):
    queryset = models.Country.objects.all()
    serializer_class = CountrySerializer


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Country.objects.all()
    serializer_class = CountrySerializer


class CityList(generics.ListCreateAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = CitySerializer


class CityDetail(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = CitySerializer


class DistrictList(generics.ListCreateAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = DistrictSerializer


class DistrictDetail(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = DistrictSerializer


class VehicleList(generics.ListCreateAPIView):
    queryset = models.RoadFreightPark.objects.all()
    serializer_class = VehicleSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        if self.request.method == 'GET':
            kwargs['fields'] = [
                'id',
                {'driver': ['id', 'username', 'organization']},
                'plate',
                'temperature_control',
                'dangerous_goods',
                {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
                {'location': ['id', 'name', 'city']},
            ]
        else:
            kwargs['fields'] = [
                'id',
                'driver',
                'plate',
                'temperature_control',
                'dangerous_goods',
                {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
                'location',
            ]
        return serializer_class(*args, **kwargs)
