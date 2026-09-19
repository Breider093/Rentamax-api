from rest_framework.routers import DefaultRouter

from .views import UsuarioViewSet


router = DefaultRouter()
router.register(r'users', UsuarioViewSet, basename='user')

urlpatterns = router.urls
