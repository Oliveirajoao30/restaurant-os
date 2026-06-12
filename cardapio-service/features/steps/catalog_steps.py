from decimal import Decimal

from behave import given, then, when
from django.core.exceptions import ValidationError

from catalog.application.use_cases import (
    CriarItemUseCase,
    ListarItensUseCase,
    ToggleDisponibilidadeUseCase,
)
from catalog.infrastructure.django_menu_repository import DjangoMenuRepository


def _repository() -> DjangoMenuRepository:
    return DjangoMenuRepository()


def _buscar_por_nome(nome: str):
    itens = ListarItensUseCase(_repository()).execute()
    return next((item for item in itens if item.nome == nome), None)


@given('que o item "{nome}" esteja cadastrado na categoria "{categoria}" com preço "{preco}"')
@when('eu cadastro o item "{nome}" na categoria "{categoria}" com preço "{preco}"')
def step_cadastrar_item(context, nome, categoria, preco):
    context.erro = None
    context.item = None
    try:
        context.item = CriarItemUseCase(_repository()).execute(
            categoria=categoria, nome=nome, preco=Decimal(preco),
        )
    except ValidationError as e:
        context.erro = e


@then('o cadastro deve ser aceito')
def step_cadastro_aceito(context):
    assert context.erro is None, f'Esperava sucesso, mas obteve erro: {context.erro}'
    assert context.item is not None
    assert context.item.id is not None


@then('o cadastro deve ser rejeitado com a mensagem "{mensagem}"')
def step_cadastro_rejeitado(context, mensagem):
    assert context.erro is not None, 'Esperava erro de validação, mas o cadastro foi aceito'
    assert mensagem in str(context.erro)


@then('o item "{nome}" deve estar disponível no cardápio')
def step_item_disponivel(context, nome):
    item = _buscar_por_nome(nome)
    assert item is not None, f'Item "{nome}" não encontrado no cardápio'
    assert item.disponivel is True


@when('eu desativo o item "{nome}"')
def step_desativar_item(context, nome):
    item = _buscar_por_nome(nome)
    context.item = ToggleDisponibilidadeUseCase(_repository()).execute(item.id)


@then('o item "{nome}" não deve estar disponível no cardápio')
def step_item_indisponivel(context, nome):
    item = _buscar_por_nome(nome)
    assert item.disponivel is False
