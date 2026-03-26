from django.conf import settings


def site_meta(request):
    return {
        "site_name": settings.SITE_NAME,
        "site_tagline": settings.SITE_TAGLINE,
    }
