from rest_framework import serializers

from products.models import Category, Product
from reviews.models import Review


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "product_count")


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    image_url = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=1, read_only=True)
    review_total = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "price",
            "stock",
            "image_url",
            "category_name",
            "category_slug",
            "avg_rating",
            "review_total",
            "detail_url",
        )

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

    def get_detail_url(self, obj):
        return obj.get_absolute_url()


class ReviewSnippetSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ("user", "rating", "comment", "updated_at")


class ProductDetailSerializer(ProductListSerializer):
    reviews = ReviewSnippetSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ("reviews",)
