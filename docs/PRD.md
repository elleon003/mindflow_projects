# One-Page PRD: ADHD-Friendly Project Manager

## Product

**Working name:** MindFlow Projects

ADHD-Friendly Project Manager is a project-first planning tool for multi-role professionals who need to manage long-running projects, recurring routines, and day-to-day tasks in one place without losing sight of progress or capacity.

## Problem

Traditional task managers are good at storing tasks but weak at helping users see project progress, coordinate recurring responsibilities, and choose work that fits their actual mental capacity in the moment. ADHD-oriented productivity tools and neurodivergent planning apps consistently emphasize reduced overwhelm, visual structure, and easier prioritization, which suggests that a flat to-do list is not enough for this use case.

## Target User

The core user is a neurodivergent, multi-role professional who juggles operational work, client or business work, and personal responsibilities at the same time. This user needs one system that can hold projects, routines, and quick capture while reducing context switching and time-blindness-related planning friction.

## Goal

Help the user answer three questions quickly: what matters now, what is at risk, and what fits the current brain state. The product should create clarity at the project level first, then guide execution at the task and calendar level through visual progress, smart filtering, and lightweight decision support.

## Product Principles

* Projects come first; tasks exist to move projects or routines forward.
* Routines live alongside projects, not buried inside them.
* The system should reduce prioritization overhead, not add another layer of manual sorting.
* Visual planning should be colorful and engaging but still low-clutter and easy to scan.
* The product should support energy-aware work selection and recovery from context switching.

## Primary User Stories

* As a user, I want to see all active projects and their current health so I know where attention is needed.
* As a user, I want recurring routines to be visible next to project work so operational responsibilities do not disappear.
* As a user, I want to choose work based on available time, energy, and brain space so I can make progress even on low-capacity days.
* As a user, I want a fast capture inbox so I can get thoughts out of my head without organizing them immediately.
* As a user, I want a weekly reset view so I can review every active project, spot drift, and schedule next actions.

---

## Implementation status (repository truth)

This section reflects what the **`mindflow`** Django app and **`config`** project actually implement today. If this document disagrees with code, **trust the code** (`mindflow/models.py`, `mindflow/api.py`, `mindflow/services/organize.py`).

### Stack (established)

* **Backend:** Python 3.12, Django 6.x, **django-ninja** HTTP API (`MindFlow API`), session authentication for API routes.
* **Frontend assets:** Tailwind CSS v4 and DaisyUI under the **`theme`** app; templates exist for base layout and two-factor auth flows.
* **Ops:** WhiteNoise, django-unfold admin, django-two-factor-auth, environment config via **environs** (see `.env.example`).
* **Optional AI:** OpenAI-compatible HTTP inference (`AI_*` settings) drives the inbox organize flow—not the future “Today” scoring engine.

### Shipped domain model (minimal)

* **InboxItem** — unstructured capture body; status workflow (in inbox, locked for AI, sorted, discarded).
* **Area** — user-scoped name + optional `sort_order`; groups projects.
* **Project** — name and optional client name; optional **area** (FK); used by organize approve step.
* **Task** — title, body, optional project, optional link to originating inbox item.
* **AiOrganizeSession** — state machine (analyzing, clarification, review, completed, cancelled, failed) with JSON snapshot fields for AI phases.
* **AiOrganizeUsage** — rate-limit accounting for completed organize sessions.

Not yet modeled: milestones, routines, time blocks, check-ins, or rich task metadata (energy, friction, etc.).

### Shipped HTTP API

Session-authenticated **inbox organize** endpoints only: start session, get session, submit clarifications, approve plan, cancel. There is **no** public REST surface yet for listing or creating inbox items, tasks, or projects from a client UI—those records are created via the organize approve path or **Django admin**.

### Shipped product UI

**None** beyond authentication-related templates and theme scaffolding. Day-to-day product screens (Today, Projects, Calendar, Capture, Weekly Reset) are **not** built in templates or views yet.

### Tests

`python manage.py test` runs API tests for organize behavior and rate limits (`mindflow/test_organize_api.py`, `mindflow/test_rate_limits.py`, etc.).

---

## Target MVP (not yet fully implemented)

The sections below describe the **intended** first full product release. Items above describe **current** progress.

### Core objects (target)

* Areas
* Projects (health, progress—not just name)
* Milestones
* Tasks (with metadata below)
* Routines
* Time blocks
* Inbox items (capture + sort)
* Check-ins / capacity signals

### Core screens (target)

* **Today:** a constrained list of must-do items, suggested next actions, routines due, and scheduled work blocks.
* **Projects:** project cards with progress, health, next milestone, and at-risk indicators.
* **Calendar:** a visual timeline combining events, tasks, and routines.
* **Capture:** frictionless inbox entry for unstructured tasks and ideas.
* **Weekly Reset:** a guided review flow for project health and next-step planning.

### Core task metadata (target)

* Energy required
* Brain space required
* Duration estimate
* Friction level
* Context / mode tags
* First tiny step
* Due date / scheduled date
* Blocked / waiting status

---

## Prioritization and intelligence (clarified)

Two different concerns:

1. **Inbox → structure (implemented):** Turning captured inbox rows into tasks and projects uses an **optional, configurable LLM** (OpenAI-compatible HTTP) inside an organize session—clarification questions, proposed plan, user approval. This reduces manual filing for capture; it is not the same subsystem as daily “what to do next.”

2. **Execution order / Today (target):** The **first version of task suggestions for working the list** should use **deterministic recommendation rules** (urgency, project risk, milestone proximity, available time, energy match, brain-space match, momentum). That keeps day-to-day guidance predictable and testable without requiring AI for core functionality.

### Success criteria (target MVP)

* The user can identify the next best action in under a minute.
* Every active project has a visible next milestone and at least one next action.
* The user can complete a weekly review of all active work in one flow.
* The app reduces reliance on multiple separate systems for project tracking, routines, and daily planning.

## Out of Scope for MVP

Team collaboration, chat, invoicing, document editing, and advanced automations should be excluded from the first release so the product stays focused on clarity, progress visibility, and execution support.

## Suggested stack (aligned with repository)

Django for core models, **Django Ninja** for APIs, Tailwind and DaisyUI for styling, and a **web UI** suitable for later PWA-style installation once screens exist. The repo already follows this direction; product templates and client flows still need to be built on top.
