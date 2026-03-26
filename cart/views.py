from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from products.models import Product

from .cart import Cart
from .forms import CartAddProductForm


def cart_detail(request):
    cart = Cart(request)
    cart_items = []
    for item in cart:
        item["update_form"] = CartAddProductForm(
            initial={"quantity": item["quantity"], "override": True}
        )
        cart_items.append(item)

    return render(request, "cart/cart_detail.html", {"cart_items": cart_items, "cart": cart})


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        override = form.cleaned_data["override"]
        target_quantity = quantity if override else cart.get_quantity(product) + quantity

        if target_quantity > product.stock:
            messages.error(
                request,
                f"Only {product.stock} unit(s) of {product.name} are currently available.",
            )
        else:
            cart.add(product=product, quantity=quantity, override_quantity=override)
            messages.success(request, f"{product.name} has been added to your cart.")

    next_url = request.POST.get("next") or "cart:cart_detail"
    return redirect(next_url)


@require_POST
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        quantity = form.cleaned_data["quantity"]
        if quantity > product.stock:
            messages.error(
                request,
                f"Only {product.stock} unit(s) of {product.name} are currently available.",
            )
        else:
            cart.add(product=product, quantity=quantity, override_quantity=True)
            messages.success(request, f"Updated {product.name} in your cart.")

    return redirect("cart:cart_detail")


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"Removed {product.name} from your cart.")
    return redirect("cart:cart_detail")

# Create your views here.
