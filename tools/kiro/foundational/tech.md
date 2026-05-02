---
inclusion: always
---

# Tech

_This is a template. Copy it to your project's `.kiro/steering/tech.md` and replace every placeholder with content specific to your stack._

## Languages

_List the languages this project is written in and the versions you target. Keep it to what's actually in use — speculative languages belong elsewhere._

- **YOUR_LANGUAGE** (version REPLACE_ME) — REPLACE_ME with where it's used (e.g. backend services, CLI, build tooling).
- REPLACE_ME

## Runtimes

_Name the runtime(s) code executes on and the version floor you support. Runtime is separate from language — list it here even when obvious._

- **YOUR_RUNTIME** (version REPLACE_ME) — REPLACE_ME with where it runs (e.g. Lambda, containers, browser).
- REPLACE_ME

## Frameworks and key libraries

_Call out the frameworks and libraries a contributor needs to know about before reading the code. Skip transitive dependencies; focus on the ones that shape how code is written._

- **REPLACE_ME** — REPLACE_ME with what it's used for and any notable conventions.
- REPLACE_ME

## Cloud and infrastructure

_Describe the cloud provider, regions, and the shape of the deployment. Include the IaC tool you use so AI-assisted changes stay in that tool._

- **Provider:** REPLACE_ME (e.g. AWS, GCP, Azure, bare metal).
- **IaC:** REPLACE_ME (e.g. AWS CDK in TypeScript, Terraform, Pulumi).
- **Key services:** REPLACE_ME (e.g. Lambda, API Gateway, DynamoDB, S3).

## Data stores

_List every place persistent state lives. Include both primary and auxiliary stores (caches, search indexes, queues treated as state)._

- **REPLACE_ME** — REPLACE_ME with what it stores and why this store was chosen.
- REPLACE_ME

## Build and deploy tooling

_Name the tools that turn source into a running system: package managers, build tools, test runners, CI, and how deploys happen._

- **Package manager:** REPLACE_ME (e.g. `uv`, `npm`, `pnpm`, `poetry`).
- **Build / task runner:** REPLACE_ME (e.g. `make`, `just`, `npm scripts`).
- **Test runner:** REPLACE_ME (e.g. `pytest`, `vitest`).
- **CI:** REPLACE_ME (e.g. GitHub Actions, GitLab CI).
- **Deploy:** REPLACE_ME (e.g. `cdk deploy`, `sam deploy`, container push to REPLACE_ME).

## Conventions

_Capture the tech-stack conventions AI dev tools should respect without being asked. Keep it to a handful of rules; split into a separate steering file if the list grows._

- **Placeholders over real values** in every committed file: `YOUR_ACCOUNT_ID`, `example.com`, `REPLACE_ME`. Never commit real account IDs, ARNs with account numbers, or personal domains.
- **Env vars over hardcoding** for anything environment-specific.
- REPLACE_ME
- REPLACE_ME
