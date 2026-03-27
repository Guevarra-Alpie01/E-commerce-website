from django.conf import settings
from django.shortcuts import redirect

from .admin_access import is_admin_user


class AdminDashboardOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_admin_user(getattr(request, "user", None)):
            path = request.path
            allowed_prefixes = ["/admin-dashboard/", "/api/"]

            if settings.STATIC_URL:
                allowed_prefixes.append(settings.STATIC_URL)
            if settings.MEDIA_URL:
                allowed_prefixes.append(settings.MEDIA_URL)

            allowed_paths = {"/favicon.ico"}

            if not any(path.startswith(prefix) for prefix in allowed_prefixes) and path not in allowed_paths:
                return redirect("admin_dashboard:index")

        return self.get_response(request)
