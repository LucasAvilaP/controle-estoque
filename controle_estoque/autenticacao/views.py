from django.contrib.auth import authenticate, logout
from django.http import JsonResponse
from rest_framework.decorators import api_view

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