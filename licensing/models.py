import uuid
from django.db import models
from django.utils import timezone


import uuid
from django.db import models
from django.utils import timezone


class InstalledLicense(models.Model):
    """
    The currently installed license file.

    NOTE: All fields here are *derived* from the signed license document.
    The signed payload is the only source of truth. These are cached copies
    for fast lookup and display, not security boundaries.
    """
    STATUS_CHOICES = [
        ("valid", "Valid"),
        ("expired", "Expired"),
        ("not_yet_valid", "Not Yet Valid"),
        ("invalid_signature", "Invalid Signature"),
        ("tampered", "Tampered / Payload Mismatch"),
        ("missing", "No License Installed"),
        ("error", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Core license identity (non-authoritative, derived from payload) ---
    license_id = models.CharField(
        max_length=64,
        blank=True,
        help_text="External license identifier as defined in the signed payload.",
    )
    license_type = models.CharField(
        max_length=32,
        blank=True,
        help_text="License type (e.g. trial, subscription, perpetual).",
    )
    edition_code = models.CharField(
        max_length=64,
        blank=True,
        help_text="Edition code from payload (e.g. 'enterprise').",
    )
    edition_name = models.CharField(
        max_length=128,
        blank=True,
        help_text="Edition name from payload (e.g. 'Enterprise').",
    )
    customer_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Customer name from payload.",
    )

    # full uploaded license JSON {meta, payload, signature}
    raw_license_json = models.JSONField()

    # extracted parts (still non-authoritative copies)
    payload = models.JSONField()
    signature = models.TextField()
    algorithm = models.CharField(max_length=50, default="Ed25519")
    key_id = models.CharField(max_length=100, default="main-v1")

    # validity window (derived from payload.validity)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    # current status (derived from validation logic)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="missing",
    )
    status_message = models.TextField(blank=True)

    # timestamps
    installed_at = models.DateTimeField(default=timezone.now)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        display_id = self.license_id or str(self.id)
        return f"InstalledLicense {display_id} [{self.status}]"


class LicenseUsage(models.Model):
    """
    Tracks daily/monthly usage for licenses that include usage limits.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        InstalledLicense,
        on_delete=models.CASCADE,
        related_name="usage",
    )

    daily_count = models.IntegerField(default=0)
    monthly_count = models.IntegerField(default=0)

    last_reset_daily = models.DateField(null=True, blank=True)
    last_reset_monthly = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Usage for license {self.license_id}"
