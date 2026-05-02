# Implementation Plan

## Overview

This plan builds v1 of the `reusable-ai-dev-standards-library` feature: a copy-first library of AI-assisted development standards for Kiro on AWS, organized as a hybrid two-layer content model (`core/` source + `steering/` consumer catalog) with Kiro foundational templates, three pack manifests, and a single Python assembly script. The sources of truth are `.kiro/specs/reusable-ai-dev-standards-library/requirements.md` (R1–R17) and `.kiro/specs/reusable-ai-dev-standards-library/design.md`. Tasks are ordered so scaffolding precedes content, content precedes tooling, tooling precedes packs, packs precede tests, and tests precede docs. Executing top-to-bottom yields a repo that satisfies R17.1–R17.6.

- [x] 1. Scaffold repository layout and project metadata
  - Create the exact top-level directory tree from design.md's "Directory structure" section and seed the minimal tooling files (no empty content Markdown stubs).
  - _Requirements: R1, R2, R3, R10, R17_

  - [x] 1.1 Create the top-level directory tree
    - Create `core/steering/`, `core/platforms/`, `core/application/`, `core/languages/`, `steering/`, `specs/templates/`, `tools/kiro/foundational/`, `packs/aws-serverless-api-python/`, `packs/aws-event-driven-workflow/`, `packs/frontend-web-typescript/`, `scripts/`, `docs/`, and `tests/` if not already present.
    - _Requirements: R1, R2, R3, R6, R10_

  - [x] 1.2 Add `.gitignore`, `LICENSE`, and pre-commit config stub
    - Write a `.gitignore` covering Python caches, venvs, and editor files; add a permissive open-source `LICENSE`; create a placeholder `.pre-commit-config.yaml` with no active hooks yet (hooks are wired in Task 10.3).
    - _Requirements: R17.6_

  - [x] 1.3 Add Python project metadata pinned to v1 dependencies
    - Create `pyproject.toml` (preferred) or `requirements.txt` declaring `python_requires = ">=3.12"` and dependencies limited to `pyyaml` (runtime) and `pytest` (dev). No other deps.
    - _Requirements: R7.5, R12.4, R16.3_

- [x] 2. Author core source content under `core/`
  - One subject per file. Use Placeholders for every deployment-specific value. No `#[[file:...]]` syntax anywhere.
  - _Requirements: R1, R9, R11, R15_

  - [x] 2.1 Write `core/steering/security.md` as tool-neutral Markdown
    - Cover secret handling, Placeholder conventions, and AWS-oriented sensitive-data rules; no Kiro front-matter.
    - _Requirements: R1.1, R1.5, R8.3, R9.1, R15.1_

  - [x] 2.2 Write `core/steering/repo-standards.md` as tool-neutral Markdown
    - Cover repo conventions (naming, structure, review expectations) independent of any AI dev tool.
    - _Requirements: R1.1, R9.1, R15.1_

  - [x] 2.3 Write `core/steering/cicd.md` as tool-neutral Markdown
    - Cover CI/CD expectations (pipelines, required checks, release hygiene) independent of any AI dev tool.
    - _Requirements: R1.1, R9.1, R15.1_

  - [x] 2.4 Write `core/steering/api-standards.md` as tool-neutral Markdown
    - Cover HTTP API conventions (shape, versioning, errors) independent of any AI dev tool.
    - _Requirements: R1.1, R9.1, R15.1_

  - [x] 2.5 Write `core/platforms/aws.md` with minimal inline Kiro front-matter
    - AWS platform guidance (services, boundaries, account hygiene) authored Kiro-ready inline.
    - _Requirements: R1.2, R9.1, R12.1, R15.2_

  - [x] 2.6 Write `core/application/aws-serverless.md` with minimal inline Kiro front-matter
    - Application-level guidance for Lambda + API Gateway + event sources, including Node.js 20+ runtime notes that live at the application layer per R11.4.
    - _Requirements: R1.2, R9.1, R11.2, R11.4, R15.2_

  - [x] 2.7 Write `core/application/frontend-web.md` with minimal inline Kiro front-matter
    - Application-level guidance for TypeScript frontend web projects.
    - _Requirements: R1.2, R9.1, R15.2_

  - [x] 2.8 Write `core/application/microservices.md` with minimal inline Kiro front-matter
    - Application-level guidance for event-driven microservices on AWS.
    - _Requirements: R1.2, R9.1, R15.2_

  - [x] 2.9 Write `core/languages/python.md` with minimal inline Kiro front-matter
    - Python 3.12+ language standards only; no runtime/platform guidance here (runtime lives in `core/platforms/` or `core/application/`).
    - _Requirements: R1.2, R9.1, R11.1, R11.4, R12.4, R15.2_

  - [x] 2.10 Write `core/languages/typescript.md` with minimal inline Kiro front-matter
    - TypeScript language standards only; no Node.js runtime guidance (R11.3 forbids representing Node.js as a language file).
    - _Requirements: R1.2, R9.1, R11.1, R11.3, R12.4, R15.2_

