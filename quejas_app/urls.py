"""
URLs de la aplicación 'quejas_app'.

Contiene las rutas para las vistas HTML (Django) y los endpoints REST (DRF).
"""
from django.urls import path, include
from rest_framework_nested import routers
from . import views 
from . import api_views 

# ----------------------------------------------------
# 1. Configuración de Rutas de la API (DRF)
# ----------------------------------------------------
# Router principal para rutas de nivel superior (Categories, Complaints)
router = routers.DefaultRouter()
router.register(r'categories', api_views.CategoryViewSet, basename='category')
router.register(r'complaints', api_views.ComplaintViewSet, basename='complaint')

# Router anidado para comentarios y adjuntos (dependen de una Queja)
complaints_router = routers.NestedSimpleRouter(router, r'complaints', lookup='complaint')
complaints_router.register(r'comments', api_views.CommentViewSet, basename='complaint-comments')
complaints_router.register(r'attachments', api_views.AttachmentViewSet, basename='complaint-attachments')

# Juntamos todas las rutas REST en una sola lista para el include.
API_URLPATTERNS = router.urls + complaints_router.urls


# ----------------------------------------------------
# 2. Configuración de Rutas del Proyecto (Django HTML y API)
# ----------------------------------------------------

# Este es el urlpatterns que se incluye en el archivo principal del proyecto
urlpatterns = [
    # Rutas de vistas de Django tradicionales (HTML)
    path('', views.menu_principal, name='menu'),
    path('nueva-queja/', views.nueva_queja, name='nueva_queja'),
    path('mis-quejas/', views.mis_quejas, name='mis_quejas'),
    path('administrador-quejas/', views.administrar_quejas, name='administrador_quejas'),
    
    # Rutas para la API REST. Se incluyen bajo el prefijo 'api/'
    path('api/', include(API_URLPATTERNS)),
]
