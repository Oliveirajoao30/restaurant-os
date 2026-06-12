# cardapio-service

Microsserviço Django + DRF responsável pelo cadastro do cardápio: itens,
categorias, preços e disponibilidade. Expõe uma API REST consumida pelo
**pedidos-service** (via Adapter HTTP) para montar pedidos.

Faz parte do monorepo `RestaurantOS` — veja o [README raiz](../README.md) para
visão geral da arquitetura.

---

## Como rodar localmente (sem Docker)

```bash
cd cardapio-service
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

Acesse: **http://127.0.0.1:8001/** (redireciona para `/cardapio/`)

Sem `DATABASE_URL` definida, usa SQLite local (`db.sqlite3`).

---

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | _(sqlite local)_ | String de conexão Postgres, ex.: `postgres://user:pass@host:5432/db` |
| `SECRET_KEY` | chave de desenvolvimento | Secret key do Django |
| `DEBUG` | `True` | `False` em produção |
| `ALLOWED_HOSTS` | `*` | Lista separada por vírgula |
| `CSRF_TRUSTED_ORIGINS` | _(vazio)_ | Lista separada por vírgula, ex.: `https://*.onrender.com` |

---

## Telas (UI)

- `/cardapio/` — lista de itens, com toggle de disponibilidade
- `/cardapio/novo/` — cadastrar item (Factory valida por categoria)
- `/cardapio/<pk>/editar/` — editar item
- `/cardapio/<pk>/excluir/` — remover item

## API REST (`/api/v1/menu-items/`)

Consumida pelo `pedidos-service` via `CardapioServiceHttpAdapter`.

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/v1/menu-items/` | Lista itens. Filtro opcional `?disponivel=true` |
| `GET` | `/api/v1/menu-items/<id>/` | Detalhe de um item |
| `POST` | `/api/v1/menu-items/` | Cria item (`nome`, `categoria`, `preco`) — valida via Factory |
| `PUT` | `/api/v1/menu-items/<id>/` | Atualiza item |
| `DELETE` | `/api/v1/menu-items/<id>/` | Remove item |
| `POST` | `/api/v1/menu-items/<id>/toggle_disponibilidade/` | Inverte `disponivel` |

Categorias (`categoria`): `ENTRADA`, `PRATO_PRINCIPAL`, `SOBREMESA`, `BEBIDA`.

Exemplo de resposta:

```json
{"id": 1, "nome": "Feijoada", "categoria": "PRATO_PRINCIPAL", "preco": "35.00", "disponivel": true}
```

Regras de validação (Factory, por categoria):
- Nome não pode ser vazio; preço deve ser > 0.
- `PRATO_PRINCIPAL`: preço mínimo R$ 10,00.
- `BEBIDA`: preço máximo R$ 100,00.

---

## Padrões de projeto neste serviço

Factory (criação de itens por categoria). Documentação completa em
[../PATTERNS.md](../PATTERNS.md).

---

## Testes

```bash
pytest    # unit + integration (TDD) — 23 testes
behave    # BDD — 1 feature, 4 cenários
```
