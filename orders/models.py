import secrets
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone

from products.models import Product


def generate_delivery_token():
    return secrets.token_urlsafe(24)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        PROCESSING = "Processing", "Processing"
        ASSIGNED = "Assigned", "Assigned"
        OUT_FOR_DELIVERY = "Out for Delivery", "Out for Delivery"
        SHIPPED = "Shipped", "Shipped"
        DELIVERED = "Delivered", "Delivered"

    class PaymentMethod(models.TextChoices):
        COD = "Cash on Delivery", "Cash on Delivery"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    assigned_rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
        null=True,
        blank=True,
    )
    full_name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    delivery_token = models.CharField(max_length=64, db_index=True, default=generate_delivery_token, editable=False)
    delivery_qr_generated_at = models.DateTimeField(default=timezone.now, editable=False)
    delivery_confirmed_at = models.DateTimeField(null=True, blank=True)
    delivery_scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="completed_delivery_scans",
        null=True,
        blank=True,
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk}"

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def status_theme(self):
        mapping = {
            self.Status.PENDING: "warning",
            self.Status.PROCESSING: "neutral",
            self.Status.ASSIGNED: "warning",
            self.Status.OUT_FOR_DELIVERY: "success",
            self.Status.SHIPPED: "neutral",
            self.Status.DELIVERED: "success",
        }
        return mapping.get(self.status, "neutral")

    @property
    def has_rider_assignment(self):
        return self.assigned_rider_id is not None


def generate_payment_reference():
    return f"PAY-{uuid4().hex[:10].upper()}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        COMPLETED = "Completed", "Completed"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=30,
        choices=Order.PaymentMethod.choices,
        default=Order.PaymentMethod.COD,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reference = models.CharField(max_length=20, unique=True, default=generate_payment_reference)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.reference} for Order #{self.order_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity
