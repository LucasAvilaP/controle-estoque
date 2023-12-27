# gestao_estoque/views.py

import csv
import xlsxwriter
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from produtos.models import Produto, HistoricoContagem
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


def exportar_produtos_xlsx(request):
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
    for idx, produto in enumerate(Produto.objects.all(), start=2):
        ultima_contagem = HistoricoContagem.objects.filter(produto=produto, data_contagem__lt=hoje).order_by('-data_contagem').first()
        diferenca = produto.quantidade - (ultima_contagem.quantidade_contagem if ultima_contagem else 0)

        worksheet.write_string(idx, 0, produto.nome)
        worksheet.write_number(idx, 1, produto.quantidade)
        worksheet.write_number(idx, 2, ultima_contagem.quantidade_contagem if ultima_contagem else '-')
        worksheet.write_number(idx, 3, diferenca)

    # Fecha o arquivo Excel
    workbook.close()

    return response