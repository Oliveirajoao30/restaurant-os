from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from catalog.domain.entities import MenuItemEntity
from catalog.domain.factory import MenuItemFactory


def test_create_entity_entrada_valida():
    item = MenuItemFactory.create_entity('ENTRADA', 'Bruschetta', Decimal('15.00'))

    assert isinstance(item, MenuItemEntity)
    assert item.nome == 'Bruschetta'
    assert item.categoria == 'ENTRADA'
    assert item.preco == Decimal('15.00')
    assert item.disponivel is True
    assert item.id is None


def test_prato_principal_abaixo_do_minimo_e_rejeitado():
    with pytest.raises(ValidationError):
        MenuItemFactory.create_entity('PRATO_PRINCIPAL', 'Arroz com Ovo', Decimal('9.99'))


def test_prato_principal_no_minimo_e_aceito():
    item = MenuItemFactory.create_entity('PRATO_PRINCIPAL', 'Arroz com Ovo', Decimal('10.00'))
    assert item.preco == Decimal('10.00')


def test_bebida_acima_do_maximo_e_rejeitada():
    with pytest.raises(ValidationError):
        MenuItemFactory.create_entity('BEBIDA', 'Vinho Importado', Decimal('150.00'))


def test_bebida_no_maximo_e_aceita():
    item = MenuItemFactory.create_entity('BEBIDA', 'Vinho', Decimal('100.00'))
    assert item.preco == Decimal('100.00')


def test_nome_vazio_e_rejeitado():
    with pytest.raises(ValidationError):
        MenuItemFactory.create_entity('SOBREMESA', '   ', Decimal('12.00'))


def test_preco_zero_ou_negativo_e_rejeitado():
    with pytest.raises(ValidationError):
        MenuItemFactory.create_entity('SOBREMESA', 'Pudim', Decimal('0'))

    with pytest.raises(ValidationError):
        MenuItemFactory.create_entity('SOBREMESA', 'Pudim', Decimal('-5'))


def test_categoria_desconhecida_e_rejeitada():
    with pytest.raises(ValidationError):
        MenuItemFactory.create_entity('LANCHE', 'Hambúrguer', Decimal('20.00'))


def test_nome_e_persistido_sem_espacos_nas_pontas():
    item = MenuItemFactory.create_entity('ENTRADA', '  Salada Caesar  ', Decimal('18.00'))
    assert item.nome == 'Salada Caesar'
