# RestaurantOS — Cardápio & Pedidos (Microsserviços)

Sistema de gestão de pedidos para restaurante, dividido em **dois microsserviços
Django independentes** que se comunicam via HTTP/REST.

Projeto acadêmico para a disciplina **Arquitetura e Projeto de Software** —
Univassouras. Cobre: divisão em microsserviços, Clean Architecture, SOLID, 5
Design Patterns (Factory, Builder, Observer, Strategy, Adapter), Clean Code,
TDD (pytest) e BDD (behave), Docker/Docker Compose e deploy em nuvem (Render).

---

## Descrição do Problema

Um restaurante opera com três papéis distintos: **caixa** (registra pedidos e fecha a conta),
**cozinha** (prepara os pratos) e **garçom** (entrega e atualiza o status). O fluxo de um pedido
percorre quatro estados: `RECEBIDO → EM_PREPARO → PRONTO → ENTREGUE`, e cada transição precisa
notificar os envolvidos sem que a lógica de negócio fique acoplada às notificações.

O cardápio é gerenciado separadamente: cada categoria de item tem regras próprias de preço
(prato principal tem preço mínimo, bebida tem preço máximo) e a disponibilidade pode mudar a
qualquer momento. Manter cardápio e pedidos no mesmo serviço criaria um acoplamento que dificultaria
evoluir cada domínio de forma independente.

No fechamento, o pagamento aceita três métodos (Dinheiro, Cartão de Crédito, PIX) com uma gorjeta
opcional de 10% para o garçom. Cada método tem lógica diferente e precisa ser extensível sem
modificar o código existente.

A solução em microsserviços resolve esses desafios com domínios isolados, padrões de projeto
adequados a cada problema e comunicação via API REST.

---

## Deploy em produção

| Serviço | URL pública |
|---|---|
| `cardapio-service` (catálogo) | https://cardapio-service-yo0i.onrender.com |
| `pedidos-service` (pedidos/UI) | https://pedidos-service-st78.onrender.com |

Acesse o `pedidos-service` para usar a aplicação — ele consome o `cardapio-service`
internamente via HTTP.

---

## Arquitetura

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

Cada serviço é um app Django independente com **Clean Architecture** em camadas:
`domain/` (entidades + regras de negócio puras), `application/` (ports + use
cases), `infrastructure/` (repositórios ORM + adapters HTTP),
`interfaces/` (views/templates/API).

Detalhes completos: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

---

## Design Patterns

| # | Padrão | Onde |
|---|---|---|
| 1 | **Factory** | `cardapio-service` — criação de itens do cardápio por categoria |
| 2 | **Builder** | `pedidos-service` — montagem de pedidos com múltiplos itens |
| 3 | **Observer** | `pedidos-service` — notificações ao avançar o status do pedido |
| 4 | **Strategy** | `pedidos-service` — formas de pagamento (Dinheiro/Cartão/PIX) |
| 5 | **Adapter** | `pedidos-service` — comunicação HTTP com o `cardapio-service` |

Detalhes, problema resolvido e benefício de cada padrão:
**[PATTERNS.md](PATTERNS.md)**.

Princípios SOLID aplicados (com exemplos de código): **[SOLID.md](SOLID.md)**.

---

## Como rodar localmente com Docker Compose

Pré-requisitos: Docker + Docker Compose.

```bash
docker compose up --build
```

Isso sobe 4 containers:
- `db-cardapio` e `db-pedidos` (Postgres)
- `cardapio-service` em **http://localhost:8001**
- `pedidos-service` em **http://localhost:8000**

Ambos os serviços rodam `migrate` automaticamente ao iniciar.

Para encerrar e remover os volumes (zera os bancos):

```bash
docker compose down -v
```

---

## Como rodar cada serviço standalone (sem Docker)

Cada serviço tem um `requirements.txt`, `manage.py` e testes próprios. Sem a
variável `DATABASE_URL` definida, ambos caem para **SQLite local**.

```bash
cd cardapio-service   # ou pedidos-service
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001   # cardapio-service
# python manage.py runserver 8000 # pedidos-service
```

O `pedidos-service` precisa saber onde está o `cardapio-service`:

```bash
set CARDAPIO_SERVICE_URL=http://localhost:8001   # Windows
```

Instruções detalhadas: [cardapio-service/README.md](cardapio-service/README.md)
e [pedidos-service/README.md](pedidos-service/README.md).

---

## Evidências de Clean Code

