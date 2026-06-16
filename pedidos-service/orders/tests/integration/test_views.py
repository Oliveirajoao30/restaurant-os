from decimal import Decimal

import pytest

from orders.domain.entities import MenuItemSnapshot
from orders.infrastructure.adapters.cardapio_service_fake import FakeCardapioServiceAdapter
from orders.interfaces.web import container
from orders.models import Notification, Order


@pytest.fixture
def prato():
    return MenuItemSnapshot(id=1, nome='Feijoada', categoria='PRATO_PRINCIPAL', preco=Decimal('35.00'), disponivel=True)


@pytest.fixture(autouse=True)
def fake_menu_catalog(monkeypatch, prato):
    """Substitui o Adapter HTTP por um fake em memória, evitando chamadas de rede nos testes."""
    fake = FakeCardapioServiceAdapter([prato])
    monkeypatch.setattr(container, 'get_menu_catalog_port', lambda: fake)
    return fake


@pytest.mark.django_db
def test_painel_carrega(client):
    response = client.get('/')
    assert response.status_code == 200
    assert 'orders_recebido' in response.context


@pytest.mark.django_db
def test_pedido_novo_cria_pedido_e_redireciona(client, prato):
    response = client.post('/pedidos/novo/', {
        f'qty_{prato.id}': '2',
        'observacoes': 'Sem cebola',
    })

    assert response.status_code == 302
    order = Order.objects.get()
    assert order.total == Decimal('70.00')
    assert order.observacoes == 'Sem cebola'
    assert response.url == f'/pedidos/{order.pk}/'


@pytest.mark.django_db
def test_pedido_novo_sem_itens_mostra_erro(client, prato):
    response = client.post('/pedidos/novo/', {
        f'qty_{prato.id}': '0',
        'observacoes': '',
    })

    assert response.status_code == 200
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_pedido_detalhe(client, prato):
    order = Order.objects.create(status='RECEBIDO', total=Decimal('35.00'))
    order.items.create(
        menu_item_id=prato.id,
        nome_snapshot=prato.nome,
        categoria_snapshot=prato.categoria,
        quantidade=1,
        preco_unit=prato.preco,
        subtotal=prato.preco,
    )

    response = client.get(f'/pedidos/{order.pk}/')

    assert response.status_code == 200
    assert response.context['order'] == order


@pytest.mark.django_db
def test_pedido_avancar_status_gera_notificacoes(client):
    order = Order.objects.create(status='RECEBIDO', total=Decimal('35.00'))

    response = client.post(f'/pedidos/{order.pk}/avancar/')

    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == 'EM_PREPARO'
    tipos = set(Notification.objects.filter(order=order).values_list('tipo', flat=True))
    assert tipos == {'COZINHA', 'LOG'}


@pytest.mark.django_db
def test_pedido_fechar_pagamento_pix_pendente(client):
    """Passo 1: POST sem pix_confirmado gera chave e não marca como pago."""
    order = Order.objects.create(status='ENTREGUE', total=Decimal('100.00'))

    response = client.post(f'/pedidos/{order.pk}/fechar/', {
        'forma': 'PIX',
        'incluir_gorjeta': 'on',
    })

    assert response.status_code == 200
    assert response.context['pix_pendente'] is True
    assert 'chave_pix' in response.context
    order.refresh_from_db()
    assert order.pago is False


@pytest.mark.django_db
def test_pedido_fechar_pagamento_pix(client):
    """Passo 2: POST com pix_confirmado=1 marca o pedido como pago."""
    order = Order.objects.create(status='ENTREGUE', total=Decimal('100.00'))

    response = client.post(f'/pedidos/{order.pk}/fechar/', {
        'forma': 'PIX',
        'incluir_gorjeta': 'on',
        'pix_confirmado': '1',
    })

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.pago is True
    assert order.forma_pagamento == 'PIX'


@pytest.mark.django_db
def test_notificacoes_list(client):
    order = Order.objects.create(status='RECEBIDO', total=Decimal('35.00'))
    client.post(f'/pedidos/{order.pk}/avancar/')

    response = client.get('/notificacoes/')

    assert response.status_code == 200
    assert len(response.context['notificacoes']) == 2
