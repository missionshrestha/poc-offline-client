# licensing/services/validation.py

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from licensing.services.verification import (
    verify_license_signature,
    SignatureVerificationResult,
)
from licensing.models import InstalledLicense
from django.db import transaction

@dataclass
class LicenseGrants:
    """
    Normalized view of what a license allows and its current status.

    This is the *only* authoritative view the application should use.
    All fields are derived from the signed payload + runtime checks.
    """
    status: str
    status_message: str

    license_id: Optional[str] = None
    license_type: Optional[str] = None

    customer_name: Optional[str] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None

    edition_code: Optional[str] = None
    edition_name: Optional[str] = None

    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

    features: Dict[str, Any] = field(default_factory=dict)
    usage_limits: Dict[str, Any] = field(default_factory=dict)
    deployment: Dict[str, Any] = field(default_factory=dict)

    warnings: List[str] = field(default_factory=list)

    raw_payload: Dict[str, Any] = field(default_factory=dict)


class LicenseDocumentError(Exception):
    """Raised when the license document is malformed or incomplete."""
    pass


def parse_license_document(raw: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """
    Parse the top-level license document structure.

    Expects:
    {
      "meta": { "version": 1, "alg": "Ed25519", "key_id": "main-v1", ... },
      "payload": { ... },
      "signature": "..."
    }
    """
    if not isinstance(raw, dict):
        raise LicenseDocumentError("License must be a JSON object.")

    try:
        meta = raw["meta"]
        payload = raw["payload"]
        signature = raw["signature"]
    except KeyError as exc:
        raise LicenseDocumentError(f"Missing required field in license document: {exc}") from exc

    if not isinstance(meta, dict):
        raise LicenseDocumentError("Field 'meta' must be an object.")
    if not isinstance(payload, dict):
        raise LicenseDocumentError("Field 'payload' must be an object.")
    if not isinstance(signature, str):
        raise LicenseDocumentError("Field 'signature' must be a string.")

    alg = meta.get("alg")
    key_id = meta.get("key_id")

    if alg is None:
        raise LicenseDocumentError("meta.alg is required.")
    if key_id is None:
        raise LicenseDocumentError("meta.key_id is required.")

    return meta, payload, signature


def _parse_iso8601(dt_str: str) -> Optional[datetime]:
    """
    Parse an ISO8601 datetime string into an aware datetime.

    We expect Z-terminated strings (UTC) from the server, e.g. "2025-01-01T00:00:00Z".
    """
    if not dt_str:
        return None
    # Replace 'Z' with '+00:00' if needed for parse_datetime
    normalized = dt_str.replace("Z", "+00:00") if dt_str.endswith("Z") else dt_str
    dt = parse_datetime(normalized)
    if dt is not None and timezone.is_naive(dt):
        # Force UTC if naive
        dt = timezone.make_aware(dt, timezone.utc)
    return dt


def _extract_core_fields_from_payload(payload: Dict[str, Any]) -> Tuple[
    Optional[str], Optional[str],
    Optional[str], Optional[str], Optional[str],
    Optional[datetime], Optional[datetime],
    Dict[str, Any], Dict[str, Any], Dict[str, Any]
]:
    """
    Extract key fields from payload:

    - license_id
    - license_type
    - customer_name
    - product_code, product_name
    - valid_from, valid_until
    - features, usage_limits, deployment
    """
    license_id = payload.get("license_id")
    license_type = payload.get("license_type")

    customer = payload.get("customer") or {}
    customer_name = customer.get("name")

    product = payload.get("product") or {}
    product_code = product.get("code")
    product_name = product.get("name")

    validity = payload.get("validity") or {}
    valid_from_str = validity.get("valid_from")
    valid_until_str = validity.get("valid_until")

    valid_from = _parse_iso8601(valid_from_str) if valid_from_str else None
    valid_until = _parse_iso8601(valid_until_str) if valid_until_str else None

    features = payload.get("features") or {}
    usage_limits = payload.get("usage_limits") or {}
    deployment = payload.get("deployment") or {}

    return (
        license_id,
        license_type,
        customer_name,
        product_code,
        product_name,
        valid_from,
        valid_until,
        features,
        usage_limits,
        deployment,
    )


def _extract_edition_fields(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract edition_code, edition_name from payload.edition
    """
    edition = payload.get("edition") or {}
    edition_code = edition.get("code")
    edition_name = edition.get("name")
    return edition_code, edition_name


def validate_license_document(
    license_obj: Dict[str, Any],
    *,
    now: Optional[datetime] = None,
) -> LicenseGrants:
    """
    Validate a license document end-to-end.

    Steps:
    - Parse structure (meta, payload, signature)
    - Verify signature (Ed25519) using server's public key
    - Extract validity window from payload
    - Evaluate current status (valid, expired, not_yet_valid, invalid_signature, error)
    - Build a LicenseGrants object with normalized fields

    NOTE: This function does not touch the database. It is pure.
    """
    if now is None:
        now = timezone.now()

    try:
        meta, payload, signature = parse_license_document(license_obj)
    except LicenseDocumentError as exc:
        return LicenseGrants(
            status="error",
            status_message=str(exc),
            raw_payload=license_obj if isinstance(license_obj, dict) else {},
        )

    alg = meta.get("alg")
    key_id = meta.get("key_id")

    # 1) Verify signature
    sig_result: SignatureVerificationResult = verify_license_signature(
        payload=payload,
        signature_b64=signature,
        alg=alg,
        key_id=key_id,
    )

    # 2) Extract fields from payload (even if signature invalid, for debugging/UI)
    (
        license_id,
        license_type,
        customer_name,
        product_code,
        product_name,
        valid_from,
        valid_until,
        features,
        usage_limits,
        deployment,
    ) = _extract_core_fields_from_payload(payload)

    edition_code, edition_name = _extract_edition_fields(payload)

    warnings: List[str] = []

    # 3) Determine status
    if not sig_result.ok:
        # Signature invalid or cannot verify; we treat license as unusable.
        status = "invalid_signature"
        status_message = sig_result.error or "Invalid signature."
    else:
        # Signature is valid. Now apply time-based checks.
        if not valid_from or not valid_until:
            status = "error"
            status_message = (
                "License payload is missing validity.valid_from or validity.valid_until."
            )
        else:
            if now < valid_from:
                status = "not_yet_valid"
                status_message = "License is not yet valid (starts at {}).".format(
                    valid_from.isoformat()
                )
            elif now > valid_until:
                status = "expired"
                status_message = "License expired at {}.".format(valid_until.isoformat())
            else:
                status = "valid"
                status_message = "License is valid."

                # Optional: add expirying-soon warning
                # e.g. warn if expires within 7 days
                delta = valid_until - now
                if delta.days < 7:
                    warnings.append(
                        f"License will expire soon (in {delta.days} day(s))."
                    )

    return LicenseGrants(
        status=status,
        status_message=status_message,
        license_id=license_id,
        license_type=license_type,
        customer_name=customer_name,
        product_code=product_code,
        product_name=product_name,
        edition_code=edition_code,
        edition_name=edition_name,
        valid_from=valid_from,
        valid_until=valid_until,
        features=features,
        usage_limits=usage_limits,
        deployment=deployment,
        warnings=warnings,
        raw_payload=payload,
    )


@transaction.atomic
def install_license_from_document(
    license_obj: Dict[str, Any],
) -> Tuple[InstalledLicense, LicenseGrants]:
    """
    Validate a license document and install it as the active InstalledLicense.

    - Runs validate_license_document() (pure, payload-based)
    - Ensures exactly one active InstalledLicense (older ones set is_active=False)
    - Writes non-authoritative, denormalized fields to InstalledLicense
      (e.g., valid_from, valid_until, status, customer_name, etc.)
    - Stores the full raw_license_json, payload, and signature.

    Returns: (installed_license, grants)
    """
    grants = validate_license_document(license_obj)

    # Extract meta + payload + signature again for storage
    try:
        meta, payload, signature = parse_license_document(license_obj)
    except LicenseDocumentError:
        # If parsing fails here, it should have already been an error grants.status.
        # But we still refuse to install.
        raise

    # Prefer a stable license_id from the payload; fallback to a random UUID for DB pk if missing.
    license_id = grants.license_id

    # Deactivate any existing active licenses
    InstalledLicense.objects.filter(is_active=True).update(is_active=False)

    # Either create a fresh record or reuse existing record for same license_id (optional behavior).
    # For simplicity, we'll always create a new record here.
    now = timezone.now()

    installed = InstalledLicense.objects.create(
        license_id=license_id or "",
        license_type=grants.license_type or "",
        edition_code=grants.edition_code or "",
        edition_name=grants.edition_name or "",
        customer_name=grants.customer_name or "",
        raw_license_json=license_obj,
        payload=payload,
        signature=signature,
        algorithm=meta.get("alg", "Ed25519"),
        key_id=meta.get("key_id", "main-v1"),
        valid_from=grants.valid_from or now,
        valid_until=grants.valid_until or now,
        status=grants.status,
        status_message=grants.status_message,
        installed_at=now,
        last_validated_at=now,
        is_active=True,
    )

    return installed, grants


def evaluate_current_license() -> Tuple[Optional[InstalledLicense], LicenseGrants]:
    """
    Load the currently active InstalledLicense (if any), re-validate it
    from its raw_license_json, and return (instance_or_None, grants).

    If no license is installed, returns (None, LicenseGrants with status='missing').
    """
    active = InstalledLicense.objects.filter(is_active=True).first()

    if active is None:
        # No license installed
        grants = LicenseGrants(
            status="missing",
            status_message="No license installed.",
            raw_payload={},
        )
        return None, grants

    license_obj = active.raw_license_json
    grants = validate_license_document(license_obj)

    # Sync DB fields with grants (overwriting any manual tampering).
    now = timezone.now()

    active.license_id = grants.license_id or ""
    active.license_type = grants.license_type or ""
    active.customer_name = grants.customer_name or ""
    active.edition_code = grants.edition_code or ""
    active.edition_name = grants.edition_name or ""
    active.valid_from = grants.valid_from or active.valid_from
    active.valid_until = grants.valid_until or active.valid_until
    active.status = grants.status
    active.status_message = grants.status_message
    active.last_validated_at = now
    active.save(update_fields=[
        "license_id",
        "license_type",
        "customer_name",
        "edition_code",
        "edition_name",
        "valid_from",
        "valid_until",
        "status",
        "status_message",
        "last_validated_at",
        "updated_at",
    ])

    return active, grants
