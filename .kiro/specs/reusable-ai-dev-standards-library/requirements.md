# Requirements Document

## Introduction

This Repo is a small library of reusable AI-assisted development standards for engineers who use Kiro on AWS-heavy projects. It is content, not a runnable application: Markdown files and a handful of lightweight YAML manifests.

The v1 consumer experience is copy-first. A user browses a short, user-facing catalog of ready-to-copy steering files and either copies individual files directly into their project's `.kiro/steering/`, or picks a pack that names the right combination of files for a given stack and assembles them into place with one small script.

The Repo uses a hybrid two-layer content model:

- A maintainer-facing **source layer** under `core/` is the reusable source of truth. It is organized by subject (`core/steering/`, `core/platforms/`, `core/application/`, `core/languages/`). Consumers are not required to read or understand `core/` to use the Repo.
- A user-facing **consumer layer** under `steering/` is the ready-to-copy catalog. Each file in `steering/` is in Kiro-ready shape and can be copied directly into a consumer's `.kiro/steering/` with no transformation. The headline example is copying `steering/security.md` into a project's `.kiro/steering/security.md`.

Kiro's foundational steering triad — `product.md`, `tech.md`, `structure.md` — lives under `tools/kiro/foundational/` as Kiro-specific templates a consumer copies and customizes.

Packs are lightweight YAML manifests that name a combination of Kiro foundational files and reusable content files to use together for a stack. v1 ships exactly three packs: `aws-serverless-api-python`, `aws-event-driven-workflow`, and `frontend-web-typescript`. A single Python assembly script assembles a pack into a target directory and validates every manifest.

v1 scope is intentionally narrow: AWS only, Kiro only, Python 3.12+ and JavaScript/TypeScript only, Node.js 20+ as the JS/TS backend runtime. There is no adapter framework, no rendering pipeline, no cross-file reference syntax, and no plugin system.

## Glossary

- **Repo**: This repository.
- **Source_Content**: Maintainer-facing reusable content under `core/`. Not required reading for consumers.
- **Core_File**: A single Markdown file under `core/` that covers exactly one subject.
- **Consumer_Steering**: The user-facing ready-to-copy catalog under `steering/`.
- **Steering_File**: An individual Kiro-ready Markdown file under `steering/`.
- **Kiro_Foundational_File**: A file under `tools/kiro/foundational/` (e.g., `product.md`, `tech.md`, `structure.md`) intended as a Kiro-specific foundational template for consumers to copy and customize.
- **Pack**: A directory under `packs/<pack-name>/` that contains a single manifest naming the files belonging together for a stack.
- **Pack_Manifest**: The YAML manifest inside a Pack at `packs/<pack-name>/manifest.yaml`.
- **Assembly_Script**: The single-purpose Python script at `scripts/assemble-pack.py` that assembles a Pack and validates Pack_Manifests.
- **Repo_Local_Steering**: This Repo's own `.kiro/steering/` directory. It steers AI-assisted development of this Repo itself and is not part of any user-facing catalog.
- **Spec_Template**: A skeleton Markdown document under `specs/templates/` used to start a new feature spec.
- **Placeholder**: A clearly fake deployment value such as `YOUR_ACCOUNT_ID`, `example.com`, or `REPLACE_ME`.

## Requirements

### Requirement 1: Source content under `core/`

**User Story:** As a maintainer, I want a single maintainer-facing source-of-truth layer organized by subject, so that reusable content has one home and consumers never have to understand my internal organization to use the Repo.

#### Acceptance Criteria

1. THE Repo SHALL maintain Source_Content as Markdown files under `core/`.
2. THE Repo SHALL organize `core/` into the subdirectories `core/steering/`, `core/platforms/`, `core/application/`, and `core/languages/`.
3. THE Repo SHALL author each Core_File so it covers exactly one subject.
4. THE Repo SHALL NOT require a consumer to read or understand `core/` in order to consume Consumer_Steering or a Pack.
5. WHERE a Core_File contains deployment-specific values, THE Repo SHALL express those values as Placeholders.

### Requirement 2: Consumer-facing steering under `steering/`

