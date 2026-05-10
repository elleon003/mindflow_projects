"""Organize session state machine and plan application."""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from mindflow import inference
from mindflow.exceptions import (
    InferenceError,
    InvalidState,
    NoInboxItems,
    OrganizeError,
)
from mindflow.models import (
    AiOrganizeSession,
    AiOrganizeSessionState,
    AiOrganizeUsage,
    Area,
    InboxItem,
    InboxItemStatus,
    Project,
    Task,
)
from mindflow.rate_limits import (
    MAX_BATCH_ITEMS,
    assert_batch_size_ok,
    assert_can_complete_organize,
)
from mindflow.schemas import FinalizePhaseResponse, PlanItem


def _unlock_session_items(session: AiOrganizeSession) -> None:
    ids = list(session.inbox_items.values_list("pk", flat=True))
    if ids:
        InboxItem.objects.filter(pk__in=ids).update(
            status=InboxItemStatus.IN_INBOX,
            updated_at=timezone.now(),
        )


def _lock_items(items: list[InboxItem]) -> None:
    if not items:
        return
    ids = [i.pk for i in items]
    InboxItem.objects.filter(pk__in=ids).update(
        status=InboxItemStatus.LOCKED_FOR_AI,
        updated_at=timezone.now(),
    )


def _select_items(
    user,
    inbox_item_ids: list[int] | None,
) -> list[InboxItem]:
    qs = InboxItem.objects.filter(user=user, status=InboxItemStatus.IN_INBOX).order_by(
        "created_at"
    )
    if inbox_item_ids is not None:
        assert_batch_size_ok(len(inbox_item_ids))
        items = list(qs.filter(pk__in=inbox_item_ids))
        if len(items) != len(set(inbox_item_ids)):
            raise OrganizeError("One or more inbox items are invalid or not in inbox.")
        missing = set(inbox_item_ids) - {i.pk for i in items}
        if missing:
            raise OrganizeError("One or more inbox items are invalid or not in inbox.")
        return items
    items = list(qs[:MAX_BATCH_ITEMS])
    assert_batch_size_ok(len(items))
    return items


def _build_organize_context(
    user,
    items: list[InboxItem],
) -> dict[str, Any]:
    """Snapshot for AI: inbox rows plus existing areas and projects."""
    base: dict[str, Any] = {
        "items": [{"id": i.pk, "body": i.body} for i in items],
        "areas": [
            {"id": a.pk, "name": a.name}
            for a in Area.objects.filter(user=user).order_by("sort_order", "name")
        ],
        "projects": [
            {
                "id": p.pk,
                "name": p.name,
                "area_id": p.area_id,
                "area_name": p.area.name if p.area_id else None,
                "client_name": p.client_name or None,
            }
            for p in Project.objects.filter(user=user).select_related("area").order_by(
                "name"
            )
        ],
    }
    return base


def _resolve_area(user, plan_item: PlanItem) -> Area | None:
    raw = (plan_item.area_name or "").strip()
    if not raw:
        return None
    name = raw[:255]
    area, _ = Area.objects.get_or_create(
        user=user,
        name=name,
        defaults={"sort_order": 0},
    )
    return area


def _validate_plan_coverage(session: AiOrganizeSession, plan: FinalizePhaseResponse) -> None:
    expected = set(session.inbox_items.values_list("pk", flat=True))
    got = {p.inbox_item_id for p in plan.plan_items}
    if expected != got:
        raise InferenceError("Plan must include every inbox item exactly once.")


def _apply_plan_items(user, plan_items: list[PlanItem]) -> None:
    for pi in plan_items:
        inbox = InboxItem.objects.get(pk=pi.inbox_item_id, user=user)
        title = (pi.task_title or inbox.body or "")[:500]
        body = inbox.body
        if pi.action_type == "quick_task":
            Task.objects.create(
                user=user,
                project=None,
                title=title,
                body=body,
                source_inbox_item=inbox,
            )
        elif pi.action_type == "new_project":
            area = _resolve_area(user, pi)
            name = (pi.new_project_name or "Untitled")[:255]
            defaults: dict[str, Any] = {"client_name": (pi.client_name or "")[:255]}
            if area is not None:
                defaults["area"] = area
            proj, _ = Project.objects.get_or_create(
                user=user,
                name=name,
                defaults=defaults,
            )
            update_fields: list[str] = []
            if pi.client_name and not proj.client_name:
                proj.client_name = (pi.client_name or "")[:255]
                update_fields.append("client_name")
            if area is not None and proj.area_id != area.pk:
                proj.area = area
                update_fields.append("area")
            if update_fields:
                proj.save(update_fields=update_fields)
            Task.objects.create(
                user=user,
                project=proj,
                title=title,
                body=body,
                source_inbox_item=inbox,
            )
        elif pi.action_type == "existing_project":
            area = _resolve_area(user, pi)
            pname = (pi.project_name or "Untitled")[:255]
            defaults = {"client_name": (pi.client_name or "")[:255]}
            if area is not None:
                defaults["area"] = area
            proj, _ = Project.objects.get_or_create(
                user=user,
                name=pname,
                defaults=defaults,
            )
            update_fields: list[str] = []
            if pi.client_name and not proj.client_name:
                proj.client_name = (pi.client_name or "")[:255]
                update_fields.append("client_name")
            if area is not None and proj.area_id != area.pk:
                proj.area = area
                update_fields.append("area")
            if update_fields:
                proj.save(update_fields=update_fields)
            Task.objects.create(
                user=user,
                project=proj,
                title=title,
                body=body,
                source_inbox_item=inbox,
            )
        inbox.status = InboxItemStatus.SORTED
        inbox.save(update_fields=["status", "updated_at"])


