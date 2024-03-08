from django.contrib import admin, messages
from django.db import models, transaction
from django.utils.html import format_html
from django.utils import timezone
from .models import HistoricoLog, Local, Restaurante, Transacoe
from django.urls import reverse
from produtos.models import EstoqueProduto


@admin.register(HistoricoLog)
class HistoricoTransacaoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade', 'tipo', 'data_hora', 'usuario', 'origem', 'destino')
    list_filter = ('tipo', 'data_hora', 'usuario', 'destino')
    search_fields = ('produto__nome',)
    date_hierarchy = 'data_hora'
    ordering = ('-data_hora',)

admin.site.register(Local)
admin.site.register(Restaurante)


@admin.register(Transacoe)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ['produto', 'quantidade', 'tipo', 'data_hora', 'usuario', 'origem', 'destino', 'estado_solicitacao', 'responsavel_por']
    list_filter = ['tipo', 'data_hora', 'usuario', 'restaurante', 'estado_solicitacao']
    search_fields = ['produto__nome']
    actions = ['aprovar_transacoes', 'rejeitar_transacoes']

    @admin.action(description='Aprovar transações selecionadas e ajustar estoque')
    def aprovar_transacoes(self, request, queryset):
        if not request.user.has_perm('gestao_estoque.can_approve_transaction'):
            self.message_user(request, "Você não tem permissão para aprovar transações.", messages.ERROR)
            return

        queryset = queryset.filter(estado_solicitacao='PE')  # Filtrar apenas transações pendentes

        for transacao in queryset:
            if transacao.tipo == 'EM':  # Se for empréstimo
                try:
                    with transaction.atomic():
                        estoque_origem = EstoqueProduto.objects.get(produto=transacao.produto, local=transacao.origem)
                        estoque_destino, created = EstoqueProduto.objects.get_or_create(
                            produto=transacao.produto, local=transacao.destino, defaults={'quantidade': 0})

                        if estoque_origem.quantidade >= transacao.quantidade:
                            estoque_origem.quantidade -= transacao.quantidade
                            estoque_origem.save()
                            estoque_destino.quantidade += transacao.quantidade
                            estoque_destino.save()

                            transacao.estado_solicitacao = 'AP'
                            transacao.responsavel_por = request.user
                            transacao.save()

                            HistoricoLog.objects.create(
                                produto=transacao.produto, usuario=request.user, restaurante=transacao.restaurante,
                                quantidade=transacao.quantidade, local=transacao.destino, tipo='EM', status='EM',
                                origem=transacao.origem, destino=transacao.destino, data_hora=timezone.now()
                            )

                            self.message_user(request, f"Empréstimo {transacao.id} aprovado com sucesso e estoque ajustado.", messages.SUCCESS)
                        else:
                            self.message_user(request, f"Estoque insuficiente para a transação {transacao.id}.", messages.ERROR)

                except EstoqueProduto.DoesNotExist:
                    self.message_user(request, f"Estoque não encontrado para a transação {transacao.id}.", messages.ERROR)

            elif transacao.tipo == 'DE':  # Se for devolução
                # Para devoluções, apenas atualize o status da transação para 'AP' (Aprovado)
                transacao.estado_solicitacao = 'AP'
                transacao.responsavel_por = request.user
                transacao.save()

                HistoricoLog.objects.create(
                    produto=transacao.produto, usuario=request.user, restaurante=transacao.restaurante,
                    quantidade=transacao.quantidade, local=transacao.destino, tipo='DE', status='DE',
                    origem=transacao.origem, destino=transacao.destino, motivo=transacao.motivo,
                    data_hora=timezone.now()
                )

                self.message_user(request, f"Devolução {transacao.id} aprovada com sucesso. Status atualizado.", messages.SUCCESS)


    @admin.action(description='Rejeitar transações selecionadas')
    def rejeitar_transacoes(self, request, queryset):
        if not request.user.has_perm('gestao_estoque.can_reject_transaction'):
            self.message_user(request, "Você não tem permissão para rejeitar transações.", messages.ERROR)
            return

        for transacao in queryset.filter(estado_solicitacao='PE'):
            if transacao.tipo == 'DE':  # Se for devolução
                try:
                    with transaction.atomic():
                        # Busca o estoque no local de origem (restaurante que tentou devolver)
                        estoque_origem, created = EstoqueProduto.objects.get_or_create(
                            produto=transacao.produto, local=transacao.origem,
                            defaults={'quantidade': 0})
                        
                        # Busca o estoque no local de destino (estoque central) para ajustar
                        estoque_destino = EstoqueProduto.objects.get(
                            produto=transacao.produto, local=transacao.destino)
                        
                        # Ajusta a quantidade no estoque do restaurante que tentou devolver
                        estoque_origem.quantidade += transacao.quantidade
                        estoque_origem.save()
                        
                        # Desfaz o ajuste indevido no estoque central, se houver
                        if estoque_destino.quantidade >= transacao.quantidade:
                            estoque_destino.quantidade -= transacao.quantidade
                            estoque_destino.save()
                        
                        # Marca a transação como rejeitada
                        transacao.estado_solicitacao = 'RE'
                        transacao.responsavel_por = request.user
                        transacao.save()

                        # Registro no HistoricoLog para a rejeição
                        HistoricoLog.objects.create(
                            produto=transacao.produto,
                            usuario=request.user,
                            restaurante=transacao.restaurante,
                            quantidade=-transacao.quantidade,  # Use valor negativo para indicar reversão
                            local=transacao.origem,
                            tipo='RJ',
                            status='RJ',  # Atualize conforme a lógica do seu sistema
                            origem=transacao.origem,
                            destino=transacao.destino,
                            motivo='Rejeição de devolução',  # Motivo da rejeição
                            data_hora=timezone.now()
                        )

                        self.message_user(request, f"Devolução rejeitada e estoque ajustado.", messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"Erro ao rejeitar a transação {transacao.id}: {str(e)}", messages.ERROR)



