from django.db import models


class Order(models.Model):
    STATUS_CHOICES = [
        ('RECEBIDO', 'Recebido'),
        ('EM_PREPARO', 'Em Preparo'),
        ('PRONTO', 'Pronto'),
        ('ENTREGUE', 'Entregue'),
    ]
    PAYMENT_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO', 'Cartão de Crédito'),
        ('PIX', 'PIX'),
    ]

    STATUS_FLOW = ['RECEBIDO', 'EM_PREPARO', 'PRONTO', 'ENTREGUE']

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEBIDO')
    observacoes = models.TextField(blank=True)
    forma_pagamento = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pago = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f'Pedido #{self.pk} — {self.get_status_display()}'

    def proximo_status(self):
        idx = self.STATUS_FLOW.index(self.status)
        if idx < len(self.STATUS_FLOW) - 1:
            return self.STATUS_FLOW[idx + 1]
        return None


class OrderItem(models.Model):
    """Item de um pedido.

    Não há FK para o cardápio: ``menu_item_id`` referencia o item no
    cardapio-service (outro banco de dados/serviço). ``nome_snapshot`` e
    ``categoria_snapshot`` preservam os dados do item no momento do pedido,
    mesmo que o cardápio mude depois.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item_id = models.PositiveIntegerField()
    nome_snapshot = models.CharField(max_length=120)
    categoria_snapshot = models.CharField(max_length=20)
    quantidade = models.PositiveIntegerField(default=1)
    preco_unit = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.quantidade}x {self.nome_snapshot}'


class Notification(models.Model):
    TIPO_CHOICES = [
        ('COZINHA', 'Cozinha'),
        ('GARCOM', 'Garçom'),
        ('LOG', 'Log do Sistema'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensagem = models.TextField()
    status_de = models.CharField(max_length=20)
    status_para = models.CharField(max_length=20)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'

    def __str__(self):
        return f'[{self.get_tipo_display()}] Pedido #{self.order_id}: {self.status_de} → {self.status_para}'
