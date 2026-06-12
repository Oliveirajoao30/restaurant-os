# pedidos-service

Microsserviço Django (UI + lógica de negócio) responsável por: montagem de
pedidos, fluxo de status (cozinha → pronto → entregue), pagamento e
notificações. Consome o **cardapio-service** via HTTP para saber quais itens
existem, seus preços e disponibilidade.

Faz parte do monorepo `RestaurantOS` — veja o [README raiz](../README.md) para
visão geral da arquitetura.

---

## Como rodar localmente (sem Docker)

```bash
cd pedidos-service
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

Acesse: **http://127.0.0.1:8000/**

Sem `DATABASE_URL` definida, usa SQLite local (`db.sqlite3`).

### Pré-requisito: cardapio-service rodando

Este serviço precisa do `cardapio-service` no ar para listar/validar itens do
cardápio ao criar pedidos. Por padrão aponta para `http://localhost:8001`
(veja variáveis de ambiente abaixo). Suba-o em outro terminal:

```bash
cd ../cardapio-service
python manage.py runserver 8001
```

---

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | _(sqlite local)_ | String de conexão Postgres, ex.: `postgres://user:pass@host:5432/db` |
| `CARDAPIO_SERVICE_URL` | `http://localhost:8001` | Base URL do `cardapio-service` (usada pelo Adapter HTTP e no link de menu da UI) |
| `SECRET_KEY` | chave de desenvolvimento | Secret key do Django |
| `DEBUG` | `True` | `False` em produção |
| `ALLOWED_HOSTS` | `*` | Lista separada por vírgula |
| `CSRF_TRUSTED_ORIGINS` | _(vazio)_ | Lista separada por vírgula, ex.: `https://*.onrender.com` |

---

## Fluxo de uso

1. **Novo Pedido** (`/pedidos/novo/`) — lista os itens disponíveis (consultados
   no `cardapio-service`), seleciona quantidades e cria o pedido (Builder).
2. **Painel** (`/`) — pedidos organizados em colunas por status
   (`RECEBIDO` → `EM_PREPARO` → `PRONTO` → `ENTREGUE`); botão **Avançar**
   move para o próximo status e dispara notificações (Observer).
3. **Fechar Pedido** (`/pedidos/<pk>/fechar/`) — com o pedido `PRONTO` ou
   `ENTREGUE`, escolha a forma de pagamento (Dinheiro/Cartão/PIX) — calcula
   troco, parcelas ou chave PIX (Strategy), com gorjeta opcional de 10%.
4. **Notificações** (`/notificacoes/`) — log de todas as transições de status
   (tipos `COZINHA`, `GARCOM`, `LOG`).
5. **Gerenciar cardápio** — link no menu abre o `cardapio-service` em outra aba.

---

## Padrões de projeto neste serviço

Builder, Observer, Strategy e Adapter. Documentação completa em
[../PATTERNS.md](../PATTERNS.md).

---

## Testes

```bash
pytest    # unit + integration (TDD) — 45 testes
behave    # BDD — 3 features, 6 cenários
```

`pytest` não depende do `cardapio-service` estar no ar (usa
`FakeCardapioServiceAdapter` via monkeypatch). `behave` também usa o fake
adapter — ambos rodam totalmente offline.
