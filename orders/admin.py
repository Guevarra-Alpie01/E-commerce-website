from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "full_name",
        "payment_method",
        "status",
        "subtotal",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("id", "user__username", "full_name", "phone", "address")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "unit_price", "quantity", "product")
    search_fields = ("order__id", "product_name")

# Register your models here.
