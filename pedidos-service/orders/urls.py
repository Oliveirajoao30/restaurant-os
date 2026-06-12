from django.urls import path

from orders.interfaces.web import views as pedido_views

urlpatterns = [
    path('', pedido_views.painel, name='painel'),

    # Pedidos
    path('pedidos/novo/', pedido_views.pedido_novo, name='pedido_novo'),
    path('pedidos/<int:pk>/', pedido_views.pedido_detalhe, name='pedido_detalhe'),
    path('pedidos/<int:pk>/avancar/', pedido_views.pedido_avancar_status, name='pedido_avancar'),
    path('pedidos/<int:pk>/fechar/', pedido_views.pedido_fechar, name='pedido_fechar'),

    # Notificações
    path('notificacoes/', pedido_views.notificacoes_list, name='notificacoes_list'),
]
