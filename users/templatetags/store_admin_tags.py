from django import template
from django.contrib.auth.models import User

from orders.models import Order
from products.models import Product
from reviews.models import Review

register = template.Library()


@register.simple_tag
def get_admin_stats():
    return {
        "users": User.objects.count(),
        "products": Product.objects.count(),
        "orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
        "reviews": Review.objects.count(),
    }
