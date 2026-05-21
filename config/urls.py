from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("oauth/", include("social_django.urls", namespace="social")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.content.urls")),
    path("", include("apps.enrollment.urls")),
    path("", include("apps.progress.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.chat.urls")),
    path("", include("apps.forums.urls")),
    path("", include("apps.reviews.urls")),
    path("", include("apps.certificates.urls")),
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
