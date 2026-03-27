from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from cart.forms import CartAddProductForm
from reviews.forms import ReviewForm

from .models import Category, Product


@ensure_csrf_cookie
def product_list(request):
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
