from django.contrib import messages
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie

from cart.forms import CartAddProductForm
from reviews.forms import ReviewForm
from reviews.models import Review
from users.admin_access import is_admin_user
from users.forms import UnifiedAuthenticationForm

from .models import Category, Product


@ensure_csrf_cookie
def product_list(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = None

    login_form = UnifiedAuthenticationForm(request=request)
    if request.method == "POST" and not request.user.is_authenticated and "login_submit" in request.POST:
        login_form = UnifiedAuthenticationForm(request=request, data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_username()}.")
            if is_admin_user(user):
                return redirect("admin_dashboard:index")
            if next_url:
                return redirect(next_url)
            return redirect("users:profile")

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .annotate(avg_rating=Avg("reviews__rating"), review_total=Count("reviews"))
        .order_by("-created_at", "-id")
    )
    categories = Category.objects.all()
    selected_category = None

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "products/product_list.html",
        {
            "query": query,
            "selected_category": selected_category,
            "page_obj": page_obj,
            "categories": categories,
            "login_form": login_form,
            "login_next": next_url,
            "react_config": {
                "productsApi": "/api/products/",
                "categoriesApi": "/api/categories/",
                "cartSummaryApi": "/api/cart/summary/",
                "cartAddApi": "/api/cart/add/",
                "productBasePath": "/products/",
                "initialSearch": query,
                "initialCategory": selected_category.slug if selected_category else "",
            },
        },
    )


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category")
        .annotate(avg_rating=Avg("reviews__rating"), review_total=Count("reviews")),
        slug=slug,
        is_active=True,
    )
    reviews = product.reviews.select_related("user").order_by("-created_at")
    user_review = None
    review_form = None

    if request.user.is_authenticated:
        user_review = Review.objects.filter(user=request.user, product=product).first()
        review_form = ReviewForm(instance=user_review)

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "cart_form": CartAddProductForm(initial={"quantity": 1}),
            "review_form": review_form,
            "user_review": user_review,
        },
    )

# Create your views here.
