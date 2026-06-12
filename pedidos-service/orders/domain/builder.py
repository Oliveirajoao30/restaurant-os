from __future__ import annotations

from decimal import Decimal

from orders.domain.entities import OrderEntity, OrderItemEntity


class PedidoBuilder:
    """Builder: monta um OrderEntity passo a passo a partir dos itens do cardápio.

    Não persiste nada — quem grava o pedido é o ``OrderRepository``
    (camada de infrastructure), chamado pelo use case.
    """

    def __init__(self) -> None:
        self._items: list[tuple] = []  # (menu_item, quantidade)
        self._observacoes: str = ''

    def add_item(self, menu_item, quantidade: int = 1) -> 'PedidoBuilder':
        if quantidade < 1:
            raise ValueError('A quantidade deve ser pelo menos 1.')
        if not menu_item.disponivel:
            raise ValueError(f'O item "{menu_item.nome}" não está disponível.')

        for i, (existing_item, qty) in enumerate(self._items):
            if existing_item.id == menu_item.id:
                self._items[i] = (existing_item, qty + quantidade)
                return self

        self._items.append((menu_item, quantidade))
        return self

    def remove_item(self, menu_item) -> 'PedidoBuilder':
        self._items = [(item, qty) for item, qty in self._items if item.id != menu_item.id]
        return self

    def set_observacoes(self, texto: str) -> 'PedidoBuilder':
        self._observacoes = texto.strip() if texto else ''
        return self

    def build(self) -> OrderEntity:
        if not self._items:
            raise ValueError('O pedido deve ter pelo menos um item.')

        order_items = []
        total = Decimal('0')
        for menu_item, quantidade in self._items:
            preco_unit = menu_item.preco
            subtotal = preco_unit * quantidade
            order_items.append(OrderItemEntity(
                menu_item_id=menu_item.id,
                nome_snapshot=menu_item.nome,
                categoria_snapshot=menu_item.categoria,
                quantidade=quantidade,
                preco_unit=preco_unit,
                subtotal=subtotal,
            ))
            total += subtotal

        return OrderEntity(items=order_items, observacoes=self._observacoes, total=total)
