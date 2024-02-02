from django.db import models
from django.contrib.auth.models import User


class Restaurante(models.Model):
    nome = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    # Outros campos relevantes, como telefone, e-mail, etc.

    def __str__(self):
        return self.nome

class Local(models.Model):
    nome = models.CharField(max_length=100)
    endereco = models.CharField(max_length=200)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.SET_NULL, null=True, blank=True)
   

    def __str__(self):
        return self.nome

class HistoricoLog(models.Model):
    TIPO_ACOES = (
        ('AD', 'Adição'),
        ('RE', 'Remoção'),
        ('EM', 'Empréstimo'),
        ('DE', 'Devolução'),
    )

    STATUS_ITEM = (
        ('EM', 'Emprestado'),
        ('DI', 'Disponível'),
        ('ND', 'Não Devolvido'),
    )

    produto = models.ForeignKey('produtos.Produto', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    restaurante = models.ForeignKey('Restaurante', on_delete=models.SET_NULL, null=True, blank=True)  # Adicionar o modelo de Restaurante
    quantidade = models.IntegerField()
    local = models.ForeignKey('gestao_estoque.Local', on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=2, choices=TIPO_ACOES)
    status = models.CharField(max_length=2, choices=STATUS_ITEM, default='DI')
    origem = models.ForeignKey(Local, related_name='log_origem', on_delete=models.SET_NULL, null=True, blank=True)
    destino = models.ForeignKey(Local, related_name='log_destino', on_delete=models.SET_NULL, null=True, blank=True)
    data_hora = models.DateTimeField(auto_now_add=True)
    data_devolucao = models.DateTimeField(null=True, blank=True)  # Data esperada para devolução

    def __str__(self):
        return f"{self.produto.nome} - {self.tipo} - {self.quantidade}"
    


class Transacao(models.Model):
    TIPO_ACOES = (
        ('EM', 'Empréstimo'),
        ('DE', 'Devolução'),
    )

    produto = models.ForeignKey('produtos.Produto', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    quantidade = models.IntegerField()
    tipo = models.CharField(max_length=2, choices=TIPO_ACOES)
    data_hora = models.DateTimeField(auto_now_add=True)
    origem = models.ForeignKey(Local, related_name='transacao_origem', on_delete=models.SET_NULL, null=True, blank=True)
    destino = models.ForeignKey(Local, related_name='transacao_destino', on_delete=models.SET_NULL, null=True, blank=True)
    restaurante = models.ForeignKey(Restaurante, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.produto.nome} - {self.tipo} - {self.quantidade} - {self.usuario.username if self.usuario else 'N/A'}"