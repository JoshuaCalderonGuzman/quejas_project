"""
Definiciones de modelos para la aplicación de Quejas (Complaint System).
Incluye modelos para Categorías, Quejas, Comentarios y Adjuntos.
"""
from django.db import models
from django.contrib.auth import get_user_model 

# Obtenemos el modelo de usuario activo de Django
User = get_user_model()

# Categoría de la queja
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        # Uso de atributos estándar de Django para nombres legibles
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías' 

    def __str__(self):
        return self.name


# Queja principal
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('new', 'Nueva'),
        ('in_progress', 'En progreso'),
        ('resolved', 'Resuelta'),
        ('rejected', 'Rechazada'),
    ]
    
    # Relación con el usuario logueado (opcional si la queja es anónima)
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
        # Uso de atributos estándar de Django para nombres legibles
        verbose_name = 'Queja'
        verbose_name_plural = 'Quejas'

    def __str__(self):
        # Deshabilitamos Pylint solo para este método, ya que get_status_display es generado por Django
        # pylint: disable=no-member 
        return f"{self.title} ({self.get_status_display()})"


# Comentarios sobre la queja
class Comment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
    
    # Usamos User para saber quién hizo el comentario
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Usuario Comentador", 
        related_name="user_comments", 
        null=True, 
        blank=True
    )
    
    # Campo para comentarios anónimos o no vinculados a un usuario registrado
    author = models.CharField('Autor (Opcional)', max_length=120, blank=True)
    
    message = models.TextField('Mensaje')
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    public = models.BooleanField('Público', default=False, help_text='Si está marcado, el comentario será visible públicamente')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios' 

    def __str__(self):
        # Uso seguro para evitar errores si la relación es nula o se elimina
        author_display = self.user.username if self.user else self.author or 'Anónimo'
        complaint_title = getattr(self.complaint, 'title', 'Queja Eliminada')
        return f"Comentario en '{complaint_title}' por {author_display}"


# Adjuntos para una queja
def attachment_upload_path(instance, filename):
    
    # Asegura que el ID de la queja sea usado en la ruta del archivo
    # Utilizamos .pk en lugar de .id para mayor seguridad y silenciamos Pylint.
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
        # Uso seguro para evitar fallos de __str__
        complaint_id = getattr(self.complaint, 'pk', 'N/A')
        return f"Adjunto {self.file.name} para queja {complaint_id}"
