from django.db import models

from catalog.domain.entities import CATEGORIA_CHOICES


class MenuItem(models.Model):
    CATEGORIA_CHOICES = CATEGORIA_CHOICES

    nome = models.CharField(max_length=120)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    disponivel = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['categoria', 'nome']
        verbose_name = 'Item do Cardápio'
        verbose_name_plural = 'Itens do Cardápio'

    def __str__(self):
        return f'{self.nome} ({self.get_categoria_display()}) — R$ {self.preco}'
