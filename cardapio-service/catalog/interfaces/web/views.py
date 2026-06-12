from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from catalog.application.use_cases import (
    AtualizarItemUseCase,
    CriarItemUseCase,
    DeletarItemUseCase,
    ListarItensUseCase,
    ToggleDisponibilidadeUseCase,
)
from catalog.domain.entities import CATEGORIA_CHOICES
from catalog.infrastructure.django_menu_repository import DjangoMenuRepository
from catalog.interfaces.web.forms import MenuItemForm
from catalog.models import MenuItem


def _repository() -> DjangoMenuRepository:
    return DjangoMenuRepository()


def cardapio_list(request):
    """Lista todos os itens do cardápio."""
    categoria_filtro = request.GET.get('categoria', '')
    itens = ListarItensUseCase(_repository()).execute()
    if categoria_filtro:
        itens = [item for item in itens if item.categoria == categoria_filtro]
    return render(request, 'catalog/cardapio_list.html', {
        'itens': itens,
        'categorias': CATEGORIA_CHOICES,
        'categoria_ativa': categoria_filtro,
    })


def cardapio_create(request):
    """Cria um novo item do cardápio via MenuItemFactory (Factory Pattern)."""
    if request.method == 'POST':
        form = MenuItemForm(request.POST)
        if form.is_valid():
            try:
                CriarItemUseCase(_repository()).execute(
                    categoria=form.cleaned_data['categoria'],
                    nome=form.cleaned_data['nome'],
                    preco=form.cleaned_data['preco'],
                )
                messages.success(request, 'Item adicionado ao cardápio com sucesso!')
                return redirect('cardapio_list')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = MenuItemForm()
    return render(request, 'catalog/cardapio_create.html', {'form': form})


def cardapio_toggle(request, pk):
    """Ativa/desativa um item do cardápio."""
    if request.method == 'POST':
        item = ToggleDisponibilidadeUseCase(_repository()).execute(pk)
        estado = 'ativado' if item.disponivel else 'desativado'
        messages.info(request, f'Item "{item.nome}" foi {estado}.')
    return redirect('cardapio_list')


def cardapio_edit(request, pk):
    """Edita um item do cardápio, reaplicando a validação da MenuItemFactory."""
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemForm(request.POST)
        if form.is_valid():
            try:
                AtualizarItemUseCase(_repository()).execute(
                    item_id=pk,
                    categoria=form.cleaned_data['categoria'],
                    nome=form.cleaned_data['nome'],
                    preco=form.cleaned_data['preco'],
                )
                messages.success(request, f'Item "{form.cleaned_data["nome"]}" atualizado com sucesso!')
                return redirect('cardapio_list')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = MenuItemForm(initial={
            'categoria': item.categoria,
            'nome': item.nome,
            'preco': item.preco,
        })
    return render(request, 'catalog/cardapio_edit.html', {'form': form, 'item': item})


def cardapio_delete(request, pk):
    """Exclui um item do cardápio, com tela de confirmação."""
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        DeletarItemUseCase(_repository()).execute(pk)
        messages.success(request, f'Item "{item.nome}" excluído com sucesso.')
        return redirect('cardapio_list')
    return render(request, 'catalog/cardapio_delete.html', {'item': item})
