from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from catalog.models import MenuItem


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_list_menu_items(api_client):
    MenuItem.objects.create(nome='Bruschetta', categoria='ENTRADA', preco=Decimal('15.00'))
    MenuItem.objects.create(nome='Pudim', categoria='SOBREMESA', preco=Decimal('10.00'))

    response = api_client.get('/api/v1/menu-items/')

    assert response.status_code == 200
    nomes = {item['nome'] for item in response.data}
    assert nomes == {'Bruschetta', 'Pudim'}


@pytest.mark.django_db
def test_filter_menu_items_by_disponibilidade(api_client):
    MenuItem.objects.create(nome='Bruschetta', categoria='ENTRADA', preco=Decimal('15.00'), disponivel=True)
    MenuItem.objects.create(nome='Pudim', categoria='SOBREMESA', preco=Decimal('10.00'), disponivel=False)

    response = api_client.get('/api/v1/menu-items/', {'disponivel': 'true'})

    assert response.status_code == 200
    assert [item['nome'] for item in response.data] == ['Bruschetta']


@pytest.mark.django_db
def test_create_menu_item_valido(api_client):
    payload = {'nome': 'Suco Natural', 'categoria': 'BEBIDA', 'preco': '8.00'}

    response = api_client.post('/api/v1/menu-items/', payload, format='json')

    assert response.status_code == 201
    assert response.data['nome'] == 'Suco Natural'
    assert response.data['disponivel'] is True
    assert MenuItem.objects.filter(nome='Suco Natural').exists()


@pytest.mark.django_db
def test_create_menu_item_invalido_retorna_400(api_client):
    payload = {'nome': 'Suco Premium', 'categoria': 'BEBIDA', 'preco': '150.00'}

    response = api_client.post('/api/v1/menu-items/', payload, format='json')

    assert response.status_code == 400
    assert not MenuItem.objects.filter(nome='Suco Premium').exists()


@pytest.mark.django_db
def test_update_menu_item(api_client):
    item = MenuItem.objects.create(nome='Bruschetta', categoria='ENTRADA', preco=Decimal('15.00'))

    payload = {'nome': 'Bruschetta Especial', 'categoria': 'ENTRADA', 'preco': '18.00'}
    response = api_client.put(f'/api/v1/menu-items/{item.pk}/', payload, format='json')

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.nome == 'Bruschetta Especial'
    assert item.preco == Decimal('18.00')


@pytest.mark.django_db
def test_toggle_disponibilidade(api_client):
    item = MenuItem.objects.create(nome='Bruschetta', categoria='ENTRADA', preco=Decimal('15.00'), disponivel=True)

    response = api_client.post(f'/api/v1/menu-items/{item.pk}/toggle_disponibilidade/')

    assert response.status_code == 200
    assert response.data['disponivel'] is False
    item.refresh_from_db()
    assert item.disponivel is False


@pytest.mark.django_db
def test_delete_menu_item(api_client):
    item = MenuItem.objects.create(nome='Bruschetta', categoria='ENTRADA', preco=Decimal('15.00'))

    response = api_client.delete(f'/api/v1/menu-items/{item.pk}/')

    assert response.status_code == 204
    assert not MenuItem.objects.filter(pk=item.pk).exists()
