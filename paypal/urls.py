from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('payment', views.Payment, basename='Payment')

urlpatterns = router.urls
