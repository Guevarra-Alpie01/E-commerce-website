from io import BytesIO

import qrcode
from django.core import signing
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from qrcode.image.svg import SvgPathImage

from .models import Order, Payment

DELIVERY_QR_SIGNING_SALT = "orders.delivery"
DELIVERY_QR_MAX_AGE = 60 * 60 * 24 * 30


def build_delivery_signed_token(order):
    return signing.dumps(
        {"order_id": order.pk, "token": order.delivery_token},
        salt=DELIVERY_QR_SIGNING_SALT,
        compress=True,
    )


def resolve_delivery_order(signed_token, for_update=False):
    payload = signing.loads(
        signed_token,
        salt=DELIVERY_QR_SIGNING_SALT,
        max_age=DELIVERY_QR_MAX_AGE,
    )
    queryset = (
        Order.objects.select_related("user", "assigned_rider", "assigned_rider__profile", "delivery_scanned_by", "payment")
        .prefetch_related("items__product")
    )
    if for_update:
        queryset = queryset.select_for_update()
    order = queryset.get(pk=payload["order_id"])
    if payload["token"] != order.delivery_token:
        raise signing.BadSignature("Delivery token does not match the current order token.")
    return order


def build_delivery_confirmation_url(request, order):
    signed_token = build_delivery_signed_token(order)
    return request.build_absolute_uri(
        reverse("orders:rider_delivery_confirm", kwargs={"signed_token": signed_token})
    )


def build_delivery_qr_svg(url):
    qr_image = qrcode.make(url, image_factory=SvgPathImage, box_size=8, border=2)
    buffer = BytesIO()
    qr_image.save(buffer)
    return mark_safe(buffer.getvalue().decode("utf-8"))


def ensure_payment_completed(order, note):
    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={
            "user": order.user,
            "amount": order.subtotal,
            "payment_method": order.payment_method,
            "status": Payment.Status.PENDING,
        },
    )
    if payment.status != Payment.Status.COMPLETED:
        payment.status = Payment.Status.COMPLETED
        payment.notes = (payment.notes + "\n" if payment.notes else "") + note
        payment.save(update_fields=["status", "notes", "updated_at"])
    return payment


def mark_order_out_for_delivery(order):
    if order.status in {Order.Status.DELIVERED, Order.Status.OUT_FOR_DELIVERY}:
        return False
    order.status = Order.Status.OUT_FOR_DELIVERY
    order.save(update_fields=["status", "updated_at"])
    return True


def mark_order_delivered(order, actor, note):
    if order.status == Order.Status.DELIVERED:
        return False
    order.status = Order.Status.DELIVERED
    order.delivery_confirmed_at = timezone.now()
    order.delivery_scanned_by = actor
    order.save(
        update_fields=[
            "status",
            "delivery_confirmed_at",
            "delivery_scanned_by",
            "updated_at",
        ]
    )
    ensure_payment_completed(order, note)
    return True
