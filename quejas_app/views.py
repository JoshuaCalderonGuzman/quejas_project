from django.shortcuts import render

# Create your views here.
def menu_principal(request):
    return render(request, 'menu.html')

def nueva_queja(request):
    if request.method == 'POST':
        pass
    return render(request, 'nueva_queja.html')