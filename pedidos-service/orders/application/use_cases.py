from __future__ import annotations

from decimal import Decimal

from orders.application.ports import MenuCatalogPort, NotificationRepository, OrderRepository
from orders.domain.builder import PedidoBuilder
from orders.domain.entities import MenuItemSnapshot, NotificationEntity, OrderEntity
from orders.domain.observer import OrderStatusSubject
from orders.domain.strategy import PaymentContext, build_strategy

GORJETA_PERCENTUAL = Decimal('0.10')


class CriarPedidoUseCase:
    """Monta e persiste um novo pedido a partir dos itens selecionados (Builder Pattern)."""

    def __init__(self, order_repository: OrderRepository, menu_catalog: MenuCatalogPort) -> None:
        self._order_repository = order_repository
        self._menu_catalog = menu_catalog

    def execute(self, items_com_qtd: list[tuple[int, int]], observacoes: str = '') -> OrderEntity:
        builder = PedidoBuilder()
        for item_id, quantidade in items_com_qtd:
            menu_item = self._menu_catalog.get_item(item_id)
            builder.add_item(menu_item, quantidade)
        builder.set_observacoes(observacoes)

        order_entity = builder.build()
        return self._order_repository.create(order_entity)


class AvancarStatusUseCase:
    """Avança o status do pedido e dispara as notificações via Observer Pattern."""

    def __init__(
        self,
        order_repository: OrderRepository,
        notification_repository: NotificationRepository,
        status_subject: OrderStatusSubject,
    ) -> None:
        self._order_repository = order_repository
        self._notification_repository = notification_repository
        self._subject = status_subject

    def execute(self, order_id: int) -> OrderEntity:
        order = self._order_repository.get_by_id(order_id)
        novo_status, notifications = self._subject.advance_status(order)

        self._order_repository.update_status(order_id, novo_status)
        for notification in notifications:
            self._notification_repository.create(order_id, notification)

        return order


class ProcessarPagamentoUseCase:
    """Processa o pagamento do pedido via Strategy Pattern, com gorjeta opcional."""

    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    def execute(self, order_id: int, forma: str, **kwargs) -> dict:
        order = self._order_repository.get_by_id(order_id)

        if order.pago:
            return {
                'metodo': order.get_forma_pagamento_display(),
                'valor': order.total,
                'status': 'aprovado',
                'mensagem': 'Este pedido já foi pago anteriormente.',
            }

        incluir_gorjeta = kwargs.pop('incluir_gorjeta', True)
        gorjeta_valor = Decimal('0')
        valor_total = order.total

        if incluir_gorjeta:
            gorjeta_valor = (order.total * GORJETA_PERCENTUAL).quantize(Decimal('0.01'))
            valor_total = order.total + gorjeta_valor

        if forma == 'DINHEIRO' and 'valor_recebido' not in kwargs:
            kwargs['valor_recebido'] = valor_total

        strategy = build_strategy(forma, **kwargs)
        context = PaymentContext(strategy)
        receipt = context.execute(order, valor_total)

        if receipt['status'] == 'aprovado':
            self._order_repository.mark_as_paid(order_id, order.forma_pagamento)

        receipt['subtotal'] = order.total
        receipt['gorjeta'] = gorjeta_valor
        receipt['incluiu_gorjeta'] = incluir_gorjeta
        return receipt


class ListarNotificacoesUseCase:
    """Lista o histórico de notificações, opcionalmente filtrado por pedido."""

    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._notification_repository = notification_repository

    def execute(self, order_id: int | None = None) -> list[NotificationEntity]:
        return self._notification_repository.list(order_id=order_id)


class ListarItensDisponiveisUseCase:
    """Lista os itens do cardápio disponíveis para compor um novo pedido."""

    def __init__(self, menu_catalog: MenuCatalogPort) -> None:
        self._menu_catalog = menu_catalog

    def execute(self) -> list[MenuItemSnapshot]:
        return self._menu_catalog.list_available()
