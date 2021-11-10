import copy
import re
from . import models, views
from users import models as user_models
from rest_framework import serializers, exceptions as rest_framework_exceptions
from django.db import transaction
from django.core import exceptions as django_exceptions


def validate_structure(element, structure, data):

    def get_type_error(element, expected, got):

        def cut_out_type(route_type) -> str:
            return re.search(r"'([^']+)", route_type).group(1)

        return {element: ['Expected a {} but got a {}'.format(cut_out_type(str(type(expected))),
                                                              cut_out_type(str(type(got))))]}

    def try_nested_validation(nested_element, structure_element, data_element):
        if isinstance(data_element, list) or isinstance(data_element, dict):
            return validate_structure(nested_element, structure_element, data_element)

    if isinstance(structure, list):
        if not isinstance(data, list):
            return get_type_error(element, structure, data)
        for item in data:
            if not isinstance(item, type(structure[0])):
                return get_type_error(element, structure[0], item)
            message = try_nested_validation(element, structure[0], item)
            if message:
                return message

    elif isinstance(structure, dict):
        if not isinstance(data, dict):
            return get_type_error(element, structure, data)
        for item in structure:
            if not data.get(item):
                return {'message': ['{} required'.format(item)]}
            if not isinstance(data[item], type(structure[item])):
                return get_type_error(item, structure[item], data[item])
            message = try_nested_validation(item, structure[item], data[item])
            if message:
                return message

    else:
        if not isinstance(data, type(structure)):
            return get_type_error(element, structure, data)
    return None


def calculate_truck_load(length, width, height, maximum_payload, *cargo):
    euro_1_pallet = {'length': 1200, 'width': 800, 'maximum_payload': 1500, 'weight': 25}
    euro_6_pallet = {'length': 800, 'width': 600, 'maximum_payload': 500, 'weight': 10}
    euro_1_cargo = []
    euro_6_cargo = []
    for unit in cargo:
        if unit['length'] < unit['width']:
            unit['length'], unit['width'] = unit['width'], unit['length']

        if unit['height'] > height:
            raise Exception  # TODO sane exception
        elif unit['length'] <= euro_6_pallet['length'] and \
                unit['width'] <= euro_6_pallet['width'] and \
                unit['weight'] <= euro_6_pallet['maximum_payload']:
            euro_6_cargo.append(unit['weight'] + euro_6_pallet['weight'])
        elif unit['length'] <= euro_1_pallet['length'] and \
                unit['width'] <= euro_1_pallet['width'] and \
                unit['weight'] <= euro_1_pallet['maximum_payload']:
            euro_1_cargo.append(unit['weight'] + euro_1_pallet['weight'])
        else:
            raise Exception  # TODO sane exception

    leftover_payload = maximum_payload - (sum(euro_1_cargo) + sum(euro_6_cargo))
    euro_1_pallet_space = length // euro_1_pallet['length']
    euro_6_pallet_space = length % euro_1_pallet['length'] // euro_6_pallet['length']
    if width > euro_1_pallet['width'] * 2:
        euro_1_pallet_space *= 2
        euro_6_pallet_space *= 2
    used_space = len(euro_1_cargo) * 2 + len(euro_6_cargo)
    vehicle_capacity = euro_1_pallet_space * 2 + euro_6_pallet_space
    leftover_space = vehicle_capacity - used_space
    if leftover_space > 1:
        return euro_1_pallet['length'], euro_1_pallet['width'], leftover_payload
    elif leftover_space > 0:
        return euro_6_pallet['length'], euro_6_pallet['width'], leftover_payload
    else:
        return 0, 0, 0


def check_if_route_is_full(ordered_route, vehicle_model, order_length, order_width, order_weight):
    route = []
    orders_in_route = models.Order.objects.filter(
        route__in=[route['id'] for route in ordered_route]).distinct()
    for order_instance in ordered_route:
        order_measurements = []
        for order in orders_in_route:
            for route_in_order in order.route.all():
                if route_in_order.id == order_instance['id']:
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
                order_instance['full'] = False
            else:
                order_instance['full'] = True
        else:
            order_instance['full'] = False
        route.append(order_instance)
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
            elif item['next_route_id'] == ordered_id:
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


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        def select_fields(serializer, serializer_fields):
            if isinstance(serializer, serializers.ListSerializer):
                existing = set(serializer.child.fields.keys())
            else:
                existing = set(serializer.fields.keys())
            allowed = set()
            nested_objects = []
            for obj in serializer_fields:
                if type(obj) is dict:
                    allowed.add(list(obj.keys())[0])
                    nested_objects.append(obj)
                else:
                    allowed.add(obj)
            if isinstance(serializer, serializers.ListSerializer):
                for field_name in existing - allowed:
                    serializer.child.fields.pop(field_name)
            else:
                for field_name in existing - allowed:
                    serializer.fields.pop(field_name)
            if nested_objects:
                for obj in nested_objects:
                    (name, serializer_fields), = obj.items()
                    if isinstance(serializer, serializers.ListSerializer):
                        select_fields(serializer.child.fields[name], serializer_fields)
                    else:
                        select_fields(serializer.fields[name], serializer_fields)

        fields = kwargs.pop('fields', None)

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        if fields:
            select_fields(self, fields)


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Country
        fields = '__all__'


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.City
        fields = '__all__'


