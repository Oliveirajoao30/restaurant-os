from __future__ import annotations

from datetime import datetime

from orders.application.ports import NotificationRepository, OrderRepository
from orders.domain.entities import NotificationData, NotificationEntity, OrderEntity


class InMemoryOrderRepository(OrderRepository):
    """Fake do OrderRepository, usado para testar use cases sem banco de dados."""

    def __init__(self) -> None:
        self._orders: dict[int, OrderEntity] = {}
        self._next_id = 1

    def get_by_id(self, order_id: int) -> OrderEntity:
        return self._orders[order_id]

    def create(self, order: OrderEntity) -> OrderEntity:
        order.id = self._next_id
        self._orders[order.id] = order
        self._next_id += 1
        return order

    def list_by_status(self, status: str) -> list[OrderEntity]:
        return [o for o in self._orders.values() if o.status == status]

    def list_entregues(self) -> list[OrderEntity]:
        return [o for o in self._orders.values() if o.status == 'ENTREGUE']

    def update_status(self, order_id: int, status: str) -> None:
        self._orders[order_id].status = status

    def mark_as_paid(self, order_id: int, forma_pagamento: str) -> None:
        order = self._orders[order_id]
        order.pago = True
        order.forma_pagamento = forma_pagamento


class InMemoryNotificationRepository(NotificationRepository):
    """Fake do NotificationRepository, usado para testar use cases sem banco de dados."""

    def __init__(self) -> None:
        self._notifications: list[NotificationEntity] = []
        self._next_id = 1

    def create(self, order_id: int, notification: NotificationData) -> None:
        self._notifications.append(NotificationEntity(
            id=self._next_id,
            order_id=order_id,
            tipo=notification.tipo,
            mensagem=notification.mensagem,
            status_de=notification.status_de,
            status_para=notification.status_para,
            criado_em=datetime.now(),
        ))
        self._next_id += 1

    def list(self, order_id: int | None = None) -> list[NotificationEntity]:
        if order_id is not None:
            return [n for n in self._notifications if n.order_id == order_id]
        return list(self._notifications)
