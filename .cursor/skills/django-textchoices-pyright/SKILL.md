---
name: django-textchoices-pyright
description: Resolves basedpyright/Pyright false positives on Django models.TextChoices member lines (tuple not assignable to str) and related model __str__ typing. Use when editing Django CharField TextChoices, seeing reportAssignmentType on value/label pairs, or Inconsistent MRO with str mixin.
disable-model-invocation: true
---

# Django TextChoices and Pyright (basedpyright)

## Problem

Type checkers see `MEMBER = "a", "Label"` as assigning a **tuple** to a member typed as **str** (or flag **Cannot create consistent method ordering** if using `class X(str, models.TextChoices)`).

Django’s metaclass is correct at runtime; the analyzer does not fully model it unless stubs/plugins align.

## Preferred order

1. **django-stubs** in dev dependencies and a Pyright config that loads Django stubs (helps project-wide).
2. **`class Foo(str, models.TextChoices)`** — Django’s documented pattern so members behave as strings; **basedpyright may still report inconsistent MRO**; treat as optional.
3. **Pragmatic suppressions** on each `TextChoices` line (reliable in strict IDE checking):

```python
class InboxItemStatus(models.TextChoices):
    IN_INBOX = "in_inbox", "In inbox"  # pyright: ignore[reportAssignmentType]
```

Use **`reportAssignmentType`** for “tuple not assignable to str” on those assignments.

## Model __str__ return types

If Pyright complains that `__str__` returns `CharField`/`TextField` instead of `str`, coerce:

```python
def __str__(self) -> str:
    return str(self.name)
```

## Do not

- Place skills under `~/.cursor/skills-cursor/` (reserved for Cursor).
- Silence entire files or disable strict checking globally unless the team agrees.
