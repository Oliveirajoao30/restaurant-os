from decimal import Decimal

import pytest

from orders.domain.entities import OrderEntity
from orders.domain.observer import KitchenNotifier, OrderLogger, OrderStatusSubject, WaiterNotifier


def build_subject():
    subject = OrderStatusSubject()
    subject.attach(KitchenNotifier())
    subject.attach(WaiterNotifier())
    subject.attach(OrderLogger())
    return subject


def test_advance_status_recebido_para_em_preparo_notifica_cozinha_e_log():
    order = OrderEntity(id=1, status='RECEBIDO', total=Decimal('50.00'))
    subject = build_subject()

    novo_status, notifications = subject.advance_status(order)

    assert novo_status == 'EM_PREPARO'
    assert order.status == 'EM_PREPARO'
    tipos = {n.tipo for n in notifications}
    assert tipos == {'COZINHA', 'LOG'}
    cozinha = next(n for n in notifications if n.tipo == 'COZINHA')
    assert 'Pedido #1' in cozinha.mensagem
    assert 'R$ 50.00' in cozinha.mensagem


def test_advance_status_em_preparo_para_pronto_notifica_garcom_e_log():
    order = OrderEntity(id=2, status='EM_PREPARO', total=Decimal('30.00'))
    subject = build_subject()

    novo_status, notifications = subject.advance_status(order)

    assert novo_status == 'PRONTO'
    tipos = {n.tipo for n in notifications}
    assert tipos == {'GARCOM', 'LOG'}
    garcom = next(n for n in notifications if n.tipo == 'GARCOM')
    assert 'PRONTO' in garcom.mensagem


def test_advance_status_pronto_para_entregue_notifica_garcom_e_log():
    order = OrderEntity(id=3, status='PRONTO', total=Decimal('30.00'))
    subject = build_subject()

    novo_status, notifications = subject.advance_status(order)

    assert novo_status == 'ENTREGUE'
    tipos = {n.tipo for n in notifications}
    assert tipos == {'GARCOM', 'LOG'}
    garcom = next(n for n in notifications if n.tipo == 'GARCOM')
    assert 'entregue' in garcom.mensagem


def test_advance_status_pedido_entregue_levanta_erro():
    order = OrderEntity(id=4, status='ENTREGUE', total=Decimal('30.00'))
    subject = build_subject()

    with pytest.raises(ValueError):
        subject.advance_status(order)


def test_logger_registra_todas_as_transicoes():
    order = OrderEntity(id=5, status='RECEBIDO', total=Decimal('10.00'))
    subject = OrderStatusSubject()
    subject.attach(OrderLogger())

    _, notifications = subject.advance_status(order)

    assert len(notifications) == 1
    assert notifications[0].tipo == 'LOG'
    assert notifications[0].status_de == 'RECEBIDO'
    assert notifications[0].status_para == 'EM_PREPARO'
