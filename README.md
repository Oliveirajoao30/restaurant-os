# RestaurantOS — Cardápio & Pedidos (Microsserviços)

Sistema de gestão de pedidos para restaurante, dividido em **dois microsserviços
Django independentes** que se comunicam via HTTP/REST.

Projeto acadêmico para a disciplina **Arquitetura e Projeto de Software** —
Univassouras. Cobre: divisão em microsserviços, Clean Architecture, SOLID, 5
Design Patterns (Factory, Builder, Observer, Strategy, Adapter), Clean Code,
TDD (pytest) e BDD (behave), Docker/Docker Compose e deploy em nuvem (Render).

---

## Deploy em produção

| Serviço | URL pública |
|---|---|
| `cardapio-service` (catálogo) | _a preencher após o deploy no Render_ |
| `pedidos-service` (pedidos/UI) | _a preencher após o deploy no Render_ |

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

## Testes

### TDD (pytest)

```bash
cd cardapio-service && pytest    # 23 testes
cd pedidos-service && pytest     # 45 testes
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
- **`CARDAPIO_SERVICE_URL`**: em `render.yaml` está como
  `https://cardapio-service.onrender.com`. Se o Render atribuir um sufixo
  diferente ao nome do serviço, ajuste essa variável no dashboard do Render
  (Settings → Environment) após o primeiro deploy.

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
