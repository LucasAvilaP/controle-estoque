# gestao_estoque/urls.py

from django.urls import path
from . import views
from .views import buscar_produtos, atualizar_quantidade, diminuir_quantidade, exportar_produtos_xlsx, realizar_devolucao, realizar_emprestimo, verificar_permissao, pagina_inicial

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('verificar_permissao/', views.verificar_permissao, name='verificar_permissao'),
    path('buscar-produtos/', views.buscar_produtos, name='buscar_produtos'),
    path('atualizar_quantidade/', views.atualizar_quantidade, name='atualizar_quantidade'),
    path('diminuir_quantidade/', views.diminuir_quantidade, name='diminuir_quantidade'),
    path('realizar_emprestimo/', views.realizar_emprestimo, name='realizar_emprestimo'),
    path('realizar_devolucao/', views.realizar_devolucao, name='realizar_devolucao'),
    path('exportar_produtos_xlsx/', views.exportar_produtos_xlsx, name='exportar_produtos_xlsx'),
    

]

