"""Use cases do bounded context "catalog" — orquestram domain + repository."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError

from catalog.application.ports import MenuRepository
from catalog.domain.entities import MenuItemEntity
from catalog.domain.factory import MenuItemFactory


class CriarItemUseCase:
    """Cria um novo item do cardápio usando a MenuItemFactory (Factory Pattern)."""

    def __init__(self, repository: MenuRepository) -> None:
        self._repository = repository

    def execute(self, categoria: str, nome: str, preco: Decimal) -> MenuItemEntity:
        item = MenuItemFactory.create_entity(categoria, nome, preco)
        return self._repository.create(item)


class ListarItensUseCase:
    """Lista os itens do cardápio, opcionalmente filtrando por disponibilidade."""

    def __init__(self, repository: MenuRepository) -> None:
        self._repository = repository

    def execute(self, disponivel: bool | None = None) -> list[MenuItemEntity]:
        return self._repository.list(disponivel=disponivel)


class AtualizarItemUseCase:
    """Atualiza um item do cardápio reaplicando as regras da MenuItemFactory."""

    def __init__(self, repository: MenuRepository) -> None:
        self._repository = repository

    def execute(self, item_id: int, categoria: str, nome: str, preco: Decimal) -> MenuItemEntity:
        product_class = MenuItemFactory._registry.get(categoria)
        if product_class is None:
            raise ValidationError(f'Categoria desconhecida: {categoria}')

        product = product_class(nome=nome, preco=preco)
        product.validate()  # pode lançar ValidationError com regras da categoria

        item = MenuItemEntity(id=item_id, nome=nome.strip(), categoria=categoria, preco=preco)
        return self._repository.update(item_id, item)


class ToggleDisponibilidadeUseCase:
    """Inverte o campo disponivel de um item do cardápio."""

    def __init__(self, repository: MenuRepository) -> None:
        self._repository = repository

    def execute(self, item_id: int) -> MenuItemEntity:
        return self._repository.toggle_disponibilidade(item_id)


class DeletarItemUseCase:
    """Exclui um item do cardápio."""

    def __init__(self, repository: MenuRepository) -> None:
        self._repository = repository

    def execute(self, item_id: int) -> None:
        self._repository.delete(item_id)
