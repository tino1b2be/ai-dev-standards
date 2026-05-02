---
inclusion: always
---

# Tech

## Repo content

Markdown, YAML, and JSON. No application runtime. Files here are consumed by AI dev tools, not executed.

## Target stacks the content optimizes for

- **Cloud:** AWS, serverless-first (Lambda, API Gateway, EventBridge, Step Functions, DynamoDB, S3, SQS, SNS, Cognito).
- **IaC:** AWS CDK (TypeScript) and AWS SAM. Terraform where a team already uses it.
- **Languages:** Python 3.12+ and Node.js 20+ (TypeScript preferred for Node).
- **Architecture:** Microservices and event-driven workflows. Prefer managed services over self-hosted.

## Conventions for content authored here

- **Markdown** for steering, specs, and docs. Use front-matter for inclusion rules where the target tool supports it.
- **File references** use the syntax `#[[file:<relative-path>]]` so adapters can resolve them consistently.
- **YAML** for pack manifests and machine-readable metadata. One top-level schema per file.
- **Placeholders** for any deployment-specific value: `YOUR_ACCOUNT_ID`, `example.com`, `REPLACE_ME`. Never commit real account IDs, ARNs with account numbers, domain names you own, or personal identifiers.
- **Env vars over hardcoding** in every snippet that touches a backend.

## Tooling (repo-level)

- **Scripts** under `scripts/` for linting, validating manifests, and rendering canonical content into tool-specific directories.
- **Pre-commit** hooks expected to run secret scanning and front-matter validation.
- **No build step** for `core/`. Adapters under `tools/` may have their own.

## Versioning

Packs and templates are versioned via their manifest. Breaking changes to `core/` require bumping dependents.
