"""Django Ninja HTTP API for inbox organize workflow."""

from __future__ import annotations

from ninja import NinjaAPI, Schema
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
