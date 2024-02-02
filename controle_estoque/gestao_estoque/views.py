# gestao_estoque/views.py

import csv
import xlsxwriter
from datetime import date
from django.shortcuts import render
from django.db import transaction
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse, HttpResponse
from produtos.models import Produto, HistoricoContagem, EstoqueProduto
from django.views.decorators.csrf import csrf_exempt
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from gestao_estoque.models import Local, Transacao
from .models import HistoricoLog
from django.utils import timezone
from django.db import models
import json
from . import views




@login_required
def pagina_inicial(request):
    restaurante_id = request.session.get('restaurante_id')

    if restaurante_id:
        produtos_abaixo_do_minimo = EstoqueProduto.objects.filter(
            local_id=restaurante_id,
            quantidade__lt=models.F('produto__nivel_minimo')
        )
        alertas = [f"O produto {estoque.produto.nome} está abaixo do nível mínimo de estoque!" for estoque in produtos_abaixo_do_minimo]
    else:
        alertas = ['Nenhum restaurante selecionado.']

    return render(request, 'gestao_estoque/pagina-inicial.html', {'alertas': alertas})


def buscar_produtos(request):
    termo = request.GET.get('termo', '')
    restaurante_id = request.session.get('restaurante_id')

    if termo and restaurante_id:
        produtos = EstoqueProduto.objects.filter(
            produto__nome__icontains=termo,
            local__restaurante_id=restaurante_id
        ).values_list('produto__nome', flat=True)[:10]
        return JsonResponse(list(produtos), safe=False)

    return JsonResponse([], safe=False)


