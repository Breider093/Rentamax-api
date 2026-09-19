from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import (
	EntradaDetalleViewSet, EntradaViewSet, InventarioViewSet, LoteViewSet,
	MovimientoInventarioViewSet, OrdenCompraDetalleViewSet, OrdenCompraViewSet,
	SalidaDetalleViewSet, SalidaViewSet,
)


router = DefaultRouter()
router.register(r'ordenes-compra', OrdenCompraViewSet, basename='orden-compra')
router.register(r'orden-compra-detalles', OrdenCompraDetalleViewSet, basename='orden-compra-detalle')
router.register(r'entradas', EntradaViewSet, basename='entrada')
router.register(r'entrada-detalles', EntradaDetalleViewSet, basename='entrada-detalle')
router.register(r'inventario', InventarioViewSet, basename='inventario')
router.register(r'salidas', SalidaViewSet, basename='salida')
router.register(r'salida-detalles', SalidaDetalleViewSet, basename='salida-detalle')
router.register(r'movimientos-inventario', MovimientoInventarioViewSet, basename='movimiento-inventario')
router.register(r'lotes', LoteViewSet, basename='lote')

urlpatterns = router.urls + [
	path(
		'reportes/inventario/exportar-pdf/',
		InventarioViewSet.as_view({'get': 'exportar_pdf'}),
		name='inventario-exportar-pdf',
	),
	path(
		'reportes/inventario/exportar-excel/',
		InventarioViewSet.as_view({'get': 'exportar_excel'}),
		name='inventario-exportar-excel',
	),
]
