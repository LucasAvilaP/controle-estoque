from django.contrib.auth import authenticate, logout, login
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
import json

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        # Aqui você pode usar o login do Django para iniciar a sessão,
        # ou retornar um token JWT, dependendo da sua abordagem de autenticação
        return JsonResponse({'message': 'Login bem-sucedido'}, status=200)
    return JsonResponse({'error': 'Login inválido'}, status=400)
    

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Logout bem-sucedido'}, status=200)

@require_http_methods(["GET", "POST"])
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Depuração: Imprimir os valores para verificar
        print("Tentativa de login com:", username, password)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('pagina_inicial')
            else:
                return JsonResponse({'error': 'Conta inativa'}, status=400)
        else:
            return JsonResponse({'error': 'Login inválido'}, status=400)
    else:
        return render(request, 'autenticacao/login.html')