- [x] 3. Author Kiro foundational templates under `tools/kiro/foundational/`
  - Kiro-ready templates with minimal front-matter and clear consumer-customization cues. Physically separate from `core/` and from repo-local `.kiro/steering/`.
  - _Requirements: R3, R4.3, R4.4, R9_

  - [x] 3.1 Write `tools/kiro/foundational/product.md` template
    - Kiro-ready skeleton with customization cues describing what the consumer fills in for their own product.
    - _Requirements: R3.1, R3.2, R3.3, R9.1_

  - [x] 3.2 Write `tools/kiro/foundational/tech.md` template
    - Kiro-ready skeleton with customization cues for the consumer's tech stack.
    - _Requirements: R3.1, R3.2, R3.3, R9.1_

  - [x] 3.3 Write `tools/kiro/foundational/structure.md` template
    - Kiro-ready skeleton with customization cues for the consumer's project structure.
    - _Requirements: R3.1, R3.2, R3.3, R9.1_

- [x] 4. Build the assembly script skeleton and shared utilities
  - Create `scripts/assemble-pack.py` with the CLI, dataclasses, front-matter map, and shared helpers used by every mode. Mode logic lands in Task 5.
  - _Requirements: R7.1, R7.5, R16.3_

  - [x] 4.1 Implement the argparse CLI surface
    - Subcommands: `assemble` (`--pack`, `--target`, `--force`), `validate`, `sync-steering` (`--check`), `scan`, `check-all`; exit `0` on success, non-zero on failure. See design.md "CLI surface".
    - _Requirements: R7.1, R7.4_

  - [x] 4.2 Define the `STEERING_FRONT_MATTER` map with the four v1 entries
    - Exact keys and values from design.md "Source-to-consumer sync (`sync-steering`)": `core/steering/security.md`, `core/steering/repo-standards.md`, `core/steering/cicd.md`, `core/steering/api-standards.md`, each mapped to `"---\ninclusion: always\n---\n"`.
    - _Requirements: R2.2, R14.1, R15.2_

  - [x] 4.3 Implement manifest loader and `Pack_Manifest` dataclass
    - Load `packs/<name>/manifest.yaml`; dataclass fields exactly: `name`, `version`, `description`, `foundational`, `files`. See design.md "Minimal schema".
    - _Requirements: R5.2, R5.5, R5.6_

  - [x] 4.4 Implement basename-collision detector
    - Scan `foundational + files` for duplicate destination basenames; return a structured error naming both source paths. See design.md "Destination layout and basename collisions".
    - _Requirements: R7.3_

  - [x] 4.5 Implement staging-path builder using `secrets.token_hex(4)`
    - Helper returns `<target>/.kiro/steering.partial-<suffix>` as a sibling of the final destination (same filesystem, never `tempfile`). See design.md "No partial writes (stage-and-atomic-move)" step 1.
    - _Requirements: R7.2_

