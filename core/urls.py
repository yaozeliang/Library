"""URL configuration for the Library Management System."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
import notifications.urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("book.urls")),
    path("auth/", include("authentication.urls")),
    path("api/", include("Api.urls")),
    path("comment/", include("comment.urls", namespace="comment")),
    path("inbox/notifications/", include(notifications.urls, namespace="notifications")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler400 = "book.views.bad_request"
handler403 = "book.views.permission_denied"
handler404 = "book.views.page_not_found"
handler500 = "book.views.server_error"
