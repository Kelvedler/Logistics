from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from rest_framework import views, generics, authentication, response, viewsets, status
from rest_framework import serializers as rest_framework_serializers, permissions as rest_framework_permissions
from . import models, serializers, permissions, fields
from mixins import SessionExpiryResetViewSetMixin
from views import exclude_fields


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


class RegisterView(generics.CreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, )
    permission_classes = [rest_framework_permissions.AllowAny]
    serializer_class = serializers.UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        login(self.request, user)


class LoginView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, )
    permission_classes = [rest_framework_permissions.AllowAny]

    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        if not serializer.is_valid():
            raise rest_framework_serializers.ValidationError(serializer.errors)
        else:
            user = serializer.validated_data['user']
            login(request, user)
            return response.Response(serializers.UserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        logout(request)
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class UserSet(SessionExpiryResetViewSetMixin, viewsets.ViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, )
    permission_classes = [permissions.UserPermission]
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    fields = fields.user_fields

    def list(self, request):
        self.check_object_permissions(request=request, obj=None)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(self.queryset, many=True, fields=display_fields)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        user = get_object_or_404(self.queryset, pk=pk)
        self.check_object_permissions(request=request, obj=user)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(user, fields=display_fields)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None):
        user = get_object_or_404(self.queryset, pk=pk)
        self.check_object_permissions(request=request, obj=user)
        excluded_fields = request.query_params.getlist('exclude')
        display_fields = exclude_fields(self.fields, excluded_fields)
        serializer = self.serializer_class(user, data=request.data, fields=display_fields,
                                           context={'group': request.user.group})
        if serializer.is_valid():
            serializer.save()
            if request.user.id == user.id:
                login(request, user)
            return response.Response(serializer.data, status=status.HTTP_200_OK)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        user = get_object_or_404(self.queryset, pk=pk)
        user.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)