class DistrictSerializer(serializers.ModelSerializer):
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
        elif action == 'list' and 'location' not in excluded_fields:
            self.fields['location'] = get_model_serializer(models.District)()

    vehicle_model = get_model_serializer(models.VehicleModel)()
    route = get_model_serializer(models.Route, location=get_model_serializer(models.District)())(many=True)

    class Meta:
        model = models.Vehicle
        fields = '__all__'
        depth = 2

    def validate(self, attrs):
        driver = attrs['driver']
        if hasattr(driver, 'vehicle'):
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
            vehicle_model_data = validated_data.pop('vehicle_model')
            vehicle_model, _ = models.VehicleModel.objects.get_or_create(**vehicle_model_data)
            validated_data['vehicle_model'] = vehicle_model
            instance = serializers.ModelSerializer.update(self, instance, validated_data)
            return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if self.context.get('serializer') == views.VehicleLocationSet.view_name and self.context.get(
                'action') == 'list':
            if representation['route']:
                pending_order = self.context.get('pending_order')
                if pending_order.length < pending_order.width:
                    pending_order.length, pending_order.width = pending_order.width, pending_order.length
                vehicle_model = instance.vehicle_model
                ordered_route = order_route(representation.pop('route'))
                representation['route'] = check_if_route_is_full(ordered_route, vehicle_model, pending_order.length,
                                                                 pending_order.width, pending_order.weight)
                valid_departure, _ = validate_order_on_route(representation['route'],
                                                             int(self.context.get('departure_id')),
                                                             int(self.context.get('destination_id')))
                if not valid_departure:
                    return None
        if self.context.get('action') == 'retrieve':
            representation['route'] = order_route(representation.pop('route'))
        return representation


class OrderSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = models.Order
        fields = '__all__'

    def validate(self, attrs):
        if attrs.get('route'):
            try:
                departure = models.Route.objects.get(pk=attrs['route'][0].id)
            except django_exceptions.ObjectDoesNotExist:
                raise rest_framework_exceptions.ValidationError(detail={'departure': 'Object not found'})
            route = models.Route.objects.filter(vehicle_id=departure.vehicle)
            ordered_route = order_route(
                [{'location': {'id': point['location_id']}, **{key: point[key] for key in point if key != 'location_id'}} for
                 point in route.values()])
            departure_index, destination_index, departure_id, destination_id = 0, 0, None, None
            for point in ordered_route:
                if point['id'] == attrs['route'][0].id:
                    departure_index, departure_id = point['index'], point['location']['id']
                elif point['id'] == attrs['route'][1].id:
                    destination_index, destination_id = point['index'], point['location']['id']
            if destination_index == 0:
                raise rest_framework_exceptions.ValidationError(detail={'destination': 'Object not found'})
            if departure_index > destination_index:
                raise rest_framework_exceptions.ValidationError(
                    detail={'route': 'Departure should come before destination'})
            checked_route = check_if_route_is_full(ordered_route, departure.vehicle.vehicle_model, attrs['length'],
                                                   attrs['width'],
                                                   attrs['weight'])
            valid_departure, valid_destination = validate_order_on_route(checked_route, departure_id, destination_id)
            if not valid_departure or not valid_destination:
                raise rest_framework_exceptions.ValidationError(detail='Could not place the order, vehicle is full')
        return attrs

    def to_internal_value(self, data):
        if data.get('route'):
            route_structure = {'departure': 1, 'destination': 1}
            route_validation = validate_structure('route', route_structure, data['route'])
            if route_validation:
                raise serializers.ValidationError(route_validation)
            else:
                data['route'] = [route_data for route_data in [data['route']['departure'], data['route']['destination']]]
        return super().to_internal_value(data)


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
                    raise rest_framework_exceptions.ValidationError({'location': 'location is identical to previous one'})
            new_route_point = models.Route.objects.create(**validated_data)
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
