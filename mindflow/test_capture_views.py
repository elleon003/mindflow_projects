"""Smoke tests for Capture HTML views."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from mindflow.models import AiOrganizeSession, InboxItem, InboxItemStatus
from mindflow.schemas import AnalyzePhaseResponse, PlanItem

User = get_user_model()


@override_settings(
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    },
)
class CaptureViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("cvu", "cvu@example.com", "pw")

    def test_capture_requires_login(self) -> None:
        r = self.client.get(reverse("capture"))
        self.assertEqual(r.status_code, 302)

    def test_capture_get_ok(self) -> None:
        self.client.login(username="cvu", password="pw")
        r = self.client.get(reverse("capture"))
        self.assertEqual(r.status_code, 200)

    def test_capture_post_create(self) -> None:
        self.client.login(username="cvu", password="pw")
        r = self.client.post(reverse("capture"), {"body": "Buy beans"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(InboxItem.objects.filter(user=self.user).count(), 1)

    def test_discard_item(self) -> None:
        self.client.login(username="cvu", password="pw")
        item = InboxItem.objects.create(user=self.user, body="gone")
        r = self.client.post(reverse("capture_discard_item", args=[item.pk]))
        self.assertEqual(r.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, InboxItemStatus.DISCARDED)

    def test_organize_session_page_after_start(self) -> None:
        item = InboxItem.objects.create(user=self.user, body="Task")
        plan_item = PlanItem(
            inbox_item_id=item.pk,
            action_type="quick_task",
            task_title="Task",
            rationale="r",
        )
        self.client.login(username="cvu", password="pw")
        with patch("mindflow.inference.analyze_batch") as ab:
            ab.return_value = AnalyzePhaseResponse(
                needs_clarification=False,
                plan_items=[plan_item],
            )
            r = self.client.post(
                reverse("capture_organize_start"),
                {"action": "selected", "item_ids": [str(item.pk)]},
            )
        self.assertEqual(r.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, InboxItemStatus.LOCKED_FOR_AI)
        session = AiOrganizeSession.objects.filter(user=self.user).latest("created_at")
        r2 = self.client.get(
            reverse("capture_organize_session", args=[session.pk]),
        )
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, "Proposed plan")

        r3 = self.client.post(
            reverse("capture_organize_session", args=[session.pk]),
            {"session_action": "approve"},
        )
        self.assertEqual(r3.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.status, InboxItemStatus.SORTED)
