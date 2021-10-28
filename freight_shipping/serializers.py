import copy
from . import models
from users import models as user_models
from rest_framework import serializers
from django.db import transaction


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
        action = self.context['action']
        if action in ['create', 'update']:
            self.fields['location'] = serializers.PrimaryKeyRelatedField(queryset=models.District.objects.all())
            self.fields['driver'] = serializers.PrimaryKeyRelatedField(queryset=user_models.User.objects.all(),
                                                                       required=False)
        elif action == 'list':
            self.fields['location'] = get_model_serializer(models.District)()

    vehicle_model = get_model_serializer(models.VehicleModel)()
    route = get_model_serializer(models.Route, location=get_model_serializer(models.District)())(many=True)

    class Meta:
        model = models.Vehicle
        fields = '__all__'
        depth = 2

    def create(self, validated_data):
        with transaction.atomic():
            vehicle_model_data = validated_data.pop('vehicle_model')
            vehicle_model, _ = models.VehicleModel.objects.get_or_create(**vehicle_model_data)
            vehicle = models.Vehicle.objects.create(vehicle_model=vehicle_model, **validated_data)
        return vehicle

    def update(self, instance, validated_data):
        with transaction.atomic():
            vehicle_model_data = validated_data.pop('vehicle_model')
            vehicle_model, _ = models.VehicleModel.objects.get_or_create(**vehicle_model_data)
            validated_data['vehicle_model'] = vehicle_model
            instance = serializers.ModelSerializer.update(self, instance, validated_data)
            return instance

    @staticmethod
    def order_route(route):
        ordered_id = route[0]['id']
        next_id = route[0].get('next_route_id', None)
        ordered_route = [route.pop(0)['location']]
        route_copy = copy.copy(route)
        iterator = len(route)
        while route:
            if iterator < 0:
                return {'message': 'Bad Data'}
            route = copy.copy(route_copy)
            route_copy.clear()
            for i, item in enumerate(route):
                if item['id'] == next_id:
                    ordered_route.append(item['location'])
                    next_id = item.get('next_route_id', None)
                elif item['next_route_id'] == ordered_id:
                    ordered_route.insert(0, item['location'])
                    ordered_id = item['id']
                else:
                    route_copy.append(item)
            iterator -= 1
        return [{'index': i, 'location': item} for i, item in enumerate(ordered_route)]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context['action'] == 'retrieve':
            representation['route'] = self.order_route(representation.pop('route'))
        return representation


class OrderSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = models.Order
        fields = '__all__'


class RouteSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = models.Route
        fields = '__all__'
