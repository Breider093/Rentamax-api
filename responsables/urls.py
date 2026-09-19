from rest_framework.routers import DefaultRouter

from .views import ResponsableViewSet


router = DefaultRouter()
router.register(r'responsables', ResponsableViewSet, basename='responsable')

urlpatterns = router.urls
