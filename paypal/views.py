import os
import base64
from rest_framework import viewsets, status
from urllib import error, request as urllib_request
from rest_framework.response import Response
from users.views import CsrfExemptSessionAuthentication


class Token(viewsets.ViewSet):
    authentication_classes = [CsrfExemptSessionAuthentication]

    def list(self, request):
        token_request = urllib_request.Request('https://api-m.sandbox.paypal.com/v1/oauth2/token')
        token_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        base64string = base64.b64encode(bytes('%s:%s' % (os.environ.get('PAYPAL_CLIENT_ID'), os.environ.get('PAYPAL_SECRET')), 'ascii'))
        body_data = bytes('%s=%s' % ('grant_type', 'client_credentials'), 'ascii')
        token_request.add_header('Authorization', 'Basic %s' % base64string.decode('utf-8'))
        try:
            access_token = urllib_request.urlopen(token_request, data=body_data)
        except error.HTTPError as http_error:
            return Response({'message': http_error}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'access_token': access_token.read()}, status=status.HTTP_200_OK)
