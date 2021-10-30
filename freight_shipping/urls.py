from django.urls import path
from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('vehicle', views.VehicleSet)
router.register(r'departure/(?P<departure_id>\d+)/destination/(?P<destination_id>\d+)/vehicle', views.VehicleLocationSet)
router.register('order', views.OrderSet)
router.register('route', views.RouteSet)

urlpatterns = [
    path('country/', views.CountryList.as_view()),
    path('country/<int:pk>/', views.CountryDetail.as_view()),
    path('country/<int:country_id>/city/', views.CityList.as_view()),
    path('country/<int:country_id>/city/<int:pk>/', views.CityDetail.as_view()),
    path('city/<int:city_id>/district/', views.DistrictList.as_view()),
    path('city/<int:city_id>/district/<int:pk>/', views.DistrictDetail.as_view()),
]

urlpatterns += router.urls
