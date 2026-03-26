from django.db.models import Avg, Count, Q
from rest_framework import generics, permissions, response, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from cart.cart import Cart
from products.models import Category, Product

from .serializers import CategorySerializer, ProductDetailSerializer, ProductListSerializer


class StorefrontPagination(PageNumberPagination):
    page_size = 8

    def get_paginated_response(self, data):
        return response.Response(
            {
                "page": self.page.number,
                "pages": self.page.paginator.num_pages,
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.annotate(product_count=Count("products")).order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductListAPIView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StorefrontPagination

    def get_queryset(self):
        queryset = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .annotate(
                avg_rating=Avg("reviews__rating"),
                review_total=Count("reviews"),
            )
            .order_by("name")
        )
        query = self.request.query_params.get("search", "").strip()
        category_slug = self.request.query_params.get("category", "").strip()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
            )

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset


class ProductDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("reviews__user")
            .annotate(avg_rating=Avg("reviews__rating"), review_total=Count("reviews"))
            .order_by("name")
        )


class CartSummaryAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = Cart(request)
        return response.Response(
            {
                "item_count": len(cart),
                "subtotal": str(cart.get_subtotal_price()),
            }
        )


class CartAddAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        product_id = request.data.get("product_id")
        try:
            quantity = int(request.data.get("quantity", 1))
        except (TypeError, ValueError):
            return response.Response(
                {"detail": "Quantity must be a whole number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if quantity < 1:
            return response.Response(
                {"detail": "Quantity must be at least 1."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return response.Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart = Cart(request)
        target_quantity = cart.get_quantity(product) + quantity
        if target_quantity > product.stock:
            return response.Response(
                {"detail": f"Only {product.stock} item(s) are available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart.add(product, quantity=quantity, override_quantity=False)
        return response.Response(
            {
                "detail": f"{product.name} added to cart.",
                "item_count": len(cart),
                "subtotal": str(cart.get_subtotal_price()),
            },
            status=status.HTTP_200_OK,
        )
