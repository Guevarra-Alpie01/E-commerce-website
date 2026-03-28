from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("history/", views.order_history, name="order_history"),
    path("rider/deliver/<str:signed_token>/", views.rider_delivery_confirm, name="rider_delivery_confirm"),
    path("<int:order_id>/", views.order_detail, name="order_detail"),
    path("<int:order_id>/success/", views.order_success, name="order_success"),
]
