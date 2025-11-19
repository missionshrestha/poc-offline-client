from django.contrib import admin
from .models import InstalledLicense, LicenseUsage


@admin.register(InstalledLicense)
class InstalledLicenseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "key_id",
        "status",
        "valid_from",
        "valid_until",
        "installed_at",
        "last_validated_at",
        "is_active",
    )
    list_filter = ("status", "is_active")
    search_fields = ("key_id", "status")


@admin.register(LicenseUsage)
class LicenseUsageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "license",
        "daily_count",
        "monthly_count",
        "last_reset_daily",
        "last_reset_monthly",
    )
