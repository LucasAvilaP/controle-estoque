# views.py dentro do seu app 'produtos'

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.exceptions import ObjectDoesNotExist
from .models import Produto, EstoqueProduto

@require_http_methods(["GET"])
def listar_produtos(request):
    restaurante_id = request.session.get('restaurante_id')
    termo_busca = request.GET.get('termo', '')

    if restaurante_id:
        # Filtrar produtos com base no restaurante selecionado
        query = EstoqueProduto.objects.filter(local_id=restaurante_id).select_related('produto')
        if termo_busca:
            query = query.filter(produto__nome__icontains=termo_busca)
        produtos = query.values('produto__id', 'produto__nome', 'produto__tipo', 'quantidade')
    else:
        # Se nenhum restaurante for selecionado, retorne uma lista vazia ou todos os produtos, dependendo da sua lógica de negócios
        produtos = []

    return JsonResponse(list(produtos), safe=False)

@require_http_methods(["GET"])
def informacao_produto_por_nome(request):
    restaurante_id = request.session.get('restaurante_id')
    nome_produto = request.GET.get('nome', None)

    if nome_produto and restaurante_id:
        try:
            produto = Produto.objects.get(nome__iexact=nome_produto, estoque__local_id=restaurante_id)
            produto_info = {
                'id': produto.id,
                'nome': produto.nome,
                'tipo': produto.tipo,
                'quantidade': produto.quantidade,
                'data_entrada': produto.data_entrada.strftime('%Y-%m-%d')
            }
            return JsonResponse(produto_info)
        except Produto.DoesNotExist:
            return JsonResponse({'erro': 'Produto não encontrado ou não disponível para o restaurante'}, status=404)
    return JsonResponse({'erro': 'Nome do produto não fornecido ou restaurante não selecionado'}, status=400)

@require_POST
def atualizar_quantidade(request, nome_produto):
    restaurante_id = request.session.get('restaurante_id')
    
    if not restaurante_id:
        return JsonResponse({'erro': 'Restaurante não selecionado'}, status=400)

    try:
        quantidade = int(request.POST.get('quantidade', 0))
        estoque = EstoqueProduto.objects.get(produto__nome__iexact=nome_produto, local_id=restaurante_id)
        estoque.quantidade += quantidade  # quantidade pode ser positiva ou negativa
        if estoque.quantidade < 0:
            return JsonResponse({'erro': 'Não é possível ter quantidade negativa no estoque'}, status=400)
        estoque.save()
        return JsonResponse({'mensagem': 'Atualização realizada com sucesso', 'nova_quantidade': estoque.quantidade})
    except EstoqueProduto.DoesNotExist:
        return JsonResponse({'erro': 'Produto não encontrado ou não disponível no restaurante selecionado'}, status=404)
    except ValueError:
        return JsonResponse({'erro': 'Quantidade inválida'}, status=400)


