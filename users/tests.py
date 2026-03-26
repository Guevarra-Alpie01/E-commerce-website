from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from orders.models import Order, Payment
from products.models import Category, Product
from reviews.models import Review

from .models import UserProfile


class RegistrationTests(TestCase):
    def test_register_creates_user_and_profile(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "first_name": "Nina",
                "last_name": "Shah",
                "username": "nina",
                "email": "nina@example.com",
                "password1": "strongpass12345",
                "password2": "strongpass12345",
            },
        )

        self.assertRedirects(response, reverse("users:profile"))
        user = User.objects.get(username="nina")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_register_redirects_admin_users_to_dashboard(self):
        admin_user = User.objects.create_user(
            username="admin-sample",
            password="secret12345",
            email="admin@example.com",
            is_staff=True,
        )
        self.client.login(username="admin-sample", password="secret12345")

        response = self.client.get(reverse("users:register"))

        self.assertRedirects(response, reverse("admin_dashboard:index"))


class CustomAdminDashboardTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="manager",
            password="secret12345",
            email="manager@example.com",
            is_staff=True,
        )
        self.normal_user = User.objects.create_user(
            username="shopper",
            password="secret12345",
            email="shopper@example.com",
        )
        self.category = Category.objects.create(name="Groceries")
        self.product = Product.objects.create(
            category=self.category,
            name="Organic Apples",
            description="Fresh apples for weekly shopping",
            price="120.00",
            stock=4,
        )
        self.order = Order.objects.create(
            user=self.normal_user,
            full_name="Shopper Sample",
            address="123 Market Street",
            phone="09170000000",
            payment_method=Order.PaymentMethod.COD,
            status=Order.Status.PENDING,
            subtotal="240.00",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            user=self.normal_user,
            amount="240.00",
            payment_method=Order.PaymentMethod.COD,
            status=Payment.Status.PENDING,
        )
        self.review = Review.objects.create(
            user=self.normal_user,
            product=self.product,
            rating=2,
            comment="Needs better packaging",
        )

    def test_staff_user_can_access_admin_dashboard(self):
        self.client.login(username="manager", password="secret12345")

        response = self.client.get(reverse("admin_dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard Overview")

    def test_staff_user_is_redirected_away_from_storefront(self):
        self.client.login(username="manager", password="secret12345")

        response = self.client.get(reverse("products:product_list"))

        self.assertRedirects(response, reverse("admin_dashboard:index"))

    def test_homepage_login_redirects_staff_to_admin_dashboard(self):
        response = self.client.post(
            reverse("products:product_list"),
            {
                "login_submit": "1",
                "username": "manager",
                "password": "secret12345",
            },
        )

        self.assertRedirects(response, reverse("admin_dashboard:index"))

    def test_homepage_login_redirects_customer_to_profile(self):
        response = self.client.post(
            reverse("products:product_list"),
            {
                "login_submit": "1",
                "username": "shopper",
                "password": "secret12345",
            },
        )

        self.assertRedirects(response, reverse("users:profile"))

    def test_normal_user_is_redirected_from_admin_dashboard(self):
        self.client.login(username="shopper", password="secret12345")

        response = self.client.get(reverse("admin_dashboard:index"))

        self.assertRedirects(response, reverse("products:product_list"))

    def test_staff_can_create_product_from_custom_admin(self):
        self.client.login(username="manager", password="secret12345")

        response = self.client.post(
            reverse("admin_dashboard:product_create"),
            {
                "category": self.category.id,
                "name": "Fresh Kale",
                "description": "Leafy greens",
                "price": "85.00",
                "stock": 12,
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("admin_dashboard:product_list"))
        self.assertTrue(Product.objects.filter(name="Fresh Kale").exists())

    def test_staff_can_create_category_from_custom_admin(self):
        self.client.login(username="manager", password="secret12345")

        response = self.client.post(
            reverse("admin_dashboard:category_create"),
            {
                "name": "Beverages",
                "description": "Drinks and refreshers",
            },
        )

        self.assertRedirects(response, reverse("admin_dashboard:category_list"))
        self.assertTrue(Category.objects.filter(name="Beverages").exists())

    def test_product_create_shows_category_guidance_when_none_exist(self):
        self.client.login(username="manager", password="secret12345")
        Product.objects.all().delete()
        Category.objects.all().delete()

        response = self.client.get(reverse("admin_dashboard:product_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Categories are required before you can create products.")

    def test_delivered_order_marks_payment_completed(self):
        self.client.login(username="manager", password="secret12345")

        response = self.client.post(
            reverse("admin_dashboard:order_detail", args=[self.order.id]),
            {"status": Order.Status.DELIVERED},
        )

        self.assertRedirects(response, reverse("admin_dashboard:order_detail", args=[self.order.id]))
        self.order.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.DELIVERED)
        self.assertEqual(self.payment.status, Payment.Status.COMPLETED)

    def test_staff_can_delete_review_from_custom_admin(self):
        self.client.login(username="manager", password="secret12345")

        response = self.client.post(reverse("admin_dashboard:review_delete", args=[self.review.id]))

        self.assertRedirects(response, reverse("admin_dashboard:review_list"))
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())
