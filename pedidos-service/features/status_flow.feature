# language: pt
Funcionalidade: Fluxo de status do pedido
  Como cozinha e garçom
  Quero acompanhar o avanço do status dos pedidos
  Para preparar e entregar os pedidos corretamente

  Contexto:
    Dado que o cardápio possui o item "Feijoada" da categoria "PRATO_PRINCIPAL" por "35.00", disponível
    E que existe um pedido criado com os itens
      | item     | quantidade |
      | Feijoada | 1          |

  Cenário: Avançar o pedido até ENTREGUE gerando notificações
    Quando eu avanço o status do pedido
    Então o status do pedido deve ser "EM_PREPARO"
    E deve haver notificações dos tipos "COZINHA, LOG" para o pedido

    Quando eu avanço o status do pedido
    Então o status do pedido deve ser "PRONTO"
    E deve haver notificações dos tipos "COZINHA, LOG, GARCOM" para o pedido

    Quando eu avanço o status do pedido
    Então o status do pedido deve ser "ENTREGUE"
    E deve haver notificações dos tipos "COZINHA, LOG, GARCOM" para o pedido

  Cenário: Não é possível avançar um pedido que já foi entregue
    Dado que o pedido já está com status "ENTREGUE"
    Quando eu tento avançar o status do pedido
    Então a operação deve falhar com a mensagem "status final"
