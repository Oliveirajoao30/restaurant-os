from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from catalog.application.use_cases import (
    AtualizarItemUseCase,
    CriarItemUseCase,
    DeletarItemUseCase,
    ListarItensUseCase,
    ToggleDisponibilidadeUseCase,
)
from catalog.infrastructure.django_menu_repository import DjangoMenuRepository
from catalog.interfaces.api.serializers import MenuItemSerializer
from catalog.models import MenuItem


class MenuItemViewSet(viewsets.ViewSet):
    """API REST do catálogo (/api/v1/menu-items/), consumida pelo pedidos-service."""

    def _repository(self) -> DjangoMenuRepository:
        return DjangoMenuRepository()

    def list(self, request):
        disponivel_param = request.query_params.get('disponivel')
        disponivel = None
        if disponivel_param is not None:
            disponivel = disponivel_param.lower() in ('1', 'true', 'sim')

        itens = ListarItensUseCase(self._repository()).execute(disponivel=disponivel)
        serializer = MenuItemSerializer(itens, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        try:
            item = self._repository().get_by_id(int(pk))
        except MenuItem.DoesNotExist as exc:
            raise Http404 from exc
        return Response(MenuItemSerializer(item).data)

    def create(self, request):
        serializer = MenuItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = CriarItemUseCase(self._repository()).execute(
                categoria=serializer.validated_data['categoria'],
                nome=serializer.validated_data['nome'],
                preco=serializer.validated_data['preco'],
            )
        except ValidationError as exc:
            return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MenuItemSerializer(item).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        serializer = MenuItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = AtualizarItemUseCase(self._repository()).execute(
                item_id=int(pk),
                categoria=serializer.validated_data['categoria'],
                nome=serializer.validated_data['nome'],
                preco=serializer.validated_data['preco'],
            )
        except MenuItem.DoesNotExist as exc:
            raise Http404 from exc
        except ValidationError as exc:
            return Response({'detail': exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response(MenuItemSerializer(item).data)

    def destroy(self, request, pk=None):
        try:
            DeletarItemUseCase(self._repository()).execute(int(pk))
        except MenuItem.DoesNotExist as exc:
            raise Http404 from exc
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def toggle_disponibilidade(self, request, pk=None):
        try:
            item = ToggleDisponibilidadeUseCase(self._repository()).execute(int(pk))
        except MenuItem.DoesNotExist as exc:
            raise Http404 from exc
        return Response(MenuItemSerializer(item).data)
