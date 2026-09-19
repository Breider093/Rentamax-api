from rest_framework.routers import DefaultRouter

from .views import FacturaDetalleViewSet, FacturaPagoViewSet, FacturaViewSet


router = DefaultRouter()
router.register(r'facturas', FacturaViewSet, basename='factura')
router.register(r'factura-detalles', FacturaDetalleViewSet, basename='factura-detalle')
router.register(r'factura-pagos', FacturaPagoViewSet, basename='factura-pago')

urlpatterns = router.urls
