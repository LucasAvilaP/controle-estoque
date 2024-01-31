from django.db import models
from produtos.models import Produto
from gestao_estoque.models import Restaurante

class Transacao(models.Model):
    TIPOS = (
        ('EM', 'Empréstimo'),
        ('DE', 'Devolução'),
    )
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    tipo = models.CharField(max_length=2, choices=TIPOS)
    data_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.restaurante.nome} - {self.produto.nome}"
    
