from django.contrib import admin
from django.db import models
from .models import HistoricoLog, Local, Restaurante, Transacao


@admin.register(HistoricoLog)
class HistoricoTransacaoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade', 'tipo', 'data_hora', 'usuario', 'restaurante')
    list_filter = ('tipo', 'data_hora', 'usuario', 'restaurante')
    search_fields = ('produto__nome',)
    date_hierarchy = 'data_hora'
    ordering = ('-data_hora',)

admin.site.register(Local)
admin.site.register(Restaurante)


@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'quantidade', 'tipo', 'data_hora', 'usuario', 'restaurante', 'origem', 'destino']
    list_filter = ['tipo', 'data_hora', 'usuario', 'restaurante']
    search_fields = ['produto__nome']