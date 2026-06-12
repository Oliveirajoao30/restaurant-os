from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

CATEGORIA_CHOICES = [
    ('ENTRADA', 'Entrada'),
    ('PRATO_PRINCIPAL', 'Prato Principal'),
    ('SOBREMESA', 'Sobremesa'),
    ('BEBIDA', 'Bebida'),
]


@dataclass
class MenuItemEntity:
    """Representação de um item do cardápio independente do ORM."""

    nome: str
    categoria: str
    preco: Decimal
    disponivel: bool = True
    id: int | None = None
