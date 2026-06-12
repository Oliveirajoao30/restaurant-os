from __future__ import annotations

from django.db import transaction

from orders.application.ports import OrderRepository
from orders.domain.entities import OrderEntity, OrderItemEntity
from orders.models import Order, OrderItem


class DjangoOrderRepository(OrderRepository):
    """Implementação do OrderRepository usando o Django ORM."""

    def _to_entity(self, order: Order) -> OrderEntity:
        items = [
            OrderItemEntity(
                menu_item_id=item.menu_item_id,
                nome_snapshot=item.nome_snapshot,
                categoria_snapshot=item.categoria_snapshot,
                quantidade=item.quantidade,
                preco_unit=item.preco_unit,
                subtotal=item.subtotal,
            )
            for item in order.items.all()
        ]
        return OrderEntity(
            id=order.pk,
            items=items,
            observacoes=order.observacoes,
            total=order.total,
            status=order.status,
            pago=order.pago,
            forma_pagamento=order.forma_pagamento,
        )

    def get_by_id(self, order_id: int) -> OrderEntity:
        order = Order.objects.prefetch_related('items').get(pk=order_id)
        return self._to_entity(order)

    @transaction.atomic
    def create(self, order: OrderEntity) -> OrderEntity:
        db_order = Order.objects.create(
            status=order.status,
            observacoes=order.observacoes,
            total=order.total,
        )
        for item in order.items:
            OrderItem.objects.create(
                order=db_order,
                menu_item_id=item.menu_item_id,
                nome_snapshot=item.nome_snapshot,
                categoria_snapshot=item.categoria_snapshot,
                quantidade=item.quantidade,
                preco_unit=item.preco_unit,
                subtotal=item.subtotal,
            )
        return self._to_entity(db_order)

    def list_by_status(self, status: str) -> list[OrderEntity]:
        qs = Order.objects.filter(status=status).prefetch_related('items')
        return [self._to_entity(order) for order in qs]

    def list_entregues(self) -> list[OrderEntity]:
        qs = Order.objects.filter(status='ENTREGUE').prefetch_related('items').order_by('pago', '-criado_em')
        return [self._to_entity(order) for order in qs]

    def update_status(self, order_id: int, status: str) -> None:
        order = Order.objects.get(pk=order_id)
        order.status = status
        order.save(update_fields=['status', 'atualizado_em'])

    def mark_as_paid(self, order_id: int, forma_pagamento: str) -> None:
        order = Order.objects.get(pk=order_id)
        order.pago = True
        order.forma_pagamento = forma_pagamento
        order.save(update_fields=['pago', 'forma_pagamento', 'atualizado_em'])
