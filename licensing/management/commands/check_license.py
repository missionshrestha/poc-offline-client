# licensing/management/commands/check_license.py
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from licensing.services.validation import evaluate_current_license
from licensing.models import InstalledLicense


class Command(BaseCommand):
    help = "Inspect the currently installed license and print its status/grants."

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output license status as JSON instead of human-readable text.",
        )

    def handle(self, *args, **options):
        as_json = options["json"]

        active, grants = evaluate_current_license()

        if as_json:
            self._print_json(active, grants)
        else:
            self._print_human(active, grants)

    # ---------------------------------------------------------------------
    # JSON output
    # ---------------------------------------------------------------------
    def _print_json(self, active: InstalledLicense | None, grants):
        installed_at = active.installed_at.isoformat() if active and active.installed_at else None
        last_validated_at = (
            active.last_validated_at.isoformat() if active and active.last_validated_at else None
        )

        payload = {
            "status": grants.status,
            "status_message": grants.status_message,
            "license_id": grants.license_id,
            "license_type": grants.license_type,
            "customer_name": grants.customer_name,
            "product_code": grants.product_code,
            "product_name": grants.product_name,
            "edition_code": grants.edition_code,
            "edition_name": grants.edition_name,
            "valid_from": grants.valid_from.isoformat() if grants.valid_from else None,
            "valid_until": grants.valid_until.isoformat() if grants.valid_until else None,
            "features": grants.features,
            "usage_limits": grants.usage_limits,
            "deployment": grants.deployment,
            "warnings": grants.warnings,
            "installed_at": installed_at,
            "last_validated_at": last_validated_at,
            "checked_at": timezone.now().isoformat(),
        }

        self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))

    # ---------------------------------------------------------------------
    # Human-readable output
    # ---------------------------------------------------------------------
    def _print_human(self, active: InstalledLicense | None, grants):
        now = timezone.now()

        self.stdout.write("")
        self.stdout.write("=== License Check ===")
        self.stdout.write(f"Checked at: {now.isoformat()}")
        self.stdout.write("")

        self.stdout.write(f"Status:        {grants.status}")
        self.stdout.write(f"Message:       {grants.status_message}")

        if active:
            self.stdout.write(f"Installed at:  {active.installed_at.isoformat()}")
            if active.last_validated_at:
                self.stdout.write(f"Last validated:{active.last_validated_at.isoformat()}")
        else:
            self.stdout.write("Installed at:  (no active license)")

        self.stdout.write("")

        # Identity
        self.stdout.write("--- Identity ---")
        self.stdout.write(f"License ID:    {grants.license_id or '-'}")
        self.stdout.write(f"License type:  {grants.license_type or '-'}")
        self.stdout.write(f"Customer:      {grants.customer_name or '-'}")
        self.stdout.write(f"Product:       {grants.product_name or '-'} "
                          f"({grants.product_code or '-'})")
        self.stdout.write(f"Edition:       {grants.edition_name or '-'} "
                          f"({grants.edition_code or '-'})")

        self.stdout.write("")

        # Validity
        self.stdout.write("--- Validity ---")
        vf = grants.valid_from.isoformat() if grants.valid_from else "-"
        vu = grants.valid_until.isoformat() if grants.valid_until else "-"
        self.stdout.write(f"Valid from:    {vf}")
        self.stdout.write(f"Valid until:   {vu}")

        if grants.valid_from and grants.valid_until and grants.status == "valid":
            remaining = grants.valid_until - now
            self.stdout.write(f"Time remaining:{remaining}")

        self.stdout.write("")

        # Warnings
        self.stdout.write("--- Warnings ---")
        if grants.warnings:
            for w in grants.warnings:
                self.stdout.write(f"- {w}")
        else:
            self.stdout.write("(none)")

        self.stdout.write("")

        # Features & limits (summarized)
        self.stdout.write("--- Features ---")
        if grants.features:
            for key, value in grants.features.items():
                self.stdout.write(f"- {key}: {value}")
        else:
            self.stdout.write("(none)")

        self.stdout.write("")

        self.stdout.write("--- Usage limits ---")
        if grants.usage_limits:
            for key, value in grants.usage_limits.items():
                self.stdout.write(f"- {key}: {value}")
        else:
            self.stdout.write("(none)")

        self.stdout.write("")

