from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from orders.delivery import build_delivery_confirmation_url
from orders.models import Order

from .admin_access import admin_required, is_admin_user, is_rider_user, rider_required
from .forms import ProfileForm, SignUpForm, UnifiedAuthenticationForm, UserUpdateForm
from .models import UserProfile


def resolve_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return None


def login_redirect_for(user, fallback="users:profile"):
    if is_admin_user(user):
        return "admin_dashboard:index"
    if is_rider_user(user):
        return "users:rider_dashboard"
    return fallback


def login_entry(request):
    next_url = resolve_next_url(request)
    if request.user.is_authenticated:
        return redirect(next_url or login_redirect_for(request.user))

    if request.method == "POST":
        form = UnifiedAuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_username()}.")
            if next_url:
                return redirect(next_url)
            return redirect(login_redirect_for(user))
    else:
        form = UnifiedAuthenticationForm(request=request)

    return render(request, "registration/login.html", {"form": form, "next": next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("products:product_list")


def register(request):
    if request.user.is_authenticated:
        return redirect(login_redirect_for(request.user))

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your account has been created successfully.")
            return redirect(login_redirect_for(user))
    else:
        form = SignUpForm()

    return render(request, "users/register.html", {"form": form})


@login_required
def profile(request):
    if is_admin_user(request.user):
        return redirect("admin_dashboard:index")
    if is_rider_user(request.user):
        return redirect("users:rider_dashboard")

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

    recent_orders = (
        request.user.orders.select_related("assigned_rider", "delivery_scanned_by")
        .prefetch_related("items")
        .order_by("-created_at")[:5]
    )
    return render(
        request,
        "users/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "recent_orders": recent_orders,
        },
    )


@rider_required
def rider_dashboard(request):
    active_orders = (
        request.user.assigned_orders.select_related("user")
        .prefetch_related("items")
        .exclude(status=Order.Status.DELIVERED)
        .order_by("created_at")
    )
    recent_deliveries = (
        request.user.assigned_orders.select_related("user")
        .prefetch_related("items")
        .filter(status=Order.Status.DELIVERED)
        .order_by("-delivery_confirmed_at")[:6]
    )
    today = timezone.localdate()
    stats = {
        "assigned": request.user.assigned_orders.filter(status=Order.Status.ASSIGNED).count(),
        "out_for_delivery": request.user.assigned_orders.filter(status=Order.Status.OUT_FOR_DELIVERY).count(),
        "delivered_today": request.user.assigned_orders.filter(
            status=Order.Status.DELIVERED,
            delivery_confirmed_at__date=today,
        ).count(),
    }
    return render(
        request,
        "users/rider_dashboard.html",
        {
            "active_orders": active_orders,
            "recent_deliveries": recent_deliveries,
            "stats": stats,
        },
    )


@rider_required
def rider_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user", "assigned_rider", "delivery_scanned_by", "payment").prefetch_related("items"),
        pk=order_id,
        assigned_rider=request.user,
    )
    return render(
        request,
        "users/rider_order_detail.html",
        {
            "order": order,
            "delivery_confirmation_url": build_delivery_confirmation_url(request, order),
        },
    )


@require_POST
@rider_required
def rider_order_start(request, order_id):
    order = get_object_or_404(Order, pk=order_id, assigned_rider=request.user)
    if order.status == Order.Status.DELIVERED:
        messages.info(request, f"Order #{order.pk} is already marked as delivered.")
    else:
        order.status = Order.Status.OUT_FOR_DELIVERY
        order.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Order #{order.pk} is now out for delivery.")
    return redirect("users:rider_order_detail", order_id=order.pk)


@rider_required
def rider_scan(request):
    return render(request, "users/rider_scan.html")


@admin_required
def dashboard(request):
    return redirect("admin_dashboard:index")
