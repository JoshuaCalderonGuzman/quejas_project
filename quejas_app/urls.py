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

# ----------------------------------------------------
# 2. Configuración de Rutas del Proyecto (Django HTML y API)
# ----------------------------------------------------
urlpatterns = [
    # Rutas de vistas de Django tradicionales (HTML)
    path('', views.menu_principal, name='menu'),
    path('nueva-queja/', views.nueva_queja, name='nueva_queja'),
    path('mis-quejas/', views.mis_quejas, name='mis_quejas'),
    path('administrador-quejas/', views.administrar_quejas, name='administrador_quejas'),
    
    # Rutas para la API REST. Incluye todas las rutas API.
    # Concatenamos las rutas del router principal y del router anidado para incluirlas en un solo path('api/', ...)
    path('api/', include(router.urls + complaints_router.urls)),
    
    # Rutas para la autenticación de la API
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]