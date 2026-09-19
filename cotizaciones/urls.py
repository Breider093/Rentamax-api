from rest_framework.routers import DefaultRouter

from .views import CotizacionDetalleViewSet, CotizacionViewSet


router = DefaultRouter()
router.register(r'cotizaciones', CotizacionViewSet, basename='cotizacion')
router.register(r'cotizacion-detalles', CotizacionDetalleViewSet, basename='cotizacion-detalle')
router.register(r'proformas', CotizacionViewSet, basename='proforma')
router.register(r'proforma-items', CotizacionDetalleViewSet, basename='proforma-item')

urlpatterns = router.urls
