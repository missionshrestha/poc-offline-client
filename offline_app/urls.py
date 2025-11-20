from django.contrib import admin
from django.urls import path, include

from data_pipeline.views import DummyProtectedView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/license/", include("licensing.urls")),
    path("api/pipelines/", include("data_pipeline.urls")),
]
