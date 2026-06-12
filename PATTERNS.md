# Padrões de Projeto

5 padrões implementados, um por bounded context/fluxo, organizados pelas
camadas de Clean Architecture (`domain/` para a lógica do padrão,
`application/use_cases.py` para a orquestração, `interfaces/web/` para a
view que aciona o fluxo).

---

## 1. Factory (Criacional)

**Serviço:** `cardapio-service`
**Arquivo:** `catalog/domain/factory.py`
**Usado em:** `catalog/application/use_cases.py` → `CriarItemUseCase`
**View:** `cardapio_create` (POST `/cardapio/novo/`) e API `POST /api/v1/menu-items/`

### Problema que resolve

Itens do cardápio pertencem a categorias diferentes (Entrada, Prato Principal,
Sobremesa, Bebida), cada uma com suas próprias regras de validação (ex.: prato
principal tem preço mínimo, bebida tem preço máximo). Sem a Factory, essa
lógica estaria espalhada pelas views/use cases.

### Como está implementado

```
MenuItemFactory.create_entity(categoria, nome, preco)
  │
  ├── Busca a classe concreta no _registry (dict categoria → classe)
  ├── Instancia EntradaProduct | PratoPrincipalProduct | SobremesaProduct | BebidaProduct
  ├── Chama product.validate() — lança ValidationError se inválido
  └── Retorna um MenuItemEntity (não persiste — quem persiste é o MenuRepository)
```

### Benefício

Adicionar uma nova categoria = criar uma subclasse de `AbstractMenuItemProduct`
+ uma chamada a `MenuItemFactory.register(...)`. Zero alterações no código
existente (Open/Closed Principle).

---

## 2. Builder (Criacional)

**Serviço:** `pedidos-service`
**Arquivo:** `orders/domain/builder.py`
**Usado em:** `orders/application/use_cases.py` → `CriarPedidoUseCase`
**View:** `pedido_novo` (POST `/pedidos/novo/`)

### Problema que resolve

Um pedido é composto por N itens com quantidades variáveis, observações e
cálculo de total. Construir tudo de uma vez seria confuso e permitiria criar
pedidos parcialmente formados. O Builder acumula o estado em memória e só
retorna o `OrderEntity` completo quando `.build()` é chamado.

### Como está implementado

```python
order_entity = (
    PedidoBuilder()
    .add_item(feijoada_snapshot, 2)   # MenuItemSnapshot vindo do cardapio-service
    .add_item(suco_snapshot, 1)
    .set_observacoes('Sem cebola')
    .build()   # retorna OrderEntity, sem persistir
)
order = order_repository.create(order_entity)   # persistência fica no use case/repository
```

`add_item()` rejeita quantidade < 1 e itens com `disponivel=False`; itens
repetidos têm a quantidade somada. `build()` calcula `subtotal`/`total` e
preenche o snapshot (`nome_snapshot`, `categoria_snapshot`) de cada
`OrderItemEntity`.

### Benefício

Se qualquer validação falhar antes de `.build()`, nada é gravado. O total e os
snapshots são calculados em um único lugar.

---

## 3. Observer (Comportamental)

**Serviço:** `pedidos-service`
**Arquivo:** `orders/domain/observer.py`
**Usado em:** `orders/application/use_cases.py` → `AvancarStatusUseCase`
**View:** `pedido_avancar_status` (POST `/pedidos/<pk>/avancar/`)

### Problema que resolve

Quando o status de um pedido muda, a cozinha precisa ser alertada (pedido
entrando em preparo), o garçom precisa ser avisado (pedido pronto/entregue), e
o sistema precisa registrar todas as transições em um log de auditoria. Sem o
Observer, essa lógica ficaria acoplada dentro da view/use case.

### Como está implementado

```
OrderStatusSubject.advance_status(order)
  │
  ├── Calcula o próximo status (RECEBIDO → EM_PREPARO → PRONTO → ENTREGUE)
  ├── Levanta ValueError se o pedido já está em ENTREGUE (status final)
  └── notify() dispara para todos os observers registrados:
        ├── KitchenNotifier → NotificationData(tipo='COZINHA') em → EM_PREPARO
        ├── WaiterNotifier  → NotificationData(tipo='GARCOM')  em → PRONTO / → ENTREGUE
        └── OrderLogger     → NotificationData(tipo='LOG')     em TODAS as transições
```

`AvancarStatusUseCase` persiste o novo status (`OrderRepository.update_status`)
e cada `NotificationData` retornada (`NotificationRepository.create`). Os
observers são montados em `container.get_status_subject()`.

### Benefício

Para adicionar um novo canal (ex.: e-mail), basta criar uma nova subclasse de
`OrderObserver` e chamar `subject.attach(NovoObserver())` no `container.py` —
sem alterar `OrderStatusSubject` nem os observers existentes.

---

## 4. Strategy (Comportamental)

