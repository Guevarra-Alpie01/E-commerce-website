from decimal import Decimal

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from products.models import Category, Product

from .cart import Cart


class CartTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.category = Category.objects.create(name="Desk")
        self.product = Product.objects.create(
            category=self.category,
            name="Task Lamp",
            description="Desk lamp with warm light",
            price="18.00",
            stock=8,
        )

    def get_request_with_session(self):
        request = self.factory.get("/")
        middleware = SessionMiddleware(lambda response: response)
        middleware.process_request(request)
        request.session.save()
        return request

    def test_cart_tracks_quantity_and_subtotal(self):
        request = self.get_request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=2)

        self.assertEqual(len(cart), 2)
        self.assertEqual(cart.get_subtotal_price(), Decimal("36.00"))
