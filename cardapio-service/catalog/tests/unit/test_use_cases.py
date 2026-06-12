from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from catalog.application.use_cases import (
    AtualizarItemUseCase,
    CriarItemUseCase,
    DeletarItemUseCase,
    ListarItensUseCase,
    ToggleDisponibilidadeUseCase,
)
from catalog.tests.unit.fakes import InMemoryMenuRepository


@pytest.fixture
def repository():
    return InMemoryMenuRepository()


def test_criar_item_use_case_persiste_item_valido(repository):
    item = CriarItemUseCase(repository).execute('ENTRADA', 'Bruschetta', Decimal('15.00'))

    assert item.id == 1
    assert repository.list() == [item]


def test_criar_item_use_case_propaga_erro_de_validacao(repository):
    with pytest.raises(ValidationError):
        CriarItemUseCase(repository).execute('BEBIDA', 'Vinho Caro', Decimal('200.00'))

    assert repository.list() == []


def test_listar_itens_use_case_filtra_por_disponibilidade(repository):
    disponivel = CriarItemUseCase(repository).execute('ENTRADA', 'Bruschetta', Decimal('15.00'))
    indisponivel = CriarItemUseCase(repository).execute('SOBREMESA', 'Pudim', Decimal('10.00'))
    ToggleDisponibilidadeUseCase(repository).execute(indisponivel.id)

    assert ListarItensUseCase(repository).execute(disponivel=True) == [disponivel]
    assert ListarItensUseCase(repository).execute(disponivel=False) == [indisponivel]
    assert len(ListarItensUseCase(repository).execute()) == 2


def test_atualizar_item_use_case_aplica_regras_da_categoria(repository):
    item = CriarItemUseCase(repository).execute('ENTRADA', 'Bruschetta', Decimal('15.00'))

    atualizado = AtualizarItemUseCase(repository).execute(
        item_id=item.id, categoria='PRATO_PRINCIPAL', nome='Bruschetta Especial', preco=Decimal('25.00'),
    )

    assert atualizado.nome == 'Bruschetta Especial'
    assert atualizado.categoria == 'PRATO_PRINCIPAL'
    assert atualizado.preco == Decimal('25.00')


def test_atualizar_item_use_case_rejeita_preco_invalido_para_categoria(repository):
    item = CriarItemUseCase(repository).execute('ENTRADA', 'Bruschetta', Decimal('15.00'))

    with pytest.raises(ValidationError):
        AtualizarItemUseCase(repository).execute(
            item_id=item.id, categoria='PRATO_PRINCIPAL', nome='Bruschetta', preco=Decimal('5.00'),
        )


def test_toggle_disponibilidade_use_case_inverte_flag(repository):
    item = CriarItemUseCase(repository).execute('ENTRADA', 'Bruschetta', Decimal('15.00'))
    assert item.disponivel is True

    atualizado = ToggleDisponibilidadeUseCase(repository).execute(item.id)
    assert atualizado.disponivel is False

    atualizado = ToggleDisponibilidadeUseCase(repository).execute(item.id)
    assert atualizado.disponivel is True


def test_deletar_item_use_case_remove_item(repository):
    item = CriarItemUseCase(repository).execute('ENTRADA', 'Bruschetta', Decimal('15.00'))

    DeletarItemUseCase(repository).execute(item.id)

    assert repository.list() == []
