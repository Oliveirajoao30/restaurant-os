# language: pt
Funcionalidade: Montagem de pedidos
  Como atendente
  Quero montar pedidos a partir dos itens disponíveis no cardápio
  Para que a cozinha possa prepará-los

  Contexto:
    Dado que o cardápio possui o item "Feijoada" da categoria "PRATO_PRINCIPAL" por "35.00", disponível
    E que o cardápio possui o item "Suco de Laranja" da categoria "BEBIDA" por "8.00", disponível
    E que o cardápio possui o item "Prato Esgotado" da categoria "PRATO_PRINCIPAL" por "20.00", indisponível

  Cenário: Criar um pedido com itens disponíveis
    Quando eu monto um pedido com os itens
      | item            | quantidade |
      | Feijoada        | 2          |
      | Suco de Laranja | 1          |
    Então o pedido deve ser criado com sucesso
    E o total do pedido deve ser "78.00"
    E o pedido deve ter 2 itens

  Cenário: Recusar item indisponível
    Quando eu monto um pedido com os itens
      | item           | quantidade |
      | Prato Esgotado | 1          |
    Então a criação do pedido deve falhar com a mensagem "não está disponível"
