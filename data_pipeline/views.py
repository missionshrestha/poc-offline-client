# data_pipeline/views.py 
from __future__ import annotations

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as drf_status

from licensing.enforcement import require_feature
from licensing.services.validation import LicenseGrants  # type hint only

from .serializers import (
    PipelineRunRequestSerializer,
    PipelineExportRequestSerializer,
    CustomConnectorRequestSerializer,
)


class PipelineRunView(APIView):
    """
    POST /api/pipelines/run/

    Simulates running a data pipeline. For the POC, we don't actually
    execute anything heavy; we just echo the request and include license info.

    Requires:
      - License status = "valid"
      - features.pipeline_execution == truthy
    """
    @require_feature("pipeline_execution")
    def post(self, request, *args, **kwargs):
        serializer = PipelineRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        grants: LicenseGrants = getattr(request, "license_grants")  # set by decorator

        response_payload = {
            "message": "Pipeline run accepted (stub).",
            "pipeline_id": data["pipeline_id"],
            "parameters": data.get("parameters", {}),
            "license": {
                "status": grants.status,
                "license_id": grants.license_id,
                "customer_name": grants.customer_name,
                "edition_code": grants.edition_code,
                "features": grants.features,
            },
        }
        return Response(response_payload, status=drf_status.HTTP_200_OK)


class PipelineExportView(APIView):
    """
    POST /api/pipelines/export/

    Simulates exporting pipeline results. Again, this is a stub that just
    echoes the request and shows that licensing is checked.

    Requires:
      - License status = "valid"
      - features.advanced_export == truthy
    """
    @require_feature("advanced_export")
    def post(self, request, *args, **kwargs):
        serializer = PipelineExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        grants: LicenseGrants = getattr(request, "license_grants")

        response_payload = {
            "message": "Pipeline export accepted (stub).",
            "pipeline_id": data["pipeline_id"],
            "export_format": data["export_format"],
            "options": data.get("options", {}),
            "license": {
                "status": grants.status,
                "license_id": grants.license_id,
                "edition_code": grants.edition_code,
                "features": grants.features,
            },
        }
        return Response(response_payload, status=drf_status.HTTP_200_OK)


class CustomConnectorInvokeView(APIView):
    """
    POST /api/pipelines/custom-connector/

    Simulates calling a custom connector (e.g. external system integration).

    Requires:
      - License status = "valid"
      - features.custom_connectors == truthy
    """
    @require_feature("custom_connectors")
    def post(self, request, *args, **kwargs):
        serializer = CustomConnectorRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        grants: LicenseGrants = getattr(request, "license_grants")

        response_payload = {
            "message": "Custom connector invocation accepted (stub).",
            "connector_key": data["connector_key"],
            "payload": data["payload"],
            "license": {
                "status": grants.status,
                "license_id": grants.license_id,
                "customer_name": grants.customer_name,
                "features": grants.features,
            },
        }
        return Response(response_payload, status=drf_status.HTTP_200_OK)


# ----------------------------------------------------------------------
# Optional: DummyProtectedView used earlier for quick testing
# ----------------------------------------------------------------------


class DummyProtectedView(APIView):
    """
    Simple test endpoint to validate license enforcement decorators.

    You can keep or delete this once you're happy with the real endpoints.
    """
    # Uncomment to enforce licensing on this dummy endpoint too:
    # @require_feature("pipeline_execution")
    def post(self, request, *args, **kwargs):
        print("DummyProtectedView called")
        grants = getattr(request, "license_grants", None)
        status_str = getattr(grants, "status", None) if grants else None
        return Response(
            {
                "message": "OK, you hit a dummy protected endpoint.",
                "license_status": status_str,
            }
        )
