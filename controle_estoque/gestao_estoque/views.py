# gestao_estoque/views.py

import csv
import xlsxwriter
from datetime import date
import logging
from django.shortcuts import render
from django.db import transaction
from django.db.models import F, Q
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse, HttpResponse
from produtos.models import Produto, HistoricoContagem, EstoqueProduto, Local
from django.views.decorators.csrf import csrf_exempt
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, redirect
from gestao_estoque.models import Local, Transacoe, Restaurante
from .models import HistoricoLog
from django.utils import timezone
from django.contrib import messages
from django.db import models
from logging import Logger
from io import BytesIO
import json
from . import views

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@login_required
def pagina_inicial(request):
    restaurante_id = request.session.get('restaurante_id')
    restaurante_nome = None  # Inicialize com None para o caso de não ter um restaurante selecionado

    if restaurante_id:
        restaurante = Restaurante.objects.get(id=restaurante_id)
        restaurante_nome = restaurante.nome
        produtos_abaixo_do_minimo = EstoqueProduto.objects.filter(
            local_id=restaurante_id,
            quantidade__lt=models.F('produto__nivel_minimo')
        )
        alertas = [f"O produto {estoque.produto.nome} está abaixo do nível mínimo de estoque!" for estoque in produtos_abaixo_do_minimo]
    else:
        alertas = ['Nenhum restaurante selecionado.']

    # Passe o nome do restaurante no contexto para a template
    context = {
        'alertas': alertas,
        'restaurante_nome': restaurante_nome,
    }
    return render(request, 'gestao_estoque/pagina-inicial.html', context)


def buscar_produtos(request):
    termo = request.GET.get('termo', '')
    restaurante_id = request.session.get('restaurante_id')

    if termo and restaurante_id:
        # Busca produtos pelo nome ou apelido, mas retorna apenas o apelido
        produtos = EstoqueProduto.objects.filter(
            Q(produto__nome__icontains=termo) | Q(produto__apelido__icontains=termo),
            local__restaurante_id=restaurante_id
        ).annotate(apelido=F('produto__apelido')).values_list('apelido', flat=True).distinct()[:10]
        return JsonResponse(list(produtos), safe=False)

    return JsonResponse([], safe=False)



@login_required
def verificar_permissao(request):
    # Supondo que a ação desejada seja enviada via POST ou GET como 'acao'
    acao = request.GET.get('acao', '')  # ou request.POST.get('acao', '')

    # Mapeia ações recebidas para os nomes das permissões correspondentes
    mapa_acoes_permissoes = {
        'atualizar': 'gestao_estoque.can_update',
        'registrar_perda': 'gestao_estoque.can_register_loss',
        'realizar_transacao': 'gestao_estoque.can_transact',
        'realizar_emprestimo': 'gestao_estoque.can_loan',
        'realizar_devolucao': 'gestao_estoque.can_return',
        # Adicione mais mapeamentos conforme necessário
    }

    permissao_requerida = mapa_acoes_permissoes.get(acao, '')

    if permissao_requerida and request.user.has_perm(permissao_requerida):
        # O usuário tem permissão
        return JsonResponse({'tem_permissao': True})
    else:
        # O usuário não tem permissão
        return JsonResponse({'tem_permissao': False})