@require_http_methods(["POST"])
def atualizar_quantidade(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    quantidade_adicionar = int(data.get('quantidade'))
    restaurante_id = request.session.get('restaurante_id')

    if not restaurante_id:
        return JsonResponse({'success': False, 'error': 'Restaurante não selecionado.'}, status=400)

    try:
        estoque = EstoqueProduto.objects.get(produto__nome__iexact=nome_produto, local_id=restaurante_id)
        estoque.quantidade += quantidade_adicionar  # Ajusta a quantidade no estoque do restaurante
        if estoque.quantidade < 0:
            return JsonResponse({'success': False, 'error': 'Não é possível ter quantidade negativa no estoque.'}, status=400)
        estoque.save()

        return JsonResponse({'success': True})
    except EstoqueProduto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produto não encontrado ou não disponível no restaurante.'}, status=404)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Quantidade inválida.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
   

@require_POST
def diminuir_quantidade(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    quantidade_diminuir = int(data.get('quantidade'))
    restaurante_id = request.session.get('restaurante_id')

    if not restaurante_id:
        return JsonResponse({'success': False, 'error': 'Restaurante não selecionado.'}, status=400)

    try:
        estoque = EstoqueProduto.objects.get(produto__nome__iexact=nome_produto, local_id=restaurante_id)
        if estoque.quantidade < quantidade_diminuir:
            return JsonResponse({'success': False, 'error': 'Quantidade insuficiente no estoque.'}, status=400)

        estoque.quantidade -= quantidade_diminuir
        estoque.save()

        HistoricoLog.objects.create(
            produto=estoque.produto,
            usuario=request.user,
            quantidade=quantidade_diminuir,
            tipo='Remoção',
            local_id=restaurante_id
        )

        return JsonResponse({'success': True})
    except EstoqueProduto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produto não encontrado ou não disponível no restaurante.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Valor inválido para quantidade.'}, status=400)

    return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405)




@require_POST
@login_required
def realizar_emprestimo(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    quantidade = int(data.get('quantidade'))
    restaurante_id = request.session.get('restaurante_id')
    usuario = request.user

    estoque_central = get_object_or_404(Local, nome='Estoque Central')
    estoque_central_id = estoque_central.id

    with transaction.atomic():
        try:
            # Diminui a quantidade no estoque central
            estoque_central_produto = EstoqueProduto.objects.select_for_update().get(
                produto__nome__iexact=nome_produto, local_id=estoque_central_id
            )

            if estoque_central_produto.quantidade < quantidade:
                return JsonResponse({'success': False, 'error': 'Estoque central não possui quantidade suficiente.'})
            
            estoque_central_produto.quantidade -= quantidade
            estoque_central_produto.save()

            # Aumenta a quantidade no estoque do restaurante
            estoque_restaurante_produto = EstoqueProduto.objects.select_for_update().get(
                produto__nome__iexact=nome_produto, local__restaurante__id=restaurante_id
            )
            estoque_restaurante_produto.quantidade += quantidade
            estoque_restaurante_produto.save()

            # Registra a transação de empréstimo no modelo Transacao
            Transacao.objects.create(
                produto=estoque_central_produto.produto,
                usuario=usuario,
                quantidade=quantidade,
                tipo='EM',
                origem=estoque_central,
                destino=estoque_restaurante_produto.local,
                restaurante=estoque_restaurante_produto.local.restaurante
            )

            return JsonResponse({'success': True, 'message': 'Empréstimo realizado com sucesso.'})

        except EstoqueProduto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado ou não disponível.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Erro ao processar o empréstimo.'})





@require_POST
@login_required
def realizar_devolucao(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    quantidade = int(data.get('quantidade'))
    restaurante_id = request.session.get('restaurante_id')
    usuario = request.user

    estoque_central = get_object_or_404(Local, nome='Estoque Central')
    estoque_central_id = estoque_central.id

    with transaction.atomic():
        try:
            # Aumenta a quantidade no estoque central
            estoque_central_produto = EstoqueProduto.objects.select_for_update().get(
                produto__nome__iexact=nome_produto, local_id=estoque_central_id
            )
            estoque_central_produto.quantidade += quantidade
            estoque_central_produto.save()

            # Diminui a quantidade no estoque do restaurante
            estoque_restaurante_produto = EstoqueProduto.objects.select_for_update().get(
                produto__nome__iexact=nome_produto, local__restaurante__id=restaurante_id
            )

            if estoque_restaurante_produto.quantidade < quantidade:
                return JsonResponse({'success': False, 'error': 'Quantidade insuficiente no estoque do restaurante.'})
            
            estoque_restaurante_produto.quantidade -= quantidade
            estoque_restaurante_produto.save()

            # Registra a transação de devolução no modelo Transacao
            Transacao.objects.create(
                produto=estoque_central_produto.produto,
                usuario=usuario,
                quantidade=quantidade,
                tipo='DE',
                origem=estoque_restaurante_produto.local,
                destino=estoque_central,
                restaurante=estoque_restaurante_produto.local.restaurante
            )

            return JsonResponse({'success': True, 'message': 'Devolução realizada com sucesso.'})

        except EstoqueProduto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado ou não disponível.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'Erro ao processar a devolução.'})




    


def exportar_produtos_xlsx(request):
    restaurante_id = request.session.get('restaurante_id')
    hoje = date.today()

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="relatorio_produtos.xlsx"'

    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    worksheet.write('A1', 'Nome do Produto')
    worksheet.write('B1', 'Quantidade Atual')
    worksheet.write('C1', 'Última Contagem')
    worksheet.write('D1', 'Diferença')

    if restaurante_id:
        estoque_produtos = EstoqueProduto.objects.filter(local_id=restaurante_id)
        for idx, estoque in enumerate(estoque_produtos, start=1):
            produto = estoque.produto
            ultima_contagem = HistoricoContagem.objects.filter(produto=produto, data_contagem__lt=hoje).order_by('-data_contagem').first()
            diferenca = estoque.quantidade - (ultima_contagem.quantidade_contagem if ultima_contagem else estoque.quantidade)

            worksheet.write(idx, 0, produto.nome)
            worksheet.write(idx, 1, estoque.quantidade)
            worksheet.write(idx, 2, ultima_contagem.quantidade_contagem if ultima_contagem else 'N/A')
            worksheet.write(idx, 3, diferenca if diferenca != 0 else '-')

    workbook.close()
    return response