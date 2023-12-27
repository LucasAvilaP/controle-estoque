from django.db import models

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    data_entrada = models.DateField()
    tipo = models.CharField(max_length=100)
    quantidade = models.IntegerField()

    def __str__(self):
        return self.nome