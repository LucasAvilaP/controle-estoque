from django.contrib import admin
from .models import HistoricoLog

@admin.register(HistoricoLog)
class HistoricoTransacaoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade', 'tipo', 'data_hora', 'usuario')
    list_filter = ('tipo', 'data_hora', 'usuario')
    search_fields = ('produto__nome',)
    date_hierarchy = 'data_hora'
    ordering = ('-data_hora',)

# Register your models here.
