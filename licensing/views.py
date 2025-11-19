from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from typing import Any, Dict

from licensing.serializers import (
    LicenseUploadSerializer,
    LicenseStatusSerializer,
)
from licensing.services.validation import (
    validate_license_document,
    install_license_from_document,
    evaluate_current_license,
    LicenseDocumentError,
)
from licensing.models import InstalledLicense


class UploadLicenseView(APIView):
    """
    POST /api/license/upload/

    Accepts:
    {
      "license": { "meta": ..., "payload": ..., "signature": "..." }
    }

    Behavior:
    - Validates the structure and signature of the provided license.
    - If signature is invalid or malformed: returns 400 and does NOT install it.
    - If valid (or expired/not_yet_valid): installs it as the active InstalledLicense.
    - Returns normalized LicenseGrants JSON representation.
    """

    def post(self, request, *args, **kwargs):
        serializer = LicenseUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        license_obj: Dict[str, Any] = serializer.validated_data["license"]

        try:
            grants = validate_license_document(license_obj)
        except Exception as exc:
            return Response(
                {
                    "detail": "Unexpected error while validating license.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if grants.status in ("invalid_signature", "error"):
            status_code = status.HTTP_400_BAD_REQUEST
            status_serializer = LicenseStatusSerializer.from_grants(grants)
            status_serializer.is_valid(raise_exception=True)
            return Response(status_serializer.data, status=status_code)

        # For 'expired' and 'not_yet_valid', we still install:
        # - 'expired': allows UI to show "you had a license but it expired"
        # - 'not_yet_valid': license is valid in future window
        try:
            installed, final_grants = install_license_from_document(license_obj)
        except LicenseDocumentError as exc:
            return Response(
                {
                    "detail": "Malformed license document.",
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            return Response(
                {
                    "detail": "Unexpected error while installing license.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_serializer = LicenseStatusSerializer.from_grants(
            final_grants,
            installed_at=installed.installed_at,
            last_validated_at=installed.last_validated_at,
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class LicenseStatusView(APIView):
    """
    GET /api/license/status/

    Returns the current license status and grants.

    - If no license installed: status='missing'
    - Otherwise:
      - Re-validates the active InstalledLicense from its raw JSON
      - Syncs DB cache fields
      - Returns normalized grants + timestamps
    """

    def get(self, request, *args, **kwargs):
        try:
            installed, grants = evaluate_current_license()
        except Exception as exc:
            return Response(
                {
                    "detail": "Unexpected error while evaluating current license.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        installed_at = installed.installed_at if installed else None
        last_validated_at = installed.last_validated_at if installed else None

        response_serializer = LicenseStatusSerializer.from_grants(
            grants,
            installed_at=installed_at,
            last_validated_at=last_validated_at,
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
