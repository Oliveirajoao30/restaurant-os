"""
PADRÃO: STRATEGY
=================
Problema que resolve:
    O restaurante aceita três formas de pagamento (Dinheiro, Cartão de Crédito,
    PIX), cada uma com lógica diferente (cálculo de troco, parcelamento, geração
    de chave PIX). Sem o Strategy, a view teria um bloco if/elif com a lógica de
    cada método misturada — difícil de manter e de estender.

Como está aplicado:
    - PaymentStrategy: interface abstrata com o método process(amount).
    - Estratégias concretas:
        * DinheiroPayment: calcula e retorna o troco.
        * CartaoCreditoPayment: retorna valor por parcela.
        * PixPayment: gera uma chave PIX simulada.
    - PaymentContext: recebe a estratégia escolhida, chama process() e atualiza
      a OrderEntity com os dados do pagamento (a persistência é feita pelo use
      case, via OrderRepository).

Benefício no sistema:
    Adicionar uma nova forma de pagamento (ex: Vale Refeição) significa criar uma
    nova subclasse de PaymentStrategy e registrá-la em build_strategy() — sem
    alterar as classes existentes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal


# ── Interface da Strategy ─────────────────────────────────────────────────────

class PaymentStrategy(ABC):
    """Interface que todas as formas de pagamento devem implementar."""

    @abstractmethod
    def process(self, amount: Decimal) -> dict:
        """
        Processa o pagamento e retorna um dicionário com o recibo.

        O dict retornado deve conter no mínimo:
            - metodo: nome legível da forma de pagamento
            - valor: valor total cobrado
            - status: 'aprovado' ou 'recusado'
            - mensagem: texto descritivo para exibir ao usuário
        """
        ...


# ── Estratégias concretas ─────────────────────────────────────────────────────

class DinheiroPayment(PaymentStrategy):
    """Pagamento em dinheiro com cálculo de troco."""

    def __init__(self, valor_recebido: Decimal) -> None:
        self.valor_recebido = Decimal(str(valor_recebido))

    def process(self, amount: Decimal) -> dict:
        if self.valor_recebido < amount:
            return {
                'metodo': 'Dinheiro',
                'valor': amount,
                'status': 'recusado',
                'mensagem': (
                    f'Valor recebido (R$ {self.valor_recebido:.2f}) é insuficiente '
                    f'para pagar R$ {amount:.2f}.'
                ),
            }
        troco = self.valor_recebido - amount
        return {
            'metodo': 'Dinheiro',
            'valor': amount,
            'valor_recebido': self.valor_recebido,
            'troco': troco,
            'status': 'aprovado',
            'mensagem': f'Pagamento em dinheiro aprovado. Troco: R$ {troco:.2f}.',
        }


class CartaoCreditoPayment(PaymentStrategy):
    """Pagamento no cartão de crédito com suporte a parcelamento."""

    def __init__(self, parcelas: int = 1) -> None:
        if parcelas < 1 or parcelas > 12:
            raise ValueError('Número de parcelas deve ser entre 1 e 12.')
        self.parcelas = parcelas

    def process(self, amount: Decimal) -> dict:
        valor_por_parcela = (amount / self.parcelas).quantize(Decimal('0.01'))
        return {
            'metodo': 'Cartão de Crédito',
            'valor': amount,
            'parcelas': self.parcelas,
            'valor_por_parcela': valor_por_parcela,
            'status': 'aprovado',
            'mensagem': (
                f'Pagamento no cartão aprovado em {self.parcelas}x '
                f'de R$ {valor_por_parcela:.2f}.'
            ),
        }


class PixPayment(PaymentStrategy):
    """Pagamento via PIX com geração de chave simulada."""

    def process(self, amount: Decimal) -> dict:
        import uuid
        chave_pix = str(uuid.uuid4()).upper()[:20]
        return {
            'metodo': 'PIX',
            'valor': amount,
            'chave_pix': chave_pix,
            'status': 'aprovado',
            'mensagem': f'PIX gerado com sucesso. Chave: {chave_pix}. Valor: R$ {amount:.2f}.',
        }


# ── Context ───────────────────────────────────────────────────────────────────

class PaymentContext:
    """
    Contexto que executa a estratégia de pagamento selecionada e aplica o
    resultado na OrderEntity (sem persistir).
    """

    def __init__(self, strategy: PaymentStrategy) -> None:
        self._strategy = strategy

    def set_strategy(self, strategy: PaymentStrategy) -> None:
        """Permite trocar a estratégia em tempo de execução."""
        self._strategy = strategy

    def execute(self, order, valor_final: Decimal | None = None) -> dict:
        """
        Executa o pagamento usando a estratégia configurada.

        1. Chama strategy.process(valor_final ou order.total).
        2. Se aprovado: atualiza order.pago e order.forma_pagamento (em memória).
        3. Retorna o dict de recibo para renderização no template.

        valor_final permite que o use case passe o total já com gorjeta aplicada.
        """
        amount = valor_final if valor_final is not None else order.total
        receipt = self._strategy.process(amount)

        if receipt['status'] == 'aprovado':
            order.pago = True
            order.forma_pagamento = self._strategy_code()

        return receipt

    def _strategy_code(self) -> str:
        """Retorna o código da forma de pagamento para salvar no modelo."""
        if isinstance(self._strategy, DinheiroPayment):
            return 'DINHEIRO'
        if isinstance(self._strategy, CartaoCreditoPayment):
            return 'CARTAO'
        if isinstance(self._strategy, PixPayment):
            return 'PIX'
        return ''


def build_strategy(forma: str, **kwargs) -> PaymentStrategy:
    """Factory simples: cria a estratégia de pagamento a partir do código (DINHEIRO/CARTAO/PIX)."""
    if forma == 'DINHEIRO':
        return DinheiroPayment(Decimal(str(kwargs.get('valor_recebido', '0'))))
    if forma == 'CARTAO':
        return CartaoCreditoPayment(int(kwargs.get('parcelas', 1)))
    if forma == 'PIX':
        return PixPayment()
    raise ValueError(f'Forma de pagamento desconhecida: {forma}')
