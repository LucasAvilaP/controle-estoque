# gestao_estoque/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from produtos.models import Produto  # Ajuste o caminho do import conforme necessário


@login_required
def pagina_inicial(request):
    return render(request, 'gestao_estoque/pagina-inicial.html')


def buscar_produtos(request):
    termo = request.GET.get('termo', '')
    if termo:
        produtos = Produto.objects.filter(nome__icontains=termo).values_list('nome', flat=True)[:10]
        return JsonResponse(list(produtos), safe=False)
    return JsonResponse([], safe=False)