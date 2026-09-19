from rest_framework.routers import DefaultRouter

from .views import DevolucionDetalleViewSet, DevolucionViewSet


router = DefaultRouter()
router.register(r'devoluciones', DevolucionViewSet, basename='devolucion')
router.register(r'devolucion-detalles', DevolucionDetalleViewSet, basename='devolucion-detalle')

urlpatterns = router.urls
