from django.contrib.auth import authenticate, logout, login
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
import json
from gestao_estoque.models import Restaurante
from .models import AcessoRestaurante

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    restaurante_nome = request.data.get('restaurante')
    
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)

        # Encontrar o restaurante com base no nome
        try:
            restaurante = Restaurante.objects.get(nome=restaurante_nome)
            request.session['restaurante_id'] = restaurante.id
        except Restaurante.DoesNotExist:
            return JsonResponse({'error': 'Restaurante inválido'}, status=400)
        
        return JsonResponse({'message': 'Login bem-sucedido', 'redirect_url': '/pagina_inicial/'}, status=200)
    else:
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
        restaurante_nome = request.POST.get('restaurante')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            try:
                restaurante = Restaurante.objects.get(nome=restaurante_nome)
                # Verifica se o usuário tem acesso ao restaurante selecionado
                if not AcessoRestaurante.objects.filter(usuario=user, restaurante=restaurante).exists():
                    # Se o usuário não tem acesso, retorna um erro
                    return JsonResponse({'error': 'Você não tem acesso a este restaurante.'}, status=403)
                
                login(request, user)
                request.session['restaurante_id'] = restaurante.id
                return JsonResponse({'redirect': True, 'redirect_url': '/pagina_inicial/'})
            except Restaurante.DoesNotExist:
                return JsonResponse({'error': 'Restaurante selecionado não existe.'}, status=400)
        else:
            return JsonResponse({'error': 'Usuário ou senha inválidos.'}, status=400)
    else:
        return render(request, 'autenticacao/login.html')