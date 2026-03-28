from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import UserProfile


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def is_rider_user(user):
    if not user.is_authenticated or is_admin_user(user):
        return False
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == UserProfile.Role.RIDER)


def admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url="login")
    def wrapped_view(request, *args, **kwargs):
        if not is_admin_user(request.user):
            messages.error(request, "You do not have permission to access the admin dashboard.")
            return redirect("products:product_list")
        return view_func(request, *args, **kwargs)

    return wrapped_view


def rider_required(view_func):
    @wraps(view_func)
    @login_required(login_url="login")
    def wrapped_view(request, *args, **kwargs):
        if not is_rider_user(request.user):
            messages.error(request, "You do not have permission to access the rider dashboard.")
            return redirect("products:product_list")
        return view_func(request, *args, **kwargs)

    return wrapped_view
