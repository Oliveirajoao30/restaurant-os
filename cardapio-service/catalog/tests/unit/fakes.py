from __future__ import annotations

from catalog.application.ports import MenuRepository
from catalog.domain.entities import MenuItemEntity


class InMemoryMenuRepository(MenuRepository):
    """Fake do MenuRepository, usado para testar use cases sem banco de dados."""

    def __init__(self) -> None:
        self._items: dict[int, MenuItemEntity] = {}
        self._next_id = 1

    def get_by_id(self, item_id: int) -> MenuItemEntity:
        try:
            return self._items[item_id]
        except KeyError:
            from catalog.models import MenuItem
            raise MenuItem.DoesNotExist(item_id)

    def list(self, disponivel: bool | None = None) -> list[MenuItemEntity]:
        items = list(self._items.values())
        if disponivel is not None:
            items = [item for item in items if item.disponivel == disponivel]
        return items

    def create(self, item: MenuItemEntity) -> MenuItemEntity:
        item.id = self._next_id
        self._items[item.id] = item
        self._next_id += 1
        return item

    def update(self, item_id: int, item: MenuItemEntity) -> MenuItemEntity:
        existing = self.get_by_id(item_id)
        existing.nome = item.nome
        existing.categoria = item.categoria
        existing.preco = item.preco
        return existing

    def toggle_disponibilidade(self, item_id: int) -> MenuItemEntity:
        existing = self.get_by_id(item_id)
        existing.disponivel = not existing.disponivel
        return existing

    def delete(self, item_id: int) -> None:
        self._items.pop(item_id, None)
