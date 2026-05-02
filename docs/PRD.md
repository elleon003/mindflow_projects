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

## MVP Scope

### Core objects

* Areas
* Projects
* Milestones
* Tasks
* Routines
* Time blocks
* Inbox items
* Check-ins / capacity signals

### Core screens

* **Today:** a constrained list of must-do items, suggested next actions, routines due, and scheduled work blocks.
* **Projects:** project cards with progress, health, next milestone, and at-risk indicators.
* **Calendar:** a visual timeline combining events, tasks, and routines.
* **Capture:** frictionless inbox entry for unstructured tasks and ideas.
* **Weekly Reset:** a guided review flow for project health and next-step planning.

### Core task metadata

* Energy required
* Brain space required
* Duration estimate
* Friction level
* Context / mode tags
* First tiny step
* Due date / scheduled date
* Blocked / waiting status

## Prioritization Logic

The first version should use deterministic recommendation rules rather than depending on AI for core functionality. Task suggestions should score items based on urgency, project risk, milestone proximity, available time, energy match, brain-space match, and momentum for already-started work.

Success Criteria

* The user can identify the next best action in under a minute.
* Every active project has a visible next milestone and at least one next action.
* The user can complete a weekly review of all active work in one flow.
* The app reduces reliance on multiple separate systems for project tracking, routines, and daily planning.

## Out of Scope for MVP

Team collaboration, chat, invoicing, document editing, and advanced automations should be excluded from the first release so the product stays focused on clarity, progress visibility, and execution support.

## Suggested Stack

A practical implementation path is Django for core models, Django Ninja for APIs, and a PWA-style frontend, which aligns with the intended technical direction already established for this product concept.