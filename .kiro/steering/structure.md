---
inclusion: always
---

# Structure

## Top-level layout

```
core/        Canonical, tool-neutral source content
docs/        Human-facing docs about this repo
packs/       Opinionated bundles for specific stacks
scripts/     Repo tooling (lint, validate, render)
specs/       Reusable spec templates
tools/       Tool-specific adapters (Kiro, others)
```

## `core/` — the source of truth

```
core/application/   App-level guidance (API design, error handling, logging, testing)
core/languages/     Language standards (python.md, nodejs.md, typescript.md)
core/platforms/     Platform standards (aws-serverless.md, aws-eventing.md, ...)
core/steering/      Foundational steering (product.md, tech.md, structure.md, ...)
```

Rules:
- Every file has one job. Split before it grows two.
- No tool-specific syntax that can't be rendered generically.
- Cross-reference via `#[[file:<relative-path>]]` instead of copy-paste.

## `specs/` — reusable spec templates

```
specs/templates/    Requirements, design, and tasks templates
```

Templates are skeletons. They reference `core/` for standards and leave project-specific sections blank.

## `packs/` — opinionated stack bundles

Each pack is a directory with a manifest describing which `core/` and `specs/` files it includes, plus any pack-specific overrides. Example:

```
packs/aws-serverless-api-python/
packs/aws-event-driven-workflow/
```

A pack **references** canonical files; it does not copy them. Overrides live alongside the manifest and are clearly marked.

## `tools/` — adapters per AI tool

```
tools/kiro/foundational/   Kiro-specific rendering of foundational steering
tools/<other-tool>/        Future adapters
```

Adapters read `core/` + a pack manifest and emit the target tool's expected layout (e.g. `.kiro/steering/`, `.kiro/specs/`). Adapters contain no canonical content.

## `scripts/` and `docs/`

- `scripts/` — validate manifests, lint front-matter, render packs into target tool layouts.
- `docs/` — contributor guide, authoring conventions, pack authoring guide.

## Minimal duplication rule

If content appears in two places, one of them is wrong. Canonical content lives in `core/`; everything else references it.
