from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from orders.application.use_cases import (
    AvancarStatusUseCase,
    CriarPedidoUseCase,
    ListarItensDisponiveisUseCase,
    ListarNotificacoesUseCase,
    ProcessarPagamentoUseCase,
)
from orders.infrastructure.adapters.exceptions import CatalogServiceUnavailableError, MenuItemNotFoundError
from orders.interfaces.web import container
from orders.interfaces.web.forms import PagamentoForm, PedidoForm
from orders.models import Order


# ── Painel principal ──────────────────────────────────────────────────────────

def painel(request):
    """Dashboard: 4 colunas Kanban. A coluna Entregue agrega pagos e não pagos."""
    orders_recebido = Order.objects.filter(status='RECEBIDO').prefetch_related('items')
    orders_em_preparo = Order.objects.filter(status='EM_PREPARO').prefetch_related('items')
    orders_pronto = Order.objects.filter(status='PRONTO').prefetch_related('items')
    orders_entregue = Order.objects.filter(status='ENTREGUE').prefetch_related('items').order_by('pago', '-criado_em')

    return render(request, 'orders/painel.html', {
        'orders_recebido': orders_recebido,
        'orders_em_preparo': orders_em_preparo,
        'orders_pronto': orders_pronto,
        'orders_entregue': orders_entregue,
        'n_aguardando': orders_entregue.filter(pago=False).count(),
    })


# ── Pedidos ───────────────────────────────────────────────────────────────────

def pedido_novo(request):
    """Monta um pedido usando o PedidoBuilder (Builder Pattern)."""
    menu_catalog = container.get_menu_catalog_port()

    try:
        itens_disponiveis = ListarItensDisponiveisUseCase(menu_catalog).execute()
    except CatalogServiceUnavailableError:
        messages.error(request, 'O cardápio está indisponível no momento. Tente novamente em instantes.')
        itens_disponiveis = []

    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            # Coleta os itens selecionados no formulário dinâmico
            items_com_qtd = []
            for item in itens_disponiveis:
                qty_str = request.POST.get(f'qty_{item.id}', '0').strip()
                try:
                    qty = int(qty_str)
                except ValueError:
                    qty = 0
                if qty > 0:
                    items_com_qtd.append((item.id, qty))

            if not items_com_qtd:
                messages.error(request, 'Adicione pelo menos um item ao pedido.')
            else:
                try:
                    order = CriarPedidoUseCase(container.get_order_repository(), menu_catalog).execute(
                        items_com_qtd=items_com_qtd,
                        observacoes=form.cleaned_data.get('observacoes', ''),
                    )
                    messages.success(request, f'Pedido #{order.id} criado com sucesso!')
                    return redirect('pedido_detalhe', pk=order.id)
                except (ValueError, CatalogServiceUnavailableError, MenuItemNotFoundError) as e:
                    messages.error(request, str(e))
    else:
        form = PedidoForm()

    return render(request, 'orders/pedido_novo.html', {
        'form': form,
        'itens_disponiveis': itens_disponiveis,
    })


def pedido_detalhe(request, pk):
    """Detalhe de um pedido com histórico de notificações."""
    order = get_object_or_404(Order, pk=pk)
    notificacoes = ListarNotificacoesUseCase(container.get_notification_repository()).execute(order_id=pk)
    return render(request, 'orders/pedido_detalhe.html', {
        'order': order,
        'notificacoes': notificacoes,
    })


def pedido_avancar_status(request, pk):
    """Avança o status do pedido — dispara o Observer Pattern."""
    if request.method == 'POST':
        try:
            order = AvancarStatusUseCase(
                container.get_order_repository(),
                container.get_notification_repository(),
                container.get_status_subject(),
            ).execute(pk)
            messages.success(
                request,
                f'Pedido #{order.id} atualizado para: {order.get_status_display()}',
            )
        except ValueError as e:
            messages.warning(request, str(e))
    return redirect('painel')


def pedido_fechar(request, pk):
    """Seleciona a forma de pagamento e executa o Strategy Pattern."""
    order = get_object_or_404(Order, pk=pk)
    receipt = None

    if request.method == 'POST':
        form = PagamentoForm(request.POST)
        if form.is_valid():
            forma = form.cleaned_data['forma']
            incluir_gorjeta = form.cleaned_data['incluir_gorjeta']
            kwargs = {'incluir_gorjeta': incluir_gorjeta}
            if forma == 'DINHEIRO':
                kwargs['valor_recebido'] = form.cleaned_data['valor_recebido']
            elif forma == 'CARTAO':
                kwargs['parcelas'] = form.cleaned_data['parcelas']

            receipt = ProcessarPagamentoUseCase(container.get_order_repository()).execute(
                order_id=pk, forma=forma, **kwargs
            )
            if receipt['status'] == 'aprovado':
                order.refresh_from_db()
                messages.success(request, receipt['mensagem'])
    else:
        form = PagamentoForm()

    return render(request, 'orders/pedido_fechar.html', {
        'order': order,
        'form': form,
        'receipt': receipt,
    })


# ── Notificações ──────────────────────────────────────────────────────────────

def notificacoes_list(request):
    """Log de todas as notificações geradas pelo sistema."""
    notificacoes = ListarNotificacoesUseCase(container.get_notification_repository()).execute()
    return render(request, 'orders/notificacoes_list.html', {
        'notificacoes': notificacoes,
    })
