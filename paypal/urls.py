from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('order', views.OrderSet)
router.register(r'order/(?P<pk>\d+)/capture', views.CaptureOrderSet, basename='capture')

urlpatterns = router.urls
