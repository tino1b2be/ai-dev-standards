# Philosophy

This Repo is content, not an application. Its job is to make a set of AI-assisted development standards easy to browse, copy, and assemble — without forcing consumers to learn an internal architecture.

## Hybrid two-layer content model

Content lives in two layers with clearly separate audiences.

### `core/` — maintainer-facing source of truth

Everything normative is authored once under `core/`, organized by subject:

- `core/steering/` — cross-cutting topics (security, CI/CD, API standards, repo standards).
- `core/platforms/` — platform guidance (e.g., AWS).
- `core/application/` — application-level guidance (serverless, microservices, frontend-web).
- `core/languages/` — language standards (Python, TypeScript).

Consumers are not required to read `core/` to use the Repo. It is the source of truth for maintainers and the place new content goes first.

### `steering/` — user-facing ready-to-copy catalog

The `steering/` directory is the consumer-facing mirror of `core/steering/`. Every file is Kiro-ready: minimal front-matter plus the body copied byte-for-byte from its source under `core/steering/`. A consumer can browse the directory on GitHub and copy any file straight into `.kiro/steering/` with no transformation.

Keeping the two layers in sync is a maintainer task, automated by one mode of the assembly script:

```bash
python scripts/assemble-pack.py sync-steering
```

CI runs `sync-steering --check` so drift is caught before merge.

### `tools/kiro/foundational/` — Kiro-specific templates

Kiro's foundational triad — `product.md`, `tech.md`, `structure.md` — lives under `tools/kiro/foundational/` as Kiro-ready templates. A consumer copies them into their own project's `.kiro/steering/` and customizes them to describe that project. They are not generated from `core/`; they are authored directly as templates.

## One file, one job

Every Markdown file and every pack manifest has exactly one top-level subject. When a file starts growing a second subject, split it before adding more content to either. This keeps changes local: updating security guidance never forces edits to CI/CD guidance, and a new language standard lives in its own file rather than buried in a general document.

The same rule applies to pack manifests: each manifest names a coherent combination for one stack, nothing more.

## Why this shape

- **Copy-first is the primary experience.** Most consumers only need `steering/` and `packs/`. The pack assembly script is a convenience on top, not the point.
- **No runtime dependency on an AI dev tool.** `steering/` and `tools/kiro/foundational/` can be consumed with `git` and `cp` alone.
- **Low duplication, high clarity.** Source and consumer layers stay in sync by tooling. If something appears in two places and looks different, one of them is wrong.
- **Small, boring tooling.** One Python script with a handful of modes, stdlib plus `pyyaml`. Easy to read, easy to trust.

See [`README.md`](../README.md) for how to consume the Repo in practice.
