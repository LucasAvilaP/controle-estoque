# views.py dentro do seu app 'produtos'

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import ObjectDoesNotExist
from .models import Produto

@require_http_methods(["GET"])
def listar_produtos(request):
    termo_busca = request.GET.get('q', '')
    if termo_busca:
        produtos = Produto.objects.filter(nome__icontains=termo_busca).values('id', 'nome', 'tipo', 'quantidade')
    else:
        produtos = Produto.objects.all().values('id', 'nome', 'tipo', 'quantidade')
    return JsonResponse(list(produtos), safe=False)

@require_http_methods(["GET"])
def informacao_produto_por_nome(request):
    nome_produto = request.GET.get('nome', None)
    if nome_produto:
        try:
            produto = Produto.objects.get(nome__iexact=nome_produto)
            produto_info = {
                'id': produto.id,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'quantidade': produto.quantidade,
                'data_entrada': produto.data_entrada.strftime('%Y-%m-%d')
            }
            return JsonResponse(produto_info)
        except Produto.DoesNotExist:
            return JsonResponse({'erro': 'Produto não encontrado'}, status=404)
    return JsonResponse({'erro': 'Nome do produto não fornecido'}, status=400)

@require_POST
def atualizar_quantidade(request, nome_produto):
    try:
        quantidade = int(request.POST.get('quantidade', 0))
        produto = Produto.objects.get(nome__iexact=nome_produto)
        produto.quantidade += quantidade  # quantidade pode ser positiva ou negativa
        if produto.quantidade < 0:
            return JsonResponse({'erro': 'Não é possível ter quantidade negativa'}, status=400)
        produto.save()
        return JsonResponse({'mensagem': 'Atualização realizada com sucesso', 'nova_quantidade': produto.quantidade})
    except Produto.DoesNotExist:
        return JsonResponse({'erro': 'Produto não encontrado'}, status=404)
    except ValueError:
        return JsonResponse({'erro': 'Quantidade inválida'}, status=400)


