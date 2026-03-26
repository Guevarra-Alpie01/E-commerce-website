from django.urls import path

from .views import (
    CartAddAPIView,
    CartSummaryAPIView,
    CategoryListAPIView,
    ProductDetailAPIView,
    ProductListAPIView,
)

app_name = "api"

urlpatterns = [
    path("categories/", CategoryListAPIView.as_view(), name="category_list"),
    path("products/", ProductListAPIView.as_view(), name="product_list"),
    path("products/<slug:slug>/", ProductDetailAPIView.as_view(), name="product_detail"),
    path("cart/summary/", CartSummaryAPIView.as_view(), name="cart_summary"),
    path("cart/add/", CartAddAPIView.as_view(), name="cart_add"),
]
