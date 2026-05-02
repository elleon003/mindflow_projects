"""Integration tests for organize API and service (mocked inference)."""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestClient

from mindflow.api import api
from mindflow.models import (
    AiOrganizeSession,
    AiOrganizeSessionState,
    AiOrganizeUsage,
    InboxItem,
    InboxItemStatus,
    Task,
)
from mindflow.schemas import (
    AnalyzePhaseResponse,
    ClarificationQuestion,
    FinalizePhaseResponse,
    PlanItem,
)

User = get_user_model()


class OrganizeApiTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api)
        self.user = User.objects.create_user("apiu", "apiu@example.com", "pw")

    def test_start_to_approve_quick_task(self) -> None:
        item = InboxItem.objects.create(user=self.user, body="Buy milk")
        plan_item = PlanItem(
            inbox_item_id=item.pk,
            action_type="quick_task",
            task_title="Buy milk",
            rationale="errand",
        )
        with patch("mindflow.inference.analyze_batch") as ab:
            ab.return_value = AnalyzePhaseResponse(
                needs_clarification=False,
                plan_items=[plan_item],
            )
            r = self.client.post(
                "/organize/start",
                json={"inbox_item_ids": [item.pk]},
                user=self.user,
            )
        self.assertEqual(r.status_code, 200)
        data = r.data
        self.assertEqual(data["state"], AiOrganizeSessionState.AWAITING_REVIEW)
        sid = data["session_id"]

        r2 = self.client.post(f"/organize/{sid}/approve", user=self.user)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["state"], AiOrganizeSessionState.COMPLETED)
        item.refresh_from_db()
        self.assertEqual(item.status, InboxItemStatus.SORTED)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 1)

        r3 = self.client.post(f"/organize/{sid}/approve", user=self.user)
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 1)

    def test_clarify_then_approve(self) -> None:
        item = InboxItem.objects.create(user=self.user, body="Follow up contract")
        q = ClarificationQuestion(
            question_id="q1",
            inbox_item_id=item.pk,
            prompt="Client or internal?",
            kind="text",
        )
        final_plan = PlanItem(
            inbox_item_id=item.pk,
            action_type="quick_task",
            task_title="Follow up contract",
            rationale="one-off",
        )
        with patch("mindflow.inference.analyze_batch") as ab:
            ab.return_value = AnalyzePhaseResponse(
                needs_clarification=True,
                questions=[q],
                plan_items=[],
            )
            r = self.client.post(
                "/organize/start",
                json={"inbox_item_ids": [item.pk]},
                user=self.user,
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.data["state"], AiOrganizeSessionState.AWAITING_CLARIFICATION
        )
        sid = r.data["session_id"]

        with patch("mindflow.inference.finalize_plan") as fb:
            fb.return_value = FinalizePhaseResponse(plan_items=[final_plan])
            r2 = self.client.post(
                f"/organize/{sid}/clarify",
                json={"answers": {"q1": "internal"}},
                user=self.user,
            )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.data["state"], AiOrganizeSessionState.AWAITING_REVIEW)

        r3 = self.client.post(f"/organize/{sid}/approve", user=self.user)
        self.assertEqual(r3.status_code, 200)

    def test_cancel_unlocks_inbox(self) -> None:
        item = InboxItem.objects.create(user=self.user, body="x")
        plan_item = PlanItem(
            inbox_item_id=item.pk,
            action_type="quick_task",
            task_title="x",
            rationale="r",
        )
        with patch("mindflow.inference.analyze_batch") as ab:
            ab.return_value = AnalyzePhaseResponse(
                needs_clarification=False,
                plan_items=[plan_item],
            )
            r = self.client.post("/organize/start", json={}, user=self.user)
        sid = r.data["session_id"]
        item.refresh_from_db()
        self.assertEqual(item.status, InboxItemStatus.LOCKED_FOR_AI)

        r2 = self.client.post(f"/organize/{sid}/cancel", user=self.user)
        self.assertEqual(r2.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.status, InboxItemStatus.IN_INBOX)

    def test_batch_too_large_returns_400(self) -> None:
        ids = []
        for i in range(9):
            item = InboxItem.objects.create(user=self.user, body=f"n{i}")
            ids.append(item.pk)
        r = self.client.post(
            "/organize/start",
            json={"inbox_item_ids": ids},
            user=self.user,
        )
        self.assertEqual(r.status_code, 400)

    def test_rate_limit_returns_429(self) -> None:
        now = timezone.now()
        for i in range(3):
            s = AiOrganizeSession.objects.create(
                user=self.user,
                state=AiOrganizeSessionState.COMPLETED,
            )
            AiOrganizeUsage.objects.create(
                user=self.user,
                session=s,
                completed_at=now - timedelta(minutes=i),
            )
        item = InboxItem.objects.create(user=self.user, body="a")
        plan_item = PlanItem(
            inbox_item_id=item.pk,
            action_type="quick_task",
            task_title="a",
            rationale="r",
        )
        with patch("mindflow.inference.analyze_batch") as ab:
            ab.return_value = AnalyzePhaseResponse(
                needs_clarification=False,
                plan_items=[plan_item],
            )
            r = self.client.post(
                "/organize/start",
                json={"inbox_item_ids": [item.pk]},
                user=self.user,
            )
        self.assertEqual(r.status_code, 429)
