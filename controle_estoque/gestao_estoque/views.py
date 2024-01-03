# gestao_estoque/views.py

import csv
import xlsxwriter
from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from produtos.models import Produto, HistoricoContagem
from django.views.decorators.csrf import csrf_exempt
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HistoricoLog
from django.utils import timezone
from django.db import models
import json



@login_required
def pagina_inicial(request):
    produtos_abaixo_do_minimo = Produto.objects.filter(quantidade__lt=models.F('nivel_minimo'))
    alertas = [f"O produto {produto.nome} está abaixo do nível mínimo de estoque!" for produto in produtos_abaixo_do_minimo]

    return render(request, 'gestao_estoque/pagina-inicial.html', {'alertas': alertas})


def buscar_produtos(request):
    termo = request.GET.get('termo', '')
    if termo:
        produtos = Produto.objects.filter(nome__icontains=termo).values_list('nome', flat=True)[:10]
        return JsonResponse(list(produtos), safe=False)
    return JsonResponse([], safe=False)

@require_http_methods(["POST"])
def atualizar_quantidade(request):
    data = json.loads(request.body)
    nome_produto = data.get('nome')
    quantidade_adicionar = int(data.get('quantidade'))
    data_contagem = data.get('data_contagem')  # Certifique-se de que o nome do campo corresponda ao seu HTML e JavaScript

    try:
        produto = Produto.objects.get(nome__iexact=nome_produto)
        produto.quantidade = quantidade_adicionar  # Se você deseja adicionar à quantidade existente
        # produto.quantidade = quantidade_adicionar  # Se você deseja definir uma nova quantidade
        produto.save()

        data_contagem = timezone.datetime.strptime(data_contagem, '%Y-%m-%d').date() if data_contagem else timezone.now().date()


        HistoricoLog.objects.create(
            produto=produto,
            usuario=request.user,
            quantidade=quantidade_adicionar,
            tipo='Adição',
            data_hora=timezone.now()  # Ou use a data_contagem se necessário
        )

        # Criar um novo registro de contagem no histórico
        HistoricoContagem.objects.create(
            produto=produto,
            data_contagem=data_contagem,
            quantidade_contagem=produto.quantidade
        )

        return JsonResponse({'success': True})
    except Produto.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produto não encontrado.'}, status=404)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Formato de data inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
   

def diminuir_quantidade(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nome_produto = data.get('nome')
        quantidade_adicionar = int(data.get('quantidade'))
        
        try:
            produto = Produto.objects.get(nome__iexact=nome_produto)
            produto.quantidade -= quantidade_adicionar
            produto.save()

            HistoricoLog.objects.create(
              produto=produto,
              usuario=request.user,
              quantidade=quantidade_adicionar,
              tipo='Remoção'
          )

            return JsonResponse({'success': True})
        except Produto.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Produto não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Método não permitido.'}, status=405)


    


def exportar_produtos_xlsx(request):
    hoje = date.today()  # Definindo a data de hoje

    # Cria uma resposta do tipo HttpResponse com o tipo de conteúdo correto
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="relatorio_produtos.xlsx"'

    # Cria um arquivo Excel na memória
    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Escreve o cabeçalho
    worksheet.write('A1', 'Nome do Produto')
    worksheet.write('B1', 'Quantidade Atual')
    worksheet.write('C1', 'Última Contagem')
    worksheet.write('D1', 'Diferença')

    # Escreve os dados dos produtos
    produtos = Produto.objects.all()
    historico_qs = HistoricoContagem.objects.filter(data_contagem__lt=hoje).order_by('-data_contagem')
    for idx, produto in enumerate(produtos, start=1):
        ultima_contagem = historico_qs.filter(produto=produto).first()
        diferenca = produto.quantidade - (ultima_contagem.quantidade_contagem if ultima_contagem else produto.quantidade)

        # Escreve os dados na linha correspondente
        worksheet.write(idx, 0, produto.nome)
        worksheet.write(idx, 1, produto.quantidade)
        worksheet.write(idx, 2, ultima_contagem.quantidade_contagem if ultima_contagem else 'N/A')
        
        # Se diferença for zero e você não quer mostrar, deixe vazio ou coloque um traço
        if diferenca == 0:
            worksheet.write(idx, 3, '-')
        else:
            worksheet.write(idx, 3, diferenca)

    # Fecha o arquivo Excel
    workbook.close()

    return response

@receiver(post_save, sender=Produto)
def criar_historico_contagem(sender, instance, created, **kwargs):
    # Supondo que 'data_contagem' seja o nome do campo de data na sua interface
    data_contagem = kwargs.get('data_contagem', timezone.now().date())

    if not created:  # Se o produto está sendo atualizado e não criado
        # Crie um novo registro de contagem no histórico com a data fornecida pelo usuário
        HistoricoContagem.objects.create(
            produto=instance,
            data_contagem=data_contagem,
            quantidade_contagem=instance.quantidade
        )