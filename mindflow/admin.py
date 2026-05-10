from django.contrib import admin

from mindflow import models as mf


@admin.register(mf.Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "sort_order", "created_at")
    list_filter = ("user",)
    search_fields = ("name",)


@admin.register(mf.InboxItem)
class InboxItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at", "body_preview")
    list_filter = ("status",)
    search_fields = ("body",)

    @admin.display(description="Body")
    def body_preview(self, obj: mf.InboxItem) -> str:
        return (obj.body or "")[:100]


@admin.register(mf.AiOrganizeSession)
class AiOrganizeSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "state", "created_at", "updated_at")
    list_filter = ("state",)
    filter_horizontal = ("inbox_items",)


@admin.register(mf.AiOrganizeUsage)
class AiOrganizeUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session", "completed_at")


@admin.register(mf.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "area", "user", "client_name")
    list_filter = ("area",)


@admin.register(mf.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "project", "created_at")
