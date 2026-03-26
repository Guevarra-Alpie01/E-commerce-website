from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_active", "updated_at")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("name", "description")
    list_editable = ("price", "stock", "is_active")
    prepopulated_fields = {"slug": ("name",)}

# Register your models here.
