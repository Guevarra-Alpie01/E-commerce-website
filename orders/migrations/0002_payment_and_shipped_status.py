# Generated manually for the custom admin dashboard payment workflow.

import uuid

import django.db.models.deletion
import orders.models
from django.conf import settings
from django.db import migrations, models


def create_payment_records(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    Payment = apps.get_model("orders", "Payment")

    for order in Order.objects.all().iterator():
        Payment.objects.get_or_create(
            order_id=order.id,
            defaults={
                "user_id": order.user_id,
                "amount": order.subtotal,
                "payment_method": order.payment_method,
                "status": "Pending",
                "reference": f"PAY-{uuid.uuid4().hex[:10].upper()}",
                "notes": "Generated for an existing order.",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("Pending", "Pending"),
                    ("Processing", "Processing"),
                    ("Shipped", "Shipped"),
                    ("Delivered", "Delivered"),
                ],
                default="Pending",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "payment_method",
                    models.CharField(
                        choices=[("Cash on Delivery", "Cash on Delivery")],
                        default="Cash on Delivery",
                        max_length=30,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("Pending", "Pending"), ("Completed", "Completed")],
                        default="Pending",
                        max_length=20,
                    ),
                ),
                ("reference", models.CharField(default=orders.models.generate_payment_reference, max_length=20, unique=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "order",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="payment", to="orders.order"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.RunPython(create_payment_records, migrations.RunPython.noop),
    ]
