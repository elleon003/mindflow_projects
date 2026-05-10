from typing import Any, cast

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class InboxItemStatus(models.TextChoices):
    IN_INBOX = "in_inbox", "In inbox"  # pyright: ignore[reportAssignmentType]
    LOCKED_FOR_AI = "locked_for_ai", "Locked for AI"  # pyright: ignore[reportAssignmentType]
    SORTED = "sorted", "Sorted"  # pyright: ignore[reportAssignmentType]
    DISCARDED = "discarded", "Discarded"  # pyright: ignore[reportAssignmentType]


class AiOrganizeSessionState(models.TextChoices):
    ANALYZING = "analyzing", "Analyzing"  # pyright: ignore[reportAssignmentType]
    AWAITING_CLARIFICATION = "awaiting_clarification", "Awaiting clarification"  # pyright: ignore[reportAssignmentType]
    AWAITING_REVIEW = "awaiting_review", "Awaiting review"  # pyright: ignore[reportAssignmentType]
    COMPLETED = "completed", "Completed"  # pyright: ignore[reportAssignmentType]
    CANCELLED = "cancelled", "Cancelled"  # pyright: ignore[reportAssignmentType]
    FAILED = "failed", "Failed"  # pyright: ignore[reportAssignmentType]


class EnergyLevel(models.TextChoices):
    LOW = "low", "Low"  # pyright: ignore[reportAssignmentType]
    MEDIUM = "medium", "Medium"  # pyright: ignore[reportAssignmentType]
    HIGH = "high", "High"  # pyright: ignore[reportAssignmentType]


class BrainSpaceLevel(models.TextChoices):
    """Kind of cognitive mode the task needs (not intensity)."""

    ADMIN = "admin", "Admin"  # pyright: ignore[reportAssignmentType]
    CREATIVE = "creative", "Creative"  # pyright: ignore[reportAssignmentType]
    SOCIAL = "social", "Social"  # pyright: ignore[reportAssignmentType]
    QUICK_FIX = "quick-fix", "Quick fix"  # pyright: ignore[reportAssignmentType]
    HYPERFOCUS = "hyperfocus", "Hyperfocus"  # pyright: ignore[reportAssignmentType]


class Area(models.Model):
    """User-scoped grouping for projects (life/work themes)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="areas",
    )
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="mindflow_area_user_name_uniq",
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)


class Project(models.Model):
    """Project container; optional link to an area."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    name = models.CharField(max_length=255)
    client_name = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="mindflow_project_user_name_uniq",
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)


class Milestone(models.Model):
    """Ordered checkpoint within a project."""

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    title = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=cast(Any, 0))
    target_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["project", "sort_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "sort_order"],
                name="mindflow_milestone_project_order_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "sort_order"]),
        ]

    def __str__(self) -> str:
        return str(self.title)[:80]


class Tag(models.Model):
    """User-scoped label for tasks (context/mode)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="mindflow_tag_user_name_uniq",
            ),
        ]

    def __str__(self) -> str:
        return str(self.name)


class Task(models.Model):
    """Task linked to a project and optional inbox origin."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True, default="")
    source_inbox_item = models.ForeignKey(
        "InboxItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
    )
    energy_level = models.CharField(
        max_length=16,
        choices=EnergyLevel.choices,
        default=EnergyLevel.MEDIUM,
    )
    brain_space_level = models.CharField(
        max_length=16,
        choices=BrainSpaceLevel.choices,
        default=BrainSpaceLevel.QUICK_FIX,
    )
    duration_estimate_minutes = models.PositiveIntegerField(null=True, blank=True)
    first_tiny_step = models.CharField(max_length=500, blank=True, default="")
    due_date = models.DateField(null=True, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    is_blocked = models.BooleanField(default=cast(Any, False))
    is_waiting = models.BooleanField(default=cast(Any, False))
    tags = models.ManyToManyField(Tag, blank=True, related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.title)[:80]


class InboxItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inbox_items",
    )
    body = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=InboxItemStatus.choices,
        default=InboxItemStatus.IN_INBOX,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return str(self.body)[:80]


# Recurrence payload shape (documented for Phase 3+ scheduling):
# - frequency: "daily" | "weekly" | "monthly"
# - interval: positive integer, default 1
# - by_weekday: optional list of weekday ints 0=Monday .. 6=Sunday (ISO-style)


class Routine(models.Model):
    """Recurring responsibility alongside projects."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="routines",
    )
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True, default="")
    recurrence = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=cast(Any, True))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.title)[:80]


class TimeBlock(models.Model):
    """Scheduled block of time; optional link to task or project."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="time_blocks",
    )
    title = models.CharField(max_length=500)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_blocks",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_blocks",
    )

    class Meta:
        ordering = ["start_at"]
        indexes = [
            models.Index(fields=["user", "start_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_at__gt=F("start_at")),
                name="mindflow_timeblock_end_after_start",
            ),
        ]

    def __str__(self) -> str:
        return str(self.title)[:80]


class CapacitySignal(models.Model):
    """Lightweight check-in for perceived capacity (weekly reset / analytics)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="capacity_signals",
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    energy_level = models.CharField(
        max_length=16,
        choices=EnergyLevel.choices,
        null=True,
        blank=True,
    )
    brain_space_level = models.CharField(
        max_length=16,
        choices=BrainSpaceLevel.choices,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["user", "recorded_at"]),
        ]

    def __str__(self) -> str:
        return f"CapacitySignal({self.pk}, user={self.user_id})"


class AiOrganizeSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_organize_sessions",
    )
    state = models.CharField(
        max_length=32,
        choices=AiOrganizeSessionState.choices,
        default=AiOrganizeSessionState.ANALYZING,
        db_index=True,
    )
    inbox_items = models.ManyToManyField(
        InboxItem,
        related_name="organize_sessions",
        blank=True,
    )
    context_snapshot = models.JSONField(default=dict, blank=True)
    clarifications = models.JSONField(default=dict, blank=True)
    proposed_plan = models.JSONField(default=dict, blank=True)
    error_detail = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "state"]),
        ]

    def __str__(self) -> str:
        return f"AiOrganizeSession({self.pk}, {self.state})"


class AiOrganizeUsage(models.Model):
    """One row per successfully completed organize session (for rate limits)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_organize_usage",
    )
    session = models.OneToOneField(
        AiOrganizeSession,
        on_delete=models.CASCADE,
        related_name="usage_record",
    )
    completed_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["user", "completed_at"]),
        ]
