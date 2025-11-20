# licensing/services/usage_limits.py 
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from django.db import transaction
from django.utils import timezone

from licensing.models import InstalledLicense, LicenseUsage
from licensing.services.validation import LicenseGrants


@dataclass
class UsageCheckResult:
    """
    Result of a usage-limit check and (optional) increment.
    """
    allowed: bool
    reason: Optional[str]

    daily_used: int
    daily_limit: Optional[int]

    monthly_used: int
    monthly_limit: Optional[int]


def _reset_counters_if_needed(usage: LicenseUsage, today: date) -> None:
    """
    Reset daily/monthly counters if we've crossed day/month boundaries.

    - Daily boundary: if last_reset_daily != today
    - Monthly boundary: if last_reset_monthly is None or month/year differ
    """
    # Daily reset
    if usage.last_reset_daily != today:
        usage.daily_count = 0
        usage.last_reset_daily = today

    # Monthly reset (check year + month)
    if (
        usage.last_reset_monthly is None
        or usage.last_reset_monthly.year != today.year
        or usage.last_reset_monthly.month != today.month
    ):
        usage.monthly_count = 0
        # Normalize to first of month for clarity
        usage.last_reset_monthly = date(today.year, today.month, 1)


@transaction.atomic
def check_and_increment_usage(
    *,
    installed_license: InstalledLicense,
    grants: LicenseGrants,
    action_key: str,
) -> UsageCheckResult:
    """
    Check usage limits for a specific action and, if allowed, increment counters.

    - Reads per-action limits from grants.usage_limits[action_key]
      (expected keys: max_per_day, max_per_month).
    - Uses a single LicenseUsage row per InstalledLicense.
    - Resets daily/monthly counts when boundaries are crossed.
    - If performing this action would exceed a limit, no counters are changed.

    Returns:
        UsageCheckResult with allowed flag, reason, and current usage snapshot.
    """
    now = timezone.now()
    today = now.date()

    usage_limits: Dict[str, Any] = grants.usage_limits or {}
    action_limits: Dict[str, Any] = usage_limits.get(action_key) or {}

    # Extract numeric limits (if present)
    max_per_day = action_limits.get("max_per_day")
    max_per_month = action_limits.get("max_per_month")

    # Get or create usage row for this license, locked for update
    usage, _created = (
        LicenseUsage.objects.select_for_update()
        .get_or_create(
            license=installed_license,
            defaults={
                "daily_count": 0,
                "monthly_count": 0,
                "last_reset_daily": today,
                "last_reset_monthly": date(today.year, today.month, 1),
            },
        )
    )

    # Reset counters if we've crossed day/month boundaries
    _reset_counters_if_needed(usage, today)

    # Proposed new counts if we allow this action
    new_daily = usage.daily_count + 1
    new_monthly = usage.monthly_count + 1

    # Decide if this exceeds any configured limits
    reason = None
    allowed = True

    # Guard: make sure limits are integers if present
    if max_per_day is not None and not isinstance(max_per_day, int):
        # Misconfigured license; treat as error and deny.
        allowed = False
        reason = (
            f"Invalid 'max_per_day' type for action '{action_key}': "
            f"expected int, got {type(max_per_day).__name__}."
        )
    elif max_per_month is not None and not isinstance(max_per_month, int):
        allowed = False
        reason = (
            f"Invalid 'max_per_month' type for action '{action_key}': "
            f"expected int, got {type(max_per_month).__name__}."
        )
    else:
        # Actual limit checks
        if isinstance(max_per_day, int) and max_per_day >= 0 and new_daily > max_per_day:
            allowed = False
            reason = (
                f"Daily usage limit exceeded for '{action_key}': "
                f"{new_daily}/{max_per_day}."
            )
        elif (
            isinstance(max_per_month, int)
            and max_per_month >= 0
            and new_monthly > max_per_month
        ):
            allowed = False
            reason = (
                f"Monthly usage limit exceeded for '{action_key}': "
                f"{new_monthly}/{max_per_month}."
            )

    if allowed:
        # Persist new counts
        usage.daily_count = new_daily
        usage.monthly_count = new_monthly
        usage.save(
            update_fields=[
                "daily_count",
                "monthly_count",
                "last_reset_daily",
                "last_reset_monthly",
            ]
        )
        daily_used = new_daily
        monthly_used = new_monthly
    else:
        # Do not change the stored counts; we report existing state
        daily_used = usage.daily_count
        monthly_used = usage.monthly_count

    return UsageCheckResult(
        allowed=allowed,
        reason=reason,
        daily_used=daily_used,
        daily_limit=max_per_day if isinstance(max_per_day, int) else None,
        monthly_used=monthly_used,
        monthly_limit=max_per_month if isinstance(max_per_month, int) else None,
    )

