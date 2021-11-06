from rest_framework import generics, status
from . import models, permissions, fields, serializers
from users import models as user_models
from rest_framework import viewsets, exceptions as rest_framework_exceptions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from users.views import CsrfExemptSessionAuthentication
from users.models import USER_GROUPS
from django.db.models import Q
from django.core import exceptions as django_exceptions


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
        excluded_fields = request.query_params.getlist('exclude')
        detailed_fields = [field for key, field in self.fields['detailed'].items() if
                           key not in excluded_fields]
        serializer = self.serializer_class(self.queryset,
                                           many=True,
                                           fields=detailed_fields,
                                           context={'action': self.action, 'excluded_fields': excluded_fields})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        if not request.data.get('driver') and request.user.group == USER_GROUPS['Driver']:
            request.data['driver'] = request.user.id
        self.check_object_permissions(request=request, obj=None)
        excluded_fields = request.query_params.getlist('exclude')
        basic_fields = [field for key, field in self.fields['basic'].items() if
                        key not in excluded_fields]
        serializer = self.serializer_class(data=request.data,
                                           fields=basic_fields,
                                           context={'action': self.action})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        excluded_fields = request.query_params.getlist('exclude')
        detailed_fields = [field for key, field in self.fields['detailed'].items() if
                           key not in excluded_fields]
        serializer = self.serializer_class(vehicle,
                                           fields=detailed_fields,
                                           context={'action': self.action})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        self.check_object_permissions(request=request, obj=vehicle)
        excluded_fields = request.query_params.getlist('exclude')
        basic_fields = [field for key, field in self.fields['basic'].items() if
                        key not in excluded_fields]
        serializer = self.serializer_class(vehicle,
                                           data=request.data,
                                           fields=basic_fields,
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
    fields = fields.vehicle_fields

    def list(self, request, departure_id=None, destination_id=None, order_id=None):
        excluded_fields = request.query_params.getlist('exclude')
        detailed_fields = [field for key, field in self.fields['detailed'].items() if
                           key not in excluded_fields]
        try:
            pending_order = models.Order.objects.get(pk=order_id)
        except django_exceptions.ObjectDoesNotExist:
            raise rest_framework_exceptions.ValidationError(detail={'order': 'Invalid ID'})
        filters = (Q(route__location=departure_id) | Q(location=departure_id))
        if pending_order.temperature_control:
            filters &= Q(temperature_control=True)
        if pending_order.dangerous_goods:
            filters &= Q(dangerous_goods=True)
        serializer = self.serializer_class(
            self.queryset.filter(filters).distinct('id'),
            many=True,
            fields=detailed_fields,
            context={'action': self.action, 'serializer': self.view_name,
                     'excluded_fields': excluded_fields, 'departure_id': departure_id, 'destination_id': destination_id,
                     'pending_order': pending_order})
        return Response([obj for obj in serializer.data if obj], status=status.HTTP_200_OK)


class OrderSet(viewsets.ViewSet):
    queryset = models.Order.objects
    serializer_class = serializers.OrderSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.OrderPermission]

    def list(self, request):
        serializer = self.serializer_class(self.queryset.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        if not request.data.get('customer'):
            request.data['customer'] = request.user.id
        self.check_object_permissions(request=request, obj=None)
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
