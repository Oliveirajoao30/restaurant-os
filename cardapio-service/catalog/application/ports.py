"""
Ports (interfaces) que a camada application depende — implementadas pela
camada infrastructure. Mantém o princípio DIP (SOLID): use cases dependem de
abstrações, não de detalhes de persistência.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from catalog.domain.entities import MenuItemEntity


class MenuRepository(ABC):
    """Porta para persistência de itens do cardápio."""

    @abstractmethod
    def get_by_id(self, item_id: int) -> MenuItemEntity:
        ...

    @abstractmethod
    def list(self, disponivel: bool | None = None) -> list[MenuItemEntity]:
        ...

    @abstractmethod
    def create(self, item: MenuItemEntity) -> MenuItemEntity:
        ...

    @abstractmethod
    def update(self, item_id: int, item: MenuItemEntity) -> MenuItemEntity:
        ...

    @abstractmethod
    def toggle_disponibilidade(self, item_id: int) -> MenuItemEntity:
        ...

    @abstractmethod
    def delete(self, item_id: int) -> None:
        ...
