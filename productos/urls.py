from rest_framework.routers import DefaultRouter

from .views import (
    ProductoProveedorViewSet,
    ProductoViewSet,
    ProveedorViewSet,
    TipoProductoViewSet,
)


router = DefaultRouter()

router.register(
    r'productos',
    ProductoViewSet,
    basename='producto'
)

router.register(
    r'tipos-producto',
    TipoProductoViewSet,
    basename='tipo-producto'
)

router.register(
    r'proveedores',
    ProveedorViewSet,
    basename='proveedor'
)

router.register(
    r'producto-proveedores',
    ProductoProveedorViewSet,
    basename='producto-proveedor'
)

urlpatterns = router.urls