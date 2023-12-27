# gestao_estoque/urls.py

from django.urls import path
from . import views
from django.urls import path
from .views import buscar_produtos, atualizar_quantidade, diminuir_quantidade, exportar_produtos_xlsx

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('buscar-produtos/', views.buscar_produtos, name='buscar_produtos'),
    path('atualizar_quantidade/', views.atualizar_quantidade, name='atualizar_quantidade'),
    path('diminuir_quantidade/', views.diminuir_quantidade, name='diminuir_quantidade'),
    path('exportar_produtos_xlsx/', views.exportar_produtos_xlsx, name='exportar_produtos_xlsx'),

]

