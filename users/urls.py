from django.urls import path
from rest_framework import routers
from . import views

router = routers.SimpleRouter()

router.register('user', views.UserSet)

urlpatterns = [
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
]

urlpatterns += router.urls
