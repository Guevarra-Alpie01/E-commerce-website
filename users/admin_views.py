from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from orders.delivery import build_delivery_confirmation_url, build_delivery_qr_svg, ensure_payment_completed, mark_order_delivered
from orders.models import Order, Payment
from products.models import Category, Product
from reviews.models import Review

from .admin_access import admin_required
from .admin_forms import (
    AdminCategoryForm,
    AdminOrderStatusForm,
    AdminPaymentStatusForm,
    AdminProductForm,
    AdminRiderCreationForm,
    AdminUserForm,
    AdminUserProfileForm,
)
from .models import UserProfile


def paginate_queryset(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def querystring_without_page(request):
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()


def resolve_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return None


def ensure_payment(order):
    payment, _ = Payment.objects.get_or_create(
        order=order,
        defaults={
            "user": order.user,
            "amount": order.subtotal,
            "payment_method": order.payment_method,
            "status": Payment.Status.PENDING,
        },
    )
    return payment


def describe_user_role(user_obj):
    if user_obj.is_superuser:
        return "Superuser"
    if user_obj.is_staff:
        return "Staff"
    if getattr(user_obj, "profile", None) and user_obj.profile.role == UserProfile.Role.RIDER:
        return "Rider"
    return "Customer"


def admin_login(request):
    next_url = resolve_next_url(request)
    target = redirect("login").url
    if next_url:
        target = f"{target}?next={next_url}"
    return redirect(target)


@require_POST
@admin_required
def admin_logout(request):
    logout(request)
    messages.info(request, "You have been signed out of the admin dashboard.")
    return redirect("admin_dashboard:login")


@admin_required
def dashboard(request):
    stats = {
        "total_users": User.objects.count(),
        "total_products": Product.objects.count(),
        "total_orders": Order.objects.count(),
        "total_revenue": Order.objects.aggregate(
            total=Coalesce(Sum("subtotal"), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
        )["total"],
    }
    recent_orders = (
        Order.objects.select_related("user", "assigned_rider")
        .prefetch_related("items")
        .order_by("-created_at")[:8]
    )
    low_stock_products = Product.objects.select_related("category").filter(stock__lte=5).order_by("stock", "name")[:6]
    pending_payments = Payment.objects.select_related("order", "user").filter(status=Payment.Status.PENDING)[:5]
    latest_reviews = Review.objects.select_related("product", "user")[:5]
    return render(
        request,
        "admin_dashboard/dashboard.html",
        {
            "stats": stats,
            "recent_orders": recent_orders,
            "low_stock_products": low_stock_products,
            "pending_payments": pending_payments,
            "latest_reviews": latest_reviews,
            "section": "dashboard",
        },
    )


@admin_required
def user_list(request):
    query = request.GET.get("q", "").strip()
    role_filter = request.GET.get("role", "").strip()
    users = (
        User.objects.select_related("profile")
        .annotate(order_count=Count("orders", distinct=True), assigned_order_count=Count("assigned_orders", distinct=True))
        .order_by("-date_joined")
    )

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(profile__phone__icontains=query)
        )

    if role_filter == "rider":
        users = users.filter(profile__role=UserProfile.Role.RIDER, is_staff=False, is_superuser=False)
    elif role_filter == "customer":
        users = users.filter(profile__role=UserProfile.Role.CUSTOMER, is_staff=False, is_superuser=False)
    elif role_filter == "staff":
        users = users.filter(Q(is_staff=True) | Q(is_superuser=True))

    page_obj = paginate_queryset(request, users, per_page=12)
    return render(
        request,
        "admin_dashboard/users/list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "role_filter": role_filter,
            "querystring": querystring_without_page(request),
            "section": "users",
        },
    )


@admin_required
def rider_create(request):
    if request.method == "POST":
        form = AdminRiderCreationForm(request.POST)
        if form.is_valid():
            rider = form.save()
            messages.success(request, f"Rider account for {rider.username} has been created.")
            return redirect("admin_dashboard:user_detail", user_id=rider.id)
    else:
        form = AdminRiderCreationForm()

    return render(
        request,
        "admin_dashboard/users/rider_form.html",
        {
            "form": form,
            "title": "Create rider account",
            "submit_label": "Create rider",
            "section": "users",
        },
    )


@admin_required
def user_detail(request, user_id):
    user_obj = get_object_or_404(User.objects.select_related("profile"), pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=user_obj)

    if request.method == "POST":
        form = AdminUserForm(request.POST, instance=user_obj)
        profile_form = AdminUserProfileForm(request.POST, instance=profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, f"{user_obj.username} has been updated.")
            return redirect("admin_dashboard:user_detail", user_id=user_obj.id)
    else:
        form = AdminUserForm(instance=user_obj)
        profile_form = AdminUserProfileForm(instance=profile)

    user_orders = user_obj.orders.select_related("assigned_rider").prefetch_related("items").order_by("-created_at")
    assigned_orders = user_obj.assigned_orders.select_related("user").prefetch_related("items").order_by("-created_at")[:10]
    user_reviews = user_obj.reviews.select_related("product").order_by("-created_at")[:8]
    return render(
        request,
        "admin_dashboard/users/detail.html",
        {
            "managed_user": user_obj,
            "profile": profile,
            "form": form,
            "profile_form": profile_form,
            "user_orders": user_orders,
            "assigned_orders": assigned_orders,
            "user_reviews": user_reviews,
            "account_role_label": describe_user_role(user_obj),
            "section": "users",
        },
    )


