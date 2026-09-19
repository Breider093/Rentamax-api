from rest_framework.routers import DefaultRouter

from .views import (
	TransportadorVehiculoViewSet,
	TransportadorViewSet,
	VehiculoViewSet,
	ViajeRemisionViewSet,
	ViajeViewSet,
)


router = DefaultRouter()
router.register(r'transportadores', TransportadorViewSet, basename='transportador')
router.register(r'vehiculos', VehiculoViewSet, basename='vehiculo')
router.register(r'transportador-vehiculos', TransportadorVehiculoViewSet, basename='transportador-vehiculo')
router.register(r'viajes', ViajeViewSet, basename='viaje')
router.register(r'viaje-remisiones', ViajeRemisionViewSet, basename='viaje-remision')

urlpatterns = router.urls