- [x] 5. Implement assembly script modes
  - One sub-task per mode; each writes to the pre-existing utilities from Task 4.
  - _Requirements: R7, R8, R14_

  - [x] 5.1 Implement `validate` mode
    - YAML well-formedness, required fields only (no unknown fields), `name` matches directory, every `foundational`/`files` path exists, no basename collisions; non-zero exit with clear message on any failure. See design.md "Mode: `validate`".
    - _Requirements: R5.2, R5.3, R5.6, R7.3, R7.4_

  - [x] 5.2 Implement `sync-steering` write path
    - For each `core/steering/<topic>.md`, write `steering/<topic>.md` as `front_matter + "\n" + core_bytes` (byte-for-byte). See design.md "Source-to-consumer sync".
    - _Requirements: R2.1, R2.2, R14.1_

  - [x] 5.3 Implement `sync-steering --check`
    - Compute expected content, diff against on-disk `steering/<topic>.md`, exit non-zero listing drifted files; flag extras under `steering/` that have no `core/steering/` counterpart but do not delete during write. See design.md "Mode: `sync-steering`".
    - _Requirements: R14.1_

  - [x] 5.4 Implement `scan` mode with inline sensitive-data regex set
    - Inline ~20 patterns from design.md "Sensitive-data regex set" (AWS ARNs with real account IDs, bare 12-digit account IDs excluding the `000000000000` sentinel, `AKIA…` access keys, plausible personal emails excluding allowlisted hosts, GitHub handles); enumerate via `git ls-files`; on match, print `<file>:<line>: pattern <name>` and exit non-zero.
    - _Requirements: R8.1, R8.2, R8.3, R8.4_

  - [x] 5.5 Implement `assemble` mode with stage-and-atomic-move and rollback
    - Pre-write plan (validate manifest, confirm paths exist, no basename collisions, target dir state vs `--force`); stage into `steering.partial-<suffix>`; commit via the three branches (no-existing, empty-existing, `--force` non-empty with backup + rollback on commit failure); leftover-backup cleanup failure is the only non-fatal warning (exit `0`). See design.md "No partial writes" steps 1–5.
    - _Requirements: R7.2, R7.4_

  - [x] 5.6 Implement `check-all` mode
    - Run `validate`, then `sync-steering --check`, then `scan`; aggregate and exit non-zero on any failure, continuing to report remaining failures where practical. See design.md "Mode: `check-all`".
    - _Requirements: R7.3, R8.1, R14.1_

- [x] 6. Author the three v1 pack manifests
  - Copy each manifest verbatim from design.md's "Concrete v1 manifests" section.
  - _Requirements: R5, R6_

  - [x] 6.1 Write `packs/aws-serverless-api-python/manifest.yaml`
    - Verbatim from design.md; `name: aws-serverless-api-python`, `version: 0.1.0`, foundational triad, plus `steering/security.md`, `steering/api-standards.md`, `core/platforms/aws.md`, `core/application/aws-serverless.md`, `core/languages/python.md`.
    - _Requirements: R5.2, R5.3, R5.5, R5.6, R5.7, R6.1, R6.2_

  - [x] 6.2 Write `packs/aws-event-driven-workflow/manifest.yaml`
    - Verbatim from design.md; foundational triad plus `steering/security.md`, `steering/cicd.md`, `core/platforms/aws.md`, `core/application/microservices.md`, `core/languages/python.md`.
    - _Requirements: R5.2, R5.3, R5.5, R5.6, R5.7, R6.1, R6.2_

  - [x] 6.3 Write `packs/frontend-web-typescript/manifest.yaml`
    - Verbatim from design.md; foundational triad plus `steering/security.md`, `steering/api-standards.md`, `core/application/frontend-web.md`, `core/languages/typescript.md`.
    - _Requirements: R5.2, R5.3, R5.5, R5.6, R5.7, R6.1, R6.2_

- [-] 7. Generate and commit the consumer `steering/` catalog
  - Run the newly-implemented sync step and commit its output so GitHub browsers don't need Python to read the catalog.
  - _Requirements: R2, R14_

  - [x] 7.1 Run `sync-steering` to populate `steering/`
    - Execute `python scripts/assemble-pack.py sync-steering`; verify `steering/security.md`, `steering/repo-standards.md`, `steering/cicd.md`, and `steering/api-standards.md` are produced with the expected front-matter + body.
    - _Requirements: R2.1, R2.2, R2.3, R14.1_

  - [ ] 7.2 Commit the generated `steering/` files
    - Stage and commit the four generated files so browse-and-copy works directly on GitHub per design.md "Maintainer-only" note.
    - _Requirements: R2.2, R16.1, R16.2_

