
from django.contrib.auth.models import User
from django.db import models
from gestao_estoque.models import Restaurante


class AcessoRestaurante(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='acessos_restaurante')
    restaurante = models.ForeignKey(Restaurante, on_delete=models.CASCADE, related_name='usuarios_acesso')
    pode_acessar = models.BooleanField(default=False)

    class Meta:
        unique_together = ('usuario', 'restaurante')