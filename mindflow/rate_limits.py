"""Rate limits for AI organize: batch size, rolling hour, calendar day."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from mindflow.exceptions import BatchTooLarge, RateLimitExceeded
from mindflow.models import AiOrganizeUsage

MAX_BATCH_ITEMS = 8
MAX_COMPLETIONS_PER_HOUR = 3
MAX_COMPLETIONS_PER_DAY = 4


@dataclass(frozen=True)
class RateLimitStatus:
    hour_count: int
    day_count: int
    can_complete: bool

    @property
    def hour_remaining(self) -> int:
        return max(0, MAX_COMPLETIONS_PER_HOUR - self.hour_count)

    @property
    def day_remaining(self) -> int:
        return max(0, MAX_COMPLETIONS_PER_DAY - self.day_count)


def _user_tz() -> ZoneInfo:
    return ZoneInfo(settings.TIME_ZONE)


def start_end_local_calendar_day(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return [start, end) in UTC for the caller's current calendar day in TIME_ZONE."""
    if now is None:
        now = timezone.now()
    tz = _user_tz()
    local = now.astimezone(tz)
    start_local = local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    return (start_local.astimezone(UTC), end_local.astimezone(UTC))


def count_completions_in_rolling_hour(user, now: datetime | None = None) -> int:
    if now is None:
        now = timezone.now()
    since = now - timedelta(hours=1)
    return AiOrganizeUsage.objects.filter(user=user, completed_at__gte=since).count()


def count_completions_today(user, now: datetime | None = None) -> int:
    start_utc, end_utc = start_end_local_calendar_day(now)
    return AiOrganizeUsage.objects.filter(
        user=user,
        completed_at__gte=start_utc,
        completed_at__lt=end_utc,
    ).count()


def get_rate_limit_status(user, now: datetime | None = None) -> RateLimitStatus:
    h = count_completions_in_rolling_hour(user, now)
    d = count_completions_today(user, now)
    return RateLimitStatus(
        hour_count=h,
        day_count=d,
        can_complete=h < MAX_COMPLETIONS_PER_HOUR and d < MAX_COMPLETIONS_PER_DAY,
    )


def assert_can_complete_organize(user, now: datetime | None = None) -> None:
    """
    Enforce limits on successful completes (rolling hour + local calendar day).
    Raises RateLimitExceeded if a new completion would exceed caps.
    """
    if now is None:
        now = timezone.now()
    status = get_rate_limit_status(user, now)
    if status.hour_count >= MAX_COMPLETIONS_PER_HOUR:
        # approximate retry: until oldest completion in window drops out
        since = now - timedelta(hours=1)
        oldest = (
            AiOrganizeUsage.objects.filter(user=user, completed_at__gte=since)
            .order_by("completed_at")
            .first()
        )
        retry_after = 60
        if oldest:
            retry_after = max(
                1,
                int((oldest.completed_at + timedelta(hours=1) - now).total_seconds()),
            )
        raise RateLimitExceeded(
            "Organize limit reached (3 completed sorts per rolling hour).",
            retry_after_seconds=retry_after,
        )
    if status.day_count >= MAX_COMPLETIONS_PER_DAY:
        _, end_utc = start_end_local_calendar_day(now)
        retry_after = max(1, int((end_utc - now).total_seconds()))
        raise RateLimitExceeded(
            "Daily organize limit reached (4 completed sorts per calendar day).",
            retry_after_seconds=retry_after,
        )


def assert_batch_size_ok(num_items: int) -> None:
    if num_items > MAX_BATCH_ITEMS:
        raise BatchTooLarge(
            f"At most {MAX_BATCH_ITEMS} inbox items per organize batch; got {num_items}."
        )