**User Story:** As a consumer, I want a user-facing directory of ready-to-copy steering files, so that I can copy files directly into my project's `.kiro/steering/` without reading about the Repo's internal structure.

#### Acceptance Criteria

1. THE Repo SHALL maintain a top-level `steering/` directory containing Kiro-ready Steering_Files.
2. THE Repo SHALL author each Steering_File so a consumer can copy it unchanged into their project's `.kiro/steering/` and have Kiro accept it.
3. THE Repo SHALL include at minimum the following Steering_Files in v1: `steering/security.md`, `steering/repo-standards.md`, `steering/cicd.md`, and `steering/api-standards.md`.
4. THE Repo SHALL author each Steering_File so it covers exactly one subject.
5. WHERE a Steering_File contains deployment-specific values, THE Repo SHALL express those values as Placeholders.

### Requirement 3: Kiro foundational files

**User Story:** As a consumer, I want Kiro-specific foundational templates for `product.md`, `tech.md`, and `structure.md`, so that I can copy them into my project's `.kiro/steering/` and customize them to describe my own project.

#### Acceptance Criteria

1. THE Repo SHALL provide three Kiro_Foundational_Files under `tools/kiro/foundational/`: `product.md`, `tech.md`, and `structure.md`.
2. THE Repo SHALL author each Kiro_Foundational_File in Kiro-ready shape so a consumer can copy it unchanged into their project's `.kiro/steering/`.
3. THE Repo SHALL author Kiro_Foundational_Files as templates that a consumer is expected to customize after copying.
4. THE Repo SHALL keep Kiro_Foundational_Files physically separate from Steering_Files under `steering/` and from Core_Files under `core/`.

### Requirement 4: Repo-local steering versus user-facing content

**User Story:** As a maintainer, I want this Repo's own `.kiro/steering/` to steer development of this Repo alone, so that internal guidance never leaks into any user-facing catalog and user-facing content never depends on internal guidance.

#### Acceptance Criteria

1. THE Repo SHALL use Repo_Local_Steering only to steer AI-assisted development of this Repo itself.
2. THE Repo SHALL NOT include any Repo_Local_Steering file in any Pack_Manifest.
3. THE Repo SHALL NOT include any Repo_Local_Steering file in Consumer_Steering or in `tools/kiro/foundational/`.
4. WHERE a foundational filename (`product.md`, `tech.md`, `structure.md`) appears in both Repo_Local_Steering and `tools/kiro/foundational/`, THE Repo SHALL keep the two copies in physically separate directories serving different projects.

### Requirement 5: Packs as lightweight manifests

**User Story:** As a consumer starting a new project, I want each stack to be described by a short YAML manifest that names the files to use together, so that I get a coherent starting set without assembling it by hand.

#### Acceptance Criteria

1. THE Repo SHALL describe every Pack with a single Pack_Manifest at `packs/<pack-name>/manifest.yaml`.
2. THE Pack_Manifest SHALL declare exactly these fields: `name`, `version`, `description`, `foundational`, and `core`.
3. THE `name` field of a Pack_Manifest SHALL equal the Pack directory name.
4. THE `version` field of a Pack_Manifest SHALL be the Pack's own semantic version.
5. THE `foundational` field of a Pack_Manifest SHALL be a list of repo-relative paths to Kiro_Foundational_Files.
6. THE Pack_Manifest SHALL express the list of reusable files as repo-relative paths to files the Assembly_Script will copy.
7. THE Repo SHALL NOT support pack overrides, pack dependencies, per-file version pinning, or cross-file reference syntax in any Pack_Manifest.
8. The core field SHALL be a list of repo-relative paths to Core_Files under core/.

### Requirement 6: v1 Packs

**User Story:** As a maintainer, I want v1 to ship exactly three Packs covering the target stacks, so that the first release is small, complete, and easy to review.

#### Acceptance Criteria

1. THE Repo SHALL ship v1 with exactly three Packs: `aws-serverless-api-python`, `aws-event-driven-workflow`, and `frontend-web-typescript`.
2. THE Repo SHALL provide a valid Pack_Manifest for each of the three v1 Packs.
3. THE Repo SHALL NOT ship any additional Packs in v1.

### Requirement 7: Minimal repo tooling

