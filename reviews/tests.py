from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product

from .models import Review


class ReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reviewer", password="secret12345")
        self.category = Category.objects.create(name="Accessories")
        self.product = Product.objects.create(
            category=self.category,
            name="Canvas Tote",
            description="Reusable shopping tote",
            price="20.00",
            stock=12,
        )

    def test_anonymous_users_cannot_submit_reviews(self):
        response = self.client.post(
            reverse("reviews:submit_review", args=[self.product.slug]),
            {"rating": 5, "comment": "Great"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Review.objects.count(), 0)

    def test_authenticated_users_can_create_and_update_reviews(self):
        self.client.login(username="reviewer", password="secret12345")

        self.client.post(
            reverse("reviews:submit_review", args=[self.product.slug]),
            {"rating": 4, "comment": "Solid quality"},
        )
        self.client.post(
            reverse("reviews:submit_review", args=[self.product.slug]),
            {"rating": 5, "comment": "Even better after a week"},
        )

        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Even better after a week")

# Create your tests here.
