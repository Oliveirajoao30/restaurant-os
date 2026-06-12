# Padrões de Projeto — RestaurantOS

## 1. Factory (Criacional)

**Arquivo:** `orders/patterns/factory.py`
**Ativado em:** `orders/services/cardapio_service.py` → `criar_item()`
**View que usa:** `cardapio_create` (POST `/cardapio/novo/`)

### Problema que resolve
Itens do cardápio pertencem a categorias diferentes (Entrada, Prato Principal, Sobremesa, Bebida), cada uma com suas próprias regras de validação. Sem a Factory, essa lógica estaria espalhada pelas views, tornando difícil adicionar novas categorias.

### Como está implementado
```
MenuItemFactory.create(categoria, nome, preco)
  │
  ├── Busca a classe concreta no _registry (dict categoria → classe)
  ├── Instancia EntradaProduct | PratoPrincipalProduct | SobremesaProduct | BebidaProduct
  ├── Chama product.validate() — lança ValidationError se inválido
  └── Persiste e retorna o MenuItem ORM
```

### Benefício
Adicionar uma nova categoria = criar uma subclasse de `AbstractMenuItemProduct` + uma linha no `_registry`. Zero alterações no código existente (Open/Closed Principle).

---

## 2. Builder (Criacional)

**Arquivo:** `orders/patterns/builder.py`
**Ativado em:** `orders/services/pedido_service.py` → `criar_pedido()`
**View que usa:** `pedido_novo` (POST `/pedidos/novo/`)

### Problema que resolve
Um pedido é composto por N itens com quantidades variáveis, observações e cálculo de total. Construir tudo de uma vez seria confuso e permitiria criar pedidos parcialmente formados. O Builder acumula o estado em memória e só persiste quando `.build()` é chamado.

### Como está implementado
```python
# Interface fluente — cada método retorna self
order = (
    PedidoBuilder()
    .add_item(frango, 2)
    .add_item(suco, 1)
    .set_observacoes('Sem cebola')
    .build()  # ← único ponto de escrita no banco (transaction.atomic)
)
```

### Benefício
Se qualquer validação falhar antes de `.build()`, nada é gravado. O total é calculado automaticamente dentro do `build()`.

---

## 3. Observer (Comportamental)

**Arquivo:** `orders/patterns/observer.py`
**Ativado em:** `orders/services/status_service.py` → `avancar_status()`
**View que usa:** `pedido_avancar_status` (POST `/pedidos/<pk>/avancar/`)

### Problema que resolve
Quando o status de um pedido muda, a cozinha precisa ser alertada (novo pedido entrando em preparo), o garçom precisa ser avisado (pedido pronto para entrega), e o sistema precisa registrar todas as transições. Sem o Observer, toda essa lógica ficaria acoplada dentro da view.

### Como está implementado
```
OrderStatusSubject.advance_status(order)
  │
  ├── Calcula próximo status (RECEBIDO → EM_PREPARO → PRONTO → ENTREGUE)
  ├── Salva o Order
  └── notify() dispara para todos os observers registrados:
        ├── KitchenNotifier → cria Notification(tipo='COZINHA') em RECEBIDO→EM_PREPARO
        ├── WaiterNotifier  → cria Notification(tipo='GARCOM') em PRONTO e ENTREGUE
        └── OrderLogger     → cria Notification(tipo='LOG') em TODAS as transições
```

### Benefício
Para adicionar um novo canal (ex: SMS, email), basta criar uma nova subclasse de `OrderObserver` e chamar `subject.attach(NovoObserver())` — sem alterar código existente.

---

## 4. Strategy (Comportamental)

**Arquivo:** `orders/patterns/strategy.py`
**Ativado em:** `orders/services/pagamento_service.py` → `processar_pagamento()`
**View que usa:** `pedido_fechar` (POST `/pedidos/<pk>/fechar/`)

### Problema que resolve
Cada forma de pagamento tem lógica diferente: Dinheiro calcula troco, Cartão de Crédito divide em parcelas, PIX gera uma chave. Sem o Strategy, a view teria um bloco `if/elif` com toda essa lógica — difícil de manter e de estender.

### Como está implementado
```
PaymentContext(strategy=DinheiroPayment(valor_recebido=50.00))
  │
  └── .execute(order)
        ├── Chama strategy.process(order.total)  ← lógica encapsulada na estratégia
        ├── Se aprovado: order.pago = True; order.save()
        └── Retorna dict com recibo para o template
```

### Estratégias disponíveis
| Classe | Lógica |
|--------|--------|
| `DinheiroPayment(valor_recebido)` | Calcula troco = recebido − total |
| `CartaoCreditoPayment(parcelas)` | Calcula valor por parcela |
| `PixPayment()` | Gera chave PIX simulada (UUID) |

### Benefício
Adicionar Vale Refeição = criar `ValeRefeicaoPayment(PaymentStrategy)` e registrá-lo no formulário. Nenhuma das classes existentes precisa ser modificada.

---

## Resumo visual

```
Request HTTP                  Service Layer              Pattern Layer
─────────────────────────────────────────────────────────────────────
POST /cardapio/novo/     → cardapio_service         → [FACTORY]  MenuItemFactory
POST /pedidos/novo/      → pedido_service           → [BUILDER]  PedidoBuilder
POST /pedidos/<pk>/avancar → status_service         → [OBSERVER] OrderStatusSubject
POST /pedidos/<pk>/fechar  → pagamento_service      → [STRATEGY] PaymentContext
```
