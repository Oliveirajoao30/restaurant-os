from __future__ import annotations

from abc import ABC, abstractmethod

from orders.domain.entities import NotificationData, OrderEntity


class OrderObserver(ABC):
    """Observer: reage a uma transição de status do pedido.

    Retorna uma ``NotificationData`` para ser persistida pelo use case, ou
    ``None`` quando a transição não interessa a este observer.
    """

    @abstractmethod
    def update(self, order: OrderEntity, status_de: str, status_para: str) -> NotificationData | None:
        ...


class KitchenNotifier(OrderObserver):
    """Avisa a cozinha quando um pedido entra em preparo."""

    def update(self, order: OrderEntity, status_de: str, status_para: str) -> NotificationData | None:
        if status_para != 'EM_PREPARO':
            return None
        return NotificationData(
            tipo='COZINHA',
            mensagem=f'Pedido #{order.id} recebido! Iniciar preparo. Total: R$ {order.total}.',
            status_de=status_de,
            status_para=status_para,
        )


class WaiterNotifier(OrderObserver):
    """Avisa o garçom quando o pedido fica pronto ou é entregue."""

    def update(self, order: OrderEntity, status_de: str, status_para: str) -> NotificationData | None:
        if status_para == 'PRONTO':
            mensagem = f'Pedido #{order.id} está PRONTO! Favor retirar na cozinha.'
        elif status_para == 'ENTREGUE':
            mensagem = f'Pedido #{order.id} foi entregue ao cliente.'
        else:
            return None
        return NotificationData(
            tipo='GARCOM',
            mensagem=mensagem,
            status_de=status_de,
            status_para=status_para,
        )


class OrderLogger(OrderObserver):
    """Registra todas as transições de status em um log de auditoria."""

    def update(self, order: OrderEntity, status_de: str, status_para: str) -> NotificationData | None:
        return NotificationData(
            tipo='LOG',
            mensagem=f'[SISTEMA] Pedido #{order.id}: status alterado de "{status_de}" para "{status_para}".',
            status_de=status_de,
            status_para=status_para,
        )


class OrderStatusSubject:
    """Subject: notifica os observers registrados a cada avanço de status."""

    def __init__(self) -> None:
        self._observers: list[OrderObserver] = []

    def attach(self, observer: OrderObserver) -> None:
        self._observers.append(observer)

    def detach(self, observer: OrderObserver) -> None:
        self._observers.remove(observer)

    def notify(self, order: OrderEntity, status_de: str, status_para: str) -> list[NotificationData]:
        notifications = []
        for observer in self._observers:
            result = observer.update(order, status_de, status_para)
            if result is not None:
                notifications.append(result)
        return notifications

    def advance_status(self, order: OrderEntity) -> tuple[str, list[NotificationData]]:
        proximo = order.proximo_status()
        if proximo is None:
            raise ValueError(f'O pedido #{order.id} já está no status final (ENTREGUE).')

        status_de = order.status
        order.status = proximo
        notifications = self.notify(order, status_de, proximo)
        return proximo, notifications
