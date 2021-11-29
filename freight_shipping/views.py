from rest_framework import status, viewsets, exceptions as rest_framework_exceptions
from . import models, permissions, fields, serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.core import exceptions as django_exceptions
from users.views import CsrfExemptSessionAuthentication
from users.models import USER_GROUPS
from mixins import SessionExpiryResetViewSetMixin
from views import exclude_fields


class DynamicFieldsModelViewSet(viewsets.ModelViewSet):
    fields = None

    def get_serializer(self, *args, **kwargs):
        excluded_fields = self.request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        return super().get_serializer(*args, fields=display_fields, **kwargs)


class CountrySet(SessionExpiryResetViewSetMixin, DynamicFieldsModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.LocationPermission]
    queryset = models.Country.objects.all()
    fields = fields.country_fields
    serializer_class = serializers.CountrySerializer


class CitySet(SessionExpiryResetViewSetMixin, DynamicFieldsModelViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.LocationPermission]
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
    permission_classes = [permissions.LocationPermission]
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

    def list(self, request, order_id=None):
        excluded_fields = request.query_params.getlist('exclude')
        detailed_fields = exclude_fields(self.fields['detailed'], excluded_fields)
        try:
            pending_order = models.Order.objects.get(pk=order_id)
        except django_exceptions.ObjectDoesNotExist:
            raise rest_framework_exceptions.ValidationError(detail={'order': 'Invalid ID'})
        departure_district_id = pending_order.departure_district.id
        destination_district_id = pending_order.destination_district.id
        filters = (Q(route__location=departure_district_id) | Q(location=departure_district_id))
        if pending_order.temperature_control:
            filters &= Q(temperature_control=True)
        if pending_order.dangerous_goods:
            filters &= Q(dangerous_goods=True)
        serializer = self.serializer_class(
            self.queryset.filter(filters).distinct('id'),
            many=True,
            fields=detailed_fields,
            context={'action': self.action, 'serializer': self.view_name,
                     'excluded_fields': excluded_fields, 'departure_district_id': departure_district_id,
                     'destination_district_id': destination_district_id,
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
        customer_filter = request.query_params.get('customer')
        driver_filter = request.query_params.get('driver')
        self.check_object_permissions(request=request,
                                      obj={'customer_id': int(customer_filter) if customer_filter else None,
                                           'driver_id': int(driver_filter) if driver_filter else None})
        filters = {}
        if customer_filter:
            filters['customer'] = customer_filter
        if driver_filter:
            filters['departure_route__vehicle__driver__id'] = driver_filter
        if filters:
            queryset = self.queryset.filter(**filters).all()
        else:
            queryset = self.queryset.all()
        display_fields = exclude_fields(self.fields['detailed'], excluded_fields)
        serializer = self.serializer_class(queryset, many=True, fields=display_fields,
                                           context={'action': self.action})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        if not request.data.get('customer'):
            request.data['customer'] = request.user.id
        self.check_object_permissions(request=request, obj=None)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields['basic'], excluded_fields)
        serializer = self.serializer_class(data=request.data, fields=display_fields,
                                           context={'action': self.action})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        order = get_object_or_404(self.queryset.all(), pk=pk)
        driver_id = getattr(getattr(getattr(order.departure_route, 'vehicle', None), 'driver', None), 'id', None)
        self.check_object_permissions(request=request, obj={'customer_id': order.customer.id,
                                                            'driver_id': driver_id})
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields['detailed'], excluded_fields)
        serializer = self.serializer_class(order, fields=display_fields,
                                           context={'action': self.action})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        if not request.data.get('customer'):
            request.data['customer'] = request.user.id
        order = get_object_or_404(self.queryset.all(), pk=pk)
        self.check_object_permissions(request=request, obj=None)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields['basic'], excluded_fields)
        serializer = self.serializer_class(order, data=request.data, fields=display_fields,
                                           context={'action': self.action, 'payment': getattr(order, 'payment', None)})
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
    queryset = models.Route.objects.all()
    serializer_class = serializers.RouteSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.RoutePermission]

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        route_instance = get_object_or_404(self.queryset, pk=pk)
        unordered_route = models.Route.objects.filter(vehicle=route_instance.vehicle)
        ordered_route = serializers.order_route([{'location': {'id': point['location_id']},
                                                  **{key: point[key] for key in point if key != 'location_id'}} for
                                                 point in unordered_route.values()])
        previous_route_instance, instance_to_delete, next_route_instance = None, None, None
        for route in ordered_route:
            if instance_to_delete:
                next_route_instance = route
                break
            elif route_instance.id == route['id']:
                instance_to_delete = route
            else:
                previous_route_instance = route
        if next_route_instance:
            previous_route_instance = unordered_route.get(id=previous_route_instance['id'])
            previous_route_instance.next_route_id = next_route_instance['id']
            previous_route_instance.save()
        else:
            previous_route_instance = unordered_route.get(id=previous_route_instance['id'])
            previous_route_instance.next_route_id = None
            previous_route_instance.save()
        route_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompleteRouteSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    queryset = models.CompletedOrder.objects.all()
    serializer_class = serializers.CompletedOrderSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.CompleteRoutePermission]

    def create(self, request, route_id=None):
        route = get_object_or_404(models.Route.objects.all(), pk=route_id)
        unordered_route = models.Route.objects.filter(vehicle_id=route.vehicle_id)
        self.check_object_permissions(request=request, obj={'driver_id': route.vehicle.driver.id})
        completed_orders = models.Order.objects.filter(destination_route=route_id,
                                                       payment__completed=True).select_related('payment')
        data = [
            {'departure': order_value.get('departure_district_id'),
             'destination': order_value.get('destination_district_id'),
             'driver': route.vehicle.driver.id, 'customer': order_value.get('customer_id'), 'payment': order.payment.id}
            for order_value, order in
            zip(completed_orders.values(), completed_orders)]
        ordered_route = serializers.order_route([{'location': {'id': point['location_id']},
                                                  **{key: point[key] for key in point if key != 'location_id'}} for
                                                 point in unordered_route.values()])
        serializer = self.serializer_class(data=data, many=True,
                                           context={'route_id': int(route_id), 'ordered_route': ordered_route,
                                                    'action': self.action})
        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                completed_orders.delete()
                route.delete()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompletedOrdersSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    queryset = models.CompletedOrder.objects
    serializer_class = serializers.CompletedOrderSerializer
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.CompleteRoutePermission]
    fields = fields.completed_order_fields

    def list(self, request):
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        customer_filter = request.query_params.get('customer')
        driver_filter = request.query_params.get('driver')
        self.check_object_permissions(request=request,
                                      obj={'customer_id': int(customer_filter) if customer_filter else None,
                                           'driver_id': int(driver_filter) if driver_filter else None})
        filters = {}
        if customer_filter:
            filters['customer'] = customer_filter
        if driver_filter:
            filters['driver'] = driver_filter
        if filters:
            queryset = self.queryset.filter(**filters).select_related('payment')
        else:
            queryset = self.queryset.all().select_related('payment')
        serializer = self.serializer_class(queryset, many=True, fields=display_fields)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        completed_order = get_object_or_404(self.queryset.all(), pk=pk)
        self.check_object_permissions(request=request, obj={'customer_id': completed_order.customer.id,
                                                            'driver_id': completed_order.driver.id})
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(completed_order, fields=display_fields)
        return Response(serializer.data, status=status.HTTP_200_OK)
