"""Tests for Phase 1 domain models (constraints, relationships)."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from mindflow.models import (
    Area,
    CapacitySignal,
    Milestone,
    Project,
    Routine,
    Tag,
    Task,
    TimeBlock,
)

User = get_user_model()


class DomainModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("dom", "dom@example.com", "pw")

    def test_full_graph_create_with_tags_and_milestone(self) -> None:
        area = Area.objects.create(user=self.user, name="Work")
        project = Project.objects.create(
            user=self.user,
            area=area,
            name="Client A",
            client_name="Acme",
        )
        milestone = Milestone.objects.create(
            project=project,
            title="Kickoff",
            sort_order=0,
        )
        tag_email = Tag.objects.create(user=self.user, name="email")
        tag_deep = Tag.objects.create(user=self.user, name="deep_work")

        task = Task.objects.create(
            user=self.user,
            project=project,
            milestone=milestone,
            title="Send proposal",
            duration_estimate_minutes=25,
            first_tiny_step="Open draft",
        )
        task.tags.add(tag_email, tag_deep)

        self.assertEqual(project.area_id, area.pk)
        self.assertEqual(task.milestone_id, milestone.pk)
        self.assertEqual(set(task.tags.values_list("name", flat=True)), {"email", "deep_work"})

    def test_area_unique_per_user(self) -> None:
        Area.objects.create(user=self.user, name="Personal")
        with self.assertRaises(IntegrityError):
            Area.objects.create(user=self.user, name="Personal")

    def test_tag_unique_per_user(self) -> None:
        Tag.objects.create(user=self.user, name="urgent")
        with self.assertRaises(IntegrityError):
            Tag.objects.create(user=self.user, name="urgent")

    def test_milestone_sort_order_unique_per_project(self) -> None:
        project = Project.objects.create(user=self.user, name="P1")
        Milestone.objects.create(project=project, title="M1", sort_order=0)
        with self.assertRaises(IntegrityError):
            Milestone.objects.create(project=project, title="M2", sort_order=0)

    def test_timeblock_rejects_equal_start_end(self) -> None:
        now = timezone.now()
        with self.assertRaises(IntegrityError):
            TimeBlock.objects.create(
                user=self.user,
                title="Bad",
                start_at=now,
                end_at=now,
            )

    def test_timeblock_rejects_end_before_start(self) -> None:
        now = timezone.now()
        with self.assertRaises(IntegrityError):
            TimeBlock.objects.create(
                user=self.user,
                title="Bad2",
                start_at=now,
                end_at=now - timezone.timedelta(minutes=5),
            )

    def test_timeblock_accepts_valid_window(self) -> None:
        now = timezone.now()
        tb = TimeBlock.objects.create(
            user=self.user,
            title="Focus",
            start_at=now,
            end_at=now + timezone.timedelta(hours=1),
        )
        self.assertIsNotNone(tb.pk)

    def test_user_delete_cascades_owned_models(self) -> None:
        Area.objects.create(user=self.user, name="A")
        Project.objects.create(user=self.user, name="P")
        Routine.objects.create(user=self.user, title="Daily standup")
        CapacitySignal.objects.create(user=self.user)

        uid = self.user.pk
        User.objects.filter(pk=uid).delete()

        self.assertEqual(Area.objects.filter(user_id=uid).count(), 0)
        self.assertEqual(Project.objects.filter(user_id=uid).count(), 0)
        self.assertEqual(Routine.objects.filter(user_id=uid).count(), 0)
        self.assertEqual(CapacitySignal.objects.filter(user_id=uid).count(), 0)
