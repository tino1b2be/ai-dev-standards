---
inclusion: always
---

# CI/CD standards

Conventions for how code moves from a pull request to production. These rules
are tool-neutral — they describe the pipeline, not any specific CI platform.
Secret handling, repo layout, and API conventions live in their own files; do
not restate them here.

## Pipeline responsibilities

Every pipeline MUST run these stages in order, and a failure at any stage
MUST block the next:

1. **Lint.** Formatters and linters for every language in the repo.
   A lint failure blocks the rest of the pipeline.
2. **Test.** Unit and integration tests. A test failure blocks build.
3. **Build.** Produce the deployable artifact (Lambda bundle, container
   image, static site, etc.). A build failure blocks deploy.
4. **Deploy.** Promote the artifact into an environment behind an
   approval gate appropriate to that environment (see below).

Stages are gates, not suggestions. Do not ship a commit that skipped one.

## Required checks before merge

A pull request MUST NOT merge into the default branch until all of the
following have passed on its head commit:

- All configured linters and formatters.
- The full automated test suite (unit and integration).
- Secret scanning over the diff and the working tree.
- Dependency vulnerability scanning at a severity threshold the team
  agreed on (for example, fail on `HIGH` and above).
- Manifest and schema validation for any machine-readable file the repo
  ships (IaC templates, OpenAPI specs, pack manifests, Dockerfiles).
- Build of every deployable artifact the PR affects.

Required checks are configured at the branch-protection layer, not as
a convention reviewers remember. A green local run is not a substitute
for a green CI run.

## Release hygiene

Releases MUST be traceable from a version number back to the exact code
that produced the artifact.

- Use **semantic versioning** (`MAJOR.MINOR.PATCH`) for any package,
  library, or pack the repo publishes.
- Every release MUST be cut from a **signed, immutable Git tag**
  (`vREPLACE_ME`, for example `v1.4.0`). Tags are never moved or deleted.
- Every release MUST update a **changelog** (`CHANGELOG.md` or equivalent)
  that lists user-visible changes grouped by type (added, changed, fixed,
  removed, security). An entry MUST reference the tag and the commit range.
- Every release MUST have a **documented rollback plan** stating how to
  revert to the previous known-good version and how long that takes. "Run
  the pipeline again on the previous tag" is an acceptable plan; "we'll
  figure it out" is not.
- Hotfixes follow the same pipeline and tagging rules as normal releases.
  Bypassing the pipeline for a hotfix is a finding, not a shortcut.

## Environment promotion

Code MUST flow through environments in order:

```
dev → staging → prod
```

Rules:

- **dev** deploys automatically on merge to the default branch. No
  human approval is required.
- **staging** deploys automatically after dev passes its post-deploy
  checks (smoke tests, health checks, synthetic probes). staging MUST
  mirror prod in configuration shape; it MAY use smaller capacity.
- **prod** deploys only after an **explicit human approval gate** on
  the same artifact that passed staging. The approver MUST be someone
  other than the commit author.
- A deploy that fails its post-deploy checks in any environment MUST
  block promotion to the next. Do not promote a red deploy by hand.

## Deployment atomicity

A deploy is **all-or-nothing per service**.

- A service either fully deploys the new version or stays fully on the
  previous version. No partial rollouts, no half-migrated fleets left
  in place after the pipeline exits.
- If a deploy fails mid-flight, the pipeline MUST roll the service back
  to the previous version before reporting success or failure to the
  caller. A service left in a mixed state is a failed deploy, even if
  some instances came up.
- Canary and blue/green strategies are allowed, but the shift itself
  MUST complete or revert within the deploy job. Long-lived canaries
  that outlive the pipeline are a separate, explicitly-managed feature
  flag, not a deploy state.
- Multi-service coordinated releases MUST be decomposed into independent
  per-service deploys. Do not design a pipeline that requires two
  services to deploy in the same transaction.

## Build artifact immutability

Build **once**, promote the **same artifact** through every environment.

- The artifact produced at the build stage MUST be identified by an
  immutable identifier (content hash, image digest, or versioned object
  key such as `s3://REPLACE_ME/REPLACE_ME/vREPLACE_ME.zip`).
- dev, staging, and prod MUST deploy the **same** artifact identifier.
  Environment differences are expressed through configuration
  (environment variables, parameter store values, IaC parameters) —
  never by rebuilding per environment.
- Rebuilding an artifact per environment is a finding. It breaks the
  promise that staging tested what prod will run.
- Artifacts MUST be stored in an immutable registry (container registry
  with tag immutability enabled, versioned S3 bucket, package registry).
  Do not overwrite an existing artifact identifier.

## Observability before traffic

A deploy is not complete until the new version is **observable**.

Before the pipeline routes traffic to a new version, the following MUST
be in place:

- **Structured logs** shipping to the central log destination, with the
  service name, version, and request/correlation ID on every line.
- **Metrics** for request rate, error rate, and latency (or the
  equivalents for non-request workloads such as queue consumers) flowing
  to the metrics backend.
- **Alarms** configured against those metrics, with a documented owner
  and on-call route. An alarm with no route is not an alarm.
- **Health checks** or synthetic probes that the deploy stage actually
  waits on before declaring success.

A deploy that completes without logs, metrics, and alarms in place MUST
be treated as a failed deploy and rolled back.
