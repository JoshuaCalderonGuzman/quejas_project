from django.db import models
from django.conf import settings


#Categoría de la queja
class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)

	class Meta:
		nameC = 'Categorías'

	def __str__(self):
		return self.name


#Queja principal
class Complaint(models.Model):
	STATUS_CHOICES = [
		('new', 'Nueva'),
		('in_progress', 'En progreso'),
		('resolved', 'Resuelta'),
		('rejected', 'Rechazada'),
	]

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
		nameQ = 'Queja(s)'

	def __str__(self):
		return f"{self.title} ({self.get_status_display()})"


#Comentarios sobre la queja
class Comment(models.Model):
	complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='comments')
	author = models.CharField('Autor', max_length=120, blank=True)
	message = models.TextField('Mensaje')
	created_at = models.DateTimeField('Creado', auto_now_add=True)
	public = models.BooleanField('Público', default=False, help_text='Si está marcado, el comentario será visible públicamente')

	class Meta:
		ordering = ['created_at']
		verbose_name_plural = 'Comentario(s)'

	def __str__(self):
		return f"Comentario en {self.complaint} por {self.author or 'Anon'}"


#Adjuntos para una queja
def attachment_upload_path(instance, filename):
    
	return f'complaints/{instance.complaint.id}/{filename}'


class Attachment(models.Model):
	complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name='attachments')
	file = models.FileField('Archivo', upload_to=attachment_upload_path)
	uploaded_at = models.DateTimeField('Subido', auto_now_add=True)

	class Meta:
		verbose_name = 'Adjunto'
		verbose_name_plural = 'Adjuntos'

	def __str__(self):
		return f"Adjunto {self.file.name} para queja {self.complaint.id}"
