import json
import os
import base64
import ast
import re
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from urllib import error, request as urllib_request
from rest_framework.response import Response
from users.views import CsrfExemptSessionAuthentication
from . import statuses, serializers, permissions
from freight_shipping import models as freight_shipping_models
from freight_shipping.serializers import validate_structure
from mixins import SessionExpiryResetViewSetMixin


def get_access_token():
    token_request = urllib_request.Request('https://api-m.sandbox.paypal.com/v1/oauth2/token')
    base64string = base64.b64encode(
        bytes('%s:%s' % (os.environ.get('PAYPAL_CLIENT_ID'), os.environ.get('PAYPAL_SECRET')), 'ascii'))
    token_request.add_header('Authorization', 'Basic %s' % base64string.decode('utf-8'))
    token_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    body_data = bytes('%s=%s' % ('grant_type', 'client_credentials'), 'ascii')

    try:
        access_token = urllib_request.urlopen(token_request, data=body_data)
    except error.HTTPError as http_error:
        rest_status = statuses.get_rest_framework_status(http_error.code)
        return {'message': http_error}, rest_status
    return {'access_token': access_token.read().decode('utf-8')}, status.HTTP_200_OK


def make_request(access_token, request_url: str, request_body: dict = None):
    request_order = urllib_request.Request(request_url, method='POST')
    request_order.add_header('Content-Type', 'application/json')
    request_order.add_header('Authorization', f'Bearer {access_token}')
    if request_body:
        json_data = {'data': json.dumps(request_body).encode('utf-8')}
    else:
        json_data = {}
    try:
        order = urllib_request.urlopen(request_order, **json_data)
    except error.HTTPError as http_error:
        rest_status = statuses.get_rest_framework_status(http_error.code)
        return {'message': http_error}, rest_status
    return {'order': order.read().decode('utf-8')}, status.HTTP_200_OK


class OrderSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.OrderPermission]
    queryset = freight_shipping_models.Payment.objects
    serializer_class = serializers.PaymentSerializer

    def create(self, request):
        create_order_url = 'https://api-m.sandbox.paypal.com/v2/checkout/orders'
        structure = {
            'amount': {
                "currency_code": "str",
                "value": "str"
            }
        }
        validated = validate_structure(structure, request.data)
        if validated is not True:
            return Response(validated, status=status.HTTP_400_BAD_REQUEST)
        access_token, rest_status = get_access_token()
        access_token = ast.literal_eval(access_token['access_token'])['access_token']
        if 'message' in access_token:
            return Response(access_token, status=rest_status)
        order_request_body = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': request.data['amount']['currency_code'],
                    'value': request.data['amount']['value']
                }
            }]
        }
        order_repr, rest_status = make_request(access_token, create_order_url, order_request_body)
        if 'message' in order_repr:
            return Response(order_repr, status=rest_status)
        filtered_order = re.search(r'(http[^"]+token=)([^"]+)', order_repr['order'])
        payment_url = filtered_order.group(1) + filtered_order.group(2)
        request.data['payment_method'] = 'paypal'
        request.data['payment_id'] = filtered_order.group(2)
        request.data['currency_code'] = request.data['amount']['currency_code']
        request.data['amount'] = request.data['amount']['value']
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'payment_url': payment_url, **serializer.data}, status=rest_status)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CaptureOrderSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [permissions.OrderPermission]
    queryset = freight_shipping_models.Payment.objects

    def create(self, request, pk=None):
        payment_order = get_object_or_404(self.queryset.all(), pk=pk)
        access_token, rest_status = get_access_token()
        access_token = ast.literal_eval(access_token['access_token'])['access_token']
        if 'message' in access_token:
            return Response(access_token, status=rest_status)
        capture_payment_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{payment_order.payment_id}/capture'
        capture_payment, rest_status = make_request(access_token, capture_payment_url)
        if 'message' in capture_payment:
            return Response(capture_payment, status=rest_status)
        capture_status = re.search(r'{}","status":"([^"]+)"'.format(payment_order.payment_id),
                                   capture_payment['order']).group(1)
        payment_order.completed = True
        payment_order.save()
        return Response({'paypal_status': capture_status, 'completed': payment_order.completed},
                        status=status.HTTP_200_OK)
