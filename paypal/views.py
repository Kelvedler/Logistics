import json
import os
import base64
import ast
from rest_framework import viewsets, status
from urllib import error, request as urllib_request
from rest_framework.response import Response
from users.views import CsrfExemptSessionAuthentication
from . import statuses
from freight_shipping.serializers import validate_structure


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
    return {'access_token': access_token.read()}, status.HTTP_200_OK


def create_order(access_token, request_body: dict):
    request_order = urllib_request.Request('https://api-m.sandbox.paypal.com/v2/checkout/orders')
    request_order.add_header('Content-Type', 'application/json')
    request_order.add_header('Authorization', f'Bearer {access_token}')
    try:
        order = urllib_request.urlopen(request_order, data=json.dumps(request_body).encode('utf-8'))
    except error.HTTPError as http_error:
        rest_status = statuses.get_rest_framework_status(http_error.code)
        return {'message': http_error}, rest_status
    return {'order': order.read()}, status.HTTP_200_OK


class Payment(viewsets.ViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]

    def create(self, request):
        body = request.data.get('amount')
        amount_structure = {
            "currency_code": "str",
            "value": "str"
        }
        if not body:
            return Response({'amount': 'not found'})
        not_validated = validate_structure('amount', amount_structure, body)
        if not_validated:
            return Response(not_validated, status=status.HTTP_400_BAD_REQUEST)
        access_token, rest_status = get_access_token()
        access_token = ast.literal_eval(access_token['access_token'].decode('utf-8'))['access_token']
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
        order_url, rest_status = create_order(access_token, order_request_body)
        return Response(order_url, status=rest_status)

