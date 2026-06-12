from decimal import Decimal

import pytest
import requests
import responses

from orders.domain.entities import MenuItemSnapshot
from orders.infrastructure.adapters.cardapio_service_adapter import CardapioServiceHttpAdapter
from orders.infrastructure.adapters.cardapio_service_fake import FakeCardapioServiceAdapter
from orders.infrastructure.adapters.exceptions import (
    CatalogServiceUnavailableError,
    MenuItemNotFoundError,
)

BASE_URL = 'http://cardapio-service.test'


@responses.activate
def test_get_item_retorna_snapshot():
    responses.add(
        responses.GET,
        f'{BASE_URL}/api/v1/menu-items/1/',
        json={'id': 1, 'nome': 'Feijoada', 'categoria': 'PRATO_PRINCIPAL', 'preco': '35.00', 'disponivel': True},
        status=200,
    )

    adapter = CardapioServiceHttpAdapter(base_url=BASE_URL)
    item = adapter.get_item(1)

    assert item == MenuItemSnapshot(id=1, nome='Feijoada', categoria='PRATO_PRINCIPAL', preco=Decimal('35.00'), disponivel=True)


@responses.activate
def test_get_item_404_levanta_menu_item_not_found():
    responses.add(responses.GET, f'{BASE_URL}/api/v1/menu-items/99/', status=404)

    adapter = CardapioServiceHttpAdapter(base_url=BASE_URL)
    with pytest.raises(MenuItemNotFoundError):
        adapter.get_item(99)


@responses.activate
def test_get_item_erro_de_conexao_levanta_catalog_service_unavailable():
    responses.add(
        responses.GET,
        f'{BASE_URL}/api/v1/menu-items/1/',
        body=requests.exceptions.ConnectionError('falha de rede'),
    )

    adapter = CardapioServiceHttpAdapter(base_url=BASE_URL)
    with pytest.raises(CatalogServiceUnavailableError):
        adapter.get_item(1)


@responses.activate
def test_get_item_status_500_levanta_catalog_service_unavailable():
    responses.add(responses.GET, f'{BASE_URL}/api/v1/menu-items/1/', status=500)

    adapter = CardapioServiceHttpAdapter(base_url=BASE_URL)
    with pytest.raises(CatalogServiceUnavailableError):
        adapter.get_item(1)


@responses.activate
def test_list_available_retorna_lista_de_snapshots():
    responses.add(
        responses.GET,
        f'{BASE_URL}/api/v1/menu-items/',
        json=[
            {'id': 1, 'nome': 'Feijoada', 'categoria': 'PRATO_PRINCIPAL', 'preco': '35.00', 'disponivel': True},
            {'id': 2, 'nome': 'Suco', 'categoria': 'BEBIDA', 'preco': '8.00', 'disponivel': True},
        ],
        status=200,
    )

    adapter = CardapioServiceHttpAdapter(base_url=BASE_URL)
    itens = adapter.list_available()

    assert [item.nome for item in itens] == ['Feijoada', 'Suco']


@responses.activate
def test_list_available_status_inesperado_levanta_catalog_service_unavailable():
    responses.add(responses.GET, f'{BASE_URL}/api/v1/menu-items/', status=503)

    adapter = CardapioServiceHttpAdapter(base_url=BASE_URL)
    with pytest.raises(CatalogServiceUnavailableError):
        adapter.list_available()


def test_fake_adapter_get_item_inexistente_levanta_menu_item_not_found():
    fake = FakeCardapioServiceAdapter()
    with pytest.raises(MenuItemNotFoundError):
        fake.get_item(1)


def test_fake_adapter_list_available_filtra_disponiveis():
    fake = FakeCardapioServiceAdapter([
        MenuItemSnapshot(id=1, nome='Disponível', categoria='ENTRADA', preco=Decimal('10.00'), disponivel=True),
        MenuItemSnapshot(id=2, nome='Indisponível', categoria='ENTRADA', preco=Decimal('10.00'), disponivel=False),
    ])

    itens = fake.list_available()

    assert [item.nome for item in itens] == ['Disponível']
