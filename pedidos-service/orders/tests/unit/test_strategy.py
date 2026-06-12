from decimal import Decimal

import pytest

from orders.domain.entities import OrderEntity
from orders.domain.strategy import (
    CartaoCreditoPayment,
    DinheiroPayment,
    PaymentContext,
    PixPayment,
    build_strategy,
)


def test_dinheiro_payment_calcula_troco():
    strategy = DinheiroPayment(Decimal('50.00'))
    receipt = strategy.process(Decimal('35.00'))

    assert receipt['status'] == 'aprovado'
    assert receipt['troco'] == Decimal('15.00')


def test_dinheiro_payment_recusa_se_valor_insuficiente():
    strategy = DinheiroPayment(Decimal('20.00'))
    receipt = strategy.process(Decimal('35.00'))

    assert receipt['status'] == 'recusado'


def test_cartao_payment_parcelas_validas():
    strategy = CartaoCreditoPayment(3)
    receipt = strategy.process(Decimal('30.00'))

    assert receipt['status'] == 'aprovado'
    assert receipt['parcelas'] == 3
    assert receipt['valor_por_parcela'] == Decimal('10.00')


@pytest.mark.parametrize('parcelas', [0, 13])
def test_cartao_payment_rejeita_parcelas_fora_do_intervalo(parcelas):
    with pytest.raises(ValueError):
        CartaoCreditoPayment(parcelas)


def test_pix_payment_gera_chave():
    strategy = PixPayment()
    receipt = strategy.process(Decimal('20.00'))

    assert receipt['status'] == 'aprovado'
    assert len(receipt['chave_pix']) == 20


def test_payment_context_aprova_e_atualiza_order_entity():
    order = OrderEntity(id=1, total=Decimal('35.00'))
    context = PaymentContext(DinheiroPayment(Decimal('50.00')))

    receipt = context.execute(order, order.total)

    assert receipt['status'] == 'aprovado'
    assert order.pago is True
    assert order.forma_pagamento == 'DINHEIRO'


def test_payment_context_nao_atualiza_order_entity_se_recusado():
    order = OrderEntity(id=1, total=Decimal('35.00'))
    context = PaymentContext(DinheiroPayment(Decimal('10.00')))

    receipt = context.execute(order, order.total)

    assert receipt['status'] == 'recusado'
    assert order.pago is False
    assert order.forma_pagamento == ''


def test_build_strategy_pix():
    assert isinstance(build_strategy('PIX'), PixPayment)


def test_build_strategy_desconhecida_levanta_erro():
    with pytest.raises(ValueError):
        build_strategy('VALE_REFEICAO')
