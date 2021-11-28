import copy
import re
from . import models, views
from serializers import DynamicFieldsModelSerializer
from users import models as user_models
from rest_framework import serializers, exceptions as rest_framework_exceptions
from django.db import transaction
from django.db.models import Q
from django.core import exceptions as django_exceptions
from django.core.cache import cache


def validate_structure(structure: dict, data: dict):
    def get_type(route_type):
        return re.search(r"'([^']+)", str(type(route_type))).group(1)

    errors_dict = {}

    for item in structure:
        if not data.get(item):
            errors_dict[item] = 'This field is required.'
        elif not isinstance(data[item], type(structure[item])):
            errors_dict[item] = 'Expected a {}, but got {}.'.format(get_type(structure[item]), get_type(data[item]))
        elif isinstance(structure[item], list):
            for list_element in data[item]:
                if not isinstance(list_element, structure[item][0]):
                    errors_dict[item] = 'Expected {} inside list, but got {}.'.format(get_type(structure[item][0]),
                                                                                      get_type(list_element))
                elif isinstance(structure[item][0], dict):
                    nested_validation = validate_structure(structure[item][0], list_element)
                    if nested_validation is not True:
                        errors_dict[item] = nested_validation
        elif isinstance(structure[item], dict):
            nested_validation = validate_structure(structure[item], data[item])
            if nested_validation is not True:
                errors_dict[item] = nested_validation

    if errors_dict:
        return errors_dict
    else:
        return True


def calculate_truck_load(length, width, height, maximum_payload, *cargo):
    euro_1_pallet = {'length': 1200, 'width': 800, 'maximum_payload': 1500, 'weight': 25}
    euro_6_pallet = {'length': 800, 'width': 600, 'maximum_payload': 500, 'weight': 10}
    euro_1_cargo = []
    euro_6_cargo = []
    for unit in cargo:
        if unit['length'] < unit['width']:
            unit['length'], unit['width'] = unit['width'], unit['length']

        if unit['height'] > height:
            raise rest_framework_exceptions.ValidationError({'message': f'Improper cargo in vehicle; height - {unit}'})
        elif unit['length'] <= euro_6_pallet['length'] and \
                unit['width'] <= euro_6_pallet['width'] and \
                unit['weight'] <= euro_6_pallet['maximum_payload']:
            euro_6_cargo.append(unit['weight'] + euro_6_pallet['weight'])
        elif unit['length'] <= euro_1_pallet['length'] and \
                unit['width'] <= euro_1_pallet['width'] and \
                unit['weight'] <= euro_1_pallet['maximum_payload']:
            euro_1_cargo.append(unit['weight'] + euro_1_pallet['weight'])
        else:
            raise rest_framework_exceptions.ValidationError({'message': f'Improper cargo in vehicle; volume - {unit}'})

    leftover_payload = maximum_payload - (sum(euro_1_cargo) + sum(euro_6_cargo))
    euro_1_pallet_space = length // euro_1_pallet['length']
    euro_6_pallet_space = length % euro_1_pallet['length'] // euro_6_pallet['length']
    if width > euro_1_pallet['width'] * 2:
        euro_1_pallet_space *= 2
        euro_6_pallet_space *= 2
    if len(euro_1_cargo) > euro_1_pallet_space:
        raise rest_framework_exceptions.ValidationError({'message': 'improper cargo in vehicle; overload'})
    if len(euro_1_cargo) == euro_1_pallet_space:
        free_euro_1_space = False
    else:
        free_euro_1_space = True
    used_space = len(euro_1_cargo) * 2 + len(euro_6_cargo)
    vehicle_capacity = euro_1_pallet_space * 2 + euro_6_pallet_space
    leftover_space = vehicle_capacity - used_space
    if leftover_space > 1 and free_euro_1_space:
        return euro_1_pallet['length'], euro_1_pallet['width'], leftover_payload
    elif leftover_space > 0:
        return euro_6_pallet['length'], euro_6_pallet['width'], leftover_payload
    elif leftover_space == 0:
        return 0, 0, 0
    else:
        raise rest_framework_exceptions.ValidationError({'message': 'improper cargo in vehicle; overload'})


