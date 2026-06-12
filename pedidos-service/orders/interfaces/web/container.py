"""Composition root: monta os repositórios, adapters e o subject de observers usados pelas views."""

from __future__ import annotations

from django.conf import settings

from orders.application.ports import MenuCatalogPort, NotificationRepository, OrderRepository
from orders.domain.observer import KitchenNotifier, OrderLogger, OrderStatusSubject, WaiterNotifier
from orders.infrastructure.adapters.cardapio_service_adapter import CardapioServiceHttpAdapter
from orders.infrastructure.django_notification_repository import DjangoNotificationRepository
from orders.infrastructure.django_order_repository import DjangoOrderRepository


def get_order_repository() -> OrderRepository:
    return DjangoOrderRepository()


def get_notification_repository() -> NotificationRepository:
    return DjangoNotificationRepository()


def get_menu_catalog_port() -> MenuCatalogPort:
    return CardapioServiceHttpAdapter(base_url=settings.CARDAPIO_SERVICE_URL)


def get_status_subject() -> OrderStatusSubject:
    subject = OrderStatusSubject()
    subject.attach(KitchenNotifier())
    subject.attach(WaiterNotifier())
    subject.attach(OrderLogger())
    return subject
