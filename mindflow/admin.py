from django.contrib import admin

from unfold.admin import ModelAdmin

from mindflow import models as mf


@admin.register(mf.InboxItem)
class InboxItemAdmin(ModelAdmin):
    list_display = ("id", "user", "status", "created_at", "body_preview")
    list_filter = ("status",)
    search_fields = ("body",)

    @admin.display(description="Body")
    def body_preview(self, obj: mf.InboxItem) -> str:
        text = str(obj.body or "")
        return text[:100]


@admin.register(mf.AiOrganizeSession)
class AiOrganizeSessionAdmin(ModelAdmin):
    list_display = ("id", "user", "state", "created_at", "updated_at")
    list_filter = ("state",)
    filter_horizontal = ("inbox_items",)


@admin.register(mf.AiOrganizeUsage)
class AiOrganizeUsageAdmin(ModelAdmin):
    list_display = ("id", "user", "session", "completed_at")


@admin.register(mf.Area)
class AreaAdmin(ModelAdmin):
    list_display = ("id", "name", "user")
    search_fields = ("name",)
    list_filter = ("user",)


@admin.register(mf.Tag)
class TagAdmin(ModelAdmin):
    list_display = ("id", "name", "user")
    search_fields = ("name",)
    list_filter = ("user",)


@admin.register(mf.Milestone)
class MilestoneAdmin(ModelAdmin):
    list_display = ("id", "title", "project", "sort_order", "target_date")
    list_filter = ("project",)
    search_fields = ("title",)
    autocomplete_fields = ("project",)


@admin.register(mf.Project)
class ProjectAdmin(ModelAdmin):
    list_display = ("id", "name", "user", "area", "client_name")
    list_filter = ("user", "area")
    search_fields = ("name", "client_name")
    autocomplete_fields = ("area",)


@admin.register(mf.Task)
class TaskAdmin(ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "project",
        "milestone",
        "energy_level",
        "due_date",
        "scheduled_date",
        "is_blocked",
        "is_waiting",
        "created_at",
    )
    list_filter = (
        "energy_level",
        "brain_space_level",
        "is_blocked",
        "is_waiting",
        "user",
        "project",
    )
    search_fields = ("title", "body", "first_tiny_step")
    autocomplete_fields = ("user", "project", "milestone", "source_inbox_item")
    filter_horizontal = ("tags",)


@admin.register(mf.Routine)
class RoutineAdmin(ModelAdmin):
    list_display = ("id", "title", "user", "is_active", "created_at")
    list_filter = ("is_active", "user")
    search_fields = ("title", "body")


@admin.register(mf.TimeBlock)
class TimeBlockAdmin(ModelAdmin):
    list_display = ("id", "title", "user", "start_at", "end_at", "task", "project")
    list_filter = ("user",)
    search_fields = ("title",)
    autocomplete_fields = ("user", "task", "project")


@admin.register(mf.CapacitySignal)
class CapacitySignalAdmin(ModelAdmin):
    list_display = ("id", "user", "recorded_at", "energy_level", "brain_space_level")
    list_filter = ("user", "energy_level", "brain_space_level")
