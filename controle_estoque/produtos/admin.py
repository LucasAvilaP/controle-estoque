from django.contrib import admin
from .models import Produto, EstoqueProduto, HistoricoContagem
from gestao_estoque.models import Local,HistoricoLog
from django.http import HttpResponse
from django.contrib.auth.models import User
import xlsxwriter



@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'apelido', 'tipo', 'nivel_minimo')
    list_filter = ('tipo',)
    search_fields = ('nome', 'apelido',)




@admin.action(description='Exportar para Excel')
def exportar_para_excel(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="estoque_produtos.xlsx"'

    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Cabeçalhos da planilha
    worksheet.write('A1', 'Nome do Produto')
    worksheet.write('B1', 'Apelido')
    worksheet.write('C1', 'Quantidade')
    worksheet.write('D1', 'Local')

    for idx, estoqueProduto in enumerate(queryset, start=2):
        nome = estoqueProduto.produto.nome
        apelido = estoqueProduto.produto.apelido  # Acessando o apelido através da relação com Produto
        quantidade = estoqueProduto.quantidade
        local = estoqueProduto.local.nome

        worksheet.write(f'A{idx}', nome)
        worksheet.write(f'B{idx}', apelido)
        worksheet.write(f'C{idx}', quantidade)
        worksheet.write(f'D{idx}', local)

    workbook.close()

    return response



@admin.register(EstoqueProduto)
class EstoqueProdutoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'local', 'quantidade', 'get_apelido')  # Adicione get_apelido no list_display

    def get_apelido(self, obj):
        return obj.produto.apelido
    get_apelido.short_description = 'Apelido'  # Nome da coluna no admin

    actions = [exportar_para_excel]

    def get_queryset(self, request):
        # Mantém a filtragem original, sem alterações
        qs = super().get_queryset(request)
        selected_restaurant_id = request.session.get('restaurante_id')
        if selected_restaurant_id:
            qs = qs.filter(local__restaurante__id=selected_restaurant_id)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Mantém a filtragem original para o campo 'local'
        if db_field.name == "local":
            selected_restaurant_id = request.session.get('restaurante_id')
            if selected_restaurant_id:
                kwargs["queryset"] = Local.objects.filter(restaurante__id=selected_restaurant_id)
            else:
                kwargs["queryset"] = Local.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        # Determina se é uma adição ou atualização
        is_addition = not change

        # Salva o EstoqueProduto
        if is_addition:
            existing = EstoqueProduto.objects.filter(produto=obj.produto, local=obj.local).first()
            if existing:
                existing.quantidade += obj.quantidade
                existing.save()
                action_type = 'AD'  # Se o produto já existe, considera como atualização
            else:
                obj.save()
                action_type = 'AD'  # Se é um novo produto, considera como adição
        else:
            obj.save()
            action_type = 'AT'  # Atualização

        # Registra a ação no HistoricoLog
        HistoricoLog.objects.create(
            produto=obj.produto,
            usuario=request.user,
            restaurante=obj.local.restaurante if hasattr(obj.local, 'restaurante') else None,
            quantidade=obj.quantidade,
            local=obj.local,
            tipo=action_type,
            status='DI',  # Assume-se que o status é 'Disponível' após adição/atualização
            origem=obj.local
        )

    @admin.action(description='Exportar para Excel')
    def exportar_para_excel(modeladmin, request, queryset):
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="estoque_produtos.xlsx"'

        workbook = xlsxwriter.Workbook(response, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Cabeçalhos da planilha
        worksheet.write('A1', 'Nome do Produto')
        worksheet.write('B1', 'Apelido')
        worksheet.write('C1', 'Quantidade')
        worksheet.write('D1', 'Local')

        for idx, estoqueProduto in enumerate(queryset, start=2):
            nome = estoqueProduto.produto.nome
            apelido = estoqueProduto.produto.apelido  # Acessando o apelido através da relação com Produto
            quantidade = estoqueProduto.quantidade
            local = estoqueProduto.local.nome

            worksheet.write(f'A{idx}', nome)
            worksheet.write(f'B{idx}', apelido)
            worksheet.write(f'C{idx}', quantidade)
            worksheet.write(f'D{idx}', local)

        workbook.close()

        return response

@admin.register(HistoricoContagem)
class HistoricoContagemAdmin(admin.ModelAdmin):
    list_display = ('produto', 'local', 'data_contagem', 'quantidade_contagem')
    list_filter = ('produto', 'local', 'data_contagem')
    search_fields = ('produto__nome',)

    def get_queryset(self, request):
        """
        Sobrescreve o queryset padrão para filtrar os registros de histórico de contagem
        com base no restaurante selecionado pelo usuário.
        """
        qs = super().get_queryset(request)
        selected_restaurant_id = request.session.get('restaurante_id')
        if selected_restaurant_id:
            qs = qs.filter(local__restaurante__id=selected_restaurant_id)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtra os campos de chave estrangeira para exibir apenas os locais associados
        ao restaurante selecionado pelo usuário.
        """
        if db_field.name == "local":
            selected_restaurant_id = request.session.get('restaurante_id')
            if selected_restaurant_id:
                kwargs["queryset"] = Local.objects.filter(restaurante__id=selected_restaurant_id)
            else:
                kwargs["queryset"] = Local.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
