from django.contrib.auth import login, logout
from rest_framework import views, generics, authentication, response, serializers, permissions
from .serializers import UserSerializer, LoginSerializer


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


class RegisterView(generics.CreateAPIView):
    authentication_classes = (CsrfExemptSessionAuthentication, )
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        login(self.request, user)


class LoginView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            raise serializers.ValidationError(serializer.errors)
        else:
            user = serializer.validated_data['user']
            login(request, user)
            return response.Response(UserSerializer(user).data)


class LogoutView(views.APIView):
    authentication_classes = (CsrfExemptSessionAuthentication, )

    def post(self, request):
        logout(request)
        return response.Response()
