from django.contrib import admin
from . import models


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'description')
	search_fields = ('name',)


@admin.register(models.Complaint)
class ComplaintAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'status', 'reporter_name', 'created_at')
	list_filter = ('status', 'category', 'created_at')
	search_fields = ('title', 'description', 'reporter_name', 'reporter_email')
	readonly_fields = ('created_at', 'updated_at')


@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
	list_display = ('complaint', 'author', 'public', 'created_at')
	list_filter = ('public', 'created_at')
	search_fields = ('author', 'message')


@admin.register(models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
	list_display = ('complaint', 'file', 'uploaded_at')
	readonly_fields = ('uploaded_at',)