@require_http_methods(["POST"])
def atualizar_quantidade(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    try:
        nova_quantidade = int(data.get('quantidade'))  # Certifica-se de que a nova quantidade é um inteiro
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Quantidade fornecida inválida.'}, status=400)
    
    restaurante_id = request.session.get('restaurante_id')
    if not restaurante_id:
        return JsonResponse({'success': False, 'error': 'Restaurante não selecionado.'}, status=400)

    try:
        with transaction.atomic():
            local = Local.objects.filter(restaurante__id=restaurante_id).first()
            if not local:
                return JsonResponse({'success': False, 'error': 'Local não encontrado.'}, status=404)
            
            estoque = EstoqueProduto.objects.select_for_update().filter(
                Q(produto__nome__iexact=nome_produto) | Q(produto__apelido__iexact=nome_produto),
                local=local
            ).first()
            
            if not estoque:
                return JsonResponse({'success': False, 'error': 'Produto não encontrado.'}, status=404)
            
            if nova_quantidade < 0:
                return JsonResponse({'success': False, 'error': 'Não é possível ter quantidade negativa no estoque.'}, status=400)

            estoque.quantidade = nova_quantidade
            estoque.save()

            HistoricoLog.objects.create(
                produto=estoque.produto,
                usuario=request.user,
                quantidade=nova_quantidade,
                origem=local,
                tipo='AT',
                local=local
            )

            HistoricoContagem.objects.update_or_create(
                produto=estoque.produto,
                local=local,
                data_contagem=timezone.now().date(),
                defaults={'quantidade_contagem': nova_quantidade}
            )

            return JsonResponse({'success': True, 'quantidade_atual': estoque.quantidade})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

   

@require_http_methods(["POST"])
def diminuir_quantidade(request):
    try:
        data = json.loads(request.body)
        nome_produto = data.get('nome')
        quantidade_diminuir_str = data.get('quantidade')
        motivo = data.get('motivo', '')
        restaurante_id = request.session.get('restaurante_id')

        if not nome_produto or quantidade_diminuir_str is None:
            raise ValueError("Nome do produto e quantidade são obrigatórios.")

        quantidade_diminuir = int(quantidade_diminuir_str)

        if not restaurante_id:
            return JsonResponse({'success': False, 'error': 'Restaurante não selecionado.'}, status=400)

        with transaction.atomic():
            produto = Produto.objects.filter(Q(nome__iexact=nome_produto) | Q(apelido__iexact=nome_produto)).first()
            if not produto:
                return JsonResponse({'success': False, 'error': 'Produto não encontrado.'}, status=404)

            local = Local.objects.filter(restaurante_id=restaurante_id).first()
            if not local:
                return JsonResponse({'success': False, 'error': 'Local não encontrado.'}, status=404)

            estoque = EstoqueProduto.objects.select_for_update().get(produto=produto, local=local)
            if estoque.quantidade < quantidade_diminuir:
                return JsonResponse({'success': False, 'error': 'Quantidade insuficiente no estoque.'}, status=400)

            # Atualiza o estoque
            estoque.quantidade -= quantidade_diminuir
            estoque.save()

            # Registra a alteração no histórico
            HistoricoLog.objects.create(
                produto=produto,
                usuario=request.user,
                quantidade=-quantidade_diminuir,  # Negativo para indicar redução
                motivo=motivo,  # Registra o motivo da perda
                origem=local,
                tipo='RE',
                local=local
            )

            return JsonResponse({'success': True, 'message': 'Quantidade diminuída e motivo registrado com sucesso.'})

    except EstoqueProduto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produto não disponível no estoque do restaurante especificado.'}, status=404)
    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'Erro na entrada de dados: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Erro interno do servidor: {str(e)}'}, status=500)




@require_http_methods(["POST"])
@login_required
def realizar_transacao(request):
    try:
        data = json.loads(request.body)
        nome_produto = data.get('nome')
        quantidade = int(data.get('quantidade'))
        motivo = data.get('motivo', '')
        restaurante_id = request.session.get('restaurante_id')
        
        if not nome_produto or quantidade <= 0:
            return JsonResponse({'success': False, 'error': 'Dados inválidos.'}, status=400)
        
        with transaction.atomic():
            estoque_central = Local.objects.get(nome='Estoque Central')
            local_destino = Local.objects.get(restaurante__id=restaurante_id)
            
            # Tenta encontrar o produto no estoque central pelo nome ou apelido
            produto = Produto.objects.get(Q(nome__iexact=nome_produto) | Q(apelido__iexact=nome_produto))
            estoque_produto_central = EstoqueProduto.objects.get(produto=produto, local=estoque_central)
            
            if estoque_produto_central.quantidade < quantidade:
                return JsonResponse({'success': False, 'error': 'Quantidade solicitada não está disponível no estoque central.'}, status=400)
            
            estoque_produto_central.quantidade -= quantidade
            estoque_produto_central.save()
            
            estoque_produto_destino, created = EstoqueProduto.objects.get_or_create(produto=produto, local=local_destino)
            estoque_produto_destino.quantidade += quantidade
            estoque_produto_destino.save()
            
            HistoricoLog.objects.create(
                produto=produto,
                usuario=request.user,
                quantidade=quantidade,
                origem=estoque_central,
                destino=local_destino,
                tipo='TR',
                motivo=motivo
            )
            
            return JsonResponse({'success': True, 'message': 'Transação realizada com sucesso.'})
    
    except Produto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produto não encontrado.'}, status=404)
    except Local.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Local não encontrado.'}, status=404)
    except Exception as e:
        logger.exception("Erro inesperado ao realizar a transação: {}".format(str(e)))
        return JsonResponse({'success': False, 'error': 'Erro ao realizar a transação.'}, status=500)





