from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('country', views.CountrySet)
router.register('city', views.CitySet)
router.register('district', views.DistrictSet)
router.register('vehicle', views.VehicleSet)
router.register(r'order/(?P<order_id>\d+)/departure/(?P<departure_id>\d+)/destination/(?P<destination_id>\d+)/vehicle',
                views.VehicleLocationSet)
router.register('order', views.OrderSet)
router.register('route', views.RouteSet)

urlpatterns = router.urls
