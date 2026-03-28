from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from products.models import Product
from users.admin_access import is_admin_user, is_rider_user
from users.models import UserProfile

from .delivery import (
    build_delivery_confirmation_url,
    build_delivery_qr_svg,
    mark_order_delivered,
    resolve_delivery_order,
)
from .forms import CheckoutForm, RiderDeliveryConfirmationForm
from .models import Order, OrderItem, Payment


def build_order_delivery_context(request, order):
    delivery_confirmation_url = build_delivery_confirmation_url(request, order)
    return {
        "delivery_confirmation_url": delivery_confirmation_url,
        "delivery_qr_svg": build_delivery_qr_svg(delivery_confirmation_url),
    }


@login_required
def checkout(request):
    if is_admin_user(request.user):
        return redirect("admin_dashboard:index")
    if is_rider_user(request.user):
        return redirect("users:rider_dashboard")

    cart = Cart(request)
    cart_items = list(cart)

    if not cart_items:
        messages.info(request, "Your cart is empty. Add products before checking out.")
        return redirect("products:product_list")

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    initial = {
        "full_name": request.user.get_full_name() or request.user.username,
        "address": profile.address,
        "phone": profile.phone,
        "payment_method": Order.PaymentMethod.COD,
    }

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            product_ids = [item["product"].id for item in cart_items]

            with transaction.atomic():
                products_map = Product.objects.select_for_update().in_bulk(product_ids)
                insufficient_items = [
                    item["product"].name
                    for item in cart_items
                    if item["quantity"] > products_map[item["product"].id].stock
                ]

                if insufficient_items:
                    messages.error(
                        request,
                        "Some items no longer have enough stock: "
                        + ", ".join(insufficient_items),
                    )
                    return redirect("cart:cart_detail")

                order = form.save(commit=False)
                order.user = request.user
                order.subtotal = cart.get_subtotal_price()
                order.save()
                Payment.objects.create(
                    order=order,
                    user=request.user,
                    amount=order.subtotal,
                    payment_method=order.payment_method,
                    status=Payment.Status.PENDING,
                )

                for item in cart_items:
                    product = products_map[item["product"].id]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=item["quantity"],
                    )
                    product.stock -= item["quantity"]
                    product.save()

                cart.clear()

            messages.success(request, f"Order #{order.pk} has been placed successfully.")
            return redirect("orders:order_success", order_id=order.pk)
    else:
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "orders/checkout.html",
        {"form": form, "cart_items": cart_items, "cart": cart},
    )


@login_required
def order_history(request):
    if is_admin_user(request.user):
        return redirect("admin_dashboard:index")
    if is_rider_user(request.user):
        return redirect("users:rider_dashboard")

    orders = (
        request.user.orders.select_related("assigned_rider", "delivery_scanned_by")
        .prefetch_related("items")
        .order_by("-created_at")
    )
    return render(request, "orders/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    if is_admin_user(request.user):
        return redirect("admin_dashboard:order_detail", order_id=order_id)
    if is_rider_user(request.user):
        rider_order = request.user.assigned_orders.filter(pk=order_id).first()
        if rider_order:
            return redirect("users:rider_order_detail", order_id=order_id)
        return redirect("users:rider_dashboard")

    order = get_object_or_404(
        Order.objects.select_related("assigned_rider", "delivery_scanned_by").prefetch_related("items"),
        id=order_id,
        user=request.user,
    )
    context = {"order": order}
    context.update(build_order_delivery_context(request, order))
    return render(request, "orders/order_detail.html", context)


@login_required
def order_success(request, order_id):
    if is_admin_user(request.user):
        return redirect("admin_dashboard:index")
    if is_rider_user(request.user):
        return redirect("users:rider_dashboard")

    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_success.html", {"order": order})


@login_required
def rider_delivery_confirm(request, signed_token):
    if not (is_admin_user(request.user) or is_rider_user(request.user)):
        messages.error(request, "Only authorized riders or admins can validate delivery QR codes.")
        return redirect("products:product_list")

    delivery_error = None
    try:
        order = resolve_delivery_order(signed_token)
    except signing.SignatureExpired:
        order = None
        delivery_error = "This delivery QR code has expired. Please refresh the order QR and try again."
    except signing.BadSignature:
        order = None
        delivery_error = "This delivery QR code is invalid or has been tampered with."
    except Order.DoesNotExist:
        order = None
        delivery_error = "We could not find the order linked to this QR code."

    if order and order.assigned_rider_id is None:
        delivery_error = "This order does not have an assigned rider yet."

    if order and order.assigned_rider_id and not is_admin_user(request.user) and request.user.id != order.assigned_rider_id:
        messages.error(request, "This QR code belongs to a different rider assignment.")
        return redirect("users:rider_dashboard")

    if request.method == "POST" and not delivery_error and order:
        form = RiderDeliveryConfirmationForm(request.POST)
        if form.is_valid() and form.cleaned_data["signed_token"] == signed_token:
            with transaction.atomic():
                order = resolve_delivery_order(signed_token, for_update=True)
                if order.assigned_rider_id is None:
                    delivery_error = "This order does not have an assigned rider yet."
                elif order.assigned_rider_id and not is_admin_user(request.user) and request.user.id != order.assigned_rider_id:
                    messages.error(request, "This QR code belongs to a different rider assignment.")
                    return redirect("users:rider_dashboard")
                elif order.status == Order.Status.DELIVERED:
                    messages.info(request, f"Order #{order.pk} was already marked as delivered.")
                else:
                    mark_order_delivered(
                        order,
                        request.user,
                        f"Delivery confirmed by {request.user.username} via QR verification.",
                    )
                    messages.success(request, f"Order #{order.pk} has been marked as delivered.")

            if is_admin_user(request.user):
                return redirect("admin_dashboard:order_detail", order_id=order.pk)
            return redirect("users:rider_order_detail", order_id=order.pk)
    else:
        form = RiderDeliveryConfirmationForm(initial={"signed_token": signed_token})

    return render(
        request,
        "orders/rider_delivery_confirm.html",
        {
            "order": order,
            "form": form,
            "delivery_error": delivery_error,
            "auto_submit": bool(order and not delivery_error and order.status != Order.Status.DELIVERED and is_rider_user(request.user)),
        },
    )
