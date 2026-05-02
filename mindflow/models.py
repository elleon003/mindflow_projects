from django.conf import settings
from django.db import models


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


class Project(models.Model):
    """Minimal project stub for AI approve step."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
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


class Task(models.Model):
    """Minimal task linked to a project and optional inbox origin."""

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
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True, default="")
    source_inbox_item = models.ForeignKey(
        "InboxItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tasks",
    )
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
