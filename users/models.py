from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        RIDER = "rider", "Rider"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    delivery_zone = models.CharField(max_length=120, blank=True)
    vehicle_details = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Profile for {self.user.username}"
