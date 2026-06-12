from __future__ import annotations

from abc import ABC, abstractmethod

from orders.domain.entities import MenuItemSnapshot, NotificationData, NotificationEntity, OrderEntity


class OrderRepository(ABC):
    """Porta para persistência de pedidos (DIP: use cases dependem desta abstração)."""

    @abstractmethod
    def get_by_id(self, order_id: int) -> OrderEntity:
        ...

    @abstractmethod
    def create(self, order: OrderEntity) -> OrderEntity:
        ...

    @abstractmethod
    def list_by_status(self, status: str) -> list[OrderEntity]:
        ...

    @abstractmethod
    def list_entregues(self) -> list[OrderEntity]:
        ...

    @abstractmethod
    def update_status(self, order_id: int, status: str) -> None:
        ...

    @abstractmethod
    def mark_as_paid(self, order_id: int, forma_pagamento: str) -> None:
        ...


class NotificationRepository(ABC):
    """Porta para persistência e consulta de notificações."""

    @abstractmethod
    def create(self, order_id: int, notification: NotificationData) -> None:
        ...

    @abstractmethod
    def list(self, order_id: int | None = None) -> list[NotificationEntity]:
        ...


class MenuCatalogPort(ABC):
    """Porta para consulta do cardápio, implementada pelo Adapter HTTP do cardapio-service."""

    @abstractmethod
    def get_item(self, item_id: int) -> MenuItemSnapshot:
        ...

    @abstractmethod
    def list_available(self) -> list[MenuItemSnapshot]:
        ...
