from rest_framework import serializers
from .models import Category, Complaint, Comment, Attachment

# Importamos el modelo de usuario para los campos de relación
from django.contrib.auth import get_user_model
User = get_user_model()


# Serializador de Usuario Básico para mostrar el reporter
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Exponemos solo campos seguros y relevantes para la API
        fields = ('id', 'username', 'first_name', 'last_name')


# 1. Categoría
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# 2. Adjunto
class AttachmentSerializer(serializers.ModelSerializer):
    # Campo de solo lectura para la URL del archivo
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        # El campo 'complaint' se asigna en la vista, no se requiere en la entrada.
        fields = ('id', 'file', 'file_url', 'uploaded_at')
        read_only_fields = ('uploaded_at',)

    def get_file_url(self, obj):
        # Devuelve la URL absoluta del archivo.
        if obj.file:
            return obj.file.url
        return None

# 3. Comentarios (Solo Lectura)
class CommentReadOnlySerializer(serializers.ModelSerializer):
    # Usa el serializador de usuario anidado
    user = UserSerializer(read_only=True) 
    
    # Campo para mostrar quién es el autor (Usuario o Nombre opcional)
    author_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ('id', 'complaint', 'user', 'author', 'author_display', 'message', 'public', 'created_at')
        read_only_fields = ('complaint', 'user', 'created_at', 'author_display')
        
    def get_author_display(self, obj):
        # Muestra el nombre del usuario logueado o el campo 'author' si se proporcionó.
        if obj.user:
            return obj.user.username 
        return obj.author or 'Anónimo'


# 4. Comentarios (Escritura)
class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        # Solo permitimos que se envíe el mensaje y el autor (si es anónimo)
        fields = ('message', 'author')
        # 'complaint', 'user' y 'public' se asignan en la vista (perform_create)

# 5. Queja Principal
class ComplaintSerializer(serializers.ModelSerializer):
    # Usamos serializadores anidados para campos de relación de solo lectura
    category_name = serializers.CharField(source='category.name', read_only=True)
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    
    # Campos anidados para mostrar relaciones (solo lectura)
    attachments = AttachmentSerializer(many=True, read_only=True) 
    
    class Meta:
        model = Complaint
        fields = (
            'id', 'reporter', 'reporter_username', 'title', 'description', 
            'category', 'category_name', 'status', 'assigned_to', 
            'reporter_name', 'reporter_email', 'reporter_phone', 
            'created_at', 'updated_at', 'attachments'
        )
        # ⚠️ CAMBIO CLAVE: Quitamos 'status' y 'assigned_to' de solo lectura.
        # Ahora, solo el campo 'reporter' y las fechas son protegidos.
        # La clase IsStaffOrOwner se encarga de que solo el Staff pueda hacer PATCH en estos campos.
        read_only_fields = ('reporter', 'created_at', 'updated_at')

    # Validación personalizada para asegurar que la categoría existe si se proporciona.
    def validate_category(self, value):
        if value is None:
            return value
        # Verifica que la instancia de Category realmente exista.
        if not Category.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("La categoría seleccionada no existe.")
        return value