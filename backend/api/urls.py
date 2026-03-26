from django.urls import path
from .views import GenerateSowView, GenerateSowFromChatView, GenerateDiagramView, HealthCheckView, ImageProxyView, ExportSowWordView

urlpatterns = [
    path("", HealthCheckView.as_view(), name="health-check"),
    path("generate-sow/", GenerateSowView.as_view(), name="generate-sow"),
    path("generate-sow/chat/", GenerateSowFromChatView.as_view(), name="generate-sow-chat"),
    path("generate-diagram/", GenerateDiagramView.as_view(), name="generate-diagram"),
    path("image-proxy/", ImageProxyView.as_view(), name="image-proxy"),
    path("export-docx/", ExportSowWordView.as_view(), name="export-docx"),
]
