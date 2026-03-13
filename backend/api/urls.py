from django.urls import path
from .views import GenerateSowView, GenerateDiagramView, HealthCheckView

urlpatterns = [
    path("", HealthCheckView.as_view(), name="health-check"),
    path("generate-sow/", GenerateSowView.as_view(), name="generate-sow"),
    path("generate-diagram/", GenerateDiagramView.as_view(), name="generate-diagram"),
]
