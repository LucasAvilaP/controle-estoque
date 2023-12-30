from django.db import models
from django.contrib.auth.models import User

class HistoricoLog(models.Model):
    produto = models.ForeignKey('produtos.Produto', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade = models.IntegerField()
    tipo = models.CharField(max_length=100)  # Exemplo: 'Adição' ou 'Remoção'
    data_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.produto.nome} - {self.tipo} - {self.quantidade}"