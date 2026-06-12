from __future__ import annotations

from catalog.application.ports import MenuRepository
from catalog.domain.entities import MenuItemEntity
from catalog.models import MenuItem


class DjangoMenuRepository(MenuRepository):
    """Implementação do MenuRepository usando o Django ORM."""

    def _to_entity(self, obj: MenuItem) -> MenuItemEntity:
        return MenuItemEntity(
            id=obj.pk,
            nome=obj.nome,
            categoria=obj.categoria,
            preco=obj.preco,
            disponivel=obj.disponivel,
        )

    def get_by_id(self, item_id: int) -> MenuItemEntity:
        return self._to_entity(MenuItem.objects.get(pk=item_id))

    def list(self, disponivel: bool | None = None) -> list[MenuItemEntity]:
        qs = MenuItem.objects.all()
        if disponivel is not None:
            qs = qs.filter(disponivel=disponivel)
        return [self._to_entity(obj) for obj in qs]

    def create(self, item: MenuItemEntity) -> MenuItemEntity:
        obj = MenuItem.objects.create(
            nome=item.nome,
            categoria=item.categoria,
            preco=item.preco,
            disponivel=item.disponivel,
        )
        return self._to_entity(obj)

    def update(self, item_id: int, item: MenuItemEntity) -> MenuItemEntity:
        obj = MenuItem.objects.get(pk=item_id)
        obj.nome = item.nome
        obj.categoria = item.categoria
        obj.preco = item.preco
        obj.save(update_fields=['nome', 'categoria', 'preco'])
        return self._to_entity(obj)

    def toggle_disponibilidade(self, item_id: int) -> MenuItemEntity:
        obj = MenuItem.objects.get(pk=item_id)
        obj.disponivel = not obj.disponivel
        obj.save(update_fields=['disponivel'])
        return self._to_entity(obj)

    def delete(self, item_id: int) -> None:
        MenuItem.objects.filter(pk=item_id).delete()
