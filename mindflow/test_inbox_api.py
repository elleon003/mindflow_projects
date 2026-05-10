"""Tests for inbox REST API."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from ninja.testing import TestClient

from mindflow.api import api
from mindflow.models import InboxItem, InboxItemStatus

User = get_user_model()


class InboxApiTests(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api)
        self.user = User.objects.create_user("ibxu", "ibxu@example.com", "pw")
        self.other = User.objects.create_user("other", "other@example.com", "pw")

    def test_list_default_only_in_inbox(self) -> None:
        InboxItem.objects.create(user=self.user, body="a")
        locked = InboxItem.objects.create(user=self.user, body="b")
        locked.status = InboxItemStatus.LOCKED_FOR_AI
        locked.save(update_fields=["status"])
        r = self.client.get("/inbox", user=self.user)
        self.assertEqual(r.status_code, 200)
        assert r.data is not None
        self.assertEqual(len(r.data), 1)
        self.assertEqual(r.data[0]["body"], "a")

    def test_list_include_locked(self) -> None:
        InboxItem.objects.create(user=self.user, body="a")
        locked = InboxItem.objects.create(user=self.user, body="b")
        locked.status = InboxItemStatus.LOCKED_FOR_AI
        locked.save(update_fields=["status"])
        r = self.client.get("/inbox?include_locked=true", user=self.user)
        self.assertEqual(r.status_code, 200)
        assert r.data is not None
        self.assertEqual(len(r.data), 2)

    def test_create(self) -> None:
        r = self.client.post(
            "/inbox",
            json={"body": "Remember dentist"},
            user=self.user,
        )
        self.assertEqual(r.status_code, 200)
        assert r.data is not None
        self.assertEqual(r.data["body"], "Remember dentist")
        self.assertEqual(r.data["status"], InboxItemStatus.IN_INBOX)

    def test_create_requires_nonempty_after_strip(self) -> None:
        r = self.client.post("/inbox", json={"body": "   "}, user=self.user)
        self.assertEqual(r.status_code, 400)

    def test_discard(self) -> None:
        item = InboxItem.objects.create(user=self.user, body="drop")
        r = self.client.patch(
            f"/inbox/{item.pk}",
            json={"status": InboxItemStatus.DISCARDED},
            user=self.user,
        )
        self.assertEqual(r.status_code, 200)
        assert r.data is not None
        self.assertEqual(r.data["status"], InboxItemStatus.DISCARDED)
        item.refresh_from_db()
        self.assertEqual(item.status, InboxItemStatus.DISCARDED)

    def test_discard_locked_conflict(self) -> None:
        item = InboxItem.objects.create(user=self.user, body="x")
        item.status = InboxItemStatus.LOCKED_FOR_AI
        item.save(update_fields=["status"])
        r = self.client.patch(
            f"/inbox/{item.pk}",
            json={"status": InboxItemStatus.DISCARDED},
            user=self.user,
        )
        self.assertEqual(r.status_code, 409)

    def test_patch_other_user_404(self) -> None:
        item = InboxItem.objects.create(user=self.other, body="nope")
        r = self.client.patch(
            f"/inbox/{item.pk}",
            json={"status": InboxItemStatus.DISCARDED},
            user=self.user,
        )
        self.assertEqual(r.status_code, 404)

    def test_list_scoped_to_user(self) -> None:
        InboxItem.objects.create(user=self.user, body="mine")
        InboxItem.objects.create(user=self.other, body="theirs")
        r = self.client.get("/inbox", user=self.user)
        self.assertEqual(r.status_code, 200)
        assert r.data is not None
        self.assertEqual(len(r.data), 1)
