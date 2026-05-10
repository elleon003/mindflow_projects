"""Django Ninja HTTP API for inbox organize workflow."""

from __future__ import annotations

from ninja import Field, NinjaAPI, Query, Schema
from ninja.errors import HttpError
from ninja.security import SessionAuth

from mindflow.exceptions import (
    BatchTooLarge,
    InferenceError,
    InvalidState,
    NoInboxItems,
    OrganizeError,
    RateLimitExceeded,
)
from mindflow.models import InboxItem, InboxItemStatus
from mindflow.services.organize import (
    approve_organize,
    cancel_organize,
    get_organize_session,
    session_to_dto,
    start_organize_session,
    submit_clarifications,
)

session_auth = SessionAuth()

api = NinjaAPI(
    title="MindFlow API",
    version="1.0.0",
    description="Capture/sort AI backend (session auth).",
    urls_namespace="mindflow_api",
)


class StartOrganizeIn(Schema):
    inbox_item_ids: list[int] | None = None


class ClarifyIn(Schema):
    answers: dict[str, str]


class OrganizeSessionOut(Schema):
    session_id: int
    state: str
    context_snapshot: dict
    clarifications: dict
    proposed_plan: dict
    error_detail: str | None = None
    created_at: str
    updated_at: str


class InboxItemCreateIn(Schema):
    body: str = Field(..., min_length=1)


class InboxItemPatchIn(Schema):
    status: str = Field(
        ...,
        description="Only 'discarded' is supported (from in_inbox).",
    )


class InboxItemOut(Schema):
    id: int
    body: str
    status: str
    created_at: str
    updated_at: str


def _inbox_to_out(item: InboxItem) -> InboxItemOut:
    return InboxItemOut(
        id=item.pk,
        body=item.body,
        status=item.status,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )


def _organize_http(exc: Exception) -> HttpError:
    if isinstance(exc, RateLimitExceeded):
        return HttpError(429, str(exc))
    if isinstance(exc, BatchTooLarge):
        return HttpError(400, str(exc))
    if isinstance(exc, NoInboxItems):
        return HttpError(400, str(exc))
    if isinstance(exc, InvalidState):
        return HttpError(409, str(exc))
    if isinstance(exc, InferenceError):
        return HttpError(502, str(exc))
    if isinstance(exc, OrganizeError):
        return HttpError(400, str(exc))
    return HttpError(500, str(exc))


@api.post(
    "/organize/start",
    response=OrganizeSessionOut,
    auth=session_auth,
    tags=["organize"],
)
def organize_start(request, payload: StartOrganizeIn):
    try:
        session = start_organize_session(request.user, payload.inbox_item_ids)
        return session_to_dto(session)
    except Exception as exc:
        raise _organize_http(exc) from exc


@api.get(
    "/inbox",
    response=list[InboxItemOut],
    auth=session_auth,
    tags=["inbox"],
)
def inbox_list(request, include_locked: bool = Query(False)):
    """List inbox rows. Default: `in_inbox` only (same pool as organize)."""
    qs = InboxItem.objects.filter(user=request.user)
    if include_locked:
        qs = qs.filter(
            status__in=[
                InboxItemStatus.IN_INBOX,
                InboxItemStatus.LOCKED_FOR_AI,
            ]
        )
    else:
        qs = qs.filter(status=InboxItemStatus.IN_INBOX)
    qs = qs.order_by("created_at")
    return [_inbox_to_out(i) for i in qs]


@api.post(
    "/inbox",
    response=InboxItemOut,
    auth=session_auth,
    tags=["inbox"],
)
def inbox_create(request, payload: InboxItemCreateIn):
    body = payload.body.strip()
    if not body:
        raise HttpError(400, "Body cannot be empty.")
    item = InboxItem.objects.create(user=request.user, body=body)
    return _inbox_to_out(item)


@api.patch(
    "/inbox/{item_id}",
    response=InboxItemOut,
    auth=session_auth,
    tags=["inbox"],
)
def inbox_patch(request, item_id: int, payload: InboxItemPatchIn):
    item = InboxItem.objects.filter(pk=item_id, user=request.user).first()
    if item is None:
        raise HttpError(404, "Inbox item not found.")

    if payload.status != InboxItemStatus.DISCARDED:
        raise HttpError(400, "Only status 'discarded' is supported.")

    if item.status != InboxItemStatus.IN_INBOX:
        raise HttpError(
            409,
            "Only items still in the inbox can be discarded.",
        )

    item.status = InboxItemStatus.DISCARDED
    item.save(update_fields=["status", "updated_at"])
    return _inbox_to_out(item)


@api.get(
    "/organize/{session_id}",
    response=OrganizeSessionOut,
    auth=session_auth,
    tags=["organize"],
)
def organize_get(request, session_id: int):
    try:
        session = get_organize_session(request.user, session_id)
        return session_to_dto(session)
    except Exception as exc:
        raise _organize_http(exc) from exc


@api.post(
    "/organize/{session_id}/clarify",
    response=OrganizeSessionOut,
    auth=session_auth,
    tags=["organize"],
)
def organize_clarify(request, session_id: int, payload: ClarifyIn):
    try:
        session = submit_clarifications(request.user, session_id, payload.answers)
        return session_to_dto(session)
    except Exception as exc:
        raise _organize_http(exc) from exc


@api.post(
    "/organize/{session_id}/approve",
    response=OrganizeSessionOut,
    auth=session_auth,
    tags=["organize"],
)
def organize_approve(request, session_id: int):
    try:
        session = approve_organize(request.user, session_id)
        return session_to_dto(session)
    except Exception as exc:
        raise _organize_http(exc) from exc


@api.post(
    "/organize/{session_id}/cancel",
    response=OrganizeSessionOut,
    auth=session_auth,
    tags=["organize"],
)
def organize_cancel(request, session_id: int):
    try:
        session = cancel_organize(request.user, session_id)
        return session_to_dto(session)
    except Exception as exc:
        raise _organize_http(exc) from exc
