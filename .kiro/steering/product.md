---
inclusion: always
---

# Product

## What this repo is

A source-of-truth library of reusable AI-assisted development standards: steering files, spec templates, and pack manifests. Canonical content lives here; tool-specific adapters consume it.

## Who it serves

Engineers building AWS-heavy serverless and microservices projects in Python and Node.js who use AI dev tools to scaffold, spec, and ship faster.

## Primary target

Kiro IDE. Content authored here is rendered into `.kiro/steering/`, `.kiro/specs/`, and related surfaces via adapters under `tools/kiro/`.

## Secondary target

Other AI dev tools (Cursor, Claude Code, Copilot, etc.). Canonical content stays tool-neutral so new adapters can be added without rewriting the source.

## Core principles

- **One source, many tools.** Content is authored once under `core/` and adapted per tool under `tools/`.
- **One file, one job.** Each steering file, template, or pack manifest has a single, narrow purpose.
- **Composable packs.** `packs/` bundle steering, specs, and scaffolding for a specific stack (e.g. `aws-serverless-api-python`) by referencing `core/` — not duplicating it.
- **Portable by default.** Nothing in `core/` should hard-depend on a specific tool's runtime or file format.

## Out of scope

- Runnable application code or deployable infrastructure.
- Tool-specific UI, plugin code, or binary distribution.
- Project-specific secrets, account IDs, or deployment values.
