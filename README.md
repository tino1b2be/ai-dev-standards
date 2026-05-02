# reusable-ai-dev-standards-library

A copy-first library of AI-assisted development standards for engineers using [Kiro](https://kiro.dev) on AWS-heavy projects. The content is Markdown plus a handful of small YAML pack manifests and one Python assembly script. It is not a runnable application — files here are consumed by AI dev tools, not executed.

The library is organized as a hybrid two-layer content model: a maintainer-facing source layer under `core/` and a user-facing ready-to-copy catalog under `steering/`. Most users only ever need `steering/` and `packs/`.

## For consumers

Two paths depending on whether you want individual files or a coherent set for a specific stack.

### Browse and copy

Open [`steering/`](steering/) on GitHub and copy any file straight into your project's `.kiro/steering/` directory. Each file there is already Kiro-ready, with the expected front-matter. No tooling required — `git` and `cp` are enough.

Example:

```bash
cp path/to/ai-dev-standards/steering/security.md my-project/.kiro/steering/security.md
```

Files available in v1:

- `steering/security.md` — secret handling and sensitive-data rules
- `steering/repo-standards.md` — repo conventions (naming, structure, review expectations)
- `steering/cicd.md` — CI/CD pipelines, required checks, release hygiene
- `steering/api-standards.md` — HTTP API shape, versioning, and error conventions

### Pack assembly

If you want a coherent starting set for a specific stack, pick a pack and assemble it with the script:

```bash
python scripts/assemble-pack.py assemble \
  --pack <pack-name> \
  --target <your-project-dir>
```

The script copies every file named by the pack manifest into `<your-project-dir>/.kiro/steering/`. Pass `--force` to replace an existing non-empty `.kiro/steering/` directory.

v1 ships three packs:

- **`aws-serverless-api-python`** — AWS serverless HTTP APIs in Python (Lambda + API Gateway).
- **`aws-event-driven-workflow`** — AWS event-driven microservices (Lambda, EventBridge, Step Functions).
- **`frontend-web-typescript`** — frontend web projects in TypeScript.

Each pack also lists Kiro's foundational triad (`product.md`, `tech.md`, `structure.md`) under [`tools/kiro/foundational/`](tools/kiro/foundational/) so your project starts with template versions you can customize.

## For maintainers

Two conventions matter when working inside this repo:

- **`sync-steering` regenerates `steering/` from `core/steering/`.** Edit `core/steering/<topic>.md`, then run `python scripts/assemble-pack.py sync-steering` so the committed consumer catalog cannot drift from its source. CI runs `sync-steering --check` to catch drift automatically.
- **`check-all` runs every validation in one pass:** `validate` (pack manifests) + `sync-steering --check` (drift) + `scan` (sensitive-data regex set). Run `python scripts/assemble-pack.py check-all` before opening a PR.

Tests live under `tests/`. Run them with `pytest tests/`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch conventions, PR expectations, and how to add a new pack or core file.

## Requirements

- **Browse-and-copy path:** nothing. `git` and `cp` are enough.
- **Pack assembly path:** Python 3.12+ and [PyYAML](https://pyyaml.org/). Install with `pip install pyyaml` or `pip install -e ".[dev]"` for the full dev environment.

## Layout at a glance

```
core/        Maintainer-facing source content, organized by subject
steering/    User-facing ready-to-copy catalog (generated from core/steering/)
tools/       Tool-specific templates (Kiro foundational triad)
packs/       Stack-specific pack manifests
specs/       Reusable spec templates
scripts/     assemble-pack.py — the one small CLI
tests/       pytest suite
docs/        Human-facing docs
```

## Further reading

- [docs/philosophy.md](docs/philosophy.md) — the hybrid two-layer content model and the one-file-one-job rule.
