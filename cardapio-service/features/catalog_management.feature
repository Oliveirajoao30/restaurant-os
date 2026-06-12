# language: pt
Funcionalidade: Gestão do cardápio
  Como gerente do restaurante
  Quero cadastrar e gerenciar os itens do cardápio
  Para que os clientes possam montar pedidos com itens válidos

  Cenário: Cadastrar um item válido
    Quando eu cadastro o item "Lasanha" na categoria "PRATO_PRINCIPAL" com preço "25.00"
    Então o cadastro deve ser aceito
    E o item "Lasanha" deve estar disponível no cardápio

  Cenário: Rejeitar prato principal abaixo do preço mínimo
    Quando eu cadastro o item "Arroz" na categoria "PRATO_PRINCIPAL" com preço "5.00"
    Então o cadastro deve ser rejeitado com a mensagem "Pratos principais devem custar no mínimo R$ 10,00."

  Cenário: Rejeitar bebida acima do preço máximo
    Quando eu cadastro o item "Vinho Raro" na categoria "BEBIDA" com preço "150.00"
    Então o cadastro deve ser rejeitado com a mensagem "Bebidas não podem custar mais de R$ 100,00."

  Cenário: Desativar um item do cardápio
    Dado que o item "Salada Caesar" esteja cadastrado na categoria "ENTRADA" com preço "18.00"
    Quando eu desativo o item "Salada Caesar"
    Então o item "Salada Caesar" não deve estar disponível no cardápio