**User Story:** As a maintainer, I want a single small Python script that assembles a Pack and validates all manifests, so that tooling is trivial to read, run, and trust.

#### Acceptance Criteria

1. THE Repo SHALL provide a single Assembly_Script at `scripts/assemble-pack.py`.
2. WHEN invoked in assemble mode with a Pack name and a target directory, THE Assembly_Script SHALL copy every file named by that Pack_Manifest into the target directory's `.kiro/steering/`.
3. WHEN invoked in validation mode, THE Assembly_Script SHALL validate every Pack_Manifest in the Repo, confirming at minimum that each referenced file exists, that `name` equals the Pack directory name, and that no two referenced files within a Pack collide on destination basename.
4. IF any validation step fails, THEN THE Assembly_Script SHALL exit with a non-zero status and SHALL NOT write any output files.
5. THE Repo SHALL NOT include any rendering pipeline, cross-file reference resolver, adapter framework, or plugin system as part of repo tooling.

### Requirement 8: Sensitive-data policy

**User Story:** As a maintainer who expects this Repo to be public, I want tooling to prevent real deployment values from being committed, so that the Repo stays safe to publish without scrubbing.

#### Acceptance Criteria

1. THE Repo SHALL provide a sensitive-data scan that runs over tracked files.
2. IF the sensitive-data scan finds any match, THEN THE scan SHALL exit with a non-zero status and SHALL identify the offending file and line.
3. THE Repo SHALL express every deployment-specific value in every committed file as a Placeholder.
4. THE Repo SHALL NOT commit real AWS account IDs, resource ARNs that embed real account IDs, real personal email addresses, real personal domain names, or secrets.

### Requirement 9: One file, one subject

**User Story:** As a maintainer, I want every content and manifest file to have a single, narrow subject, so that I can change one piece of guidance without editing unrelated content.

#### Acceptance Criteria

1. THE Repo SHALL author each Core_File, Steering_File, Kiro_Foundational_File, and Pack_Manifest with exactly one top-level subject.
2. WHEN a file grows to cover two distinct subjects, THE maintainer SHALL split the file before adding further content to either subject.

### Requirement 10: Reusable spec templates

**User Story:** As an engineer starting a new feature spec, I want small, consistent skeletons for requirements, design, and tasks documents, so that specs begin in a consistent shape.

#### Acceptance Criteria

1. THE Repo SHALL provide Spec_Templates under `specs/templates/` for requirements, design, and tasks documents.
2. THE Repo SHALL keep Spec_Templates free of project-specific content by using blank sections or Placeholders for anything a consumer must fill in.
3. THE Repo SHALL author the requirements Spec_Template so it guides authors toward clear, testable requirements expressed as user stories with acceptance criteria.
4. THE Repo SHALL NOT reference any Spec_Template from any Pack_Manifest in v1.

### Requirement 11: v1 languages and runtime

**User Story:** As a maintainer, I want v1 language guidance to cover exactly the languages we support and to keep runtime notes out of the language layer, so that each file stays honest about what it describes.

#### Acceptance Criteria

1. THE Repo SHALL ship exactly two v1 language files under `core/languages/`: `python.md` and `typescript.md`.
2. THE Repo SHALL treat Node.js 20+ as the supported JS/TS backend runtime.
3. THE Repo SHALL NOT represent Node.js as a language file under `core/languages/`.
4. THE Repo SHALL place runtime guidance (for example, Lambda packaging, cold-start behavior, event-loop concerns) under `core/platforms/` or `core/application/` where it operationally belongs.

### Requirement 12: v1 scope limits

**User Story:** As a maintainer, I want v1 scope to be small and explicit, so that the first release ships without speculative breadth.

#### Acceptance Criteria

1. THE Repo SHALL limit v1 cloud guidance to AWS.
2. THE Repo SHALL limit v1 AI-dev-tool support to Kiro.
3. THE Repo SHALL limit v1 Packs to the three listed in Requirement 6.
4. THE Repo SHALL limit v1 languages to Python 3.12+ and JavaScript/TypeScript.

### Requirement 13: Explicit out-of-scope items for v1

**User Story:** As a contributor, I want the v1 out-of-scope list to be explicit, so that I do not spend effort on content that does not belong in this release.

