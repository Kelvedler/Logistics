from . import views
from django.urls import path
from rest_framework import routers

router = routers.SimpleRouter()
router.register('country', views.CountrySet)
router.register('city', views.CitySet)
router.register('district', views.DistrictSet)
router.register('vehicle', views.VehicleSet)
router.register(r'order/(?P<order_id>\d+)/vehicle', views.VehicleLocationSet)
router.register('order', views.OrderSet)
router.register('route', views.RouteSet)
router.register(r'route/(?P<route_id>\d+)/complete', views.CompleteRouteSet)

urlpatterns = [
    path('order/completed/', views.CompletedOrdersSet.as_view({'get': 'list'})),
    path('order/completed/<int:pk>/', views.CompletedOrdersSet.as_view({'get': 'retrieve'})),
]

urlpatterns += router.urls
