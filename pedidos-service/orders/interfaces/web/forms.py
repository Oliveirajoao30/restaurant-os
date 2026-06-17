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
    PARCELAS_CHOICES = [('', '— Selecione as parcelas —')] + [(i, f'{i}x') for i in range(1, 13)]

    forma = forms.ChoiceField(
        choices=FORMA_CHOICES,
        label='Forma de Pagamento',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='PIX',
    )
    valor_recebido = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Valor Recebido (R$)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    )
    parcelas = forms.ChoiceField(
        choices=PARCELAS_CHOICES,
        required=False,
        label='Número de Parcelas',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    incluir_gorjeta = forms.BooleanField(
        required=False,
        initial=True,
        label='Incluir 10% de serviço (garçom)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    def clean(self):
        cleaned = super().clean()
        forma = cleaned.get('forma')
        if forma == 'DINHEIRO' and not cleaned.get('valor_recebido'):
            self.add_error('valor_recebido', 'Informe o valor recebido para pagamento em dinheiro.')
        if forma == 'CARTAO' and not cleaned.get('parcelas'):
            self.add_error('parcelas', 'Selecione o número de parcelas.')
        return cleaned
