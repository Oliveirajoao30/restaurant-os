from decimal import Decimal

from behave import given, then, when

from orders.application.use_cases import (
    AvancarStatusUseCase,
    CriarPedidoUseCase,
    ListarNotificacoesUseCase,
    ProcessarPagamentoUseCase,
)
from orders.domain.entities import MenuItemSnapshot
from orders.domain.observer import KitchenNotifier, OrderLogger, OrderStatusSubject, WaiterNotifier
from orders.infrastructure.adapters.cardapio_service_fake import FakeCardapioServiceAdapter
from orders.infrastructure.django_notification_repository import DjangoNotificationRepository
from orders.infrastructure.django_order_repository import DjangoOrderRepository


def _build_subject() -> OrderStatusSubject:
    subject = OrderStatusSubject()
    subject.attach(KitchenNotifier())
    subject.attach(WaiterNotifier())
    subject.attach(OrderLogger())
    return subject


def _ensure_context(context):
    if not hasattr(context, 'menu_catalog'):
        context.menu_catalog = FakeCardapioServiceAdapter()
        context.menu_items_by_name = {}
    if not hasattr(context, 'order_repository'):
        context.order_repository = DjangoOrderRepository()
        context.notification_repository = DjangoNotificationRepository()


# ── Cardápio (Fake Adapter) ────────────────────────────────────────────────────

@given('que o cardápio possui o item "{nome}" da categoria "{categoria}" por "{preco}", {disponibilidade}')
def step_cardapio_possui_item(context, nome, categoria, preco, disponibilidade):
    _ensure_context(context)
    item_id = len(context.menu_items_by_name) + 1
    item = MenuItemSnapshot(
        id=item_id,
        nome=nome,
        categoria=categoria,
        preco=Decimal(preco),
        disponivel=(disponibilidade.strip() == 'disponível'),
    )
    context.menu_catalog.add_item(item)
    context.menu_items_by_name[nome] = item


# ── Criação de pedidos (Builder) ───────────────────────────────────────────────

def _montar_pedido(context):
    items_com_qtd = [
        (context.menu_items_by_name[row['item']].id, int(row['quantidade']))
        for row in context.table
    ]
    context.erro = None
    context.order = None
    try:
        context.order = CriarPedidoUseCase(context.order_repository, context.menu_catalog).execute(items_com_qtd)
    except ValueError as e:
        context.erro = e


@when('eu monto um pedido com os itens')
def step_montar_pedido(context):
    _ensure_context(context)
    _montar_pedido(context)


@given('que existe um pedido criado com os itens')
def step_existe_pedido_criado(context):
    _ensure_context(context)
    _montar_pedido(context)
    assert context.erro is None, f'Falha ao criar pedido de apoio: {context.erro}'


@then('o pedido deve ser criado com sucesso')
def step_pedido_criado(context):
    assert context.erro is None, f'Esperava sucesso, mas obteve erro: {context.erro}'
    assert context.order is not None
    assert context.order.id is not None


@then('o total do pedido deve ser "{total}"')
def step_total_pedido(context, total):
    assert context.order.total == Decimal(total)


@then('o pedido deve ter {n:d} itens')
def step_pedido_tem_n_itens(context, n):
    assert len(context.order.items) == n


@then('a criação do pedido deve falhar com a mensagem "{trecho}"')
def step_criacao_falha(context, trecho):
    assert context.erro is not None, 'Esperava erro, mas o pedido foi criado'
    assert trecho in str(context.erro)


# ── Fluxo de status (Observer) ─────────────────────────────────────────────────

@given('que o pedido já está com status "{status}"')
def step_pedido_com_status(context, status):
    while context.order_repository.get_by_id(context.order.id).status != status:
        AvancarStatusUseCase(
            context.order_repository, context.notification_repository, _build_subject(),
        ).execute(context.order.id)
    context.order = context.order_repository.get_by_id(context.order.id)


@when('eu avanço o status do pedido')
def step_avancar_status(context):
    context.order = AvancarStatusUseCase(
        context.order_repository, context.notification_repository, _build_subject(),
    ).execute(context.order.id)


@when('eu tento avançar o status do pedido')
def step_tentar_avancar_status(context):
    context.erro = None
    try:
        context.order = AvancarStatusUseCase(
            context.order_repository, context.notification_repository, _build_subject(),
        ).execute(context.order.id)
    except ValueError as e:
        context.erro = e


@then('o status do pedido deve ser "{status}"')
def step_status_pedido(context, status):
    assert context.order.status == status


@then('deve haver notificações dos tipos "{tipos}" para o pedido')
def step_notificacoes_dos_tipos(context, tipos):
    esperados = {t.strip() for t in tipos.split(',')}
    notificacoes = ListarNotificacoesUseCase(context.notification_repository).execute(order_id=context.order.id)
    encontrados = {n.tipo for n in notificacoes}
    assert encontrados == esperados, f'esperado {esperados}, encontrado {encontrados}'


@then('a operação deve falhar com a mensagem "{trecho}"')
def step_operacao_falha(context, trecho):
    assert context.erro is not None, 'Esperava erro, mas a operação foi concluída'
    assert trecho in str(context.erro)


# ── Pagamento (Strategy) ────────────────────────────────────────────────────────

@when('eu pago o pedido em "{forma}" sem gorjeta com valor recebido "{valor}"')
def step_pagar_sem_gorjeta_com_valor(context, forma, valor):
    context.receipt = ProcessarPagamentoUseCase(context.order_repository).execute(
        context.order.id, forma, incluir_gorjeta=False, valor_recebido=Decimal(valor),
    )


@when('eu pago o pedido em "{forma}" com gorjeta')
def step_pagar_com_gorjeta(context, forma):
    context.receipt = ProcessarPagamentoUseCase(context.order_repository).execute(
        context.order.id, forma, incluir_gorjeta=True,
    )


@then('o pagamento deve ser aprovado')
def step_pagamento_aprovado(context):
    assert context.receipt['status'] == 'aprovado', context.receipt.get('mensagem')


@then('o troco deve ser "{valor}"')
def step_troco(context, valor):
    assert context.receipt['troco'] == Decimal(valor)


@then('a gorjeta deve ser "{valor}"')
def step_gorjeta(context, valor):
    assert context.receipt['gorjeta'] == Decimal(valor)


@then('o valor total cobrado deve ser "{valor}"')
def step_valor_total_cobrado(context, valor):
    assert context.receipt['valor'] == Decimal(valor)


@then('o pedido deve estar marcado como pago via "{forma}"')
def step_pedido_pago_via(context, forma):
    order = context.order_repository.get_by_id(context.order.id)
    assert order.pago is True
    assert order.forma_pagamento == forma