def delete_unpaid_route(ordered_route, orders_in_route):
    instances_to_delete = []
    for route_instance in ordered_route:
        delete_route_instance = True
        if cache.get(f'route_{route_instance["id"]}'):
            delete_route_instance = False
        else:
            for order in orders_in_route:
                for route_in_order in [order.departure_route, order.destination_route]:
                    if route_in_order.id == route_instance['id']:
                        payment = getattr(order, 'payment', None)
                        if payment and payment.completed:
                            delete_route_instance = False
                            break
        if delete_route_instance:
            instances_to_delete.insert(0, route_instance)
    for instance in instances_to_delete:
        instance_index = ordered_route.index(instance)
        if instance_index > 0:
            previous_route_instance = models.Route.objects.get(pk=ordered_route[instance_index - 1]['id'])
            if instance_index < len(ordered_route) - 1:
                previous_route_instance.next_route_id = int(ordered_route[instance_index + 1]['id'])
            else:
                previous_route_instance.next_route_id = None
            previous_route_instance.save()
        for index in range(instance_index + 1, len(ordered_route)):
            ordered_route[index]['index'] = index - 1
        instance_to_delete = models.Route.objects.get(pk=ordered_route[instance_index]['id'])
        instance_to_delete.delete()
        ordered_route.pop(instance_index)


def check_if_route_is_full(ordered_route, vehicle_model, order_length, order_width, order_weight):
    route = []
    orders_in_route = models.Order.objects.filter(
        Q(departure_route__in=[route['id'] for route in ordered_route]) | Q(
            destination_route__in=[route['id'] for route in ordered_route])).distinct()
    delete_unpaid_route(ordered_route, orders_in_route)
    for route_instance in ordered_route:
        order_measurements = []
        for order in orders_in_route:
            for route_in_order in [order.departure_route, order.destination_route]:
                if route_in_order.id == route_instance['id']:
                    order_measurements.append(
                        {'length': order.length, 'width': order.width, 'height': order.height,
                         'weight': order.weight})
        if order_measurements:
            leftover_length, leftover_width, leftover_payload = calculate_truck_load(vehicle_model.length,
                                                                                     vehicle_model.width,
                                                                                     vehicle_model.height,
                                                                                     vehicle_model.maximum_payload,
                                                                                     *order_measurements)
            if leftover_length >= order_length and \
                    leftover_width >= order_width and \
                    leftover_payload >= order_weight:
                route_instance['full'] = False
            else:
                route_instance['full'] = True
        else:
            route_instance['full'] = False
        route.append(route_instance)
    return route


def validate_order_on_route(checked_route, departure_id: int, destination_id: int):
    valid_departure, valid_destination = False, False
    for waypoint in checked_route:
        if waypoint['full']:
            valid_departure = False
        elif waypoint['location']['id'] == departure_id:
            valid_departure = True
        elif waypoint['location']['id'] == destination_id and valid_departure:
            valid_destination = True
            break
    return valid_departure, valid_destination


def order_route(route):
    ordered_id = route[0]['id']
    next_id = route[0].get('next_route_id', None)
    ordered_route = [{'id': route[0]['id'], 'location': route[0]['location']}]
    route.pop(0)
    route_copy = copy.copy(route)
    iterator = len(route)
    while route:
        if iterator < 0:
            raise rest_framework_exceptions.ValidationError(detail={"route": "Bad data"})
        route = copy.copy(route_copy)
        route_copy.clear()
        for i, item in enumerate(route):
            if item['id'] == next_id:
                ordered_route.append({'id': item['id'], 'location': item['location']})
                next_id = item.get('next_route_id', None)
            elif item.get('next_route_id') == ordered_id:
                ordered_route.insert(0, {'id': item['id'], 'location': item['location']})
                ordered_id = item['id']
            else:
                route_copy.append(item)
        iterator -= 1
    return [{'index': i, 'id': item['id'], 'location': item['location']} for i, item in enumerate(ordered_route)]


