"""
ViewSets de Django REST Framework para la API del Sistema de Quejas.
Define las reglas de negocio, permisos y filtrado para cada modelo.
"""
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny, BasePermission # Se añade BasePermission
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q 

# Importamos todos los modelos y serializadores (AÑADIMOS AdminProfile)
from .models import Category, Complaint, Comment, Attachment, AdminProfile # <--- ¡IMPORTANTE! Se añade AdminProfile
from .serializers import (
    CategorySerializer, 
    ComplaintSerializer, 
    CommentReadOnlySerializer, 
    CommentWriteSerializer,
    AttachmentSerializer
)

# ----------------------------------------------------------------------
# CLASE DE PERMISO PERSONALIZADA: IsStaffOrOwner
# ----------------------------------------------------------------------
class IsStaffOrOwner(BasePermission):
    """
    Permite:
    - Acceso total (CRUD) si el usuario es STAFF.
    - Acceso de lectura/creación (GET/POST) si el usuario está autenticado.
    - Modificación/Eliminación (PUT/PATCH/DELETE) solo si el usuario es el reportante (owner) de la queja.
    """
    def has_permission(self, request, view):
        # Permite la creación (POST) a todos los usuarios autenticados.
        if view.action == 'create':
            return True    
        return request.user and request.user.is_authenticated
        
    
    def has_object_permission(self, request, view, obj):
        # El staff tiene permiso total sobre CUALQUIER objeto.
        if request.user and request.user.is_staff:
            return True

        # Permiso de solo lectura (GET/HEAD/OPTIONS) para cualquier usuario autenticado.
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True 
        
        # Para métodos de modificación/eliminación (PUT, PATCH, DELETE)
        # Solo el dueño puede modificar/eliminar su queja.
        if obj.reporter and obj.reporter == request.user:
            return True

        # Denegar por defecto
        return False


# ----------------------------------------------------
# 1. Modelo Básico (CRUD completo)
# ----------------------------------------------------

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API CRUD completo para Categorías. 
    Rutas: /api/categories/
    
    Regla de Seguridad: Lectura para todos, Escritura/Modificación solo para autenticados.
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    # Permiso: Lectura para todos, Escritura/Modificación solo a autenticados
    permission_classes = [IsAuthenticatedOrReadOnly] 

# ----------------------------------------------------
# 2. Modelo Principal (CRUD completo y filtrado)
# ----------------------------------------------------

class ComplaintViewSet(viewsets.ModelViewSet):
    """
    API CRUD para Quejas. Soporta filtrado por status (admin) y por categorías asignadas (staff).
    Rutas: /api/complaints/ y /api/complaints/{id}/
    """
    queryset = Complaint.objects.all().order_by('-created_at')
    serializer_class = ComplaintSerializer
    # PERMISO APLICADO: Permiso personalizado para manejar Staff y Dueño
    permission_classes = [IsStaffOrOwner] 

    def get_queryset(self):
        """
        Filtra la lista de quejas:
        - Superuser: Ve todas las quejas, potencialmente filtradas por 'status'.
        - Staff (con AdminProfile): Solo ve las quejas de sus categorías asignadas.
        - Usuario Logueado (No-Staff): Solo ve las quejas que reportó.
        - Anónimo: No ve ninguna en la lista.
        """
        user = self.request.user
        base_queryset = self.queryset

        # 1. Si no hay usuario autenticado, devolver vacío.
        if not user or not user.is_authenticated:
            return base_queryset.none()
            
        # 2. Lógica para Staff/Admin (NUEVO FILTRADO POR CATEGORÍA)
        if user.is_staff:
            # 2a. Superusuario: Acceso total (puede ver todas las categorías)
            if user.is_superuser:
                queryset_to_filter = base_queryset
            
            # 2b. Staff NO Superusuario: Filtrar por categorías asignadas
            else:
                try:
                    # Obtener el perfil de administrador y sus categorías
                    admin_profile = AdminProfile.objects.get(user=user)
                    assigned_categories_ids = admin_profile.categories.values_list('id', flat=True)
                    
                    # Si no tiene categorías asignadas o el perfil no existe, no ve ninguna queja.
                    if not assigned_categories_ids:
                        return base_queryset.none()
                    
                    # Filtrar quejas por las categorías asignadas al admin
                    queryset_to_filter = base_queryset.filter(category__id__in=assigned_categories_ids)

                except AdminProfile.DoesNotExist:
                    # Si es staff pero no tiene un AdminProfile, no ve nada.
                    return base_queryset.none()
            
            # Aplicar filtrado por status a la queryset final (solo para Staff/Superuser)
            status_filter = self.request.query_params.get('status')
            if status_filter and status_filter != 'all':
                return queryset_to_filter.filter(status=status_filter)
            
            return queryset_to_filter

        # 3. Lógica para Usuario Logueado (No-Staff)
        # Solo ve las quejas que reportó.
        return base_queryset.filter(reporter=user)
    
    def perform_create(self, serializer):
        """Asigna automáticamente al usuario logueado como 'reporter' si existe."""
        if self.request.user.is_authenticated:
            # Asignar el usuario logueado como reporter.
            serializer.save(reporter=self.request.user)
        else:
            # Caso en que se permite crear anónimamente (si has_permission se ajusta).
            serializer.save()


