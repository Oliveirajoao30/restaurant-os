from __future__ import annotations

from orders.application.ports import MenuCatalogPort
from orders.domain.entities import MenuItemSnapshot
from orders.infrastructure.adapters.exceptions import MenuItemNotFoundError


class FakeCardapioServiceAdapter(MenuCatalogPort):
    """Implementação em memória do MenuCatalogPort, usada em testes e steps do behave."""

    def __init__(self, items: list[MenuItemSnapshot] | None = None) -> None:
        self._items: dict[int, MenuItemSnapshot] = {item.id: item for item in (items or [])}

    def add_item(self, item: MenuItemSnapshot) -> None:
        self._items[item.id] = item

    def get_item(self, item_id: int) -> MenuItemSnapshot:
        try:
            return self._items[item_id]
        except KeyError:
            raise MenuItemNotFoundError(f'Item {item_id} não encontrado no cardápio.')

    def list_available(self) -> list[MenuItemSnapshot]:
        return [item for item in self._items.values() if item.disponivel]
