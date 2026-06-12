from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

STATUS_FLOW = ['RECEBIDO', 'EM_PREPARO', 'PRONTO', 'ENTREGUE']

STATUS_LABELS = {
    'RECEBIDO': 'Recebido',
    'EM_PREPARO': 'Em Preparo',
    'PRONTO': 'Pronto',
    'ENTREGUE': 'Entregue',
}

PAYMENT_LABELS = {
    'DINHEIRO': 'Dinheiro',
    'CARTAO': 'Cartão de Crédito',
    'PIX': 'PIX',
    '': '',
}

CATEGORIA_LABELS = {
    'ENTRADA': 'Entrada',
    'PRATO_PRINCIPAL': 'Prato Principal',
    'SOBREMESA': 'Sobremesa',
    'BEBIDA': 'Bebida',
}


@dataclass
class MenuItemSnapshot:
    """Representação de um item do cardápio obtida via MenuCatalogPort.

    É o tipo retornado pelo cardapio-service (via Adapter) e consumido pelo
    PedidoBuilder — não é um model do Django.
    """

    id: int
    nome: str
    categoria: str
    preco: Decimal
    disponivel: bool

    def get_categoria_display(self) -> str:
        return CATEGORIA_LABELS.get(self.categoria, self.categoria)


@dataclass
class OrderItemEntity:
    menu_item_id: int
    nome_snapshot: str
    categoria_snapshot: str
    quantidade: int
    preco_unit: Decimal
    subtotal: Decimal


@dataclass
class OrderEntity:
    items: list[OrderItemEntity] = field(default_factory=list)
    observacoes: str = ''
    total: Decimal = Decimal('0')
    status: str = 'RECEBIDO'
    pago: bool = False
    forma_pagamento: str = ''
    id: int | None = None

    def proximo_status(self) -> str | None:
        idx = STATUS_FLOW.index(self.status)
        if idx < len(STATUS_FLOW) - 1:
            return STATUS_FLOW[idx + 1]
        return None

    def get_status_display(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)

    def get_forma_pagamento_display(self) -> str:
        return PAYMENT_LABELS.get(self.forma_pagamento, self.forma_pagamento)


@dataclass
class NotificationData:
    tipo: str
    mensagem: str
    status_de: str
    status_para: str


@dataclass
class NotificationEntity(NotificationData):
    id: int
    order_id: int
    criado_em: datetime
