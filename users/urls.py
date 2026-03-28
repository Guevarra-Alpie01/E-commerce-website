from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("rider/", views.rider_dashboard, name="rider_dashboard"),
    path("rider/scan/", views.rider_scan, name="rider_scan"),
    path("rider/orders/<int:order_id>/", views.rider_order_detail, name="rider_order_detail"),
    path("rider/orders/<int:order_id>/start/", views.rider_order_start, name="rider_order_start"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