| Prática | Exemplo no código |
|---|---|
| **Nomes que revelam intenção** | `ProcessarPagamentoUseCase`, `AvancarStatusUseCase`, `PedidoBuilder` — o nome diz exatamente o que faz |
| **Sem magic numbers** | `GORJETA_PERCENTUAL = Decimal('0.10')` em `use_cases.py` — constante nomeada |
| **Funções pequenas e coesas** | Cada use case expõe um único método `execute()` com responsabilidade única |
| **Separação view/lógica** | Views Django apenas coordenam (validam form, chamam use case, renderizam template) — zero lógica de negócio |
| **Snapshots para integridade** | `OrderItemEntity` armazena `nome_snapshot` e `preco_unit` no momento do pedido, preservando histórico mesmo que o cardápio mude depois |
| **Fakes em vez de mocks** | `FakeCardapioServiceAdapter` e `FakeOrderRepository` implementam as mesmas interfaces de produção — testes sem `patch()` frágeis |
| **Composition root isolado** | `container.py` é o único arquivo que instancia dependências concretas; os use cases nunca importam infraestrutura diretamente |
| **Exceções de domínio** | `MenuItemNotFoundError`, `CatalogServiceUnavailableError`, `ValidationError` — erros com contexto semântico, não `Exception` genérico |

---

## Testes

### TDD (pytest)

```bash
cd cardapio-service && pytest    # 23 testes
cd pedidos-service && pytest     # 46 testes
```

### BDD (behave)

```bash
cd cardapio-service && behave    # 1 feature, 4 cenários
cd pedidos-service && behave     # 3 features, 6 cenários
```

---

## Notas sobre o deploy no Render (free tier)

- **Cold start**: serviços no plano free hibernam após inatividade; a primeira
  requisição pode levar 30–60 s para responder.
- **Timeout do Adapter**: o `CardapioServiceHttpAdapter` tem `timeout=10 s`.
  Aumentar para 60 s (`CARDAPIO_SERVICE_URL` via env var) se o cold start do
  `cardapio-service` for mais lento quando chamado pelo `pedidos-service`.
- **CSRF_TRUSTED_ORIGINS**: necessário para formulários POST no `pedidos-service`
  em produção — já configurado em `render.yaml` como `https://*.onrender.com`.
- **Postgres free**: o banco Postgres gratuito do Render expira após 90 dias;
  se a avaliação ocorrer depois, recreie o banco e re-faça o deploy.
- **`CARDAPIO_SERVICE_URL`**: configurado em `render.yaml` como
  `https://cardapio-service-yo0i.onrender.com` (URL atribuída pelo Render).

---

## Justificativa Técnica das Escolhas

| Escolha | Justificativa |
|---|---|
| **Django** | Ecossistema maduro (ORM, forms, templates, admin, migrations) que permite focar na arquitetura sem reimplementar infraestrutura. DRF adiciona serialização REST com mínimo de código. |
| **Dois microsserviços independentes** | Cardápio e pedidos têm domínios diferentes, taxas de mudança diferentes (cardápio evolui com o menu; pedidos evoluem com o fluxo operacional) e podem ser escalados, versionados e deployados de forma independente. |
| **Clean Architecture em camadas** | Isola as regras de negócio (`domain/`) de frameworks e bancos de dados. Trocar Django por FastAPI ou SQLite por MongoDB afeta apenas `infrastructure/` e `interfaces/`, sem tocar nos use cases. |
| **SQLite (dev) + Postgres (prod)** | SQLite é zero-configuração para desenvolvimento local (sem Docker obrigatório). Postgres em produção garante concorrência, integridade transacional e suporte a conexões simultâneas de múltiplos workers do gunicorn. |
| **pytest + behave** | `pytest` para TDD: testes escritos antes da implementação guiam o design das classes. `behave` para BDD: cenários `.feature` em português descrevem comportamento de negócio de forma legível por qualquer parte interessada (professor, cliente). |
| **Ports & Adapters (Hexagonal)** | `MenuCatalogPort` desacopla os use cases do protocolo de comunicação. Em testes e BDD, `FakeCardapioServiceAdapter` substitui o HTTP sem alterar nenhum use case — o mesmo padrão permitiria trocar REST por gRPC ou fila de mensagens. |
| **Render (deploy)** | Suporte nativo a Docker, auto-deploy via `render.yaml` no push do GitHub, plano gratuito com Postgres incluído — suficiente para avaliação acadêmica sem custo. |
| **Padrões de domínio escolhidos** | Factory onde a criação envolve validações por tipo; Builder para construção incremental com validação ao final; Observer para notificações sem acoplar quem notifica a quem é notificado; Strategy para algoritmos intercambiáveis de pagamento; Adapter para tradução de protocolo externo em interface interna. Cada padrão resolve um problema específico — detalhes em [PATTERNS.md](PATTERNS.md). |

---

## Estrutura do monorepo

```
.
├── cardapio-service/   # Django + DRF — catálogo (Factory pattern)
├── pedidos-service/    # Django — pedidos/pagamento/notificações (Builder, Observer, Strategy, Adapter)
├── docker-compose.yml  # orquestração local (2 serviços + 2 bancos Postgres)
├── render.yaml         # Blueprint de deploy no Render
├── ARCHITECTURE.md
├── SOLID.md
└── PATTERNS.md
```
