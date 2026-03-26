from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "Lola Josie Tindahan Admin"
admin.site.site_title = "Lola Josie Tindahan Control Room"
admin.site.index_title = "Store Management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin-dashboard/", include(("users.admin_urls", "admin_dashboard"), namespace="admin_dashboard")),
    path("api/", include("api.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("users/", include("users.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("reviews/", include("reviews.urls")),
    path("dashboard/", RedirectView.as_view(pattern_name="admin_dashboard:index", permanent=False)),
    path("", include("products.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