- [x] 8. Author reusable spec templates under `specs/templates/`
  - Skeletons only; Placeholders or blank sections for anything project-specific. Not referenced by any pack.
  - _Requirements: R10_

  - [x] 8.1 Write `specs/templates/requirements.md`
    - User-story + EARS-style acceptance-criteria skeleton that guides authors toward clear, testable requirements; no methodology name-dropping.
    - _Requirements: R10.1, R10.2, R10.3_

  - [x] 8.2 Write `specs/templates/design.md`
    - Skeleton with Overview / Structure / Responsibilities / Error handling / Testing sections; Placeholders for project-specific content.
    - _Requirements: R10.1, R10.2_

  - [x] 8.3 Write `specs/templates/tasks.md`
    - Checkbox skeleton matching the shape used in this file (top-level tasks, decimal sub-tasks, `_Requirements:_` traceability lines).
    - _Requirements: R10.1, R10.2_

- [x] 9. Write pytest test suite under `tests/`
  - Plain pytest only. No Hypothesis, no property-based testing, no fuzzing. One test module per concern, ordered to mirror the mode implementations in Task 5.
  - _Requirements: R7, R8, R13.7, R14_

  - [x] 9.1 Write `tests/test_manifest_parsing.py`
    - Cover valid manifest, missing required fields (including missing `files`), unknown fields, and malformed YAML; assert clear error per case. See design.md "Manifest parsing".
    - _Requirements: R5.2, R5.6_

  - [x] 9.2 Write `tests/test_validate.py`
    - Golden manifests pass; broken-manifest fixtures (wrong `name`, missing referenced file, basename collision, unknown field, `files` entry pointing at nonexistent path) each fail with the expected message. See design.md `validate` test bullet.
    - _Requirements: R5.3, R7.3, R7.4_

  - [x] 9.3 Write `tests/test_assemble_success.py`
    - For each v1 pack: assemble into a tmp target, assert resolved basenames and byte-for-byte file contents, assert no `.partial-*`/`.backup-*` residue.
    - _Requirements: R6.1, R7.2, R17.4_

  - [x] 9.4 Write `tests/test_assemble_force.py`
    - Pre-populate `<target>/.kiro/steering/` with fixtures whose basenames differ from the manifest; run `assemble --force`; assert final contents match the manifest exactly and no `.backup-*` residue remains.
    - _Requirements: R7.2, R7.4_

  - [x] 9.5 Write `tests/test_assemble_noforce_rejection.py`
    - Pre-populate non-empty `<target>/.kiro/steering/`; run `assemble` without `--force`; assert non-zero exit, fixture untouched, no staging or backup directories exist.
    - _Requirements: R7.2, R7.4_

  - [x] 9.6 Write `tests/test_assemble_staging_failure.py`
    - Inject a staging-phase I/O failure (monkey-patch `shutil.copy` to raise partway, or remove a source file between validate and copy); assert non-zero exit, consumer fixtures byte-for-byte unchanged, no residue.
    - _Requirements: R7.2, R7.4_

  - [x] 9.7 Write `tests/test_assemble_force_commit_rollback.py`
    - Monkey-patch `os.replace` to raise at commit; run `assemble --force`; assert rollback restored fixtures byte-for-byte, message names both the commit failure and rollback success, and no `.partial-*`/`.backup-*` residue remains.
    - _Requirements: R7.2, R7.4_

  - [x] 9.8 Write `tests/test_assemble_force_double_fault.py`
    - Monkey-patch both `os.replace` (commit) and the rollback `os.rename` to raise; assert the backup directory survives with original fixtures byte-for-byte and the error message names the backup path plus manual-recovery instructions.
    - _Requirements: R7.2, R7.4_

  - [x] 9.9 Write `tests/test_sync_steering.py`
    - Given a `core/steering/<topic>.md` and a `STEERING_FRONT_MATTER` entry, assert the generated `steering/<topic>.md` is byte-for-byte equal to `front_matter + "\n" + core_bytes`.
    - _Requirements: R2.2, R14.1_

  - [x] 9.10 Write `tests/test_sync_steering_check.py`
    - Assert `sync-steering --check` exits `0` when in sync and exits non-zero with a drifted-file list when any `steering/<topic>.md` differs from its expected content.
    - _Requirements: R14.1_

  - [x] 9.11 Write `tests/test_scan.py`
    - Known-bad strings (real-looking 12-digit account IDs, `AKIA…` keys, plausible personal emails, real ARN shapes) match; Placeholders (`YOUR_ACCOUNT_ID`, `000000000000`, `example.com`, `REPLACE_ME`) do not.
    - _Requirements: R8.1, R8.2, R8.3, R8.4_

