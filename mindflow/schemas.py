"""Pydantic schemas for AI JSON and API payloads."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClarificationQuestion(BaseModel):
    question_id: str = Field(..., min_length=1)
    inbox_item_id: int
    prompt: str
    kind: Literal["choice", "text"] = "text"
    options: list[str] = Field(default_factory=list)


class PlanItem(BaseModel):
    inbox_item_id: int
    action_type: Literal["existing_project", "new_project", "quick_task"]
    project_name: str | None = None
    new_project_name: str | None = None
    client_name: str | None = None
    area_name: str | None = Field(
        default=None,
        description="Place project under this area (reuse name from areas list or create).",
    )
    task_title: str | None = None
    rationale: str = ""


class AnalyzePhaseResponse(BaseModel):
    needs_clarification: bool
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    plan_items: list[PlanItem] = Field(default_factory=list)


class FinalizePhaseResponse(BaseModel):
    plan_items: list[PlanItem] = Field(default_factory=list)
