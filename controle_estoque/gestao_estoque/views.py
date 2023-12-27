# gestao_estoque/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from produtos.models import Produto  # Ajuste o caminho do import conforme necessário
from django.views.decorators.csrf import csrf_exempt
import json


@login_required
def pagina_inicial(request):
    return render(request, 'gestao_estoque/pagina-inicial.html')


def buscar_produtos(request):
    termo = request.GET.get('termo', '')
    if termo:
        produtos = Produto.objects.filter(nome__icontains=termo).values_list('nome', flat=True)[:10]
        return JsonResponse(list(produtos), safe=False)
    return JsonResponse([], safe=False)

def atualizar_quantidade(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nome_produto = data.get('nome')
        quantidade_adicionar = int(data.get('quantidade'))
        
        try:
            produto = Produto.objects.get(nome__iexact=nome_produto)
            produto.quantidade = quantidade_adicionar
            produto.save()
            return JsonResponse({'success': True})
        except Produto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405)

def diminuir_quantidade(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nome_produto = data.get('nome')
        quantidade_adicionar = int(data.get('quantidade'))
        
        try:
            produto = Produto.objects.get(nome__iexact=nome_produto)
            produto.quantidade -= quantidade_adicionar
            produto.save()
            return JsonResponse({'success': True})
        except Produto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405)