# licensing/admin.py

from django.contrib import admin

from .models import InstalledLicense, LicenseUsage


@admin.register(InstalledLicense)
class InstalledLicenseAdmin(admin.ModelAdmin):
    list_display = (
        "license_id",
        "customer_name",
        "product_name_short",
        "edition_code",
        "license_type",
        "status",
        "valid_from",
        "valid_until",
        "installed_at",
        "last_validated_at",
        "is_active",
    )
    list_filter = (
        "status",
        "license_type",
        "edition_code",
        "is_active",
    )
    search_fields = (
        "license_id",
        "customer_name",
        "edition_code",
        "edition_name",
    )
    readonly_fields = (
        # identity / display
        "license_id",
        "license_type",
        "customer_name",
        "product_name_short",
        "edition_code",
        "edition_name",

        # raw license data
        "payload",
        "raw_license_json",
        "signature",
        "algorithm",
        "key_id",

        # validity + status
        "valid_from",
        "valid_until",
        "status",
        "status_message",

        # meta / timestamps
        "installed_at",
        "last_validated_at",
        "updated_at",
        # "is_active",
    )

    fieldsets = (
        ("Identity", {
            "fields": (
                "license_id",
                "license_type",
                "customer_name",
                "product_name_short", 
                "edition_code",
                "edition_name",
            )
        }),
        ("Validity", {
            "fields": (
                "valid_from",
                "valid_until",
                "status",
                "status_message",
            )
        }),
        ("Raw Data", {
            "classes": ("collapse",),
            "fields": (
                "payload",
                "raw_license_json",
                "signature",
                "algorithm",
                "key_id",
            )
        }),
        ("Meta", {
            "fields": (
                "installed_at",
                "last_validated_at",
                "updated_at",
                "is_active",
            )
        }),
    )

    def product_name_short(self, obj: InstalledLicense) -> str:
        """
        Convenience display: pull product.name from the payload JSON if present.
        Falls back to '-' if not available.
        """
        try:
            product = obj.payload.get("product") or {}
            return product.get("name") or "-"
        except Exception:
            return "-"
    product_name_short.short_description = "Product"


@admin.register(LicenseUsage)
class LicenseUsageAdmin(admin.ModelAdmin):
    """
    Admin for the current simple LicenseUsage model:

    - id
    - license (FK to InstalledLicense)
    - daily_count
    - monthly_count
    - last_reset_daily
    - last_reset_monthly
    """

    list_display = (
        "id",
        "license",
        "daily_count",
        "monthly_count",
        "last_reset_daily",
        "last_reset_monthly",
    )
    list_filter = (
        "last_reset_daily",
        "last_reset_monthly",
    )
    search_fields = (
        "license__license_id",
        "license__customer_name",
    )
    readonly_fields = (
        "license",
        "daily_count",
        "monthly_count",
        "last_reset_daily",
        "last_reset_monthly",
    )
