"""
PADRÃO: ADAPTER
================
Problema que resolve:
    O pedidos-service precisa consultar o cardápio (itens disponíveis, preços,
    disponibilidade) para montar pedidos, mas esse cardápio agora vive em um
    serviço separado (cardapio-service), exposto via API REST. Os use cases não
    devem conhecer detalhes de HTTP/JSON — apenas a abstração MenuCatalogPort.

Como está aplicado:
    - MenuCatalogPort (application/ports.py): interface que os use cases usam.
    - CardapioServiceHttpAdapter: implementa MenuCatalogPort fazendo chamadas
      HTTP (via requests) para a API do cardapio-service e traduzindo as
      respostas JSON em MenuItemSnapshot.
    - FakeCardapioServiceAdapter: implementação em memória da mesma porta,
      usada em testes e cenários BDD para evitar dependência de rede.

Benefício no sistema:
    Trocar o protocolo de comunicação (ex: gRPC, fila de mensagens) ou apontar
    para outra instância do cardapio-service exige apenas um novo Adapter — os
    use cases (CriarPedidoUseCase, ListarItensDisponiveisUseCase) não mudam.
"""

from __future__ import annotations

from decimal import Decimal

import requests

from orders.application.ports import MenuCatalogPort
from orders.domain.entities import MenuItemSnapshot
from orders.infrastructure.adapters.exceptions import (
    CatalogServiceUnavailableError,
    MenuItemNotFoundError,
)


class CardapioServiceHttpAdapter(MenuCatalogPort):
    """Adapter HTTP para a API REST do cardapio-service (/api/v1/menu-items/)."""

    def __init__(self, base_url: str, timeout: int = 10) -> None:
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout

    def get_item(self, item_id: int) -> MenuItemSnapshot:
        url = f'{self._base_url}/api/v1/menu-items/{item_id}/'
        response = self._get(url)

        if response.status_code == 404:
            raise MenuItemNotFoundError(f'Item {item_id} não encontrado no cardápio.')
        if response.status_code != 200:
            raise CatalogServiceUnavailableError(
                f'cardapio-service retornou status {response.status_code} ao buscar o item {item_id}.'
            )
        return self._to_snapshot(response.json())

    def list_available(self) -> list[MenuItemSnapshot]:
        url = f'{self._base_url}/api/v1/menu-items/'
        response = self._get(url, params={'disponivel': 'true'})

        if response.status_code != 200:
            raise CatalogServiceUnavailableError(
                f'cardapio-service retornou status {response.status_code} ao listar itens disponíveis.'
            )
        return [self._to_snapshot(item) for item in response.json()]

    def _get(self, url: str, **kwargs) -> requests.Response:
        try:
            return requests.get(url, timeout=self._timeout, **kwargs)
        except requests.RequestException as exc:
            raise CatalogServiceUnavailableError(f'cardapio-service indisponível: {exc}') from exc

    def _to_snapshot(self, data: dict) -> MenuItemSnapshot:
        return MenuItemSnapshot(
            id=data['id'],
            nome=data['nome'],
            categoria=data['categoria'],
            preco=Decimal(str(data['preco'])),
            disponivel=data['disponivel'],
        )
