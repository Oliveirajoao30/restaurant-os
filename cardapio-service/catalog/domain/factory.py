"""
PADRÃO: FACTORY (Factory Method)
=================================
Problema que resolve:
    Centralizar e encapsular a criação de itens do cardápio. Cada categoria
    (Entrada, Prato Principal, Sobremesa, Bebida) pode ter regras de validação
    próprias. Sem a Factory, essa lógica ficaria espalhada pelas views/use cases.

Como está aplicado:
    - AbstractMenuItemProduct: interface que define o contrato de validação.
    - Subclasses concretas (EntradaProduct, etc.): implementam validate() com
      regras específicas de cada categoria.
    - MenuItemFactory: registra as categorias e expõe create_entity(), que
      seleciona a classe correta, valida os dados e retorna um MenuItemEntity
      (sem persistir — a persistência é responsabilidade do repositório).

Benefício no sistema:
    O use case só chama MenuItemFactory.create_entity(categoria, nome, preco).
    Não precisa saber qual classe concreta é usada, nem quais regras cada
    categoria aplica.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from django.core.exceptions import ValidationError

from catalog.domain.entities import MenuItemEntity


# ── Produto abstrato ─────────────────────────────────────────────────────────

class AbstractMenuItemProduct(ABC):
    """Interface que todas as categorias de item devem implementar."""

    def __init__(self, nome: str, preco: Decimal) -> None:
        self.nome = nome
        self.preco = preco

    @abstractmethod
    def validate(self) -> None:
        """Levanta ValidationError se os dados violam as regras da categoria."""
        ...

    def _base_validate(self) -> None:
        """Validações comuns a todas as categorias."""
        if not self.nome or not self.nome.strip():
            raise ValidationError('O nome do item não pode ser vazio.')
        if self.preco <= Decimal('0'):
            raise ValidationError('O preço deve ser maior que zero.')


# ── Produtos concretos ────────────────────────────────────────────────────────

class EntradaProduct(AbstractMenuItemProduct):
    def validate(self) -> None:
        self._base_validate()


class PratoPrincipalProduct(AbstractMenuItemProduct):
    def validate(self) -> None:
        self._base_validate()
        if self.preco < Decimal('10.00'):
            raise ValidationError('Pratos principais devem custar no mínimo R$ 10,00.')


class SobremesaProduct(AbstractMenuItemProduct):
    def validate(self) -> None:
        self._base_validate()


class BebidaProduct(AbstractMenuItemProduct):
    def validate(self) -> None:
        self._base_validate()
        if self.preco > Decimal('100.00'):
            raise ValidationError('Bebidas não podem custar mais de R$ 100,00.')


# ── Factory ───────────────────────────────────────────────────────────────────

class MenuItemFactory:
    """
    Factory responsável por validar e criar entidades de itens do cardápio.

    O _registry mapeia o código da categoria para a classe de produto concreta,
    seguindo o princípio Open/Closed: adicionar uma nova categoria é apenas
    registrar uma nova entrada, sem alterar código existente.
    """

    _registry: dict[str, type[AbstractMenuItemProduct]] = {
        'ENTRADA': EntradaProduct,
        'PRATO_PRINCIPAL': PratoPrincipalProduct,
        'SOBREMESA': SobremesaProduct,
        'BEBIDA': BebidaProduct,
    }

    @classmethod
    def create_entity(cls, categoria: str, nome: str, preco: Decimal) -> MenuItemEntity:
        """
        Valida os dados e retorna um MenuItemEntity pronto para ser persistido.

        1. Localiza a classe concreta no registry.
        2. Instancia e chama validate() — lança ValidationError se inválido.
        3. Retorna a entidade (não persiste).
        """
        product_class = cls._registry.get(categoria)
        if product_class is None:
            raise ValidationError(f'Categoria desconhecida: {categoria}')

        product = product_class(nome=nome, preco=preco)
        product.validate()  # pode lançar ValidationError

        return MenuItemEntity(nome=nome.strip(), categoria=categoria, preco=preco, disponivel=True)

    @classmethod
    def register(cls, categoria: str, klass: type[AbstractMenuItemProduct]) -> None:
        """Permite registrar novas categorias sem alterar este arquivo."""
        cls._registry[categoria] = klass
