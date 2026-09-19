from rest_framework.routers import DefaultRouter

from .views import (
    RemisionAlarmaViewSet,
    RemisionDetalleViewSet,
    RemisionReservaViewSet,
    RemisionViewSet,
)


router = DefaultRouter()
router.register(r'remisiones', RemisionViewSet, basename='remision')
router.register(r'remision-detalles', RemisionDetalleViewSet, basename='remision-detalle')
router.register(r'remision-reservas', RemisionReservaViewSet, basename='remision-reserva')
router.register(r'remision-alarmas', RemisionAlarmaViewSet, basename='remision-alarma')

urlpatterns = router.urls
