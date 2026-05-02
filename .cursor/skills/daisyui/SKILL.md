---
name: daisyui
description: DaisyUI v5 usage with Tailwind v4 in mindflow_projects — @plugin directives and custom themes in theme/static_src/src/styles.css. Use when adding or styling UI components with DaisyUI classes or changing themes.
disable-model-invocation: true
---

# DaisyUI (this project)

## Versions

- **DaisyUI 5.x** with **Tailwind CSS 4.x** — see `theme/static_src/package.json`.
- Plugins are declared in CSS (Tailwind v4 style), not only in a legacy `tailwind.config.js`.

## Where it is wired

- **File**: `theme/static_src/src/styles.css`
- After `@import "tailwindcss";`:
  - `@plugin "daisyui";`
  - `@plugin "daisyui/theme" { ... }` blocks define named themes for this app.

## Themes in this repo

- **`django-starter-light`**: `default: true`, light color scheme, OKLCH-based semantic tokens (`--color-base-100`, `--color-primary`, etc.).
- **`django-starter-dark`**: `prefersdark: true`, dark palette.

To add or tweak colors, edit the corresponding `@plugin "daisyui/theme"` block; rebuild CSS (`npm run dev` or `npm run build` from `theme/static_src/`).

## Components and classes

- Use DaisyUI component class names (e.g. `btn`, `card`, `modal`) in Django templates under `theme/templates/` and elsewhere covered by `@source` in `styles.css`.
- Prefer semantic tokens (`primary`, `base-100`, …) aligned with the theme blocks so light/dark stay consistent.

## When unsure

- DaisyUI 5 behavior and class names can differ from v4; verify with current DaisyUI + Tailwind v4 docs (e.g. Context7) when API or class names are ambiguous.
