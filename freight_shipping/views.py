from rest_framework import generics, status
from . import models, permissions, fields, serializers
from users import models as user_models
from rest_framework import viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from users.views import CsrfExemptSessionAuthentication
from users.models import USER_GROUPS


class CountryList(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer


class CityList(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = serializers.CitySerializer


class CityDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(country=self.kwargs['country_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['country'] = self.kwargs.pop('country_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.City.objects.all()
    serializer_class = serializers.CitySerializer


class DistrictList(generics.ListCreateAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = serializers.DistrictSerializer


class DistrictDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    def get_queryset(self):
        return super().get_queryset().filter(city=self.kwargs['city_id'])

    def get_serializer(self, *args, **kwargs):
        self.request.data['city'] = self.kwargs.pop('city_id')
        return super().get_serializer(*args, **kwargs)

    queryset = models.District.objects.all()
    serializer_class = serializers.DistrictSerializer


class VehicleSet(viewsets.ViewSet):
    queryset = models.Vehicle.objects.prefetch_related('route')
    serializer_class = serializers.VehicleSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.VehiclePermission]
    fields = fields.vehicle_fields

    def list(self, request):
        if str(request.user) == 'AnonymousUser' or request.user.group == USER_GROUPS['Customer']:
            fields = self.fields['list_for_customer']
        else:
            fields = self.fields['list']
        serializer = self.serializer_class(self.queryset,
                                           many=True,
                                           fields=fields,
                                           context={'action': self.action})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        self.check_object_permissions(request=request, obj=None)
        serializer = self.serializer_class(data=request.data,
                                           fields=self.fields['basic'],
                                           context={'action': self.action})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        if str(request.user) == 'AnonymousUser' or request.user.group == USER_GROUPS['Customer']:
            fields = self.fields['detailed_for_customer']
        else:
            fields = self.fields['detailed']
        serializer = self.serializer_class(vehicle,
                                           fields=fields,
                                           context={'action': self.action})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        self.check_object_permissions(request=request, obj=vehicle)
        serializer = self.serializer_class(vehicle,
                                           data=request.data,
                                           fields=self.fields['basic_no_id'],
                                           context={'action': self.action})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        vehicle.delete()
        return Response(status=status.HTTP_200_OK)


class VehicleLocationSet(viewsets.ViewSet):
    view_name = 'VehicleLocationSet'
    queryset = models.Vehicle.objects
    serializer_class = serializers.VehicleSerializer
    fields = {
        'basic': [
            'id',
            'temperature_control',
            'dangerous_goods',
            {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
            {'route': ['location', 'next_location']},
        ]
    }

    def list(self, request, departure_id=None, destination_id=None):
        districts_in_db = models.District.objects.filter(id__in=[departure_id, destination_id]).all()
        if len(districts_in_db) == 0 or departure_id != destination_id and len(districts_in_db) == 1:
            return Response({'message': 'Invalid route'}, status=status.HTTP_400_BAD_REQUEST)
        print(self.queryset.filter(route__location_id__in=[departure_id, destination_id]))
        serializer = self.serializer_class(self.queryset.filter(route__location__in=[departure_id, destination_id]),
                                           many=True,
                                           fields=self.fields['basic'],
                                           context={'action': self.action, 'serializer': self.view_name})
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderSet(viewsets.ViewSet):
    queryset = models.Order.objects
    serializer_class = serializers.OrderSerializer

    def list(self, request):
        serializer = self.serializer_class(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RouteSet(viewsets.ViewSet):
    queryset = models.Route.objects
    serializer_class = serializers.RouteSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]

    def list(self, request):
        route_heads = self.queryset.filter(vehicle__isnull=False)
        serializer = self.serializer_class(route_heads, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
