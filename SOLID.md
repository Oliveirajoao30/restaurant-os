# Princípios SOLID

Para cada princípio, um exemplo concreto do código (com caminho do arquivo).

---

## S — Single Responsibility Principle

Cada classe tem um único motivo para mudar.

- **`pedidos-service/orders/domain/builder.py` — `PedidoBuilder`**: só monta um
  `OrderEntity` a partir de itens/quantidades (acumula estado, calcula
  totais). Não persiste, não valida pagamento, não notifica.
- **`pedidos-service/orders/domain/observer.py` — `KitchenNotifier`,
  `WaiterNotifier`, `OrderLogger`**: cada observer decide se/como reagir a
  *uma* transição de status. `OrderStatusSubject` só orquestra a notificação.
- **`pedidos-service/orders/domain/strategy.py` — `DinheiroPayment`,
  `CartaoCreditoPayment`, `PixPayment`**: cada estratégia conhece apenas sua
  própria lógica de processamento de pagamento.
- **`infrastructure/django_order_repository.py`**: única responsabilidade é
  traduzir `OrderEntity` ↔ modelos Django ORM. Não contém regra de negócio.

---

## O — Open/Closed Principle

Aberto para extensão, fechado para modificação.

- **Factory (`cardapio-service/catalog/domain/factory.py`)**: `MenuItemFactory._registry`
  mapeia categoria → classe de validação. Adicionar uma nova categoria =
  criar uma subclasse de `AbstractMenuItemProduct` + `MenuItemFactory.register(...)`.
  Nenhuma classe existente é alterada.
- **Strategy (`pedidos-service/orders/domain/strategy.py`)**: adicionar uma
  nova forma de pagamento (ex.: Vale Refeição) = criar `ValeRefeicaoPayment(PaymentStrategy)`
  + registrar em `build_strategy()`. `PaymentContext` e as estratégias
  existentes não mudam.
- **Observer (`pedidos-service/orders/domain/observer.py`)**: adicionar um
  novo canal de notificação (ex.: SMS) = criar `SmsNotifier(OrderObserver)` e
  `subject.attach(SmsNotifier())` em `container.py`. `OrderStatusSubject` e os
  observers existentes não mudam.

---

## L — Liskov Substitution Principle

Subtipos devem ser substituíveis pelo tipo base sem alterar o comportamento
esperado pelo cliente.

- **`MenuCatalogPort`** (`pedidos-service/orders/application/ports.py`): tanto
  `CardapioServiceHttpAdapter` (HTTP real) quanto `FakeCardapioServiceAdapter`
  (em memória, usado em testes/BDD) implementam `get_item()` e
  `list_available()` com a mesma assinatura e o mesmo contrato — devolvem
  `MenuItemSnapshot`/`list[MenuItemSnapshot]` ou levantam
  `MenuItemNotFoundError`/`CatalogServiceUnavailableError`. Os use cases
  (`CriarPedidoUseCase`, `ListarItensDisponiveisUseCase`) funcionam
  identicamente com qualquer um dos dois.
- **`PaymentStrategy`**: `DinheiroPayment`, `CartaoCreditoPayment` e
  `PixPayment` são todas usadas via `PaymentContext.execute()` sem nenhum
  `isinstance` no caminho principal — qualquer uma pode substituir a outra
  (o único `isinstance` existe em `_strategy_code()`, apenas para mapear o
  código a salvar no banco, não para alterar o fluxo).

---

## I — Interface Segregation Principle

Interfaces pequenas e específicas, sem métodos que os implementadores não usam.

- **`pedidos-service/orders/application/ports.py`** define três portas
  separadas — `OrderRepository`, `NotificationRepository`, `MenuCatalogPort` —
  em vez de uma única interface "Repository" gigante. Cada use case depende
  apenas da porta que realmente usa:
  - `ListarNotificacoesUseCase` depende só de `NotificationRepository`.
  - `ListarItensDisponiveisUseCase` depende só de `MenuCatalogPort`.
  - `CriarPedidoUseCase` depende de `OrderRepository` **e** `MenuCatalogPort`,
    mas não de `NotificationRepository`.
- **`cardapio-service/catalog/application/ports.py`** define `MenuRepository`
  com apenas os métodos que o catálogo precisa (`get_by_id`, `list`, `create`,
  `update`, `toggle_disponibilidade`, `delete`) — não herda nem expõe nada
  relacionado a pedidos/pagamento.

---

## D — Dependency Inversion Principle

Módulos de alto nível dependem de abstrações, não de implementações concretas.

- Todos os **use cases** (`application/use_cases.py` em ambos os serviços)
  recebem ports (`OrderRepository`, `MenuCatalogPort`, `MenuRepository`, ...)
  via construtor — nunca instanciam `DjangoOrderRepository` ou
  `CardapioServiceHttpAdapter` diretamente.
- **`interfaces/web/container.py`** (composition root) é o único lugar que
  conhece as implementações concretas: `get_order_repository()` retorna
  `DjangoOrderRepository()`, `get_menu_catalog_port()` retorna
  `CardapioServiceHttpAdapter(base_url=settings.CARDAPIO_SERVICE_URL)`. Trocar
  Django ORM por outro banco, ou HTTP por gRPC, exige mudar apenas o
  `container.py` e a nova implementação do port — use cases e domain
  permanecem intocados.
- Nos testes, `monkeypatch.setattr(container, 'get_menu_catalog_port', lambda: fake)`
  injeta `FakeCardapioServiceAdapter` sem tocar nas views nem nos use cases —
  prova prática de que a inversão de dependência está no lugar certo.
