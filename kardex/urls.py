from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import KardexClienteView, KardexDetalleViewSet, KardexMovimientoViewSet


router = DefaultRouter()
router.register(r'kardex-movimientos', KardexMovimientoViewSet, basename='kardex-movimiento')
router.register(r'kardex-detalles', KardexDetalleViewSet, basename='kardex-detalle')

urlpatterns = [path('clientes/<int:cliente_id>/kardex/', KardexClienteView.as_view(), name='cliente-kardex')] + router.urls
