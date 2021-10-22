from . import models
from users import models as user_models
from rest_framework import serializers
from django.db import transaction


def get_model_serializer(set_model, set_fields='__all__'):

    class ModelSerializer(serializers.ModelSerializer):

        class Meta:
            model = set_model
            fields = set_fields

    return ModelSerializer


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        def select_fields(serializer, serializer_fields):
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
                existing = set(serializer.child.fields.keys())
                for field_name in existing - allowed:
                    serializer.child.fields.pop(field_name)
            else:
                for field_name in existing - allowed:
                    serializer.fields.pop(field_name)
            if nested_objects:
                for obj in nested_objects:
                    (name, serializer_fields), = obj.items()
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
        request = self.context['request']
        if request.method in ['POST', 'PUT']:
            self.fields['location'] = serializers.PrimaryKeyRelatedField(queryset=models.District.objects.all())
            self.fields['driver'] = serializers.PrimaryKeyRelatedField(queryset=user_models.User.objects.all(),
                                                                       required=False)

    vehicle_model = get_model_serializer(models.VehicleModel)()

    class Meta:
        model = models.RoadFreightPark
        fields = '__all__'
        depth = 1

    def create(self, validated_data):
        with transaction.atomic():
            vehicle_model_data = validated_data.pop('vehicle_model')
            vehicle_model, _ = models.VehicleModel.objects.get_or_create(**vehicle_model_data)
            vehicle = models.RoadFreightPark.objects.create(vehicle_model=vehicle_model, **validated_data)
        return vehicle

    def update(self, instance, validated_data):
        with transaction.atomic():
            vehicle_model_data = validated_data.pop('vehicle_model')
            vehicle_model, _ = models.VehicleModel.objects.get_or_create(**vehicle_model_data)
            validated_data['vehicle_model'] = vehicle_model
            instance = serializers.ModelSerializer.update(self, instance, validated_data)
            return instance