@require_POST
@admin_required
def user_toggle_active(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)

    if user_obj == request.user and user_obj.is_active:
        messages.error(request, "You cannot deactivate your own admin account.")
        return redirect("admin_dashboard:user_detail", user_id=user_obj.id)

    user_obj.is_active = not user_obj.is_active
    user_obj.save(update_fields=["is_active"])
    messages.success(
        request,
        f"{user_obj.username} is now {'active' if user_obj.is_active else 'inactive'}.",
    )
    return redirect(request.POST.get("next") or "admin_dashboard:user_list")


@admin_required
def product_list(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.select_related("category").order_by("name")

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query) | Q(category__name__icontains=query)
        )

    page_obj = paginate_queryset(request, products, per_page=12)
    return render(
        request,
        "admin_dashboard/products/list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "querystring": querystring_without_page(request),
            "section": "products",
            "low_stock_threshold": 5,
            "category_count": Category.objects.count(),
        },
    )


@admin_required
def product_create(request):
    category_count = Category.objects.count()
    if request.method == "POST":
        form = AdminProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"{product.name} has been added.")
            return redirect("admin_dashboard:product_list")
    else:
        form = AdminProductForm()

    return render(
        request,
        "admin_dashboard/products/form.html",
        {
            "form": form,
            "title": "Add product",
            "submit_label": "Create product",
            "section": "products",
            "category_count": category_count,
        },
    )


@admin_required
def product_edit(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    category_count = Category.objects.count()

    if request.method == "POST":
        form = AdminProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"{product.name} has been updated.")
            return redirect("admin_dashboard:product_list")
    else:
        form = AdminProductForm(instance=product)

    return render(
        request,
        "admin_dashboard/products/form.html",
        {
            "form": form,
            "title": f"Edit {product.name}",
            "submit_label": "Save changes",
            "section": "products",
            "category_count": category_count,
        },
    )


@admin_required
def product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == "POST":
        product_name = product.name
        product.delete()
        messages.success(request, f"{product_name} has been deleted.")
        return redirect("admin_dashboard:product_list")

    return render(
        request,
        "admin_dashboard/products/confirm_delete.html",
        {"product": product, "section": "products"},
    )


@admin_required
def category_list(request):
    query = request.GET.get("q", "").strip()
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")

    if query:
        categories = categories.filter(Q(name__icontains=query) | Q(description__icontains=query))

    page_obj = paginate_queryset(request, categories, per_page=12)
    return render(
        request,
        "admin_dashboard/categories/list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "querystring": querystring_without_page(request),
            "section": "products",
        },
    )


@admin_required
def category_create(request):
    if request.method == "POST":
        form = AdminCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"{category.name} has been added.")
            if request.POST.get("continue_to_product"):
                return redirect("admin_dashboard:product_create")
            return redirect("admin_dashboard:category_list")
    else:
        form = AdminCategoryForm()

    return render(
        request,
        "admin_dashboard/categories/form.html",
        {
            "form": form,
            "title": "Add category",
            "submit_label": "Create category",
            "section": "products",
        },
    )


@admin_required
def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == "POST":
        form = AdminCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"{category.name} has been updated.")
            return redirect("admin_dashboard:category_list")
    else:
        form = AdminCategoryForm(instance=category)

    return render(
        request,
        "admin_dashboard/categories/form.html",
        {
            "form": form,
            "title": f"Edit {category.name}",
            "submit_label": "Save changes",
            "section": "products",
        },
    )


@admin_required
def category_delete(request, category_id):
    category = get_object_or_404(Category.objects.annotate(product_count=Count("products")), pk=category_id)

    if request.method == "POST":
        if category.product_count:
            messages.error(request, f"{category.name} still has products assigned to it.")
            return redirect("admin_dashboard:category_list")

        category_name = category.name
        category.delete()
        messages.success(request, f"{category_name} has been deleted.")
        return redirect("admin_dashboard:category_list")

    return render(
        request,
        "admin_dashboard/categories/confirm_delete.html",
        {"category": category, "section": "products"},
    )


