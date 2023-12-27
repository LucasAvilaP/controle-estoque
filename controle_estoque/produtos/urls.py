# urls.py dentro do seu app 'produtos'

from django.urls import path
from . import views

urlpatterns = [
    path('api/produtos/', views.listar_produtos, name='listar_produtos'),
    path('api/produtos/info/', views.informacao_produto_por_nome, name='informacao_produto_por_nome'),
    path('api/produtos/atualizar/<str:nome_produto>/', views.atualizar_quantidade, name='atualizar_quantidade'),
]