#### Acceptance Criteria

1. THE Repo SHALL exclude runnable application code and deployable infrastructure from v1.
2. THE Repo SHALL exclude support for AI dev tools other than Kiro from v1.
3. THE Repo SHALL exclude cloud providers other than AWS from v1.
4. THE Repo SHALL exclude languages other than Python 3.12+ and JavaScript/TypeScript from v1.
5. THE Repo SHALL exclude rendering pipelines, cross-file reference syntax, pack dependencies, pack overrides, per-file version pinning, binary distribution, and plugin SDKs from v1.
6. THE Repo SHALL exclude heavyweight validation mechanisms (for example, schema registries, semantic diff, and content hashing) from v1.
7. THE Repo SHALL NOT require property-based testing as part of v1 acceptance.

### Requirement 14: Low duplication between layers

**User Story:** As a consumer, I want the source and consumer layers to stay in sync, so that a piece of guidance never appears in two drifted versions.

#### Acceptance Criteria

1. WHERE the Repo maintains both `core/<subpath>/<subject>.md` and `steering/<subject>.md` for the same subject, THE Repo SHALL keep the two files in sync.
2. THE Repo SHALL NOT allow the source and consumer layers to express conflicting normative guidance on the same subject.
3. THE Repo SHALL leave the mechanism by which the consumer layer stays in sync with the source layer (manual review, a sync script, or a generator step) as a design decision, not a requirement.

### Requirement 15: Portability

**User Story:** As a future maintainer, I want `core/` to remain tool-neutral where practical so that future non-Kiro consumers can still read it, while allowing Kiro-ready files to carry the minimal Kiro front-matter Kiro expects.

#### Acceptance Criteria

1. THE Repo SHALL author Core_Files as tool-neutral Markdown where practical.
2. THE Repo SHALL permit Kiro-specific front-matter in Steering_Files under `steering/` and in Kiro_Foundational_Files under `tools/kiro/foundational/`.
3. THE Repo SHALL keep Core_Files tool-neutral where practical and SHALL require Kiro-specific front-matter only in Steering_Files under steering/ and in Kiro_Foundational_Files under tools/kiro/foundational/.
4. THE Repo SHALL NOT use any cross-file reference syntax in any Core_File, Steering_File, Kiro_Foundational_File, or Pack_Manifest in v1.

### Requirement 16: No runtime dependencies on AI dev tools

**User Story:** As a consumer, I want to be able to consume the Repo with only `git` and `cp`, so that I am not forced to run an AI dev tool to get value from the content.

#### Acceptance Criteria

1. THE Repo SHALL NOT require any AI dev tool to be installed in order to consume Consumer_Steering, Kiro_Foundational_Files, or Source_Content.
2. THE Repo SHALL allow a consumer to copy Markdown files from `steering/` or `tools/kiro/foundational/` using standard file-copy tools.
3. THE Repo SHALL limit required tooling to Python 3.12+ for the Assembly_Script only, and only for consumers who choose to use Packs.

### Requirement 17: v1 acceptance

**User Story:** As a maintainer, I want a concrete definition of "v1 is good enough", so that I know when to cut the first release.

#### Acceptance Criteria

1. THE Repo SHALL be considered v1-complete WHEN a maintainer-facing source layer exists under `core/` organized as defined in Requirement 1 AND a user-facing consumer layer exists under `steering/` as defined in Requirement 2.
2. THE Repo SHALL be considered v1-complete WHEN `tools/kiro/foundational/` contains `product.md`, `tech.md`, and `structure.md` as defined in Requirement 3.
3. THE Repo SHALL be considered v1-complete WHEN all three v1 Packs exist with valid Pack_Manifests as defined in Requirements 5 and 6.
4. THE Repo SHALL be considered v1-complete WHEN the Assembly_Script can assemble each v1 Pack into a target directory without error AND can validate every Pack_Manifest without error.
5. THE Repo SHALL be considered v1-complete WHEN the sensitive-data scan finds no matches in tracked files.
6. THE Repo SHALL be considered v1-complete WHEN a new contributor can consume the Repo using only the top-level `README.md` and `docs/` without reading any internal architecture document.
