from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url="admin_dashboard:login")
    def wrapped_view(request, *args, **kwargs):
        if not is_admin_user(request.user):
            messages.error(request, "You do not have permission to access the admin dashboard.")
            return redirect("products:product_list")
        return view_func(request, *args, **kwargs)

    return wrapped_view
