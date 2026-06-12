from django.contrib import admin
from orders.models import Order, OrderItem, Notification


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item_id', 'nome_snapshot', 'categoria_snapshot', 'preco_unit', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'status', 'total', 'pago', 'forma_pagamento', 'criado_em')
    list_filter = ('status', 'pago')
    inlines = [OrderItemInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('order', 'tipo', 'status_de', 'status_para', 'criado_em')
    list_filter = ('tipo',)
    readonly_fields = ('order', 'tipo', 'mensagem', 'status_de', 'status_para', 'criado_em')
