from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('country', views.CountrySet)
router.register('city', views.CitySet)
router.register('district', views.DistrictSet)
router.register('vehicle', views.VehicleSet)
router.register(r'vehicle/order/(?P<order_id>\d+)', views.VehicleLocationSet)
router.register('order', views.OrderSet)
router.register('route', views.RouteSet)
router.register(r'route/(?P<route_id>\d+)/complete', views.CompleteRouteSet)
router.register(r'completed-order', views.CompletedOrdersSet)

urlpatterns = router.urls
