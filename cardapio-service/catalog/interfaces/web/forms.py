from django import forms

from catalog.domain.entities import CATEGORIA_CHOICES


class MenuItemForm(forms.Form):
    nome = forms.CharField(
        max_length=120,
        label='Nome',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Frango Grelhado'}),
    )
    categoria = forms.ChoiceField(
        choices=CATEGORIA_CHOICES,
        label='Categoria',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    preco = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=0.01,
        label='Preço (R$)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
