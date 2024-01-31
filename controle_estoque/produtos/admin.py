from django.contrib import admin
from .models import Produto, EstoqueProduto, HistoricoContagem
from gestao_estoque.models import Local

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'data_entrada', 'nivel_minimo')
    list_filter = ('tipo', 'data_entrada')
    search_fields = ('nome',)

class EstoqueProdutoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'local', 'quantidade')

    def get_queryset(self, request):
        # Filtra os produtos com base no restaurante selecionado
        qs = super().get_queryset(request)
        selected_restaurant_id = request.session.get('restaurante_id')
        if selected_restaurant_id:
            qs = qs.filter(local__restaurante__id=selected_restaurant_id)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "local":
            # Filtra as opções do campo 'local' com base no restaurante selecionado
            selected_restaurant_id = request.session.get('restaurante_id')
            if selected_restaurant_id:
                kwargs["queryset"] = Local.objects.filter(restaurante__id=selected_restaurant_id)
            else:
                kwargs["queryset"] = Local.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(EstoqueProduto, EstoqueProdutoAdmin)

@admin.register(HistoricoContagem)
class HistoricoContagemAdmin(admin.ModelAdmin):
    list_display = ('produto', 'local', 'data_contagem', 'quantidade_contagem')
    list_filter = ('produto', 'local', 'data_contagem')
    search_fields = ('produto__nome',)
