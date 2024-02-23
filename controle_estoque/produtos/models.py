from django.db import models
from django.utils import timezone
from gestao_estoque.models import Local

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    apelido = models.CharField(max_length=100, blank=True, null=True)  # Campo para o apelido do produto
    data_entrada = models.DateField()
    tipo = models.CharField(max_length=100)
    unidade = models.CharField(max_length=20, blank=True, null=True)
    nivel_minimo = models.IntegerField(default=15)

    def __str__(self):
        return self.nome  # ou return f"{self.nome} ({self.apelido})" para mostrar ambos


class EstoqueProduto(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='estoque')
    local = models.ForeignKey('gestao_estoque.Local', on_delete=models.CASCADE)  # Modelo 'Local' representando restaurantes e estoque central
    quantidade = models.IntegerField()  # Quantidade no local específico

    def __str__(self):
        return f"{self.local.nome} - {self.produto.nome} - {self.quantidade}"
    


class HistoricoContagem(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='historico_contagem')
    local = models.ForeignKey('gestao_estoque.Local', on_delete=models.CASCADE, blank=True, null=True)  # Local da contagem
    data_contagem = models.DateField(default=timezone.now)
    quantidade_contagem = models.IntegerField()

    def __str__(self):
        return f"{self.produto.nome} - {self.local.nome} - {self.data_contagem} - {self.quantidade_contagem}"

    class Meta:
        ordering = ['-data_contagem']
        get_latest_by = 'data_contagem'
