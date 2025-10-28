from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, Complaint, Comment, Attachment

User = get_user_model()

# ----------------------------------------------------------------------
# 1. Serializer para Modelos Relacionados Anidados (Lectura)
# ----------------------------------------------------------------------

class CommentReadOnlySerializer(serializers.ModelSerializer):
    """
    Serializador de LECTURA para Comentarios.
    Usado para anidar información de comentarios dentro de una Queja.
    """
    # Determina el nombre del autor a mostrar.
    author_display = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        # Excluye el campo 'complaint' para evitar redundancia al anidar.
        exclude = ('complaint',) 
        
    def get_author_display(self, obj):
        """Devuelve el username si hay usuario, sino el campo 'author', sino 'Anónimo'."""
        return obj.user.username if obj.user else obj.author or 'Anónimo'

class AttachmentSerializer(serializers.ModelSerializer):
    """
    Serializador para Adjuntos. Se usa para crear, listar y eliminar adjuntos.
    """
    class Meta:
        model = Attachment
        # Incluye todos los campos, el campo 'file' manejará la subida de archivos.
        fields = '__all__'
        read_only_fields = ('uploaded_at', 'complaint') # 'complaint' se establece en la vista.

# ----------------------------------------------------------------------
# 2. Serializer para Modelos Básicos (CRUD completo)
# ----------------------------------------------------------------------

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Category. Permite CRUD completo.
    """
    class Meta:
        model = Category
        fields = '__all__' 


class CommentWriteSerializer(serializers.ModelSerializer):
    """
    Serializador de ESCRITURA para Comentarios (POST/PUT/PATCH).
    Permite establecer los campos necesarios para crear o modificar un comentario.
    """
    class Meta:
        model = Comment
        # Incluye 'complaint' y 'user', aunque se suelen asignar en la vista
        # por seguridad al crear, es necesario que existan aquí.
        fields = ('id', 'complaint', 'user', 'author', 'message', 'public')

# ----------------------------------------------------------------------
# 3. Serializer para el Modelo Principal (Complaint - Lectura/Escritura)
# ----------------------------------------------------------------------

class ComplaintSerializer(serializers.ModelSerializer):
    """
    Serializador principal para el modelo Complaint.
    Incluye campos de solo lectura para la categoría y el reportante.
    Muestra comentarios anidados (solo lectura).
    """
    # Campo de solo lectura para mostrar el nombre de la categoría
    category_name = serializers.ReadOnlyField(source='category.name') 
    
    # Campo de solo lectura para mostrar el username del reportante
    reporter_username = serializers.SerializerMethodField()
    
    # Comentarios anidados (solo lectura de los comentarios públicos)
    comments = CommentReadOnlySerializer(many=True, read_only=True)
    
    # Adjuntos anidados (solo lectura)
    attachments = AttachmentSerializer(many=True, read_only=True)


    class Meta:
        model = Complaint
        fields = ('id', 'title', 'description', 
                  'category', 'category_name', # FK y nombre de la categoría
                  'reporter', 'reporter_username', # FK y nombre del usuario reportante
                  'reporter_name', 'reporter_email', 'reporter_phone', 
                  'status', 'created_at', 'updated_at', 'assigned_to', 
                  'comments', 'attachments')
                  
        # Campos que la API maneja automáticamente o que no deben ser modificados por el cliente.
        read_only_fields = ('created_at', 'updated_at', 'status')
        
    def get_reporter_username(self, obj):
        """Devuelve el username del reportante si existe, sino None."""
        return obj.reporter.username if obj.reporter else None
