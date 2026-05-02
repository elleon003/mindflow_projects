---
name: tailwind
description: Tailwind CSS v4 build pipeline for mindflow_projects using @tailwindcss/postcss, PostCSS CLI, and django-tailwind theme app "theme". Use when editing styles, content scanning, or frontend build scripts for this repo.
disable-model-invocation: true
---

# Tailwind CSS (this project)

## Versions

- **Tailwind v4** and **@tailwindcss/postcss** — see `theme/static_src/package.json`.
- Django integration: `django-tailwind` (~4.4) with `TAILWIND_APP_NAME = 'theme'` in `config/settings/base.py`.

## Entry and config

- **Source stylesheet**: `theme/static_src/src/styles.css`
  - Uses v4-style `@import "tailwindcss";`
  - **Content scanning**: `@source "../../../**/*.{html,py,js}"` — adjust this path if classes in new folders are not picked up.
- **PostCSS**: `theme/static_src/postcss.config.js` — registers `@tailwindcss/postcss`, `postcss-simple-vars`, `postcss-nested`.
- **Output**: production build writes minified CSS to `theme/static/css/dist/styles.css` (see npm `build:tailwind` script).

## npm scripts (run from `theme/static_src/`)

| Script | Purpose |
|--------|---------|
| `npm run dev` | Watch mode: rebuild CSS on change |
| `npm run build` | Clean dist + production Tailwind build |

After changing templates or Python files that embed Tailwind classes, ensure dev watch is running or run a build so the generated CSS includes new utilities.

## DaisyUI

- DaisyUI is loaded from the same `styles.css` via `@plugin` directives. Theme customization lives there — see the **daisyui** skill.

## When unsure

- Tailwind v4 differs from v3 (config file location, `@source`, `@import`). Prefer Context7 or official Tailwind v4 docs over v3 habits.
