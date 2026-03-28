from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orders.delivery import build_delivery_signed_token
from products.models import Category, Product

from .models import Order, Payment


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="checkout-user",
            password="secret12345",
            first_name="Ava",
            last_name="Buyer",
        )
        self.rider = User.objects.create_user(
            username="rider-checkout",
            password="secret12345",
            first_name="Rider",
            last_name="One",
        )
        self.rider.profile.role = self.rider.profile.Role.RIDER
        self.rider.profile.save()
        self.category = Category.objects.create(name="Home")
        self.product = Product.objects.create(
            category=self.category,
            name="Ceramic Mug",
            description="Minimal mug for tea and coffee",
            price="12.50",
            stock=5,
        )

    def test_checkout_requires_authentication(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("orders:checkout"), response.url)

    def test_checkout_creates_order_and_reduces_stock(self):
        self.client.login(username="checkout-user", password="secret12345")
        session = self.client.session
        session["cart"] = {str(self.product.id): 2}
        session.save()

        response = self.client.post(
            reverse("orders:checkout"),
            {
                "full_name": "Ava Buyer",
                "address": "123 Test Street",
                "phone": "09170000000",
                "payment_method": "Cash on Delivery",
            },
        )

        order = Order.objects.get()
        self.assertRedirects(response, reverse("orders:order_success", args=[order.id]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(order.items.count(), 1)
        self.assertTrue(Payment.objects.filter(order=order, status=Payment.Status.PENDING).exists())
        self.assertTrue(order.delivery_token)
        self.assertEqual(self.client.session.get("cart"), None)

    def test_checkout_blocks_when_stock_is_insufficient(self):
        self.client.login(username="checkout-user", password="secret12345")
        session = self.client.session
        session["cart"] = {str(self.product.id): 7}
        session.save()

        response = self.client.post(
            reverse("orders:checkout"),
            {
                "full_name": "Ava Buyer",
                "address": "123 Test Street",
                "phone": "09170000000",
                "payment_method": "Cash on Delivery",
            },
        )

        self.assertRedirects(response, reverse("cart:cart_detail"))
        self.assertEqual(Order.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_assigned_rider_can_confirm_delivery_from_qr(self):
        order = Order.objects.create(
            user=self.user,
            assigned_rider=self.rider,
            full_name="Ava Buyer",
            address="123 Test Street",
            phone="09170000000",
            payment_method=Order.PaymentMethod.COD,
            status=Order.Status.OUT_FOR_DELIVERY,
            subtotal="25.00",
        )
        payment = Payment.objects.create(
            order=order,
            user=self.user,
            amount="25.00",
            payment_method=Order.PaymentMethod.COD,
            status=Payment.Status.PENDING,
        )
        signed_token = build_delivery_signed_token(order)

        self.client.login(username="rider-checkout", password="secret12345")
        response = self.client.post(
            reverse("orders:rider_delivery_confirm", args=[signed_token]),
            {"signed_token": signed_token},
        )

        self.assertRedirects(response, reverse("users:rider_order_detail", args=[order.id]))
        order.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
        self.assertEqual(order.delivery_scanned_by, self.rider)
        self.assertEqual(payment.status, Payment.Status.COMPLETED)

    def test_unassigned_order_qr_shows_error_for_rider(self):
        order = Order.objects.create(
            user=self.user,
            full_name="Ava Buyer",
            address="123 Test Street",
            phone="09170000000",
            payment_method=Order.PaymentMethod.COD,
            status=Order.Status.PENDING,
            subtotal="25.00",
        )
        signed_token = build_delivery_signed_token(order)

        self.client.login(username="rider-checkout", password="secret12345")
        response = self.client.get(reverse("orders:rider_delivery_confirm", args=[signed_token]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not have an assigned rider yet")

# Create your tests here.
