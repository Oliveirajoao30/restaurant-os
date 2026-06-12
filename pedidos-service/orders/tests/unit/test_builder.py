from decimal import Decimal

import pytest

from orders.domain.builder import PedidoBuilder
from orders.domain.entities import MenuItemSnapshot, OrderEntity


@pytest.fixture
def prato():
    return MenuItemSnapshot(id=1, nome='Feijoada', categoria='PRATO_PRINCIPAL', preco=Decimal('35.00'), disponivel=True)


@pytest.fixture
def bebida():
    return MenuItemSnapshot(id=2, nome='Suco', categoria='BEBIDA', preco=Decimal('8.00'), disponivel=True)


@pytest.fixture
def indisponivel():
    return MenuItemSnapshot(
        id=3, nome='Prato Esgotado', categoria='PRATO_PRINCIPAL', preco=Decimal('20.00'), disponivel=False,
    )


def test_build_retorna_order_entity_com_itens_e_total(prato, bebida):
    builder = PedidoBuilder()
    builder.add_item(prato, 2).add_item(bebida, 1)

    order = builder.build()

    assert isinstance(order, OrderEntity)
    assert order.id is None
    assert order.status == 'RECEBIDO'
    assert order.total == Decimal('78.00')
    assert len(order.items) == 2

    item_prato = next(i for i in order.items if i.menu_item_id == prato.id)
    assert item_prato.nome_snapshot == 'Feijoada'
    assert item_prato.categoria_snapshot == 'PRATO_PRINCIPAL'
    assert item_prato.quantidade == 2
    assert item_prato.preco_unit == Decimal('35.00')
    assert item_prato.subtotal == Decimal('70.00')


def test_add_item_repetido_soma_quantidades(prato):
    builder = PedidoBuilder()
    builder.add_item(prato, 1).add_item(prato, 2)

    order = builder.build()

    assert len(order.items) == 1
    assert order.items[0].quantidade == 3
    assert order.items[0].subtotal == Decimal('105.00')


def test_add_item_quantidade_invalida_levanta_erro(prato):
    builder = PedidoBuilder()
    with pytest.raises(ValueError):
        builder.add_item(prato, 0)


def test_add_item_indisponivel_levanta_erro(indisponivel):
    builder = PedidoBuilder()
    with pytest.raises(ValueError):
        builder.add_item(indisponivel, 1)


def test_build_sem_itens_levanta_erro():
    builder = PedidoBuilder()
    with pytest.raises(ValueError):
        builder.build()


def test_set_observacoes_e_remove_item(prato, bebida):
    builder = PedidoBuilder()
    builder.add_item(prato, 1).add_item(bebida, 1)
    builder.set_observacoes('  Sem cebola  ')
    builder.remove_item(bebida)

    order = builder.build()

    assert order.observacoes == 'Sem cebola'
    assert len(order.items) == 1
    assert order.items[0].menu_item_id == prato.id
