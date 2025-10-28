"""
Definiciones de modelos para la aplicación de Quejas (Complaint System).
Incluye modelos para Categorías, Quejas, Comentarios y Adjuntos.
"""
from django.db import models
from django.contrib.auth import get_user_model 

# Obtenemos el modelo de usuario activo de Django
User = get_user_model()

# --------------------------------------------------------------------
# 1. Categoría
# --------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        # Atributos CORRECTOS
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías' 

    def __str__(self):
        return self.name


# --------------------------------------------------------------------
# 2. Queja Principal
# --------------------------------------------------------------------
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('new', 'Nueva'),
        ('in_progress', 'En progreso'),
        ('resolved', 'Resuelta'),
        ('rejected', 'Rechazada'),
    ]
    
    # Relación con el usuario (puede ser null si la queja es anónima)
    reporter = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reported_complaints',
        verbose_name='Reportado por Usuario'
    )

    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descripción')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')
    reporter_name = models.CharField('Nombre del reportante', max_length=120, blank=True)
    reporter_email = models.EmailField('Email del reportante', blank=True)
    reporter_phone = models.CharField('Teléfono', max_length=30, blank=True)
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    assigned_to = models.CharField('Asignado a', max_length=150, blank=True)

    class Meta:
        ordering = ['-created_at']
        # Atributos CORRECTOS
        verbose_name = 'Queja'
        verbose_name_plural = 'Quejas'

    def __str__(self):
        # pylint: disable=no-member 
        return f"{self.title} ({self.get_status_display()})"


# --------------------------------------------------------------------
# 3. Comentarios sobre la queja
# --------------------------------------------------------------------
class Comment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Usuario Comentador", 
        related_name="user_comments", 
        null=True, 
        blank=True
    )
    
    author = models.CharField('Autor (Opcional)', max_length=120, blank=True)
    message = models.TextField('Mensaje')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    public = models.BooleanField('Público', default=False, help_text='Si está marcado, el comentario será visible públicamente')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios' 

    def __str__(self):
        author_display = self.user.username if self.user else self.author or 'Anónimo'
        complaint_title = getattr(self.complaint, 'title', 'Queja Eliminada')
        return f"Comentario en '{complaint_title}' por {author_display}"


# --------------------------------------------------------------------
# 4. Adjuntos para una queja
# --------------------------------------------------------------------
def attachment_upload_path(instance, filename):
    # pylint: disable=no-member 
    complaint_pk = getattr(instance.complaint, 'pk', 'unknown')
    return f'complaints/{complaint_pk}/{filename}'


class Attachment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField('Archivo', upload_to=attachment_upload_path)
    uploaded_at = models.DateTimeField('Subido', auto_now_add=True)

    class Meta:
        verbose_name = 'Adjunto'
        verbose_name_plural = 'Adjuntos'

    def __str__(self):
        complaint_id = getattr(self.complaint, 'pk', 'N/A')
        return f"Adjunto {self.file.name} para queja {complaint_id}"
# --------------------------------------------------------------------
# 5. Perfil de Administrador (para filtrar por Categoría) <-- ¡NUEVO!
# --------------------------------------------------------------------
class AdminProfile(models.Model):
    """
    Extiende el modelo User para definir qué categorías puede administrar.
    Debe crearse una instancia para cada usuario staff que deba tener acceso restringido.
    """
    # Enlaza al usuario de Django (relación uno a uno).
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Categorías que este administrador puede ver/gestionar.
    # Uso de ManyToManyField para que un admin pueda tener muchas categorías.
    categories = models.ManyToManyField(
        Category, 
        blank=True, 
        related_name='administrators', 
        verbose_name='Categorías Asignadas'
    )
    
    class Meta:
        verbose_name = 'Perfil de Administrador'
        verbose_name_plural = 'Perfiles de Administradores'
        
    def __str__(self):
        is_staff_status = " (Staff)" if self.user.is_staff else " (NO Staff)"
        return f"Perfil Admin: {self.user.username}{is_staff_status}"