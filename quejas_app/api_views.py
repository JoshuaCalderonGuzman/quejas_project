"""
ViewSets de Django REST Framework para la API del Sistema de Quejas.
Define las reglas de negocio, permisos y filtrado para cada modelo.
"""
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny, BasePermission
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q 

# Importamos todos los modelos y serializadores (incluye AdminProfile)
from .models import Category, Complaint, Comment, Attachment, AdminProfile
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
    - Modificación (PUT/PATCH) solo si el usuario es el dueño (reporter).
    - Eliminación (DELETE) solo si el usuario es STAFF.
    """
    def has_permission(self, request, view):
        # Permite listar (GET) y crear (POST) a usuarios autenticados
        if view.action in ['list', 'create']:
            return request.user and request.user.is_authenticated
        
        # Para métodos de lectura
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        
        # Para los demás métodos se delega a has_object_permission
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # STAFF: acceso total
        if request.user.is_staff:
            return True
        
        # Solo lectura
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated
        
        # Modificar (PUT/PATCH): solo si es el dueño (reporter)
        if request.method in ['PUT', 'PATCH']:
            return obj.reporter == request.user
        
        # Eliminar (DELETE): solo staff
        if request.method == 'DELETE':
            return False
        
        return False

# ----------------------------------------------------------------------
# VIEWS: Categories
# ----------------------------------------------------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    """API CRUD para Categorías."""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ----------------------------------------------------------------------
# VIEWS: Complaints
# ----------------------------------------------------------------------
class ComplaintViewSet(viewsets.ModelViewSet):
    """
    API CRUD para Quejas.
    Permite filtrar por status y búsqueda por texto.
    """
    serializer_class = ComplaintSerializer
    permission_classes = [IsStaffOrOwner]
    
    def get_queryset(self):
        user = self.request.user
        
        # 1. Base del queryset: Solo staff ve todas las quejas, otros solo las suyas.
        if user.is_staff:
            queryset = Complaint.objects.all()
        elif user.is_authenticated:
            queryset = Complaint.objects.filter(reporter=user)
        else:
            return Complaint.objects.none()

        # 2. Aplicar el filtro de status si está presente en la URL.
        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'all':
            # Solo filtramos si el parámetro es válido y no es 'all'
            queryset = queryset.filter(status=status_param)
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        reporter = self.request.user if self.request.user.is_authenticated else None
        serializer.save(reporter=reporter)

# ----------------------------------------------------------------------
# VIEWS: Comments
# ----------------------------------------------------------------------
class CommentViewSet(mixins.ListModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    """
    API CRUD para Comentarios, anidado bajo Queja.
    Rutas: /api/complaints/{complaint_pk}/comments/
    """
    queryset = Comment.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentWriteSerializer
        return CommentReadOnlySerializer

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        complaint_pk = self.kwargs.get('complaint_pk')
        
        if complaint_pk is not None:
            # Filtra los comentarios que pertenecen a la queja en la URL
            return self.queryset.filter(complaint__pk=complaint_pk).order_by('created_at')
            
        return self.queryset.none()
        
    def perform_create(self, serializer):
        complaint_pk = self.kwargs.get('complaint_pk')
        complaint = get_object_or_404(Complaint, pk=complaint_pk)
        serializer.save(user=self.request.user, complaint=complaint)

# ----------------------------------------------------------------------
# VIEWS: Attachments
# ----------------------------------------------------------------------
class AttachmentViewSet(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        viewsets.GenericViewSet):
    """
    API CRUD para Adjuntos, anidado bajo Queja.
    Rutas: /api/complaints/{complaint_pk}/attachments/
    """
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def get_queryset(self):
        complaint_pk = self.kwargs.get('complaint_pk')
        if complaint_pk is not None:
            return self.queryset.filter(complaint__pk=complaint_pk)
        return self.queryset.none()
        
    def perform_create(self, serializer):
        complaint_pk = self.kwargs.get('complaint_pk')
        complaint = get_object_or_404(Complaint, pk=complaint_pk)
        serializer.save(complaint=complaint)
        
    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Solo el personal de Staff puede eliminar adjuntos."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)