@login_required
def realizar_emprestimo(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    quantidade = int(data.get('quantidade'))
    motivo = data.get('motivo', '')
    restaurante_id = request.session.get('restaurante_id')
    usuario = request.user

    local_destino = get_object_or_404(Local, restaurante__id=restaurante_id)
    estoque_central = get_object_or_404(Local, nome='Estoque Central')

    with transaction.atomic():
        try:
            produto_estoque_central = EstoqueProduto.objects.get(
                Q(produto__nome__iexact=nome_produto) | Q(produto__apelido__iexact=nome_produto), 
                local=estoque_central)

            if produto_estoque_central.quantidade < quantidade:
                return JsonResponse({'success': False, 'error': 'Estoque central não possui quantidade suficiente.'})
            
            Transacoe.objects.create(
                produto=produto_estoque_central.produto,
                usuario=usuario,
                quantidade=quantidade,
                tipo='EM',  # Empréstimo
                origem=estoque_central,
                destino=local_destino,
                estado_solicitacao='PE',  # Pendente
                motivo=motivo  # Adiciona o motivo na transação
            )

            return JsonResponse({'success': True, 'message': 'Solicitação de empréstimo criada com sucesso. Aguardando aprovação.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Erro ao processar a solicitação de empréstimo: {str(e)}'})





@require_POST
@login_required
def realizar_devolucao(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    quantidade = int(data.get('quantidade'))
    motivo = data.get('motivo', '')
    restaurante_id = request.session.get('restaurante_id')
    usuario = request.user

    estoque_central = get_object_or_404(Local, nome='Estoque Central')
    estoque_central_id = estoque_central.id

    with transaction.atomic():
        try:
            estoque_central_produto = EstoqueProduto.objects.select_for_update().get(
                Q(produto__nome__iexact=nome_produto) | Q(produto__apelido__iexact=nome_produto), 
                local_id=estoque_central_id
            )
            estoque_central_produto.quantidade += quantidade
            estoque_central_produto.save()

            estoque_restaurante_produto = EstoqueProduto.objects.select_for_update().get(
                Q(produto__nome__iexact=nome_produto) | Q(produto__apelido__iexact=nome_produto), 
                local__restaurante__id=restaurante_id
            )
            estoque_restaurante_produto.quantidade -= quantidade
            estoque_restaurante_produto.save()

            Transacoe.objects.create(
                produto=estoque_central_produto.produto,
                usuario=usuario,
                quantidade=quantidade,
                tipo='DE',  # Devolução
                origem=estoque_restaurante_produto.local,
                destino=estoque_central,
                restaurante=estoque_restaurante_produto.local.restaurante,
                motivo=motivo  # Adiciona o motivo na transação
            )

            return JsonResponse({'success': True, 'message': 'Devolução realizada com sucesso.'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Erro ao processar a devolução: {str(e)}'})


    


def exportar_produtos_xlsx(request):
    restaurante_id = request.session.get('restaurante_id')
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="relatorio_produtos.xlsx"'

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#D7E4BC',
        'border': 1
    })

    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top',
        'num_format': '0'
    })

    # Set column widths
    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:E', 15)

    # Write headers
    worksheet.write('A1', 'Nome do Produto', header_format)
    worksheet.write('B1', 'Apelido', header_format)
    worksheet.write('C1', 'Quantidade Atual', header_format)
    worksheet.write('D1', 'Última Contagem', header_format)
    worksheet.write('E1', 'Diferença', header_format)

    worksheet.freeze_panes(1, 0)  # Freeze top row

    # Fetch products
    produtos_estoque = EstoqueProduto.objects.filter(local__restaurante_id=restaurante_id).order_by('produto__nome')

    for idx, estoque in enumerate(produtos_estoque, start=2):
        contagens = HistoricoContagem.objects.filter(
            produto=estoque.produto,
            local=estoque.local
        ).order_by('-data_contagem')[:2]  # Get the last two contagem records

        if len(contagens) == 2:
            ultima_contagem = contagens[1].quantidade_contagem  # Use the second last as the "last"
            penultima_contagem = contagens[0].quantidade_contagem
            diferenca = penultima_contagem - ultima_contagem
        else:
            ultima_contagem = contagens[0].quantidade_contagem if contagens else 0
            diferenca = 0

        # Write data to cells
        worksheet.write(idx, 0, estoque.produto.nome, cell_format)
        worksheet.write(idx, 1, estoque.produto.apelido, cell_format)
        worksheet.write(idx, 2, estoque.quantidade, cell_format)
        worksheet.write(idx, 3, ultima_contagem, cell_format)
        worksheet.write(idx, 4, diferenca, cell_format)

    end_row = idx + 1

    # Insert a chart
    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
        'name': 'Diferença',
        'categories': f'=Sheet1!$A$2:$A${end_row}',
        'values': f'=Sheet1!$E$2:$E${end_row}',
    })
    chart.set_x_axis({'name': 'Produtos', 'label_position': 'low', 'num_font': {'rotation': 45}})
    chart.set_title({'name': 'Diferença de Contagem dos Produtos'})
    chart.set_y_axis({'name': 'Diferença na Quantidade'})
    worksheet.insert_chart('H2', chart)  # Adjust the position of the chart

    workbook.close()
    output.seek(0)
    response.write(output.read())
    return response

