# Contributing

Thanks for contributing to the reusable-ai-dev-standards-library. This guide covers branches, PRs, local checks, and how to add new content.

## Branches

- Work on short-lived feature branches cut from `main`.
- Name branches for the change, e.g., `add-api-error-envelope-guidance` or `pack/frontend-web-typescript-cicd`.
- Rebase or merge `main` regularly to keep branches small.

## Pull requests

- One logical change per PR. Split unrelated edits into separate PRs.
- Keep PRs small and focused — reviewers should be able to read them end-to-end.
- In the description, link to the spec or issue this change serves and list the acceptance criteria it touches.
- CI runs `check-all` and `pytest`. Both must pass before merge.

## Running checks locally

Install the dev extras once:

```bash
pip install -e ".[dev]"
```

Then:

```bash
# Run the full pytest suite
pytest tests/

# Run every validation the CI does (validate + sync-steering --check + scan)
python scripts/assemble-pack.py check-all
```

Pre-commit wires `check-all` to every commit — install with `pre-commit install` if you want that locally.

## Adding content

### Add a new pack

1. Create `packs/<pack-name>/manifest.yaml` with the five required fields: `name`, `version`, `description`, `foundational`, `files`.
2. The `name` field must equal the directory name.
3. Every path in `foundational` and `files` must be repo-relative and must exist.
4. Run `python scripts/assemble-pack.py validate` to confirm the manifest is good, then `python scripts/assemble-pack.py assemble --pack <pack-name> --target /tmp/try-it` to sanity-check the output.
5. Add a smoke test under `tests/test_smoke_packs.py` for the new pack.

### Add a new core file

1. Put the source under the right subject directory: `core/steering/`, `core/platforms/`, `core/application/`, or `core/languages/`.
2. Files under `core/steering/` are tool-neutral (no front-matter). Files under `core/platforms/`, `core/application/`, and `core/languages/` carry minimal inline Kiro front-matter.
3. Use Placeholders for any deployment-specific value (`YOUR_ACCOUNT_ID`, `example.com`, `REPLACE_ME`). Never commit real account IDs, ARNs, or personal domains.
4. One subject per file. Split before it grows two.

### Update a steering file

The `steering/` directory is generated from `core/steering/`. Do not edit files under `steering/` directly.

1. Edit the corresponding source file under `core/steering/<topic>.md`.
2. Run `python scripts/assemble-pack.py sync-steering` to regenerate `steering/<topic>.md`.
3. Commit both the source change and the regenerated `steering/` file.

If you skip step 2, CI will fail on `sync-steering --check`.
