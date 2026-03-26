from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from cart.cart import Cart
from products.models import Product
from users.models import UserProfile

from .forms import CheckoutForm
from .models import Order, OrderItem, Payment


@login_required
def checkout(request):
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
    orders = request.user.orders.prefetch_related("items").order_by("-created_at")
    return render(request, "orders/order_history.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        user=request.user,
    )
    return render(request, "orders/order_detail.html", {"order": order})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "orders/order_success.html", {"order": order})
