from __future__ import annotations

from orders.application.ports import NotificationRepository
from orders.domain.entities import NotificationData, NotificationEntity
from orders.models import Notification


class DjangoNotificationRepository(NotificationRepository):
    """Implementação do NotificationRepository usando o Django ORM."""

    def create(self, order_id: int, notification: NotificationData) -> None:
        Notification.objects.create(
            order_id=order_id,
            tipo=notification.tipo,
            mensagem=notification.mensagem,
            status_de=notification.status_de,
            status_para=notification.status_para,
        )

    def list(self, order_id: int | None = None) -> list[NotificationEntity]:
        qs = Notification.objects.all()
        if order_id is not None:
            qs = qs.filter(order_id=order_id)
        return [
            NotificationEntity(
                id=n.pk,
                order_id=n.order_id,
                tipo=n.tipo,
                mensagem=n.mensagem,
                status_de=n.status_de,
                status_para=n.status_para,
                criado_em=n.criado_em,
            )
            for n in qs
        ]
