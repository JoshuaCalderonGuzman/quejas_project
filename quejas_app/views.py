from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required

#vista principal
def menu_principal(request):
    return render(request, 'menu.html')

#Vistas de usuario
@login_required
def nueva_queja(request):
    if request.method == 'POST':
        #Lógica para procesar la nueva queja
        pass
    return render(request, 'nueva_queja.html')

@login_required
def mis_quejas(request):
    #Lógica para mostrar las quejas del usuario actual
    return render(request, 'mis_quejas.html')

# Vista administrativa: REQUIERE autenticación y un permiso específico (Autorización)
#'quejas_app.puede_administrar' es un permiso de ejemplo que debes definir en el modelo.
@permission_required('quejas_app.puede_administrar', raise_exception=True)
def administrar_quejas(request):
    #Solo los usuarios con el permiso 'puede_administrar' llegarán a esta línea
    return render(request, 'administrador_quejas.html')