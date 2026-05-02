"""Tests for organize rate limits."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from mindflow.exceptions import BatchTooLarge, RateLimitExceeded
from mindflow.models import (
    AiOrganizeSession,
    AiOrganizeSessionState,
    AiOrganizeUsage,
)
from mindflow.rate_limits import (
    MAX_BATCH_ITEMS,
    assert_batch_size_ok,
    assert_can_complete_organize,
    count_completions_in_rolling_hour,
    count_completions_today,
)
from mindflow.rate_limits import (
    start_end_local_calendar_day as day_bounds,
)

User = get_user_model()


class RateLimitTests(TestCase):
    def test_batch_size_ok(self) -> None:
        assert_batch_size_ok(8)
        with self.assertRaises(BatchTooLarge):
            assert_batch_size_ok(9)

    def test_max_batch_constant(self) -> None:
        self.assertEqual(MAX_BATCH_ITEMS, 8)

    def test_daily_completion_counts_calendar_day(self) -> None:
        user = User.objects.create_user("rl1", "rl1@example.com", "pw")
        start_utc, _ = day_bounds()
        s = AiOrganizeSession.objects.create(
            user=user, state=AiOrganizeSessionState.COMPLETED
        )
        AiOrganizeUsage.objects.create(
            user=user,
            session=s,
            completed_at=start_utc + timedelta(seconds=10),
        )
        self.assertEqual(count_completions_today(user), 1)

    def test_hourly_rolling_window_counts_three_then_blocks_fourth(self) -> None:
        user = User.objects.create_user("rl2", "rl2@example.com", "pw")
        now = timezone.now()
        for i in range(3):
            s = AiOrganizeSession.objects.create(
                user=user, state=AiOrganizeSessionState.COMPLETED
            )
            AiOrganizeUsage.objects.create(
                user=user,
                session=s,
                completed_at=now - timedelta(minutes=30 - i * 5),
            )
        self.assertEqual(count_completions_in_rolling_hour(user, now=now), 3)
        with self.assertRaises(RateLimitExceeded):
            assert_can_complete_organize(user, now=now)

    def test_daily_limit_four_completions(self) -> None:
        user = User.objects.create_user("rl3", "rl3@example.com", "pw")
        now = timezone.now()
        for i in range(4):
            s = AiOrganizeSession.objects.create(
                user=user, state=AiOrganizeSessionState.COMPLETED
            )
            AiOrganizeUsage.objects.create(
                user=user,
                session=s,
                completed_at=now - timedelta(minutes=i),
            )
        with self.assertRaises(RateLimitExceeded):
            assert_can_complete_organize(user, now=now)
