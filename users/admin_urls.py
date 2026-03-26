from django.urls import path

from . import admin_views

app_name = "admin_dashboard"

urlpatterns = [
    path("login/", admin_views.admin_login, name="login"),
    path("logout/", admin_views.admin_logout, name="logout"),
    path("", admin_views.dashboard, name="index"),
    path("users/", admin_views.user_list, name="user_list"),
    path("users/<int:user_id>/", admin_views.user_detail, name="user_detail"),
    path("users/<int:user_id>/toggle-active/", admin_views.user_toggle_active, name="user_toggle_active"),
    path("products/", admin_views.product_list, name="product_list"),
    path("products/add/", admin_views.product_create, name="product_create"),
    path("products/categories/", admin_views.category_list, name="category_list"),
    path("products/categories/add/", admin_views.category_create, name="category_create"),
    path("products/categories/<int:category_id>/edit/", admin_views.category_edit, name="category_edit"),
    path("products/categories/<int:category_id>/delete/", admin_views.category_delete, name="category_delete"),
    path("products/<int:product_id>/edit/", admin_views.product_edit, name="product_edit"),
    path("products/<int:product_id>/delete/", admin_views.product_delete, name="product_delete"),
    path("orders/", admin_views.order_list, name="order_list"),
    path("orders/<int:order_id>/", admin_views.order_detail, name="order_detail"),
    path("payments/", admin_views.payment_list, name="payment_list"),
    path("payments/<int:payment_id>/status/", admin_views.payment_update_status, name="payment_update_status"),
    path("reviews/", admin_views.review_list, name="review_list"),
    path("reviews/<int:review_id>/delete/", admin_views.review_delete, name="review_delete"),
]
