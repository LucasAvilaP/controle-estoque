from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import AcessoRestaurante

# Personaliza o texto do cabeçalho do site de administração
admin.site.site_header = 'Gerenciamento de utensílios'

# Personaliza o título da aba do navegador
admin.site.site_title = 'Portal de Administração'

# Personaliza o texto do cabeçalho na página inicial do admin
admin.site.index_title = 'Recursos do Site de Administração'


@admin.register(AcessoRestaurante)
class AcessoRestauranteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'restaurante', 'pode_acessar')
    list_filter = ('restaurante', 'pode_acessar')
    search_fields = ('usuario__username', 'restaurante__nome')


# Define uma classe Inline para editar acessos no admin do User
class AcessoRestauranteInline(admin.TabularInline):
    model = AcessoRestaurante
    extra = 1  # Quantidade de campos extras para adicionar novos acessos

# Cria uma nova classe UserAdmin que inclui as informações de acesso
class UserAdmin(BaseUserAdmin):
    inlines = (AcessoRestauranteInline,)

# Primeiro, desregistra o modelo User padrão
admin.site.unregister(User)
# Depois, registra o modelo User com a nova configuração de admin
admin.site.register(User, UserAdmin)