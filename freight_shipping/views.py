import re
from rest_framework import status, viewsets, exceptions as rest_framework_exceptions
from . import models, permissions, fields, serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from users.views import CsrfExemptSessionAuthentication
from users.models import USER_GROUPS
from django.db.models import Q
from django.core import exceptions as django_exceptions
from mixins import SessionExpiryResetViewSetMixin


def exclude_fields(fields, exclude):
    return_fields = {}
    for field, nested_field in fields.items():
        if field not in exclude:
            if nested_field is not None:
                nested_exclude = [re.search(r'{}__(.+)'.format(field), exclude_item).group(1) for exclude_item in
                                  exclude if re.search(r'{}__(.+)'.format(field), exclude_item)]
                return_fields[field] = exclude_fields(nested_field, nested_exclude)
            else:
                return_fields[field] = None
    return return_fields


class DynamicFieldsModelViewSet(viewsets.ModelViewSet):
    fields = None

    def get_serializer(self, *args, **kwargs):
        excluded_fields = self.request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        return super().get_serializer(*args, fields=display_fields, **kwargs)


class CountrySet(SessionExpiryResetViewSetMixin, DynamicFieldsModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = models.Country.objects.all()
    fields = fields.country_fields
    serializer_class = serializers.CountrySerializer


class CitySet(SessionExpiryResetViewSetMixin, DynamicFieldsModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = models.City.objects.all()
    fields = fields.city_fields
    serializer_class = serializers.CitySerializer

    def get_queryset(self):
        country_filter = self.request.query_params.get('country')
        if country_filter:
            return models.City.objects.filter(country=country_filter)
        return super().get_queryset()


class DistrictSet(SessionExpiryResetViewSetMixin, DynamicFieldsModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    queryset = models.District.objects.all()
    fields = fields.district_fields
    serializer_class = serializers.DistrictSerializer

    def get_queryset(self):
        city_filter = self.request.query_params.get('city')
        if city_filter:
            return models.District.objects.filter(city=city_filter)
        return super().get_queryset()


class VehicleSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    queryset = models.Vehicle.objects.prefetch_related('route')
    serializer_class = serializers.VehicleSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.VehiclePermission]
    fields = fields.vehicle_fields

    def list(self, request):
        excluded_fields = request.query_params.getlist('exclude')
        detailed_fields = exclude_fields(self.fields['detailed'], excluded_fields)
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
        basic_fields = exclude_fields(self.fields['basic'], excluded_fields)
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
        detailed_fields = exclude_fields(self.fields['detailed'], excluded_fields)
        serializer = self.serializer_class(vehicle,
                                           fields=detailed_fields,
                                           context={'action': self.action})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        vehicle = get_object_or_404(self.queryset, pk=pk)
        self.check_object_permissions(request=request, obj=vehicle)
        excluded_fields = request.query_params.getlist('exclude')
        basic_fields = exclude_fields(self.fields['basic'], excluded_fields)
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
        return Response(status=status.HTTP_204_NO_CONTENT)


class VehicleLocationSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    view_name = 'VehicleLocationSet'
    queryset = models.Vehicle.objects
    serializer_class = serializers.VehicleSerializer
    fields = fields.vehicle_fields

    def list(self, request, departure_id=None, destination_id=None, order_id=None):
        excluded_fields = request.query_params.getlist('exclude')
        detailed_fields = exclude_fields(self.fields['detailed'], excluded_fields)
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
        return Response([obj for obj in serializer.data if obj], status=status.HTTP_204_NO_CONTENT)


class OrderSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    queryset = models.Order.objects
    serializer_class = serializers.OrderSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.OrderPermission]
    fields = fields.order_fields

    def list(self, request):
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(self.queryset.all(), many=True, fields=display_fields)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        if not request.data.get('customer'):
            request.data['customer'] = request.user.id
        self.check_object_permissions(request=request, obj=None)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(data=request.data, fields=display_fields)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        order = get_object_or_404(self.queryset.all(), pk=pk)
        self.check_object_permissions(request=request, obj=order)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(order, fields=display_fields)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        if not request.data.get('customer'):
            request.data['customer'] = request.user.id
        order = get_object_or_404(self.queryset.all(), pk=pk)
        self.check_object_permissions(request=request, obj=None)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(order, data=request.data, fields=display_fields)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        order = get_object_or_404(self.queryset, pk=pk)
        self.check_object_permissions(request=request, obj=order)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RouteSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
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
