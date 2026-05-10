"""Authenticated product views (Capture flow)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from mindflow.exceptions import (
    BatchTooLarge,
    NoInboxItems,
    OrganizeError,
    RateLimitExceeded,
)
from mindflow.models import AiOrganizeSession, InboxItem, InboxItemStatus
from mindflow.services.organize import (
    approve_organize,
    cancel_organize,
    start_organize_session,
    submit_clarifications,
)


def _organize_start_redirect_errors(request, exc: Exception) -> None:
    if isinstance(exc, RateLimitExceeded):
        messages.error(request, str(exc))
    elif isinstance(exc, BatchTooLarge):
        messages.error(request, str(exc))
    elif isinstance(exc, NoInboxItems):
        messages.error(request, str(exc))
    elif isinstance(exc, OrganizeError):
        messages.error(request, str(exc))
    else:
        messages.error(request, "Could not start organize session.")


@login_required
@require_http_methods(["GET", "POST"])
def capture(request):
    if request.method == "POST":
        body = (request.POST.get("body") or "").strip()
        if body:
            InboxItem.objects.create(user=request.user, body=body)
            messages.success(request, "Added to inbox.")
        else:
            messages.error(request, "Enter something to capture.")
        return redirect("capture")

    inbox_items = InboxItem.objects.filter(
        user=request.user,
        status__in=[
            InboxItemStatus.IN_INBOX,
            InboxItemStatus.LOCKED_FOR_AI,
        ],
    ).order_by("created_at")
    return render(
        request,
        "mindflow/capture.html",
        {"inbox_items": inbox_items},
    )


@login_required
@require_http_methods(["POST"])
def capture_organize_start(request):
    action = request.POST.get("action")
    raw_ids = request.POST.getlist("item_ids")

    try:
        if action == "all":
            session = start_organize_session(request.user, None)
        elif action == "selected":
            if not raw_ids:
                messages.error(request, "Select at least one inbox item.")
                return redirect("capture")
            ids = [int(x) for x in raw_ids]
            session = start_organize_session(request.user, ids)
        else:
            messages.error(request, "Unknown action.")
            return redirect("capture")
    except Exception as exc:
        _organize_start_redirect_errors(request, exc)
        return redirect("capture")

    return redirect("capture_organize_session", session_id=session.pk)


@login_required
@require_http_methods(["POST"])
def capture_discard_item(request, item_id: int):
    item = get_object_or_404(InboxItem, pk=item_id, user=request.user)
    if item.status != InboxItemStatus.IN_INBOX:
        messages.error(request, "Only inbox items that are not being organized can be discarded.")
    else:
        item.status = InboxItemStatus.DISCARDED
        item.save(update_fields=["status", "updated_at"])
        messages.success(request, "Item discarded.")
    return redirect("capture")


@login_required
@require_http_methods(["GET", "POST"])
def capture_organize_session(request, session_id: int):
    session = get_object_or_404(
        AiOrganizeSession.objects.filter(user=request.user),
        pk=session_id,
    )

    if request.method == "POST":
        act = request.POST.get("session_action")
        try:
            if act == "clarify":
                qrows = (session.clarifications or {}).get("questions") or []
                answers: dict[str, str] = {}
                for q in qrows:
                    qid = str(q["question_id"])
                    answers[qid] = (request.POST.get(f"answer_{qid}") or "").strip()
                submit_clarifications(request.user, session.pk, answers)
                messages.success(request, "Plan updated. Review below.")
            elif act == "approve":
                approve_organize(request.user, session.pk)
                messages.success(request, "Plan approved; tasks and projects updated.")
                return redirect("capture")
            elif act == "cancel":
                cancel_organize(request.user, session.pk)
                messages.info(request, "Organize session cancelled.")
                return redirect("capture")
            else:
                messages.error(request, "Unknown action.")
        except OrganizeError as exc:
            messages.error(request, str(exc))

        return redirect("capture_organize_session", session_id=session_id)

    questions = (session.clarifications or {}).get("questions") or []
    plan_items = (session.proposed_plan or {}).get("plan_items") or []
    return render(
        request,
        "mindflow/organize_session.html",
        {
            "session": session,
            "questions": questions,
            "plan_items": plan_items,
        },
    )
