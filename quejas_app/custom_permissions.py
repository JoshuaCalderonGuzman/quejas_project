from rest_framework import permissions
from django.contrib.auth.models import Group

# ====================================================================
# 1. Permiso para Vistas de Nivel Superior (e.g., Categorías)
# ====================================================================
class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite LECTURA (GET, HEAD, OPTIONS) a todos los autenticados.
    Permite ESCRITURA (POST, PUT, DELETE) solo a usuarios en el grupo 'Administradores'.
    """
    def has_permission(self, request, view):
        # Permite lectura si está autenticado.
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Para operaciones de escritura, comprueba la autenticación y el grupo.
        if not (request.user and request.user.is_authenticated):
            return False

        try:
            admin_group = Group.objects.get(name='Administradores')
        except Group.DoesNotExist:
            return False
            
        return admin_group in request.user.groups.all()

# ====================================================================
# 2. Permiso para Vistas Relacionadas con Quejas (e.g., Queja, Comentario)
# ====================================================================
class IsAdminOrOwner(permissions.BasePermission):
    """
    Permite:
    - Acceso total (CRUD) si el usuario pertenece al grupo 'Administradores'.
    - Acceso de LECTURA/CREACIÓN (GET/POST) si el usuario está autenticado.
    - Modificación/Eliminación (PUT/DELETE) solo si el usuario es el reportante (owner) de la queja/comentario.
    """
    def has_permission(self, request, view):
        # Permite creación (POST) si está autenticado
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        
        # Permite cualquier otra operación si es Administrador
        try:
            admin_group = Group.objects.get(name='Administradores')
            if admin_group in request.user.groups.all():
                return True
        except Group.DoesNotExist:
            pass # Continúa con la verificación de objeto
            
        # Para el resto (GET, PUT, DELETE), continúa a has_object_permission
        return request.user and request.user.is_authenticated
        
    def has_object_permission(self, request, view, obj):
        # Permite lectura a todos (ya cubierto en has_permission, pero mejor revalidar)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permite al administrador acceder a cualquier objeto (CRUD)
        try:
            admin_group = Group.objects.get(name='Administradores')
            if admin_group in request.user.groups.all():
                return True
        except Group.DoesNotExist:
            pass
            
        # Si no es administrador, solo el dueño puede modificar/eliminar
        # El objeto 'obj' debe tener un campo 'reporter' o 'user'
        user_field = getattr(obj, 'reporter', None) or getattr(obj, 'user', None)

        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Verifica si el usuario actual es el 'reporter' (dueño) del objeto
            return user_field == request.user
            
        return False # Denegar cualquier otra cosa por defecto
