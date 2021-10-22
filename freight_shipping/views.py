from rest_framework import generics, status
from . import models, permissions
from users import models as user_models
from .serializers import CountrySerializer, CitySerializer, DistrictSerializer, VehicleSerializer
from rest_framework import serializers, viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from users.views import CsrfExemptSessionAuthentication
from users.models import USER_GROUPS


class CountryList(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = models.Country.objects.all()
    serializer_class = CountrySerializer


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = models.Country.objects.all()
    serializer_class = CountrySerializer


class CityList(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = CitySerializer


class CityDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = CitySerializer


class DistrictList(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = DistrictSerializer


class DistrictDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = DistrictSerializer


class VehicleSet(viewsets.ViewSet):
    queryset = models.RoadFreightPark.objects.all()
    serializer_class = VehicleSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.VehiclePermission]
    fields = {
        'detailed': [
                'id',
                {'driver': ['id', 'username', 'organization']},
                'plate',
                'temperature_control',
                'dangerous_goods',
                {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
                {'location': ['id', 'name', 'city']},
            ],
        'basic': [
                'id',
                'driver',
                'plate',
                'temperature_control',
                'dangerous_goods',
                {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
                'location',
            ],
        'basic_no_id': [
                'driver',
                'plate',
                'temperature_control',
                'dangerous_goods',
                {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
                'location',
            ],
        'detailed_for_customer': [
            'id',
            'temperature_control',
            'dangerous_goods',
            {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
            'location',
            {'route': ['location', 'next_location']},
        ]
    }

    def list(self, request):
        serializer = self.serializer_class(self.queryset,
                                           many=True,
                                           fields=self.fields['detailed'],
                                           context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        self.check_object_permissions(request=request, obj=None)
        serializer = self.serializer_class(data=request.data,
                                           fields=self.fields['basic'],
                                           context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        if not request.user == 'AnonymousUser' or (request.user.group == USER_GROUPS['Customer']):
            fields = self.fields['detailed_for_customer']
        else:
            fields = self.fields['detailed']
        serializer = self.serializer_class(vehicle,
                                           fields=fields,
                                           context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        self.check_object_permissions(request=request, obj=vehicle)
        serializer = self.serializer_class(vehicle,
                                           data=request.data,
                                           fields=self.fields['basic_no_id'],
                                           context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        vehicle.delete()
        return Response(status=status.HTTP_200_OK)


class VehicleLocationSet(viewsets.ViewSet):
    queryset = models.RoadFreightPark.objects
    serializer_class = VehicleSerializer
    fields = {
        'basic': [
            'temperature_control',
            'dangerous_goods',
            {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
            {'route': ['location', 'next_location']},
        ]
    }

    def list(self, request, location_id=None):
        serializer = self.serializer_class(self.queryset.filter(location=location_id),
                                           many=True,
                                           fields=self.fields['basic'],
                                           context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