def get_model_serializer(set_model, set_fields='__all__', **nested_serializers):
    class ModelSerializer(serializers.ModelSerializer):

        def __init__(self, *args, **kwargs):

            def set_nested_fields():
                for field, serializer in nested_serializers.items():
                    self.fields[field] = serializer
                    serializer.source = None

            super(ModelSerializer, self).__init__(*args, **kwargs)
            if nested_serializers:
                set_nested_fields()

        class Meta:
            model = set_model
            fields = set_fields

    return ModelSerializer


class CountrySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = models.Country
        fields = '__all__'


class CitySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = models.City
        fields = '__all__'


class DistrictSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = models.District
        fields = '__all__'


class VehicleSerializer(DynamicFieldsModelSerializer):

    def __init__(self, *args, **kwargs):
        super(VehicleSerializer, self).__init__(*args, **kwargs)
        action = self.context.get('action')
        excluded_fields = self.context.get('excluded_fields', [])
        if action in ['create', 'update']:
            self.fields['location'] = serializers.PrimaryKeyRelatedField(queryset=models.District.objects.all())
            self.fields['driver'] = serializers.PrimaryKeyRelatedField(queryset=user_models.User.objects.all(),
                                                                       required=False)
        elif action in ['list', 'retrieve'] and 'location' not in excluded_fields:
            self.fields['location'] = get_model_serializer(models.District)()

    vehicle_model = get_model_serializer(models.VehicleModel)()
    route = get_model_serializer(models.Route, location=get_model_serializer(models.District)())(many=True)

    class Meta:
        model = models.Vehicle
        fields = '__all__'
        depth = 2

    def validate(self, attrs):
        driver = attrs['driver']
        if self.context.get('action') == 'create' and hasattr(driver, 'vehicle'):
            raise rest_framework_exceptions.ValidationError(detail='Driver can have only one vehicle')
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            vehicle_model_data = validated_data.pop('vehicle_model')
            vehicle_model, _ = models.VehicleModel.objects.get_or_create(**vehicle_model_data)
            driver = validated_data.pop('driver')
            vehicle = models.Vehicle.objects.create(driver_id=driver.id, vehicle_model=vehicle_model, **validated_data)
        return vehicle

    def update(self, instance, validated_data):
        with transaction.atomic():
            vehicle_model_data = validated_data.pop('vehicle_model', None)
            if vehicle_model_data:
                vehicle_model, _ = models.VehicleModel.objects.get_or_create(**vehicle_model_data)
                validated_data['vehicle_model'] = vehicle_model
            instance = serializers.ModelSerializer.update(self, instance, validated_data)
            return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if self.context.get('serializer') == views.VehicleLocationSet.view_name and self.context.get(
                'action') == 'list':
            vehicle_model = instance.vehicle_model
            pending_order = self.context.get('pending_order')
            if vehicle_model.height < pending_order.height:
                return None
            if representation['route']:
                if pending_order.length < pending_order.width:
                    pending_order.length, pending_order.width = pending_order.width, pending_order.length
                ordered_route = order_route(representation.pop('route'))
                representation['route'] = check_if_route_is_full(ordered_route, vehicle_model, pending_order.length,
                                                                 pending_order.width, pending_order.weight)
                valid_departure, _ = validate_order_on_route(representation['route'],
                                                             int(self.context.get('departure_district_id')),
                                                             int(self.context.get('destination_district_id')))
                if not valid_departure:
                    return None
        elif self.context.get('action') in ['list', 'retrieve'] and representation.get('route'):
            representation['route'] = order_route(representation.pop('route'))
        return representation


