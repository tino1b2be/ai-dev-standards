---
inclusion: always
---

# Structure

_This is a template. Copy it to your project's `.kiro/steering/structure.md` and replace every placeholder with content specific to your project's layout._

## Top-level layout

_Sketch the top-level directories a new contributor sees when they open the repo. One line each. Replace this placeholder tree with your own._

```
YOUR_PROJECT_ROOT/
├── REPLACE_ME/   Short description of what lives here
├── REPLACE_ME/   Short description of what lives here
├── REPLACE_ME/   Short description of what lives here
└── REPLACE_ME/   Short description of what lives here
```

## Where source code lives

_Name the directory or directories that hold production source, and the conceptual layers inside them. If the project has more than one deployable, describe each one briefly._

Example:

> Source lives under `YOUR_PROJECT_ROOT/REPLACE_ME/`. REPLACE_ME with the layering convention (e.g. domain / application / infrastructure, or feature folders).

## Where tests live

_State whether tests are co-located with source, live in a parallel tree, or both. Name the convention for test file names._

Example:

> Tests live in `YOUR_PROJECT_ROOT/REPLACE_ME/`. Test files follow the pattern `REPLACE_ME` (e.g. `*.test.ts`, `test_*.py`).

## Naming conventions

_List the naming rules that are non-obvious or easy to get wrong. Skip anything the language or framework already enforces._

- Files: REPLACE_ME (e.g. kebab-case, snake_case).
- Modules/packages: REPLACE_ME.
- Public types and exports: REPLACE_ME.

## Import and dependency rules between layers

_State which layers may import which. Keep it to a few rules — the goal is to prevent accidental coupling, not to describe every edge case._

- REPLACE_ME may import from REPLACE_ME.
- REPLACE_ME MUST NOT import from REPLACE_ME.
- Shared code lives in REPLACE_ME and may be imported by any layer.

## One file, one job

_Keep each file focused on a single subject. When a file grows two subjects, split it before adding more content to either._
