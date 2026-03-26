from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.shortcuts import redirect, render

from orders.models import Order
from products.models import Product

from .forms import ProfileForm, SignUpForm, UserUpdateForm
from .models import UserProfile


def register(request):
    if request.user.is_authenticated:
        return redirect("users:profile")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your account has been created successfully.")
            return redirect("users:profile")
    else:
        form = SignUpForm()

    return render(request, "users/register.html", {"form": form})


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("users:profile")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    recent_orders = request.user.orders.prefetch_related("items").order_by("-created_at")[:5]
    return render(
        request,
        "users/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "recent_orders": recent_orders,
        },
    )


@user_passes_test(lambda user: user.is_staff)
def dashboard(request):
    stats = {
        "total_users": User.objects.count(),
        "total_products": Product.objects.count(),
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
        "inventory_units": Product.objects.aggregate(total=Sum("stock"))["total"] or 0,
    }
    recent_orders = Order.objects.select_related("user").order_by("-created_at")[:8]
    top_categories = (
        Product.objects.values("category__name")
        .annotate(total=Count("id"))
        .order_by("-total", "category__name")[:5]
    )
    return render(
        request,
        "users/dashboard.html",
        {"stats": stats, "recent_orders": recent_orders, "top_categories": top_categories},
    )
