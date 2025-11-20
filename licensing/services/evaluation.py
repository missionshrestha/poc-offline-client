import datetime
from typing import Any, Dict

from django.utils import timezone

from licensing.models import InstalledLicense


def _normalize_features(payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Normalize the features block from the payload into a consistent structure.

    Input (from signed payload):
        {
            "pipeline_execution": true,
            "advanced_export": {
                "enabled": true,
                "max_export_size_mb": 500
            },
            "custom_connectors": false
        }

    Output (normalized):
        {
            "pipeline_execution": {"enabled": True, "config": {}},
            "advanced_export": {
                "enabled": True,
                "config": {"max_export_size_mb": 500}
            },
            "custom_connectors": {"enabled": False, "config": {}}
        }
    """
    features_raw = (payload or {}).get("features") or {}
    normalized: Dict[str, Dict[str, Any]] = {}

    for key, value in features_raw.items():
        # Boolean: simple enable/disable
        if isinstance(value, bool):
            normalized[key] = {"enabled": bool(value), "config": {}}
        # Dict: advanced config, expect "enabled" + extras
        elif isinstance(value, dict):
            enabled = bool(value.get("enabled", True))
            config = {k: v for k, v in value.items() if k != "enabled"}
            normalized[key] = {"enabled": enabled, "config": config}
        # Anything else: treat as disabled but keep raw for debugging
        else:
            normalized[key] = {"enabled": False, "config": {"raw": value}}

    return normalized


def _normalize_limits(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize limits block from payload.

    Example input:
        {
            "max_runs_per_day": 50,
            "max_runs_per_month": 1000,
            "max_concurrent_runs": 3
        }

    We currently just pass through known keys; can be extended later.
    """
    limits_raw = (payload or {}).get("limits") or {}
    limits: Dict[str, Any] = {}

    for key in ("max_runs_per_day", "max_runs_per_month", "max_concurrent_runs"):
        if key in limits_raw:
            limits[key] = limits_raw[key]

    return limits


def evaluate_current_license() -> Dict[str, Any]:
    """
    Evaluate the currently active InstalledLicense and return a normalized
    'LicenseGrants' dict that can be attached to the request.

    IMPORTANT:
        - This does NOT verify signatures here.
        - It trusts InstalledLicense.status (set by the upload/validation logic).
        - It does NOT enforce usage limits (that will be built on top in Phase 5.4).

    Structure:
        {
            "status": str,        # "valid", "expired", "missing", ...
            "is_valid": bool,
            "license_id": str | None,
            "customer_name": str | None,
            "edition_code": str | None,
            "edition_name": str | None,
            "license_type": str | None,
            "valid_from": datetime | None,
            "valid_until": datetime | None,
            "features": dict,
            "limits": dict,
            "warnings": list[str],
        }
    """
    now = timezone.now()

    # Pick the most recently installed active license, if any
    installed = (
        InstalledLicense.objects.filter(is_active=True)
        .order_by("-installed_at")
        .first()
    )

    if installed is None:
        return {
            "status": "missing",
            "is_valid": False,
            "license_id": None,
            "customer_name": None,
            "edition_code": None,
            "edition_name": None,
            "license_type": None,
            "valid_from": None,
            "valid_until": None,
            "features": {},
            "limits": {},
            "warnings": [],
        }

    # Use status from InstalledLicense as primary source
    status = installed.status or "error"
    is_valid = status == "valid"

    payload = installed.payload or {}
    features = _normalize_features(payload)
    limits = _normalize_limits(payload)

    warnings = []

    # Simple "expiring soon" warning (e.g., within 7 days)
    try:
        if installed.valid_until and installed.valid_until <= now:
            warnings.append("expired")
        elif installed.valid_until and installed.valid_until - now <= datetime.timedelta(days=7):
            warnings.append("expiring_soon")
    except Exception:
        # Just ignore warning if we can't compare times
        pass

    return {
        "status": status,
        "is_valid": is_valid,
        "license_id": installed.license_id or str(installed.id),
        "customer_name": installed.customer_name or None,
        "edition_code": installed.edition_code or None,
        "edition_name": installed.edition_name or None,
        "license_type": installed.license_type or None,
        "valid_from": installed.valid_from,
        "valid_until": installed.valid_until,
        "features": features,
        "limits": limits,
        "warnings": warnings,
    }
