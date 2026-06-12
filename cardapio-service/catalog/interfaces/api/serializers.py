from decimal import Decimal

from rest_framework import serializers

from catalog.domain.entities import CATEGORIA_CHOICES


class MenuItemSerializer(serializers.Serializer):
    """Serializa MenuItemEntity para a API REST (/api/v1/menu-items/)."""

    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(max_length=120)
    categoria = serializers.ChoiceField(choices=CATEGORIA_CHOICES)
    preco = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.01'))
    disponivel = serializers.BooleanField(read_only=True)