- [x] 10. Wire smoke tests, CI, and pre-commit
  - Convert the unit suite into an end-to-end guarantee that `check-all` + per-pack assemble both work on the actual repo.
  - _Requirements: R7, R8, R14, R17_

  - [x] 10.1 Write per-pack smoke tests
    - One test per v1 pack: run `assemble --pack <name> --target <tmpdir>`, assert exit `0` and expected basenames under `<tmpdir>/.kiro/steering/`. Cover all three v1 packs.
    - _Requirements: R6.1, R7.2, R17.4_

  - [x] 10.2 Add a minimal CI workflow
    - Create `.github/workflows/ci.yml` (or equivalent) that installs `pyyaml`+`pytest`, runs `python scripts/assemble-pack.py check-all`, then runs the pytest suite. Python 3.12+.
    - _Requirements: R7.1, R8.1, R14.1, R17.4, R17.5_

  - [x] 10.3 Wire `check-all` into pre-commit
    - Fill in `.pre-commit-config.yaml` with a local hook that runs `python scripts/assemble-pack.py check-all` on push/commit; leave hook repo minimal and dependency-free.
    - _Requirements: R8.1, R14.1_

- [x] 11. Author top-level documentation
  - The two files a new contributor needs to consume the Repo per R17.6.
  - _Requirements: R17.6_

  - [x] 11.1 Write `README.md` landing page
    - Describe the copy-first workflow; point at `steering/` for browse-and-copy; list the three v1 packs; include the one-liner `python scripts/assemble-pack.py assemble --pack <name> --target <dir>`; link to `docs/philosophy.md`.
    - _Requirements: R16.1, R16.2, R17.6_

  - [x] 11.2 Write `docs/philosophy.md`
    - Explain the hybrid two-layer model (`core/` source + `steering/` consumer) and the one-file-one-job rule; link back to `README.md`.
    - _Requirements: R9.1, R17.6_

  - [x] 11.3 Add a `CONTRIBUTING.md`
    - Optional contributor guide covering branch/PR conventions and how to run `check-all` locally.
    - _Requirements: R17.6_

  - [x] 11.4 Add a `Makefile` convenience wrapper
    - Optional Makefile exposing `make check`, `make test`, `make sync` as thin wrappers around `assemble-pack.py` and `pytest`. Does not replace direct script invocation.
    - _Requirements: R7.1_

- [x] 12. Verify v1 acceptance
  - Final verification walk against R17.1–R17.6 and the green-build gate.
  - _Requirements: R17_

  - [x] 12.1 Run `check-all` locally and assert exit 0
    - Execute `python scripts/assemble-pack.py check-all` on the repo working tree; confirm exit `0`.
    - _Requirements: R17.4, R17.5_

  - [x] 12.2 Run the full pytest suite and assert green
    - Execute `pytest tests/` (or `pytest`) and confirm all tests pass.
    - _Requirements: R17.4_

  - [x] 12.3 Walk through R17.1–R17.6 against the repo state
    - For each of R17.1 (core organized), R17.2 (foundational triad present), R17.3 (three valid pack manifests), R17.4 (assemble + validate succeed), R17.5 (scan clean), R17.6 (README + docs sufficient for a new contributor), confirm the criterion is met; record any gap as a defect before cutting v1.
    - _Requirements: R17.1, R17.2, R17.3, R17.4, R17.5, R17.6_

## Notes

- Tasks marked with `*` are optional and can be skipped without affecting v1 acceptance.
- Every leaf task carries a `_Requirements:_` line mapping it back to requirements.md.
- No property-based testing tasks, no Hypothesis, no fuzzing per R13.7 and design.md's testing strategy. Plain pytest only.
- No adapter framework, rendering pipeline, or cross-file reference resolver appears anywhere in this plan.
- This plan does not touch this Repo's own `.kiro/steering/` (Repo_Local_Steering) per R4.
