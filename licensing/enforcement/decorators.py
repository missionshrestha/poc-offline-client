# licensing/enforcement/decorators.py
from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from rest_framework.request import Request
from rest_framework.response import Response

from licensing.services.validation import LicenseGrants
from licensing.enforcement.context import (
    LicenseContext,
    get_current_license_context,
    build_license_error_response,
    build_feature_not_licensed_response,
)

# Type var for view methods
ViewMethod = TypeVar("ViewMethod", bound=Callable[..., Any])


def _attach_license_to_request(
    request: Request,
    ctx: LicenseContext,
) -> None:
    """
    Attach license context to the DRF request object so views can use it.

    This is internal; the public contract is that views MAY access:
      - request.license_grants
      - request.installed_license
    """
    # These attributes don't exist on Request by default, so we set them dynamically.
    setattr(request, "license_grants", ctx.grants)
    setattr(request, "installed_license", ctx.installed)


def require_valid_license(view_method: ViewMethod) -> ViewMethod:
    """
    Decorator for DRF view methods (e.g. post/get) that require a valid license.

    Usage:

        from licensing.enforcement.decorators import require_valid_license

        class PipelineRunView(APIView):
            @require_valid_license
            def post(self, request, *args, **kwargs):
                # request.license_grants is available here
                ...
    """
    @wraps(view_method)
    def _wrapped(self, request: Request, *args, **kwargs) -> Response:
        ctx: LicenseContext = get_current_license_context()
        grants: LicenseGrants = ctx.grants

        # If license is not valid, immediately return a standardized error response.
        if grants.status != "valid":
            return build_license_error_response(grants)

        # License is valid; attach context to request for downstream usage.
        _attach_license_to_request(request, ctx)

        # Proceed with the original view method.
        return cast(Response, view_method(self, request, *args, **kwargs))

    return cast(ViewMethod, _wrapped)


def require_feature(feature_key: str) -> Callable[[ViewMethod], ViewMethod]:
    """
    Decorator factory that enforces a specific feature flag.

    It implicitly requires a valid license first, then checks if
    grants.features[feature_key] is truthy.

    Usage:

        from licensing.enforcement.decorators import require_feature

        class PipelineRunView(APIView):
            @require_feature("pipeline_execution")
            def post(self, request, *args, **kwargs):
                ...
    """
    def decorator(view_method: ViewMethod) -> ViewMethod:
        @wraps(view_method)
        def _wrapped(self, request: Request, *args, **kwargs) -> Response:
            ctx: LicenseContext = get_current_license_context()
            grants: LicenseGrants = ctx.grants

            # 1) License must be valid at all.
            if grants.status != "valid":
                return build_license_error_response(grants)

            # 2) Check the feature flag.
            features = grants.features or {}
            allowed = bool(features.get(feature_key))

            if not allowed:
                return build_feature_not_licensed_response(grants, feature_key)

            # 3) Attach context and proceed.
            _attach_license_to_request(request, ctx)
            return cast(Response, view_method(self, request, *args, **kwargs))

        return cast(ViewMethod, _wrapped)

    return decorator
