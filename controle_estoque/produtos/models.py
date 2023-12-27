from django.db import models
from django.utils import timezone

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    data_entrada = models.DateField()
    tipo = models.CharField(max_length=100)
    quantidade = models.IntegerField()  # Isto vai representar a quantidade atual

    def __str__(self):
        return self.nome

class HistoricoContagem(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name='historico_contagem')
    data_contagem = models.DateField(default=timezone.now)
    quantidade_contagem = models.IntegerField()

    def __str__(self):
        return f"{self.produto.nome} - {self.data_contagem} - {self.quantidade_contagem}"

    class Meta:
        ordering = ['-data_contagem']  # Garante que a última contagem venha primeiro
        get_latest_by = 'data_contagem'