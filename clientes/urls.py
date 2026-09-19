from rest_framework.routers import DefaultRouter

from .views import ClienteDocumentoViewSet, ClienteViewSet


router = DefaultRouter()
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(
    r'cliente-documentos',
    ClienteDocumentoViewSet,
    basename='cliente-documento',
)

urlpatterns = router.urls
