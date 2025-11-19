# licensing/serializers.py

from rest_framework import serializers
from typing import Any, Dict

from licensing.services.validation import LicenseGrants


class LicenseUploadSerializer(serializers.Serializer):
    """
    Accepts a full license document as JSON under the 'license' key.

    {
      "license": {
        "meta": {...},
        "payload": {...},
        "signature": "..."
      }
    }
    """
    license = serializers.JSONField()

    def validate_license(self, value: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise serializers.ValidationError("License must be a JSON object.")
        # We leave detailed structural validation to the validation pipeline.
        return value


class LicenseStatusSerializer(serializers.Serializer):
    """
    Serializes LicenseGrants (and optionally some DB metadata) into JSON.
    """

    # Core status
    status = serializers.CharField()
    status_message = serializers.CharField()

    # Identity / product
    license_id = serializers.CharField(allow_null=True, required=False)
    license_type = serializers.CharField(allow_null=True, required=False)
    customer_name = serializers.CharField(allow_null=True, required=False)
    product_code = serializers.CharField(allow_null=True, required=False)
    product_name = serializers.CharField(allow_null=True, required=False)
    edition_code = serializers.CharField(allow_null=True, required=False)
    edition_name = serializers.CharField(allow_null=True, required=False)

    # Validity window
    valid_from = serializers.DateTimeField(allow_null=True, required=False)
    valid_until = serializers.DateTimeField(allow_null=True, required=False)

    # Grants
    features = serializers.JSONField()
    usage_limits = serializers.JSONField()
    deployment = serializers.JSONField()

    # Extra info
    warnings = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
    )

    # Optional DB metadata
    installed_at = serializers.DateTimeField(allow_null=True, required=False)
    last_validated_at = serializers.DateTimeField(allow_null=True, required=False)

    @classmethod
    def from_grants(
        cls,
        grants: LicenseGrants,
        *,
        installed_at=None,
        last_validated_at=None,
    ) -> "LicenseStatusSerializer":
        """
        Helper to build serializer instance from LicenseGrants + optional DB timestamps.
        """
        data = {
            "status": grants.status,
            "status_message": grants.status_message,
            "license_id": grants.license_id,
            "license_type": grants.license_type,
            "customer_name": grants.customer_name,
            "product_code": grants.product_code,
            "product_name": grants.product_name,
            "edition_code": grants.edition_code,
            "edition_name": grants.edition_name,
            "valid_from": grants.valid_from,
            "valid_until": grants.valid_until,
            "features": grants.features,
            "usage_limits": grants.usage_limits,
            "deployment": grants.deployment,
            "warnings": grants.warnings,
            "installed_at": installed_at,
            "last_validated_at": last_validated_at,
        }
        return cls(data=data)
