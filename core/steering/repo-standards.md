# Repo standards

Conventions for how a repository is laid out, named, versioned in source
control, and reviewed. These rules apply to any project in the target stacks
(Python 3.12+ and TypeScript on Node.js 20+, AWS serverless-first). They are
tool-neutral — they describe the repo, not any AI dev tool or CI platform.
Security, CI/CD, and API conventions live in their own files; do not restate
them here.

## Repo structure

A repo SHOULD start from the following layout and add only what it needs:

```
<repo-root>/
├── README.md          Landing page. What this is, how to run it, where to look next.
├── docs/              Human-facing documentation.
├── scripts/           Repo tooling (lint, validate, render, local dev helpers).
├── tests/             Automated tests, mirroring the source tree where practical.
└── <source dirs>/     Language- or service-specific source (e.g. src/, lib/, services/).
```

Rules:

- `README.md` MUST live at the repo root. It is the single landing page.
- `docs/` holds anything longer than a README section. Do not scatter
  architecture notes across random directories.
- `scripts/` holds repo-level tooling that a contributor runs locally
  (validators, formatters, assembly scripts). Scripts MUST be safe to run
  from a fresh clone.
- `tests/` holds automated tests. A test file MUST mirror the path of the
  source it covers where the language ecosystem allows it.
- A file or directory that does not fit the layout above is a finding.
  Split it into one of these locations before adding further content.

## Naming conventions

- **Directories:** `kebab-case` (`aws-serverless-api/`, `event-handlers/`).
  No spaces, no underscores, no mixed case.
- **Documentation and Markdown files:** `kebab-case` (`repo-standards.md`,
  `getting-started.md`).
- **Configuration files:** use the ecosystem's conventional name and case
  (`pyproject.toml`, `package.json`, `tsconfig.json`, `.pre-commit-config.yaml`).
- **Python modules and packages:** `snake_case` (`event_router.py`,
  `user_service/`). Test files are prefixed `test_` (`test_event_router.py`).
- **TypeScript and JavaScript source files:** `kebab-case` for modules and
  files (`event-router.ts`, `user-service.ts`). Co-located test files use
  the `.test.ts` / `.test.tsx` suffix.
- **Exported symbols:** follow the language's idiom.
  `PascalCase` for classes and TypeScript types, `camelCase` for
  TypeScript functions and variables, `snake_case` for Python functions
  and variables, `UPPER_SNAKE_CASE` for constants in both.
- **Environment variables:** `UPPER_SNAKE_CASE` (`API_BASE_URL`,
  `LOG_LEVEL`). Never hardcode a value a deployment would vary — read it
  from an env var.

## One file, one job

Every source file, script, and document MUST have a single, narrow subject.

- When a file grows a second distinct responsibility, split it before
  adding further content to either responsibility.
- Prefer several small, focused files over one large file that does
  "most of a subsystem". Reviewers and AI tools both read small files
  more reliably than long ones.
- A filename SHOULD make the single job obvious. `event-router.ts` routes
  events. `parse-config.py` parses config. If a name needs "and" or "misc"
  to describe what it does, split the file.

## Commit messages

Commits are part of the audit trail. Write them for the next reviewer, not
for yourself.

- Use the **imperative mood** in the subject line:
  `Add retry policy to event handler`, not `Added…` or `Adds…`.
- Keep the subject **under ~70 characters** and free of trailing punctuation.
- If the change needs explanation, add a blank line and a body. The body
  explains **what** changed and **why**, not **how** — the diff shows how.
- One logical change per commit. A commit that touches unrelated concerns
  is two commits waiting to happen.
- Reference issue or ticket IDs in the body (or a trailer), not in the
  subject line.

Example:

```
Add retry policy to event handler

The handler previously dropped events on transient DynamoDB throttling.
Add a bounded exponential backoff with a dead-letter fallback after
three attempts so upstream producers do not need to retry.
```

## Branch conventions

- `main` is the default branch and is always releasable.
- Work happens on **short-lived feature branches** cut from `main` and
  merged back within days, not weeks. Long-running forks are a smell —
  rebase onto `main` frequently or split the work.
- Branch names are `kebab-case` and scoped to one change
  (`add-retry-policy`, `fix-cold-start-logging`). Optional prefixes
  (`feat/`, `fix/`, `chore/`) are fine if the team agrees; do not require
  them.
- Do not commit directly to `main`. Changes land via pull request.
- Delete branches after merge. Stale branches hide the real state of work.

## Code review expectations

Pull requests are the primary unit of review.

- Keep PRs **small**. A PR SHOULD be reviewable in under 30 minutes. If it
  isn't, split it.
- **One logical change per PR.** A PR that fixes a bug and refactors an
  unrelated module is two PRs.
- The PR description MUST state:
  - What changed (one or two sentences).
  - Why it changed (the problem it solves).
  - How it was tested or verified.
  - **Explicit acceptance criteria** the reviewer can check — the
    conditions under which the PR is correct and complete.
- A PR MUST pass required checks (tests, linters, security scans) before
  merge. A failing check blocks merge; do not merge around it.
- Reviewers focus on correctness, clarity, and scope. Style issues
  belong to the linter, not the reviewer.
- At least one reviewer other than the author MUST approve before merge.
  Self-merge is reserved for emergency fixes and is documented after the
  fact.
- Squash or rebase on merge to keep `main` history linear and readable.
  Never force-push to `main` or to someone else's branch.
