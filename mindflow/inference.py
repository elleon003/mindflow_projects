"""HTTP client for local OpenAI-compatible inference (Ollama, TGI, vLLM, etc.)."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

import httpx
from django.conf import settings
from pydantic import BaseModel, ValidationError

from mindflow.exceptions import InferenceError
from mindflow.schemas import AnalyzePhaseResponse, FinalizePhaseResponse

T = TypeVar("T", bound=BaseModel)

JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def extract_json_object(text: str) -> str:
    text = (text or "").strip()
    m = JSON_FENCE.search(text)
    if m:
        return m.group(1).strip()
    return text


def _chat(
    messages: list[dict[str, str]],
    *,
    max_tokens: int | None = None,
) -> str:
    base = settings.AI_INFERENCE_BASE_URL.rstrip("/")
    url = f"{base}/chat/completions"
    timeout = httpx.Timeout(settings.AI_REQUEST_TIMEOUT_SECONDS)
    headers: dict[str, str] = {"Content-Type": "application/json"}
    key = getattr(settings, "AI_API_KEY", "") or ""
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body: dict[str, Any] = {
        "model": settings.AI_MODEL_ID,
        "messages": messages,
        "temperature": 0.2,
    }
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    else:
        body["max_tokens"] = settings.AI_MAX_TOKENS
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=body, headers=headers)
            r.raise_for_status()
    except httpx.HTTPError as e:
        raise InferenceError(f"Inference request failed: {e}") from e
    data = r.json()
    try:
        return str(data["choices"][0]["message"]["content"] or "")
    except (KeyError, IndexError, TypeError) as e:
        raise InferenceError("Unexpected inference response shape") from e


def _parse_model(text: str, model_type: type[T], *, repair: bool) -> T:
    raw = extract_json_object(text)
    try:
        return model_type.model_validate_json(raw)
    except ValidationError as e:
        if not repair:
            raise InferenceError(f"Invalid model JSON: {e}") from e
        fix_messages = [
            {
                "role": "system",
                "content": "You output only valid JSON. Fix the following to match the required schema.",
            },
            {
                "role": "user",
                "content": f"Schema errors: {e!s}\n\nInvalid JSON or text:\n{raw[:8000]}",
            },
        ]
        fixed = _chat(fix_messages)
        raw2 = extract_json_object(fixed)
        try:
            return model_type.model_validate_json(raw2)
        except ValidationError as e2:
            raise InferenceError(f"Invalid model JSON after repair: {e2}") from e2


SYSTEM_ANALYZE = """You are an inbox organizer for a personal productivity app.
Given inbox items (id + text), decide if you need clarifying questions from the user.
If anything is ambiguous (which project, client vs personal, etc.), set needs_clarification true and provide concise questions.
Otherwise set needs_clarification false and fill plan_items directly.

Output ONLY a single JSON object with this shape:
{
  "needs_clarification": boolean,
  "questions": [
    {
      "question_id": string,
      "inbox_item_id": number,
      "prompt": string,
      "kind": "choice" | "text",
      "options": string[]   // only for kind \"choice\"
    }
  ],
  "plan_items": [
    {
      "inbox_item_id": number,
      "action_type": "existing_project" | "new_project" | "quick_task",
      "project_name": string | null,
      "new_project_name": string | null,
      "client_name": string | null,
      "area_name": string | null,
      "task_title": string | null,
      "rationale": string
    }
  ]
}

Context includes "areas" (existing area ids + names) and "projects" (existing projects with optional area_name). Prefer matching area_name to an existing area when appropriate.

Rules:
- action_type existing_project: task ties to an existing project name (project_name).
- new_project: create a project with new_project_name (and optional client_name).
- For existing_project and new_project: optional area_name places the project in that life/work area (reuse a name from areas if it fits, else a short new label).
- quick_task: standalone task; use task_title; project and area fields may be null.
- If needs_clarification is true, plan_items should be an empty array.
- If false, questions should be an empty array and plan_items must cover every inbox item id."""


SYSTEM_FINALIZE = """You are an inbox organizer. The user answered clarifying questions.
Produce the final plan as JSON only:
{
  "plan_items": [
    {
      "inbox_item_id": number,
      "action_type": "existing_project" | "new_project" | "quick_task",
      "project_name": string | null,
      "new_project_name": string | null,
      "client_name": string | null,
      "area_name": string | null,
      "task_title": string | null,
      "rationale": string
    }
  ]
}
Cover every inbox item exactly once. Use area_name when the project belongs to a known area from context or a sensible new area label."""


def analyze_batch(context: dict[str, Any]) -> AnalyzePhaseResponse:
    user_payload = json.dumps(context, ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM_ANALYZE},
        {"role": "user", "content": user_payload},
    ]
    content = _chat(messages)
    return _parse_model(content, AnalyzePhaseResponse, repair=True)


def finalize_plan(context: dict[str, Any]) -> FinalizePhaseResponse:
    user_payload = json.dumps(context, ensure_ascii=False)
    messages = [
        {"role": "system", "content": SYSTEM_FINALIZE},
        {"role": "user", "content": user_payload},
    ]
    content = _chat(messages)
    return _parse_model(content, FinalizePhaseResponse, repair=True)
