from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "city", "postal_code", "updated_at")
    list_filter = ("city", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "phone", "city")

# Register your models here.
