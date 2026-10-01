from rest_framework.permissions import SAFE_METHODS, BasePermission
from .models import Membresia


class EmpresaPermission(BasePermission):
    message = 'El usuario no pertenece a una empresa activa.'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        m = getattr(user, 'membresia', None)
        if not m or not m.activo or not m.empresa.activa:
            return False
        request.membresia, request.empresa = m, m.empresa
        if getattr(view, 'solo_admin', False):
            return m.rol == Membresia.Rol.ADMIN
        if request.method in SAFE_METHODS:
            return True
        return m.rol in (Membresia.Rol.ADMIN, Membresia.Rol.OPERADOR)