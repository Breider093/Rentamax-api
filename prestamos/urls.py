from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import EquipoObraViewSet, PrestamoDetalleViewSet, PrestamoViewSet


router = DefaultRouter()
router.register(r'prestamos', PrestamoViewSet, basename='prestamo')
router.register(
    r'prestamo-detalles',
    PrestamoDetalleViewSet,
    basename='prestamo-detalle',
)
router.register(r'equipos-obra', EquipoObraViewSet, basename='equipo-obra')

urlpatterns = router.urls + [
    path(
        'reportes/equipos-obra/exportar-pdf/',
        EquipoObraViewSet.as_view({'get': 'exportar_pdf'}),
        name='equipos-obra-exportar-pdf',
    ),
    path(
        'reportes/equipos-obra/exportar-excel/',
        EquipoObraViewSet.as_view({'get': 'exportar_excel'}),
        name='equipos-obra-exportar-excel',
    ),
]
