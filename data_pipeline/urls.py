# data_pipeline/urls.py
from django.urls import path

from .views import (
    PipelineRunView,
    PipelineExportView,
    CustomConnectorInvokeView,
    DummyProtectedView,
)

urlpatterns = [
    path("run/", PipelineRunView.as_view(), name="pipeline-run"),
    path("export/", PipelineExportView.as_view(), name="pipeline-export"),
    path(
        "custom-connector/",
        CustomConnectorInvokeView.as_view(),
        name="pipeline-custom-connector",
    ),

    # Optional testing endpoint (you can remove later)
    path("dummy-protected/", DummyProtectedView.as_view(), name="dummy-protected"),
]

