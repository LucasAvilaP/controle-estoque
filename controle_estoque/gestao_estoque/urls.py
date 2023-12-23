# gestao_estoque/urls.py

from django.urls import path
from . import views
from django.urls import path
from .views import buscar_produtos  # Certifique-se de importar a view correta

urlpatterns = [
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('buscar-produtos/', views.buscar_produtos, name='buscar_produtos'),

]

