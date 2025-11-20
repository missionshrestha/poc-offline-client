# licensing/enforcement/context.py 
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from rest_framework import status as drf_status
from rest_framework.response import Response

from licensing.models import InstalledLicense
from licensing.services.validation import (
    evaluate_current_license,
    LicenseGrants,
)


@dataclass
class LicenseContext:
    """
    Small container for the currently active license and its grants.
    """
    installed: Optional[InstalledLicense]
    grants: LicenseGrants


def get_current_license_context() -> LicenseContext:
    """
    Wrapper around evaluate_current_license() so all enforcement code
    goes through a single place.
    """
    installed, grants = evaluate_current_license()
    return LicenseContext(installed=installed, grants=grants)


def build_license_error_response(grants: LicenseGrants) -> Response:
    """
    Map LicenseGrants.status into a canonical JSON error response and HTTP status.

    Error codes:
      - license_missing
      - license_invalid
      - license_internal_error
    """
    status = grants.status

    if status == "missing":
        # No license installed at all.
        error_code = "license_missing"
        http_status = drf_status.HTTP_403_FORBIDDEN
        detail = grants.status_message or "No license installed."
    elif status in {
        "expired",
        "not_yet_valid",
        "invalid_signature",
        "tampered",
        "error",
    }:
        # We have a license but it's not usable.
        error_code = "license_invalid"
        http_status = drf_status.HTTP_403_FORBIDDEN
        detail = grants.status_message or "License is not valid."
    else:
        # This should not normally happen; treat as internal error.
        error_code = "license_internal_error"
        http_status = drf_status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = (
            grants.status_message
            or f"Unexpected license status '{status}'."
        )

    payload = {
        "error_code": error_code,
        "detail": detail,
        "status": status,
    }

    return Response(payload, status=http_status)


def build_feature_not_licensed_response(
    grants: LicenseGrants,
    feature_key: str,
) -> Response:
    """
    Build the canonical error response when a feature is not licensed.
    """
    payload = {
        "error_code": "feature_not_licensed",
        "detail": f"Feature '{feature_key}' is not enabled in the license.",
        "feature": feature_key,
        "status": grants.status,
    }
    return Response(payload, status=drf_status.HTTP_403_FORBIDDEN)

