from django.db import models
from produtos.models import Produto
from django.contrib.auth.models import User

class Emprestimo(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    data_emprestimo = models.DateField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # quem fez o empréstimo
    restaurante_destino = models.CharField(max_length=100)  # Identificador do restaurante que recebe o empréstimo
    devolvido = models.BooleanField(default=False)
    data_devolucao = models.DateField(null=True, blank=True)  # Quando o item foi devolvido

    def __str__(self):
        return f"Empréstimo de {self.quantidade}x {self.produto.nome} para {self.restaurante_destino}"

class Devolucao(models.Model):
    emprestimo = models.OneToOneField(Emprestimo, on_delete=models.CASCADE)
    quantidade_devolvida = models.IntegerField()
    data_devolucao = models.DateField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # quem fez a devolução

    def __str__(self):
        return f"Devolução de {self.quantidade_devolvida}x {self.emprestimo.produto.nome} de {self.emprestimo.restaurante_destino}"