@admin_required
def order_list(request):
    status_filter = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    orders = (
        Order.objects.select_related("user", "payment", "assigned_rider")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    if status_filter:
        orders = orders.filter(status=status_filter)

    if query:
        query_filter = (
            Q(user__username__icontains=query)
            | Q(full_name__icontains=query)
            | Q(assigned_rider__username__icontains=query)
            | Q(assigned_rider__first_name__icontains=query)
            | Q(assigned_rider__last_name__icontains=query)
        )
        if query.isdigit():
            query_filter |= Q(pk=int(query))
        orders = orders.filter(query_filter)

    page_obj = paginate_queryset(request, orders, per_page=12)
    return render(
        request,
        "admin_dashboard/orders/list.html",
        {
            "page_obj": page_obj,
            "status_filter": status_filter,
            "query": query,
            "querystring": querystring_without_page(request),
            "status_choices": Order.Status.choices,
            "section": "orders",
        },
    )


@admin_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("user", "assigned_rider", "delivery_scanned_by").prefetch_related("items__product"),
        pk=order_id,
    )
    previous_status = order.status
    payment = ensure_payment(order)

    if request.method == "POST":
        form = AdminOrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            selected_status = form.cleaned_data["status"]
            assigned_rider = form.cleaned_data["assigned_rider"]
            order.assigned_rider = assigned_rider

            if assigned_rider and selected_status in {
                Order.Status.PENDING,
                Order.Status.PROCESSING,
                Order.Status.SHIPPED,
            }:
                selected_status = Order.Status.ASSIGNED

            with transaction.atomic():
                if selected_status == Order.Status.DELIVERED:
                    order.status = previous_status
                    order.save(update_fields=["assigned_rider", "updated_at"])
                    if previous_status != Order.Status.DELIVERED:
                        mark_order_delivered(
                            order,
                            request.user,
                            "Marked completed when order was delivered from the admin dashboard.",
                        )
                else:
                    order.status = selected_status
                    order.save(update_fields=["assigned_rider", "status", "updated_at"])
                    if payment.status != Payment.Status.COMPLETED and order.status == Order.Status.DELIVERED:
                        ensure_payment_completed(order, "Marked completed when order was delivered from the admin dashboard.")

            messages.success(request, f"Order #{order.pk} status updated to {order.status}.")
            return redirect("admin_dashboard:order_detail", order_id=order.pk)
    else:
        form = AdminOrderStatusForm(instance=order)

    delivery_confirmation_url = build_delivery_confirmation_url(request, order)
    return render(
        request,
        "admin_dashboard/orders/detail.html",
        {
            "order": order,
            "payment": payment,
            "form": form,
            "delivery_confirmation_url": delivery_confirmation_url,
            "delivery_qr_svg": build_delivery_qr_svg(delivery_confirmation_url),
            "section": "orders",
        },
    )


@admin_required
def payment_list(request):
    status_filter = request.GET.get("status", "").strip()
    query = request.GET.get("q", "").strip()
    payments = Payment.objects.select_related("order", "user").order_by("-created_at")

    if status_filter:
        payments = payments.filter(status=status_filter)

    if query:
        query_filter = Q(reference__icontains=query) | Q(user__username__icontains=query) | Q(order__full_name__icontains=query)
        if query.isdigit():
            query_filter |= Q(order_id=int(query))
        payments = payments.filter(query_filter)

    page_obj = paginate_queryset(request, payments, per_page=12)
    return render(
        request,
        "admin_dashboard/payments/list.html",
        {
            "page_obj": page_obj,
            "status_filter": status_filter,
            "query": query,
            "querystring": querystring_without_page(request),
            "status_choices": Payment.Status.choices,
            "payment_form": AdminPaymentStatusForm(),
            "section": "payments",
        },
    )


@require_POST
@admin_required
def payment_update_status(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id)
    form = AdminPaymentStatusForm(request.POST, instance=payment)

    if form.is_valid():
        form.save()
        messages.success(request, f"Payment {payment.reference} updated to {payment.status}.")
    else:
        messages.error(request, "Could not update the payment status. Please check the form and try again.")

    return redirect("admin_dashboard:payment_list")


@admin_required
def review_list(request):
    rating_filter = request.GET.get("rating", "").strip()
    query = request.GET.get("q", "").strip()
    reviews = Review.objects.select_related("user", "product").order_by("-created_at")

    if rating_filter:
        reviews = reviews.filter(rating=rating_filter)

    if query:
        reviews = reviews.filter(
            Q(comment__icontains=query) | Q(product__name__icontains=query) | Q(user__username__icontains=query)
        )

    page_obj = paginate_queryset(request, reviews, per_page=12)
    return render(
        request,
        "admin_dashboard/reviews/list.html",
        {
            "page_obj": page_obj,
            "rating_filter": rating_filter,
            "query": query,
            "querystring": querystring_without_page(request),
            "ratings": Review.RATING_CHOICES,
            "section": "reviews",
        },
    )


@require_POST
@admin_required
def review_delete(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    product_name = review.product.name
    review.delete()
    messages.success(request, f"The review for {product_name} has been deleted.")
    return redirect("admin_dashboard:review_list")
