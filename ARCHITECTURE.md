# Arquitetura

## Visão geral

O sistema original (monólito Django `RestaurantOS`, um único app `orders`) foi
dividido em **2 microsserviços** independentes, cada um com seu próprio banco
de dados e ciclo de deploy:

```
  cardapio-service (Django + DRF)        pedidos-service (Django + UI)
  --------------------------------       -----------------------------
  - Cadastro de itens                    - Montagem de pedidos (Builder)
  - Categorias e preços                  - Fluxo de status (Observer)
  - Disponibilidade                      - Pagamento (Strategy)
  - DB próprio (Postgres)                - Notificações
  - API: GET /api/v1/menu-items/         - DB próprio (Postgres)

           ^------------ HTTP/REST ------------|
              (CardapioServiceHttpAdapter, padrão Adapter)
```

### Por que 2 serviços?

Os dois bounded contexts do domínio são claramente separáveis:

- **Cardápio**: cadastro/edição/disponibilidade de itens — muda com baixa
  frequência, é consultado por qualquer cliente (totem, app, garçom).
- **Pedidos**: criação de pedidos, fluxo de status (cozinha → pronto →
  entregue), pagamento e notificações — muda com alta frequência durante o
  expediente, tem regras de negócio próprias (Builder/Observer/Strategy).

Separar os dois permite escalar/deployar cada um independentemente e evita que
uma falha no fluxo de pedidos afete o cadastro do cardápio (e vice-versa).

---

## Clean Architecture por serviço

Cada serviço é **um app Django** (`catalog` no `cardapio-service`, `orders` no
`pedidos-service`) organizado em 4 camadas. `models.py`, `migrations/`,
`admin.py` e `apps.py` ficam na raiz do app — é uma exigência do Django e
representam a camada de **infrastructure** (persistência).

```
<app>/
├── models.py, migrations/, admin.py, apps.py   # infrastructure (ORM Django)
├── domain/             # entidades puras (dataclasses) + regras de negócio
│                        # (Factory / Builder / Observer / Strategy) — zero Django
├── application/
│   ├── ports.py          # interfaces ABC (repositórios, adapters)
│   └── use_cases.py        # orquestração: ports + domain
├── infrastructure/
│   ├── django_*_repository.py   # implementação dos ports via Django ORM
│   └── adapters/                 # implementação dos ports via HTTP (Adapter)
└── interfaces/
    ├── web/             # views, forms, templates, container.py (composition root)
    └── api/              # serializers/views/urls DRF (só cardapio-service)
```

### Fluxo de uma requisição

```
View (interfaces/web)
  → Use Case (application/use_cases.py)
      → Domain (entities, Factory/Builder/Observer/Strategy — regra de negócio pura)
      → Port (application/ports.py — interface)
          → Repository/Adapter (infrastructure — implementação concreta)
```

A view nunca acessa o ORM ou `requests` diretamente para os fluxos de escrita
e regra de negócio — sempre passa por um use case. Para telas somente-leitura
simples (ex.: listar pedidos no painel), a view consulta o ORM diretamente,
uma simplificação pragmática documentada e aceita para projetos deste porte.

### Composition root

Cada serviço tem `interfaces/web/container.py` com funções `get_*()` que
instanciam repositórios/adapters concretos. As views chamam `container.get_*()`
e passam o resultado para os use cases — não há framework de DI, apenas
**Dependency Inversion** manual via funções factory.

---

## Modelagem cross-service: `OrderItem` sem FK

O `pedidos-service` precisa saber nome, categoria e preço dos itens do pedido,
mas o `MenuItem` agora vive no banco do `cardapio-service` — **não é possível
ter uma Foreign Key entre bancos de dados diferentes**.

Solução: `OrderItem` guarda uma **referência externa** (`menu_item_id`, sem FK)
mais um **snapshot** dos dados no momento da criação do pedido:

```python
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item_id = models.PositiveIntegerField()   # id no cardapio-service (sem FK)
    nome_snapshot = models.CharField(max_length=120)
    categoria_snapshot = models.CharField(max_length=20)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unit = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
```

Justificativa:

- **Sem FK cross-database**: tecnicamente impossível e indesejável (acopla os
  bancos dos dois serviços).
- **Snapshot preserva histórico**: se o preço/nome de um item mudar no
  cardápio depois do pedido feito, o pedido antigo continua mostrando os
  valores cobrados na época — comportamento correto para um sistema de
  pedidos/recibos.
- **`menu_item_id` mantém rastreabilidade**: permite, se necessário, consultar
  o item atual no `cardapio-service`.

O `PedidoBuilder.build()` recebe `MenuItemSnapshot` (vindos do
`CardapioServiceHttpAdapter`) e monta o `OrderEntity`/`OrderItemEntity` já com
os campos de snapshot preenchidos.

---

## Comunicação entre serviços

`pedidos-service` consome `cardapio-service` via HTTP/JSON:

| Operação | Endpoint no cardapio-service |
|---|---|
| Listar itens disponíveis | `GET /api/v1/menu-items/?disponivel=true` |
| Buscar item por id | `GET /api/v1/menu-items/<id>/` |

Implementado pelo **Adapter** `CardapioServiceHttpAdapter`
(`pedidos-service/orders/infrastructure/adapters/cardapio_service_adapter.py`),
que traduz JSON em `MenuItemSnapshot` e mapeia erros HTTP/rede para
`MenuItemNotFoundError` / `CatalogServiceUnavailableError`. Detalhes no
[PATTERNS.md](PATTERNS.md#5-adapter-estrutural).

Em testes (pytest) e cenários BDD, o adapter real é substituído por
`FakeCardapioServiceAdapter` (implementação em memória da mesma porta
`MenuCatalogPort`), evitando dependência de rede.

---

## Infraestrutura

- **Banco de dados**: cada serviço tem seu próprio Postgres (`DATABASE_URL`),
  com fallback para SQLite quando a variável não está definida (dev local e
  testes).
- **Arquivos estáticos**: servidos via WhiteNoise (`CompressedManifestStaticFilesStorage`),
  sem depender de S3/CDN externo — adequado ao free tier do Render.
- **Containers**: cada serviço tem seu `Dockerfile` (`python:3.12-slim` +
  `gunicorn`), que roda `collectstatic` no build e `migrate` no start.
- **Orquestração local**: `docker-compose.yml` na raiz sobe os 2 serviços + 2
  bancos Postgres, com `pedidos-service` apontando para
  `CARDAPIO_SERVICE_URL=http://cardapio-service:8000` (nome do serviço na rede
  Docker).
- **Deploy**: `render.yaml` (Blueprint) provisiona 2 web services Docker + 2
  bancos Postgres free no Render.
