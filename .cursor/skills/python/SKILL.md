---
name: python
description: Python conventions and tooling for the mindflow_projects Django codebase (dependencies in requirements.txt, app code under mindflow/ and config/). Use when writing or refactoring Python, scripts, tests, or environment handling in this repository.
disable-model-invocation: true
---

# Python (this project)

## Stack reference

- Pin runtime libraries in `requirements.txt`; dev-only extras in `requirements-dev.txt`.
- Prefer matching versions already pinned there before adding new packages.

## Layout

- **Project package**: `config/` — settings (`config/settings/`), URLs, WSGI, custom `AdminConfig`.
- **Domain app**: `mindflow/` — models, views, `api.py` (django-ninja), services, inference helpers.
- **Env**: `environs` reads variables (see `config/settings/base.py` and `.env.example`).

## Conventions

- Use `pathlib.Path` for filesystem paths (`BASE_DIR`-relative patterns in settings).
- Keep service logic in `mindflow/services/` when it grows beyond a single view/API handler.
- Follow existing test layout: `mindflow/test_*.py` alongside the code under test.
- For behavior or APIs not obvious from this repo, verify with current docs (e.g. Context7) rather than assuming.

## Commands

- Run Django management: `python manage.py <command>` from the repository root.
- Install deps: `pip install -r requirements.txt` (and `requirements-dev.txt` for local dev tools).
