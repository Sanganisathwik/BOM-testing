from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from api.views import HealthCheckView

urlpatterns = [
    path("", HealthCheckView.as_view(), name="root"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
