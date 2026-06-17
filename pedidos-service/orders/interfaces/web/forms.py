from django import forms


class PedidoForm(forms.Form):
    observacoes = forms.CharField(
        required=False,
        label='Observações',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ex: Sem cebola, bem passado...',
        }),
    )


class PagamentoForm(forms.Form):
    FORMA_CHOICES = [
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO', 'Cartão de Crédito'),
        ('PIX', 'PIX'),
    ]

    forma = forms.ChoiceField(
        choices=FORMA_CHOICES,
        label='Forma de Pagamento',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='PIX',
    )
    incluir_gorjeta = forms.BooleanField(
        required=False,
        initial=True,
        label='Incluir 10% de serviço (garçom)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
