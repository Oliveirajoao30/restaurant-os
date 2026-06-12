from django.urls import path
from django.views.generic import RedirectView

from catalog.interfaces.web import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='cardapio_list'), name='home'),
    path('cardapio/', views.cardapio_list, name='cardapio_list'),
    path('cardapio/novo/', views.cardapio_create, name='cardapio_create'),
    path('cardapio/<int:pk>/toggle/', views.cardapio_toggle, name='cardapio_toggle'),
    path('cardapio/<int:pk>/editar/', views.cardapio_edit, name='cardapio_edit'),
    path('cardapio/<int:pk>/excluir/', views.cardapio_delete, name='cardapio_delete'),
]
