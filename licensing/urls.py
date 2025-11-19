from django.urls import path

from .views import UploadLicenseView, LicenseStatusView

urlpatterns = [
    path("upload/", UploadLicenseView.as_view(), name="license-upload"),
    path("status/", LicenseStatusView.as_view(), name="license-status"),
]
