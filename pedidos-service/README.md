# RestaurantOS

Sistema de pedidos para restaurante desenvolvido em Django.
Projeto acadêmico para a disciplina **Arquitetura e Projeto de Software** — Univassouras.

---

## Como rodar localmente

### Pré-requisitos
- Python 3.10 ou superior
- pip

### Passos

```bash
# 1. Entre na pasta do projeto
cd restaurantos

# 2. (Recomendado) Crie um ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Aplique as migrações do banco de dados
python manage.py migrate

# 5. (Opcional) Crie um superusuário para acessar /admin
python manage.py createsuperuser

# 6. Inicie o servidor
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000/**

---

## Fluxo de uso

1. **Cardápio** (`/cardapio/novo/`) — Cadastre itens (Entrada, Prato Principal, Sobremesa, Bebida)
2. **Novo Pedido** (`/pedidos/novo/`) — Selecione itens e quantidades, confirme o pedido
3. **Painel** (`/`) — Veja os pedidos em quatro colunas por status; clique em **Avançar** para mover entre status
4. **Fechar Pedido** — Com o pedido no status "Pronto", clique em **Pagar** e escolha a forma de pagamento
5. **Notificações** (`/notificacoes/`) — Veja o log completo de todas as mudanças de status

---

## Padrões de Projeto implementados

Consulte o arquivo **`PATTERNS.md`** para a documentação detalhada de cada padrão.

| Padrão | Arquivo | Onde é usado |
|--------|---------|--------------|
| Factory | `orders/patterns/factory.py` | Criação de itens do cardápio |
| Builder | `orders/patterns/builder.py` | Montagem de pedidos |
| Observer | `orders/patterns/observer.py` | Notificações de mudança de status |
| Strategy | `orders/patterns/strategy.py` | Processamento de pagamentos |