def get_organize_session(user, session_id: int) -> AiOrganizeSession:
    try:
        return AiOrganizeSession.objects.get(pk=session_id, user=user)
    except AiOrganizeSession.DoesNotExist as e:
        raise OrganizeError("Organize session not found.") from e


def session_to_dto(session: AiOrganizeSession) -> dict[str, Any]:
    return {
        "session_id": session.pk,
        "state": session.state,
        "context_snapshot": session.context_snapshot,
        "clarifications": session.clarifications,
        "proposed_plan": session.proposed_plan,
        "error_detail": session.error_detail or None,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


def start_organize_session(
    user,
    inbox_item_ids: list[int] | None = None,
) -> AiOrganizeSession:
    assert_can_complete_organize(user)
    items = _select_items(user, inbox_item_ids)
    if inbox_item_ids is not None and len(inbox_item_ids) == 0:
        raise NoInboxItems("No inbox item ids provided.")
    if not items:
        raise NoInboxItems("No inbox items available to organize.")

    session = AiOrganizeSession.objects.create(
        user=user,
        state=AiOrganizeSessionState.ANALYZING,
    )
    session.inbox_items.set(items)
    _lock_items(items)

    context = _build_organize_context(user, items)
    session.context_snapshot = context

    try:
        analyzed = inference.analyze_batch(context)
    except Exception as exc:
        session.state = AiOrganizeSessionState.FAILED
        session.error_detail = str(exc)[:2000]
        session.save()
        _unlock_session_items(session)
        if isinstance(exc, InferenceError):
            raise
        raise InferenceError(str(exc)) from exc

    if analyzed.needs_clarification:
        if not analyzed.questions:
            session.state = AiOrganizeSessionState.FAILED
            session.error_detail = "Model requested clarification but sent no questions."
            session.save()
            _unlock_session_items(session)
            raise InferenceError(session.error_detail)
        session.state = AiOrganizeSessionState.AWAITING_CLARIFICATION
        session.clarifications = {
            "questions": [q.model_dump() for q in analyzed.questions],
            "answers": {},
        }
        session.proposed_plan = {}
    else:
        if not analyzed.plan_items:
            session.state = AiOrganizeSessionState.FAILED
            session.error_detail = "Model returned no plan items."
            session.save()
            _unlock_session_items(session)
            raise InferenceError(session.error_detail)
        partial = FinalizePhaseResponse(plan_items=analyzed.plan_items)
        _validate_plan_coverage(session, partial)
        session.state = AiOrganizeSessionState.AWAITING_REVIEW
        session.proposed_plan = {
            "plan_items": [p.model_dump() for p in analyzed.plan_items],
        }
        session.clarifications = {}

    session.save()
    return session


def submit_clarifications(
    user,
    session_id: int,
    answers: dict[str, str],
) -> AiOrganizeSession:
    session = get_organize_session(user, session_id)
    if session.state != AiOrganizeSessionState.AWAITING_CLARIFICATION:
        raise InvalidState("Session is not awaiting clarification.")

    questions_raw = session.clarifications.get("questions") or []
    qids = {str(q["question_id"]) for q in questions_raw}
    answer_keys = {str(k) for k in answers.keys()}
    missing = qids - answer_keys
    if missing:
        raise OrganizeError(f"Missing answers for questions: {sorted(missing)}")

    merged = dict(session.clarifications)
    merged["answers"] = {str(k): str(v) for k, v in answers.items()}
    session.clarifications = merged
    session.save(update_fields=["clarifications", "updated_at"])

    ctx = {
        **session.context_snapshot,
        "questions": merged.get("questions", []),
        "answers": merged["answers"],
    }

    try:
        finalized = inference.finalize_plan(ctx)
    except Exception as exc:
        session.state = AiOrganizeSessionState.FAILED
        session.error_detail = str(exc)[:2000]
        session.save()
        _unlock_session_items(session)
        if isinstance(exc, InferenceError):
            raise
        raise InferenceError(str(exc)) from exc

    _validate_plan_coverage(session, finalized)
    session.proposed_plan = {"plan_items": [p.model_dump() for p in finalized.plan_items]}
    session.state = AiOrganizeSessionState.AWAITING_REVIEW
    session.save()
    return session


def approve_organize(user, session_id: int) -> AiOrganizeSession:
    session = get_organize_session(user, session_id)
    if session.state == AiOrganizeSessionState.COMPLETED:
        return session
    if session.state != AiOrganizeSessionState.AWAITING_REVIEW:
        raise InvalidState("Session is not awaiting review.")

    assert_can_complete_organize(user)

    raw_items = (session.proposed_plan or {}).get("plan_items") or []
    plan_items = [PlanItem.model_validate(x) for x in raw_items]
    partial = FinalizePhaseResponse(plan_items=plan_items)
    _validate_plan_coverage(session, partial)

    with transaction.atomic():
        _apply_plan_items(user, plan_items)
        session.state = AiOrganizeSessionState.COMPLETED
        session.save()
        AiOrganizeUsage.objects.create(
            user=user,
            session=session,
            completed_at=timezone.now(),
        )
    return session


def cancel_organize(user, session_id: int) -> AiOrganizeSession:
    session = get_organize_session(user, session_id)
    if session.state in (
        AiOrganizeSessionState.COMPLETED,
        AiOrganizeSessionState.CANCELLED,
    ):
        return session
    session.state = AiOrganizeSessionState.CANCELLED
    session.save()
    _unlock_session_items(session)
    return session
