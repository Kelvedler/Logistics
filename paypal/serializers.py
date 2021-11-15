from freight_shipping import models as freight_shipping_models, serializers as freight_shipping_serializers


class PaymentSerializer(freight_shipping_serializers.DynamicFieldsModelSerializer):

    class Meta:
        model = freight_shipping_models.Payment
        fields = '__all__'

    def to_internal_value(self, data):
        if data.get('order_id'):
            data['order'] = data.pop('order_id')
        return super().to_internal_value(data)
