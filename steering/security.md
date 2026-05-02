---
inclusion: always
---

# Security standards

Treat secrets and real deployment values as first-class. Code, docs, and specs
in this repo are public-by-default, so nothing committed should leak an account,
identity, or credential. These rules are prescriptive — follow them exactly.

## Secret handling

- Never commit real secrets. This includes API keys, tokens, passwords,
  session cookies, TLS private keys, SSH private keys, and database credentials.
- Load runtime secrets from environment variables or a secret manager. Never
  hardcode them in source, config, or sample commands.
- Use a secret scanner on every commit (for example a git-leaks–style tool
  wired into pre-commit and CI). A scan failure blocks the commit.
- If a secret is ever committed, rotate it immediately, then remove it from
  history. Rotation comes first; history rewrites do not replace rotation.
- Do not paste real secrets into issues, pull request descriptions, code
  review comments, or chat transcripts attached to the repo.

## Placeholder conventions

Every deployment-specific value in a committed file MUST be a placeholder.
Use these exact tokens so scanners and reviewers can recognize them:

- `YOUR_ACCOUNT_ID` for any AWS account ID a consumer must fill in.
- `000000000000` as the sentinel 12-digit account ID inside example ARNs
  or anywhere a numeric shape is required. Scanners treat this value as safe.
- `example.com` for any domain name in URLs, email addresses, or DNS examples.
- `REPLACE_ME` for any other opaque value a consumer must fill in
  (region, bucket name, function name, stack name, user pool ID, etc.).
- `YOUR_GITHUB_USERNAME` for GitHub handles and `github.com/...` URLs.

Example ARN using the sentinel account ID:

```
arn:aws:lambda:us-east-1:000000000000:function:REPLACE_ME
```

Example email and domain:

```
alerts@example.com
https://api.example.com/v1/REPLACE_ME
```

## AWS-oriented sensitive-data rules

Never commit any of the following:

- Real AWS account IDs. A bare 12-digit number other than `000000000000`
  is assumed to be a real account ID.
- ARNs embedding a real account ID. Use `000000000000` in every example ARN.
- AWS access key IDs. These match the shape `AKIA` followed by 16
  uppercase alphanumerics and are always treated as credentials, even if
  claimed to be rotated or revoked.
- AWS secret access keys, session tokens, or pre-signed URLs containing
  signature material.
- Personal email addresses. Use `@example.com` in samples.
- Personal or team-owned domains. Use `example.com` in samples.

If a file needs a realistic-looking identifier for documentation, compose
it from placeholders rather than obfuscating a real value.

## Runtime secrets on AWS

Use managed secret stores for anything a running workload needs:

- **AWS Secrets Manager** for credentials that rotate (database passwords,
  third-party API keys, OAuth client secrets). Enable automatic rotation
  where the source system supports it.
- **AWS SSM Parameter Store** (`SecureString`) for lower-churn configuration
  that still must not be plaintext (signing keys, feature-flag tokens,
  per-stage endpoints that are sensitive).
- Grant each workload read access only to the specific secret or parameter
  path it needs. Never share one broad secret across unrelated services.
- Reference secrets by name or ARN from infrastructure-as-code. Resolve the
  value at runtime inside the workload; do not bake it into a build artifact,
  container image, or Lambda deployment package.
- Do not log secret values. Redact them at the logging boundary.

## Least-privilege IAM

IAM policies MUST follow least privilege. In practice that means:

- Scope every policy to the specific actions a workload performs, not to
  service-wide wildcards. Prefer explicit action lists over `service:*`.
- Scope every policy to the specific resource ARNs it acts on. Prefer
  explicit resource ARNs over `Resource: "*"` whenever the action supports
  resource-level permissions.
- Give each workload its own role. Do not reuse one role across unrelated
  workloads, and do not attach human-user policies to machine roles.
- Prefer short-lived credentials (assumed roles, IAM Identity Center,
  Cognito-issued credentials) over long-lived access keys. Long-lived keys
  for humans or CI should be the exception, justified, and rotated on a
  schedule.
- Review policies when the workload changes. A role that accreted permissions
  over time is a finding, not a feature.

Deeper IAM patterns (condition keys, permission boundaries, SCPs, resource
policies) belong in platform-level guidance, not here.
