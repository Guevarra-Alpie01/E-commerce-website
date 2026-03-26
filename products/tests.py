from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class ProductCatalogTests(TestCase):
    def setUp(self):
        self.tech = Category.objects.create(name="Tech")
        self.books = Category.objects.create(name="Books")
        self.camera = Product.objects.create(
            category=self.tech,
            name="Travel Camera",
            description="Compact camera for city trips",
            price="499.00",
            stock=10,
        )
        self.notebook = Product.objects.create(
            category=self.books,
            name="Notebook Planner",
            description="Weekly planner and note pages",
            price="15.00",
            stock=30,
        )

    def test_product_list_supports_search(self):
        response = self.client.get(reverse("products:product_list"), {"q": "camera"})
        self.assertContains(response, self.camera.name)
        self.assertNotContains(response, self.notebook.name)

    def test_product_list_supports_category_filter(self):
        response = self.client.get(
            reverse("products:product_list"),
            {"category": self.books.slug},
        )
        self.assertContains(response, self.notebook.name)
        self.assertNotContains(response, self.camera.name)

# Create your tests here.
