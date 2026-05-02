---
name: django
description: Django architecture and patterns for mindflow_projects — Django 6.x, split settings, django-ninja API, django-tailwind theme app, Unfold admin, two-factor auth, WhiteNoise. Use when changing models, views, URLs, settings, middleware, templates integration, or admin in this repo.
disable-model-invocation: true
---

# Django (this project)

## Versions and docs

- Target **Django ~6.0** per `requirements.txt`. Confirm breaking-change details against current Django docs when editing upgrade-sensitive areas.

## Project shape

| Area | Location |
|------|----------|
| Settings | `config/settings/base.py`, `development.py`, etc. |
| URLConf | `config/urls.py` |
| Domain app | `mindflow/` |
| Tailwind theme app | `theme/` (`TAILWIND_APP_NAME = 'theme'`) |
| Templates dir | `theme/templates/` (see `TEMPLATES` in base settings) |
| Static (theme output) | `theme/static/` via `STATICFILES_DIRS` |

## Installed stack (high level)

- **Admin**: `django-unfold` — `UNFOLD` dict in `config/settings/base.py`.
- **API**: `django-ninja` — see `mindflow/api.py` and URL inclusion from `config/urls.py`.
- **Auth**: `django-two-factor-auth`, `django_otp` — `LOGIN_URL` points at two-factor login.
- **Assets**: `django-tailwind`, app label `theme`; production static files via **WhiteNoise** `CompressedManifestStaticFilesStorage`.

## Practices here

- Add new Django apps under the repo root (same level as `mindflow`), register in `INSTALLED_APPS` in `config/settings/base.py`.
- Keep secrets and environment-specific values in env vars (`environs`), documented in `.env.example`.
- After model changes: `python manage.py makemigrations` / `migrate` from repo root.

## Tailwind + templates

- Compiled CSS is produced by the `theme` app’s npm scripts; templates reference static paths consistent with `STATIC_URL` / theme static layout. For CSS pipeline details, use the **tailwind** and **daisyui** skills in this project.