# ----------------------------------------------------
# 3. Modelos Anidados (Comentarios)
# ----------------------------------------------------
class CommentViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    """
    API para Comentarios, anidado bajo Queja. 
    Rutas: /api/complaints/{complaint_pk}/comments/
    Permite: Listar (GET), Recuperar (GET por ID), Crear (POST).
    """
    queryset = Comment.objects.all()
    # Lectura para todos, creación solo para autenticados
    permission_classes = [IsAuthenticatedOrReadOnly] 
    
    def get_serializer_class(self):
        """Usa el serializador de escritura para POST y el de lectura para GET."""
        if self.action == 'create':
            return CommentWriteSerializer
        return CommentReadOnlySerializer

    def get_queryset(self):
        """
        Filtra los comentarios por la Queja (complaint_pk). 
        Solo muestra comentarios públicos a usuarios no-staff.
        """
        complaint_pk = self.kwargs.get('complaint_pk')
        if complaint_pk is not None:
            if self.request.user.is_staff:
                # Staff ve todos los comentarios
                return self.queryset.filter(complaint__pk=complaint_pk)
            else:
                # Usuario normal solo ve comentarios públicos
                return self.queryset.filter(complaint__pk=complaint_pk, public=True)
        return self.queryset.none()
        
    def perform_create(self, serializer):
        """Asigna la Queja y el Usuario logueado (si existe) al crear el comentario."""
        complaint_pk = self.kwargs.get('complaint_pk')
        complaint = get_object_or_404(Complaint, pk=complaint_pk)
        
        user = self.request.user if self.request.user.is_authenticated else None
        
        # Si el usuario está autenticado y es staff, el comentario es público por defecto.
        is_public = self.request.user.is_staff if user else False
        
        serializer.save(complaint=complaint, user=user, public=is_public)


# ----------------------------------------------------
# 4. Modelos Anidados (Adjuntos)
# ----------------------------------------------------

class AttachmentViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """
    API CRUD para Adjuntos, anidado bajo Queja. 
    Rutas: /api/complaints/{complaint_pk}/attachments/
    Permite: Listar (GET), Crear (POST), Eliminar (DELETE).
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    # Permiso: Permite leer a todos, subir/eliminar solo a autenticados
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def get_queryset(self):
        """Filtra los adjuntos por la Queja (complaint_pk)."""
        complaint_pk = self.kwargs.get('complaint_pk')
        if complaint_pk is not None:
            return self.queryset.filter(complaint__pk=complaint_pk)
        return self.queryset.none()
        
    def perform_create(self, serializer):
        """Asigna la Queja al crear el adjunto."""
        complaint_pk = self.kwargs.get('complaint_pk')
        complaint = get_object_or_404(Complaint, pk=complaint_pk)
        serializer.save(complaint=complaint)
        
    def destroy(self, request, *args, **kwargs):
        """Solo el staff puede eliminar adjuntos."""
        if not request.user.is_staff:
            return Response(
                {"detail": "No tienes permiso para eliminar adjuntos."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)