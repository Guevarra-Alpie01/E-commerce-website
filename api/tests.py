from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product


class StorefrontApiTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Snacks")
        self.product = Product.objects.create(
            category=self.category,
            name="Banana Chips",
            description="Sweet and crunchy banana chips",
            price="85.00",
            stock=10,
        )

    def test_product_api_returns_catalog_data(self):
        response = self.client.get(reverse("api:product_list"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["results"][0]["name"], "Banana Chips")

    def test_cart_add_api_updates_session_cart(self):
        response = self.client.post(
            reverse("api:cart_add"),
            data={"product_id": self.product.id, "quantity": 2},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item_count"], 2)