class OrderSerializer(DynamicFieldsModelSerializer):

    def __init__(self, *args, **kwargs):
        super(OrderSerializer, self).__init__(*args, **kwargs)
        action = self.context.get('action')
        if action in ['create', 'update']:
            self.fields['departure_district'] = serializers.PrimaryKeyRelatedField(
                queryset=models.District.objects.all())
            self.fields['destination_district'] = serializers.PrimaryKeyRelatedField(
                queryset=models.District.objects.all())
            self.fields['departure_route'] = serializers.PrimaryKeyRelatedField(queryset=models.Route.objects.all(),
                                                                                allow_null=True, required=False)
            self.fields['destination_route'] = serializers.PrimaryKeyRelatedField(queryset=models.Route.objects.all(),
                                                                                  allow_null=True, required=False)

    customer = serializers.PrimaryKeyRelatedField(queryset=user_models.User.objects.all())
    payment = get_model_serializer(models.Payment)(read_only=True)

    class Meta:
        model = models.Order
        fields = '__all__'
        depth = 1

    def validate(self, attrs):
        if self.context.get('action') == 'update' and getattr(self.context.get('payment'), 'completed', None):
            raise rest_framework_exceptions.ValidationError(
                detail={'message': 'cannot modify order after payment has been completed'})
        if bool(attrs.get('departure_route')) != bool(attrs.get('destination_route')):
            raise rest_framework_exceptions.ValidationError(
                detail={'message': 'not allowed to provide destination without departure or vice versa'})
        elif attrs.get('departure_route') and attrs.get('destination_route'):
            try:
                departure = models.Route.objects.get(pk=attrs['departure_route'].id)
            except django_exceptions.ObjectDoesNotExist:
                raise rest_framework_exceptions.ValidationError(detail={'departure_route': 'Object not found'})
            if departure.vehicle.vehicle_model.height < attrs['height']:
                raise rest_framework_exceptions.ValidationError({'message': 'order height is higher then vehicle'})
            route = models.Route.objects.filter(vehicle_id=departure.vehicle)
            ordered_route = order_route(
                [{'location': {'id': point['location_id']},
                  **{key: point[key] for key in point if key != 'location_id'}} for
                 point in route.values()])
            departure_index, destination_index, departure_id, destination_id = -1, -1, None, None
            for point in ordered_route:
                if point['id'] == attrs['departure_route'].id:
                    departure_index, departure_id = point['index'], point['location']['id']
                elif point['id'] == attrs['destination_route'].id:
                    destination_index, destination_id = point['index'], point['location']['id']
            if destination_index == -1:
                raise rest_framework_exceptions.ValidationError(detail={'destination_route': 'Object not found'})
            if departure_index > destination_index:
                raise rest_framework_exceptions.ValidationError(
                    detail={'route': 'Departure should come before destination'})
            checked_route = check_if_route_is_full(ordered_route, departure.vehicle.vehicle_model, attrs['length'],
                                                   attrs['width'], attrs['weight'])
            valid_departure, valid_destination = validate_order_on_route(checked_route, departure_id, destination_id)
            if not valid_departure or not valid_destination:
                raise rest_framework_exceptions.ValidationError(detail='Could not place the order, vehicle is full')
        return attrs


class RouteSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = models.Route
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            route = models.Route.objects.filter(vehicle_id=validated_data['vehicle'].id)
            route_to_order = [
                {'location': point['location_id'], **{key: point[key] for key in point if key != 'location_id'}} for
                point in route.values()]
            if route_to_order:
                last_route = order_route(list(route_to_order))[-1]
                if last_route['location'] == validated_data['location'].id:
                    raise rest_framework_exceptions.ValidationError(
                        {'location': 'location is identical to previous one'})
            new_route_point = models.Route.objects.create(**validated_data)
            cache.set(f'route_{new_route_point.id}', 'unpaid_route', timeout=30 * 60)
            if route_to_order:
                for point in route:
                    if point.id == last_route['id']:
                        point.next_route_id = new_route_point.id
                        point.save()
            return new_route_point

    def validate(self, attrs):
        if attrs.get('next_route_id'):
            try:
                models.Route.objects.get(pk=attrs['next_route_id'])
            except django_exceptions.ObjectDoesNotExist:
                raise rest_framework_exceptions.ValidationError(detail='next_route_id object does not exist')
        return attrs


class CompletedOrderSerializer(DynamicFieldsModelSerializer):
    payment = serializers.PrimaryKeyRelatedField(queryset=models.Payment.objects.all())

    class Meta:
        model = models.CompletedOrder
        fields = '__all__'

    def validate(self, attrs):
        ordered_route = self.context.get('ordered_route')
        route_id = self.context.get('route_id')
        if ordered_route[0]['id'] != route_id:
            raise rest_framework_exceptions.ValidationError(detail='cannot complete non first route point')
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            payment = validated_data.pop('payment')
            completed_order = models.CompletedOrder.objects.create(**validated_data)
            payment.completed_order = completed_order
            payment.save()
        return completed_order