**Serviço:** `pedidos-service`
**Arquivo:** `orders/domain/strategy.py`
**Usado em:** `orders/application/use_cases.py` → `ProcessarPagamentoUseCase`
**View:** `pedido_fechar` (POST `/pedidos/<pk>/fechar/`)

### Problema que resolve

Cada forma de pagamento tem lógica diferente: Dinheiro calcula troco, Cartão de
Crédito divide em parcelas, PIX gera uma chave. Sem o Strategy, o use case
teria um bloco `if/elif` com toda essa lógica — difícil de manter e estender.

### Como está implementado

```
PaymentContext(strategy=build_strategy('DINHEIRO', valor_recebido=100))
  │
  └── .execute(order, valor_final)
        ├── strategy.process(valor_final)   ← lógica encapsulada na estratégia
        ├── Se aprovado: order.pago = True; order.forma_pagamento = <código>
        └── Retorna dict (recibo) usado pelo use case/template
```

### Estratégias disponíveis

| Classe | Lógica |
|--------|--------|
| `DinheiroPayment(valor_recebido)` | Calcula troco = recebido − total (ou recusa se insuficiente) |
| `CartaoCreditoPayment(parcelas)` | Valida 1–12 parcelas e calcula valor por parcela |
| `PixPayment()` | Gera chave PIX simulada (UUID) |

`build_strategy(forma, **kwargs)` é uma factory simples que instancia a
estratégia certa a partir do código (`DINHEIRO`/`CARTAO`/`PIX`).
`ProcessarPagamentoUseCase` aplica gorjeta opcional de 10% antes de chamar o
`PaymentContext`.

### Benefício

Adicionar Vale Refeição = criar `ValeRefeicaoPayment(PaymentStrategy)` e
registrá-la em `build_strategy()`. Nenhuma classe existente é modificada.

---

## 5. Adapter (Estrutural)

**Serviço:** `pedidos-service`
**Arquivo:** `orders/infrastructure/adapters/cardapio_service_adapter.py`
**Porta:** `orders/application/ports.py` → `MenuCatalogPort`
**Usado em:** `CriarPedidoUseCase`, `ListarItensDisponiveisUseCase`
**Views:** `pedido_novo` (GET/POST `/pedidos/novo/`)

### Problema que resolve

Após o split em microsserviços, o catálogo de itens (`MenuItem`) passou a
viver em outro serviço (`cardapio-service`), acessível só via API REST. Os use
cases de `pedidos-service` não devem conhecer detalhes de HTTP/JSON — apenas
uma abstração que devolve itens do cardápio.

### Como está implementado

```
MenuCatalogPort (interface)              ← o que os use cases conhecem
  ├── get_item(item_id) -> MenuItemSnapshot
  └── list_available() -> list[MenuItemSnapshot]

CardapioServiceHttpAdapter(MenuCatalogPort)   ← Adapter real
  - GET {base_url}/api/v1/menu-items/<id>/
  - GET {base_url}/api/v1/menu-items/?disponivel=true
  - Traduz JSON -> MenuItemSnapshot
  - Erros de rede/HTTP -> CatalogServiceUnavailableError / MenuItemNotFoundError

FakeCardapioServiceAdapter(MenuCatalogPort)   ← Adapter em memória (testes/BDD)
  - add_item(snapshot) / get_item() / list_available() sem rede
```

`container.get_menu_catalog_port()` é o único ponto que decide qual Adapter
usar (lê `settings.CARDAPIO_SERVICE_URL`). Em testes e steps do `behave`, o
`FakeCardapioServiceAdapter` é injetado no lugar do adapter HTTP.

### Benefício

Trocar o protocolo de comunicação (ex.: gRPC, fila de mensagens) ou apontar
para outra instância do `cardapio-service` exige apenas um novo Adapter —
`CriarPedidoUseCase`, `ListarItensDisponiveisUseCase`, `PedidoBuilder` e as
views não mudam. É o que viabiliza testar o fluxo completo de criação de
pedidos sem rede (via `FakeCardapioServiceAdapter`).

---

## Resumo visual

```
Request HTTP                        Use Case                       Pattern (domain/)
──────────────────────────────────────────────────────────────────────────────────
POST /cardapio/novo/         → CriarItemUseCase              → [FACTORY]   MenuItemFactory
GET  /pedidos/novo/          → ListarItensDisponiveisUseCase → [ADAPTER]   MenuCatalogPort
POST /pedidos/novo/          → CriarPedidoUseCase            → [BUILDER]   PedidoBuilder
                                                              → [ADAPTER]   MenuCatalogPort
POST /pedidos/<pk>/avancar/  → AvancarStatusUseCase          → [OBSERVER]  OrderStatusSubject
POST /pedidos/<pk>/fechar/   → ProcessarPagamentoUseCase     → [STRATEGY]  PaymentContext
```
