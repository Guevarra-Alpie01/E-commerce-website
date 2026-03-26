from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

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

# Create your tests here.
