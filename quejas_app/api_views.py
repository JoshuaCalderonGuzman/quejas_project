"""
ViewSets de Django REST Framework para la API del Sistema de Quejas.
Define las reglas de negocio, permisos y filtrado para cada modelo.
"""
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q # Importado para futuras lógicas de filtrado

# Importamos todos los modelos y serializadores (asumimos que existen)
from .models import Category, Complaint, Comment, Attachment
from .serializers import (
    CategorySerializer, 
    ComplaintSerializer, 
    CommentReadOnlySerializer, 
    CommentWriteSerializer,
    AttachmentSerializer
)

# ----------------------------------------------------
# 1. Modelo Básico (CRUD completo)
# ----------------------------------------------------

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API CRUD completo para Categorías. 
    Rutas: /api/categories/
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    # Permiso: Permite leer a todos, escribir/modificar solo a autenticados
    permission_classes = [IsAuthenticatedOrReadOnly] 

# ----------------------------------------------------
# 2. Modelo Principal (CRUD completo y filtrado)
# ----------------------------------------------------

class ComplaintViewSet(viewsets.ModelViewSet):
    """
    API CRUD completo para Quejas. 
    Rutas: /api/complaints/
    """
    # Consulta base para todos los complaints, ordenado por fecha de creación descendente
    # La consulta final será ajustada en get_queryset
    queryset = Complaint.objects.all().order_by('-created_at')
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario logueado como reporter si está autenticado.
        Si es anónimo, se asegura de que los campos de contacto se manejen correctamente.
        """
        user = self.request.user
        reporter = user if user.is_authenticated else None
        
        # Si el usuario está autenticado, asigna el reporter y borra cualquier info anónima
        if reporter:
            serializer.save(reporter=reporter, reporter_name="", reporter_email="", reporter_phone="")
        else:
            # Si es anónimo (reporter=None), DRF se encarga de que al menos 
            # reporter_name o reporter_email hayan sido proporcionados a través del Serializer.
            # Aquí solo se asigna el reporter como None.
            serializer.save(reporter=None)
        
    def get_queryset(self):
        """
        Define qué complaints puede ver el usuario basado en su autenticación y rol,
        e implementa el filtrado por 'status' solo para usuarios staff.
        """
        user = self.request.user
        queryset = Complaint.objects.all().order_by('-created_at')
        
        # 1. Lógica para usuarios staff/admin: ven todas las quejas y pueden filtrar
        if user.is_staff:
            status_filter = self.request.query_params.get('status')
            if status_filter:
                # Si se proporciona un filtro de estado, se aplica.
                queryset = queryset.filter(status=status_filter)
            return queryset
        
        # 2. Lógica para usuarios autenticados (no staff): solo ven sus propias quejas
        if user.is_authenticated:
            # Usuarios autenticados solo ven las quejas que ellos reportaron
            return Complaint.objects.filter(reporter=user).order_by('-created_at')
            
        # 3. Usuarios anónimos: No ven ninguna queja en el listado (GET List)
        return Complaint.objects.none()

# ----------------------------------------------------
# 3. Modelo Relacionado (Comentarios - Anidado)
# ----------------------------------------------------

class CommentViewSet(mixins.ListModelMixin, 
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     viewsets.GenericViewSet):
    """
    API CRUD para Comentarios, anidado bajo Queja.
    Rutas: /api/complaints/{complaint_pk}/comments/
    Permite: Listar, Recuperar, Crear, Eliminar.
    """
    # Queryset base, que se filtrará en get_queryset
    queryset = Comment.objects.all()
    
    def get_serializer_class(self):
        """Usa el serializador de escritura para POST y el de lectura para GET/otros."""
        if self.request.method == 'POST':
            return CommentWriteSerializer
        return CommentReadOnlySerializer

    def get_queryset(self):
        """
        Filtra los comentarios por la Queja (complaint_pk) y por estado público/privado.
        """
        complaint_pk = self.kwargs.get('complaint_pk')
        if complaint_pk is not None:
            qs = self.queryset.filter(complaint__pk=complaint_pk)
            
            # Lógica de visibilidad: 
            # Si el usuario NO es staff, solo ve comentarios públicos (public=True).
            if not self.request.user.is_staff:
                qs = qs.filter(public=True)
            
            return qs.order_by('created_at')
            
        return self.queryset.none() # Si no hay PK, no devuelve nada
        
    def perform_create(self, serializer):
        """Asigna la Queja y el Usuario al crear el comentario."""
        complaint_pk = self.kwargs.get('complaint_pk')
        # Garantiza que la queja exista, o devuelve 404
        complaint = get_object_or_404(Complaint, pk=complaint_pk)
        
        # Asigna el usuario si está autenticado
        user = self.request.user if self.request.user.is_authenticated else None
        
        # Si el usuario está autenticado, asigna el campo 'user' y vacía 'author'
        if user:
            # El campo 'author' en el modelo Comment se vacía si hay un usuario registrado
            serializer.save(complaint=complaint, user=user, author="") 
        else:
            # Si es anónimo, usa el campo 'author' que debería venir en el serializer.
            serializer.save(complaint=complaint, user=None)
            
    def destroy(self, request, *args, **kwargs):
        """Solo el staff puede eliminar comentarios."""
        if not request.user.is_staff:
            return Response(
                {"detail": "No tiene permiso para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

# ----------------------------------------------------
# 4. Modelo Relacionado (Adjuntos - Anidado)
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
                {"detail": "No tiene permiso para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
