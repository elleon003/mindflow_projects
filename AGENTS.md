# AGENTS.md

Guidance for AI coding agents and humans working on this repository. Prefer reading actual code and configs over this file when they disagree.

**Virtual environment:** Activate the project virtualenv **before every Python-related command** (`python`, `pip`, `python -m pip`, `manage.py`, tests, formatters/linters that run on this codebase, etc.). The system interpreter may not have dependencies installed. Example: `source .venv/bin/activate` from the repo root (use your actual venv path if different).

## Project overview

**MindFlow Projects** (working name) is an ADHD-oriented project and planning product; product intent is documented in `docs/PRD.md`. The Django app **`mindflow`** implements domain logic and a **django-ninja** HTTP API described in code as an inbox capture/sort workflow (e.g. `MindFlow API`, organize session endpoints in `mindflow/api.py`). There is no root `README.md`; use `docs/PRD.md` for product terminology and the `mindflow/` and `config/` packages for what is implemented today.

## Stack

| Layer | Details |
|--------|---------|
| **Python** | `3.12.3` (`.python-version`) |
| **Django** | `~=6.0.4` (`requirements.txt`) |
| **Key Python libraries** | `environs`, `dj-database-url`, `django-tailwind`, `whitenoise`, `django-two-factor-auth` (+ `django_otp`), `django-unfold`, `django-ninja`, `httpx` |
| **Dev-only** | `requirements-dev.txt`: includes `-r requirements.txt`, `pip-review`, `django-debug-toolbar`, `django-browser-reload`, `honcho` |
| **Frontend build** | Node tooling under `theme/static_src/` — `tailwindcss` and `@tailwindcss/postcss` `^4.1.16`, `daisyui` `^5.3.10`, `postcss` `^8.5.6`, `postcss-cli` `^11.0.1`, plus `cross-env`, `rimraf`, etc. (`theme/static_src/package.json`) |

## Layout

| Area | Location |
|------|-----------|
| **Django project** | `config/` — `settings/` (`base`, `development`, `production`, loaded via `config/settings/__init__.py`), `urls.py`, `wsgi.py`, custom `AdminConfig` |
| **Domain app** | `mindflow/` — models, services, `api.py` (Ninja), tests `mindflow/test_*.py`, `tests.py` |
| **Tailwind theme app** | `theme/` — `TAILWIND_APP_NAME = 'theme'` in settings |
| **Templates** | `theme/templates/` (also `APP_DIRS` for app templates) |
| **Static assets** | Built CSS output under `theme/static/`; source and npm scripts in `theme/static_src/` |
| **Collected static** | `staticfiles/` (production); `media/` for uploads |
| **Local DB (dev)** | SQLite at `db.sqlite3` (development settings) |
| **Docs** | `docs/` (e.g. `PRD.md`) |

## Environment

- **Template**: copy from `.env.example` to `.env` at the repo root. Loading is via **`environs`**: `env.read_env()` in `config/settings/__init__.py`, then `DJANGO_ENV` selects **`production`** (`config/settings/production.py`) vs default **`development`** (`config/settings/development.py`).
- **Critical variables (names only)**  
  - **Core**: `DJANGO_ENV`, `SECRET_KEY`, `DEBUG`, `TIME_ZONE`, `ALLOWED_HOSTS`, `INTERNAL_IPS`  
  - **Production DB**: `DATABASE_URL`, `DATABASE_SSL_REQUIRE`  
  - **Production security / cookies**: `USE_X_FORWARDED_HOST`, `CSRF_TRUSTED_ORIGINS`, `CSRF_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`, `CSRF_COOKIE_SAMESITE`, `SECURE_REFERRER_POLICY`, `X_FRAME_OPTIONS`  
  - **Production email**: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL`, `EMAIL_ADMIN`  
  - **AI inference** (OpenAI-compatible HTTP): `AI_INFERENCE_BASE_URL`, `AI_MODEL_ID`, `AI_REQUEST_TIMEOUT_SECONDS`, `AI_MAX_TOKENS`, `AI_API_KEY` — see `config/settings/base.py` for defaults and comments (e.g. local Ollama `/v1`).

Do not commit real secrets; keep them in `.env` (gitignored).

## Common commands

From the repository root, **with the virtualenv activated**:

```bash
pip install -r requirements.txt -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

**Tailwind / DaisyUI** — from `theme/static_src/`:

```bash
npm install
npm run dev      # watch: postcss rebuild to theme/static/css/dist/styles.css
npm run build    # clean + production minified CSS
```

Optional **django-tailwind** dev process (see `Procfile.tailwind`): with venv activated, `python manage.py tailwind start` alongside `runserver`.

## Agent skills

Project-specific Cursor skills live under **`.cursor/skills/`** (each folder has a `SKILL.md`):

| Skill | When to use |
|-------|-------------|
| **`python`** | Python conventions, deps, layout (`mindflow/`, `config/`), tests naming, `environs` |
| **`django`** | Django 6.x settings split, Ninja API, Unfold admin, 2FA, Tailwind theme app, WhiteNoise |
| **`tailwind`** | Tailwind v4 pipeline, `theme/static_src/src/styles.css`, PostCSS scripts, `@source` scanning |
| **`daisyui`** | DaisyUI v5 plugins/themes in `styles.css`, component classes in templates |

There is also **`django-textchoices-pyright`** for TextChoices typing patterns when relevant.

## Testing

There is **no** `pytest.ini` or `pyproject.toml` test runner in this repo. Tests live under **`mindflow/`** (`test_organize_api.py`, `test_rate_limits.py`, plus `tests.py`). With the virtualenv activated, run:

```bash
python manage.py test
```

`manage.py` sets `NINJA_SKIP_REGISTRY=true` when the command is `test`, so django-ninja registry behavior matches the test client.

## Credentials and external services

- **Database**: production uses `DATABASE_URL` (PostgreSQL via `dj-database-url`). Development uses SQLite (`db.sqlite3`).
- **SMTP**: production email variables listed above.
- **AI**: configurable via `AI_*` env vars; optional `AI_API_KEY` for backends that require it. Point `AI_INFERENCE_BASE_URL` at any OpenAI-compatible server (comments in `base.py` mention Ollama, TGI, vLLM).
