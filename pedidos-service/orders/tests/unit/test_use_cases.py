from decimal import Decimal

import pytest

from orders.application.use_cases import (
    AvancarStatusUseCase,
    CriarPedidoUseCase,
    ListarItensDisponiveisUseCase,
    ListarNotificacoesUseCase,
    ProcessarPagamentoUseCase,
)
from orders.domain.entities import MenuItemSnapshot, OrderEntity
from orders.domain.observer import KitchenNotifier, OrderLogger, OrderStatusSubject, WaiterNotifier
from orders.infrastructure.adapters.cardapio_service_fake import FakeCardapioServiceAdapter
from orders.tests.unit.fakes import InMemoryNotificationRepository, InMemoryOrderRepository


def build_subject():
    subject = OrderStatusSubject()
    subject.attach(KitchenNotifier())
    subject.attach(WaiterNotifier())
    subject.attach(OrderLogger())
    return subject


def test_criar_pedido_use_case_persiste_pedido():
    item = MenuItemSnapshot(id=1, nome='Feijoada', categoria='PRATO_PRINCIPAL', preco=Decimal('35.00'), disponivel=True)
    repository = InMemoryOrderRepository()
    menu_catalog = FakeCardapioServiceAdapter([item])

    order = CriarPedidoUseCase(repository, menu_catalog).execute([(item.id, 2)], observacoes='Sem cebola')

    assert order.id == 1
    assert order.total == Decimal('70.00')
    assert order.observacoes == 'Sem cebola'
    assert repository.get_by_id(1) is order


def test_criar_pedido_use_case_propaga_erro_de_item_indisponivel():
    item = MenuItemSnapshot(id=1, nome='Esgotado', categoria='PRATO_PRINCIPAL', preco=Decimal('35.00'), disponivel=False)
    repository = InMemoryOrderRepository()
    menu_catalog = FakeCardapioServiceAdapter([item])

    with pytest.raises(ValueError):
        CriarPedidoUseCase(repository, menu_catalog).execute([(item.id, 1)])


def test_avancar_status_use_case_atualiza_status_e_persiste_notificacoes():
    order_repository = InMemoryOrderRepository()
    notification_repository = InMemoryNotificationRepository()
    order_repository.create(OrderEntity(status='RECEBIDO', total=Decimal('50.00')))

    use_case = AvancarStatusUseCase(order_repository, notification_repository, build_subject())
    order = use_case.execute(1)

    assert order.status == 'EM_PREPARO'
    assert order_repository.get_by_id(1).status == 'EM_PREPARO'
    notificacoes = notification_repository.list(order_id=1)
    tipos = {n.tipo for n in notificacoes}
    assert tipos == {'COZINHA', 'LOG'}


def test_avancar_status_use_case_pedido_entregue_levanta_erro():
    order_repository = InMemoryOrderRepository()
    notification_repository = InMemoryNotificationRepository()
    order_repository.create(OrderEntity(status='ENTREGUE', total=Decimal('50.00')))

    use_case = AvancarStatusUseCase(order_repository, notification_repository, build_subject())
    with pytest.raises(ValueError):
        use_case.execute(1)


def test_processar_pagamento_use_case_aprova_e_marca_pedido_como_pago():
    order_repository = InMemoryOrderRepository()
    order_repository.create(OrderEntity(status='ENTREGUE', total=Decimal('100.00')))

    receipt = ProcessarPagamentoUseCase(order_repository).execute(1, 'PIX', incluir_gorjeta=True)

    assert receipt['status'] == 'aprovado'
    assert receipt['subtotal'] == Decimal('100.00')
    assert receipt['gorjeta'] == Decimal('10.00')
    assert receipt['valor'] == Decimal('110.00')

    order = order_repository.get_by_id(1)
    assert order.pago is True
    assert order.forma_pagamento == 'PIX'


def test_processar_pagamento_use_case_sem_gorjeta():
    order_repository = InMemoryOrderRepository()
    order_repository.create(OrderEntity(status='ENTREGUE', total=Decimal('100.00')))

    receipt = ProcessarPagamentoUseCase(order_repository).execute(1, 'PIX', incluir_gorjeta=False)

    assert receipt['gorjeta'] == Decimal('0')
    assert receipt['valor'] == Decimal('100.00')


def test_processar_pagamento_use_case_pedido_ja_pago_retorna_mensagem():
    order_repository = InMemoryOrderRepository()
    order_repository.create(OrderEntity(status='ENTREGUE', total=Decimal('100.00'), pago=True, forma_pagamento='PIX'))

    receipt = ProcessarPagamentoUseCase(order_repository).execute(1, 'DINHEIRO', valor_recebido=Decimal('100.00'))

    assert receipt['status'] == 'aprovado'
    assert 'já foi pago' in receipt['mensagem']


def test_listar_notificacoes_use_case():
    notification_repository = InMemoryNotificationRepository()
    order_repository = InMemoryOrderRepository()
    order_repository.create(OrderEntity(status='RECEBIDO', total=Decimal('50.00')))
    AvancarStatusUseCase(order_repository, notification_repository, build_subject()).execute(1)

    todas = ListarNotificacoesUseCase(notification_repository).execute()
    do_pedido = ListarNotificacoesUseCase(notification_repository).execute(order_id=1)

    assert len(todas) == 2
    assert len(do_pedido) == 2


def test_listar_itens_disponiveis_use_case():
    menu_catalog = FakeCardapioServiceAdapter([
        MenuItemSnapshot(id=1, nome='Disponível', categoria='ENTRADA', preco=Decimal('15.00'), disponivel=True),
        MenuItemSnapshot(id=2, nome='Indisponível', categoria='ENTRADA', preco=Decimal('15.00'), disponivel=False),
    ])

    itens = ListarItensDisponiveisUseCase(menu_catalog).execute()

    assert [item.nome for item in itens] == ['Disponível']
