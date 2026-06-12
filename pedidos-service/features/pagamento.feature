# language: pt
Funcionalidade: Pagamento do pedido
  Como caixa
  Quero registrar o pagamento de um pedido entregue
  Para fechar a conta do cliente

  Contexto:
    Dado que o cardápio possui o item "Feijoada" da categoria "PRATO_PRINCIPAL" por "35.00", disponível
    E que existe um pedido criado com os itens
      | item     | quantidade |
      | Feijoada | 2          |
    E que o pedido já está com status "ENTREGUE"

  Cenário: Pagamento em dinheiro com troco
    Quando eu pago o pedido em "DINHEIRO" sem gorjeta com valor recebido "100.00"
    Então o pagamento deve ser aprovado
    E o troco deve ser "30.00"
    E o pedido deve estar marcado como pago via "DINHEIRO"

  Cenário: Pagamento via PIX com gorjeta de 10%
    Quando eu pago o pedido em "PIX" com gorjeta
    Então o pagamento deve ser aprovado
    E a gorjeta deve ser "7.00"
    E o valor total cobrado deve ser "77.00"
    E o pedido deve estar marcado como pago via "PIX"
