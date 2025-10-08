from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu_principal, name='menu'),
    path('nueva-queja/', views.nueva_queja, name='nueva_queja'),
]