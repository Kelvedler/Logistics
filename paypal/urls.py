from . import views
from rest_framework import routers

router = routers.SimpleRouter()
router.register('token', views.Token, basename='Token')

urlpatterns = router.urls
